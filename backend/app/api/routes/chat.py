
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.agents.pi_agent import PiAgent, PiAgentError
from app.db.models import ChatSession, Message
from app.db.session import get_db
from app.knowledge.retriever import retrieve_chunks


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are Lenny's Growth Assistant, a product, startup, and growth advisor
grounded in Lenny's Podcast transcripts.

CORE RULES
- Answer the user's actual question directly.
- Use relevant transcript evidence when it is available.
- Give practical, specific, actionable advice.
- Do not invent quotations, guests, episode titles, or citations.
- Do not attribute a claim to a guest unless the excerpt supports it.
- Distinguish transcript-supported claims from general advice.
- If the retrieved evidence is insufficient, say so.
- Never force unrelated podcast excerpts into an answer.
- Use clear Markdown with useful headings and concise paragraphs.

CITATION RULES
- Cite retrieved excerpts using their exact source labels: [S1], [S2], etc.
- Put citations immediately after the claims they support.
- Never invent author-year citations or source labels.
- Do not imply that retrieved excerpts support claims they do not contain.
- If the evidence is insufficient, acknowledge the limitation.

WRITING QUALITY
- Follow the user's requested format and length.
- Avoid repetition, filler, and unsupported claims.
- Provide concrete examples and actionable takeaways when useful.
"""


# =========================================================
# SHIP 30 FOR 30 WRITING SKILL
# =========================================================

SKILL_PATH = (
    Path(__file__).resolve().parents[2]
    / "agents"
    / "skills"
    / "ship_30_for_30.md"
)


def load_ship30_skill() -> str:
    """Load the dedicated writing skill from disk."""
    try:
        return SKILL_PATH.read_text(encoding="utf-8")
    except OSError:
        logger.exception("Could not load the Ship 30 for 30 skill.")
        return ""


def needs_ship30_skill(message: str) -> bool:
    """Identify requests that should use the writing skill."""
    text = message.lower()

    triggers = (
        "ship 30 for 30",
        "ship30",
        "1250-word essay",
        "1250 word essay",
        "1,250-word essay",
        "1,250 word essay",
        "write an essay",
        "write a newsletter",
        "write a blog post",
        "turn this into an essay",
        "long-form article",
    )

    return any(trigger in text for trigger in triggers)


def build_system_prompt(user_message: str) -> str:
    """Add the writing skill when a request calls for it."""
    prompt = SYSTEM_PROMPT

    if needs_ship30_skill(user_message):
        skill_text = load_ship30_skill()

        if skill_text:
            prompt += (
                "\n\nDEDICATED SHIP 30 FOR 30 WRITING SKILL\n"
                "Follow the instructions below for this writing request.\n\n"
                f"{skill_text}"
            )
        else:
            logger.warning(
                "A Ship 30 for 30 request was received, but its skill "
                "file could not be loaded."
            )

    return prompt


# =========================================================
# GREETING DETECTION
# =========================================================

def is_simple_greeting(message: str) -> bool:
    """
    Recognize greetings that do not need transcript retrieval.

    Questions such as 'hi, how do I find product-market fit?'
    are not treated as simple greetings.
    """
    normalized = re.sub(r"[^\w\s']", "", message.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)

    greetings = {
        "hi",
        "hello",
        "hey",
        "hi there",
        "hello there",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "howdy",
        "good day",
    }

    return normalized in greetings


GREETING_RESPONSE = (
    "Hi! I'm Lenny Growth Assistant. I can help you explore product "
    "strategy, product-market fit, customer research, startup growth, "
    "and lessons from Lenny's Podcast. What would you like to work on?"
)


# =========================================================
# REQUEST AND RESPONSE SCHEMAS
# =========================================================

class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="The user's message.",
    )
    session_id: UUID | None = None
    user_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    user_message_id: str
    assistant_message_id: str
    answer: str
    provider: str
    model: str
    grounded_in_transcripts: bool
    sources: list[dict[str, Any]]


# =========================================================
# TRANSCRIPT RETRIEVAL
# =========================================================

def retrieve_transcript_chunks(
    db: Session,
    query: str,
    limit: int = 5,
):
    """Use the existing ranked transcript retriever."""
    try:
        return retrieve_chunks(
            db=db,
            query=query,
            top_k=limit,
        )
    except Exception as exc:
        logger.exception("Transcript retrieval failed.")
        raise HTTPException(
            status_code=500,
            detail="Transcript retrieval failed. Check backend logs.",
        ) from exc


def build_sources(chunks) -> list[dict[str, Any]]:
    """Convert retrieved chunks into API source objects."""
    sources: list[dict[str, Any]] = []

    for index, chunk in enumerate(chunks, start=1):
        sources.append(
            {
                "source_id": f"S{index}",
                "episode_title": chunk.episode_title,
                "guest": chunk.guest,
                "date": chunk.episode_date,
                "source_filename": chunk.source_file,
                "chunk_index": chunk.chunk_index,
                "excerpt": chunk.content[:1800],
                "score": chunk.score,
            }
        )

    return sources


def build_retrieval_context(
    sources: list[dict[str, Any]],
) -> str:
    """Format transcript excerpts with stable source labels."""
    if not sources:
        return (
            "No transcript excerpts were retrieved. Do not invent podcast "
            "citations. If answering from general knowledge, distinguish "
            "that advice from evidence in Lenny's Podcast."
        )

    sections = []

    for source in sources:
        sections.append(
            f"[{source['source_id']}]\n"
            f"Episode: {source.get('episode_title') or 'Unknown episode'}\n"
            f"Guest: {source.get('guest') or 'Unknown'}\n"
            f"Date: {source.get('date') or 'Unknown'}\n"
            f"Source file: "
            f"{source.get('source_filename') or 'Unknown'}\n"
            f"Relevance score: {source.get('score')}\n"
            f"Transcript excerpt:\n{source['excerpt']}"
        )

    return "\n\n---\n\n".join(sections)


# =========================================================
# DATABASE HELPERS
# =========================================================

def get_or_create_session(
    db: Session,
    session_id: UUID | None,
    user_id: str | None,
) -> ChatSession:
    """Retrieve an existing conversation or create a new one."""
    if session_id is not None:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found.",
            )

        if (
            user_id
            and session.user_id
            and session.user_id != user_id
        ):
            raise HTTPException(
                status_code=403,
                detail="This chat session does not belong to this user.",
            )

        return session

    session = ChatSession(
        id=uuid4(),
        title="New conversation",
        user_id=user_id,
    )

    db.add(session)
    db.flush()

    return session


def persist_message(
    db: Session,
    session_id: UUID,
    role: str,
    content: str,
) -> Message:
    """Create a persisted chat message."""
    record = Message(
        id=uuid4(),
        session_id=session_id,
        role=role,
        content=content,
    )

    db.add(record)
    db.flush()

    return record


# =========================================================
# CHAT ENDPOINT
# =========================================================

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Handle a chat request.

    Simple greetings receive a direct response. Other requests use
    transcript retrieval and the configured Pi Agent.
    """
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    try:
        # 1. Find or create the conversation.
        session = get_or_create_session(
            db=db,
            session_id=request.session_id,
            user_id=request.user_id,
        )

        # 2. Load recent conversation context.
        recent_messages = (
            db.query(Message)
            .filter(Message.session_id == session.id)
            .order_by(Message.created_at.desc())
            .limit(10)
            .all()
        )
        recent_messages.reverse()

        conversation_context = "\n".join(
            f"{item.role.upper()}: {item.content}"
            for item in recent_messages
        )

        # Initialize these values for every request.
        sources: list[dict[str, Any]] = []
        provider = "local"
        model_name = "greeting-handler"

        # 3. Handle simple greetings without retrieving transcripts.
        if is_simple_greeting(user_message):
            answer = GREETING_RESPONSE

        else:
            # 4. Retrieve relevant transcript chunks.
            chunks = retrieve_transcript_chunks(
                db=db,
                query=user_message,
                limit=5,
            )

            sources = build_sources(chunks)
            retrieval_context = build_retrieval_context(sources)

            # 5. Build the model prompt.
            prompt = f"""
RECENT CONVERSATION
{conversation_context or "(No previous messages)"}

RETRIEVED PODCAST EVIDENCE
{retrieval_context}

CURRENT USER QUESTION
{user_message}

RESPONSE REQUIREMENTS
1. Answer the current question directly.
2. Use source labels exactly as provided, such as [S1] and [S2].
3. Cite sources immediately after claims they support.
4. Do not invent quotations, citations, guests, or episode details.
5. If retrieved passages are only partially relevant, explain the limitation.
6. Distinguish general recommendations from transcript-supported claims.
7. Follow any applicable writing-skill instructions.
8. If the user requests an approximately 1,250-word essay, aim for
   1,150–1,350 words, with a hook, central idea, useful sections,
   practical examples, and actionable takeaways.
9. Never claim a specific word count unless it has been checked.
"""

            system_prompt = build_system_prompt(user_message)

            # 6. Generate the answer through the existing Pi Agent.
            agent = PiAgent()

            answer = await agent.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            if not isinstance(answer, str) or not answer.strip():
                raise HTTPException(
                    status_code=502,
                    detail="The AI provider returned an empty response.",
                )

            answer = answer.strip()
            provider = "pi"
            model_name = getattr(
                getattr(agent, "settings", None),
                "ollama_model",
                "llama3.2:latest",
            )

        # 7. Persist the user and assistant messages.
        user_record = persist_message(
            db=db,
            session_id=session.id,
            role="user",
            content=user_message,
        )

        assistant_record = persist_message(
            db=db,
            session_id=session.id,
            role="assistant",
            content=answer,
        )

        # 8. Set a title on the first exchange.
        if session.title == "New conversation":
            session.title = user_message[:80]

        db.commit()

        # 9. Return the answer and source metadata.
        return ChatResponse(
            session_id=str(session.id),
            user_message_id=str(user_record.id),
            assistant_message_id=str(assistant_record.id),
            answer=answer,
            provider=provider,
            model=model_name,
            grounded_in_transcripts=bool(sources),
            sources=sources,
        )

    except HTTPException:
        db.rollback()
        raise

    except PiAgentError as exc:
        db.rollback()
        logger.exception("Pi Agent generation failed.")

        raise HTTPException(
            status_code=503,
            detail=f"Pi Agent generation failed: {exc}",
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception("Chat request failed.")

        raise HTTPException(
            status_code=500,
            detail="The chat request failed. Check the backend logs.",
        ) from exc
