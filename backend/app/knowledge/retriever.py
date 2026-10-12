
import re
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TranscriptChunk


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
    "for", "from", "had", "has", "have", "he", "her", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "me", "my", "of",
    "on", "or", "our", "she", "so", "that", "the", "their", "them",
    "there", "they", "this", "to", "up", "us", "was", "we", "were",
    "what", "when", "where", "which", "who", "why", "will", "with",
    "you", "your",
}


@dataclass
class RetrievedChunk:
    episode_title: str
    guest: str | None
    episode_date: str | None
    source_file: str
    chunk_index: int
    content: str
    score: float


def tokenize(text: str) -> list[str]:
    """Normalize text into searchable word tokens."""
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [word for word in words if word not in STOP_WORDS and len(word) > 1]


def retrieve_chunks(
    db: Session,
    query: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Rank transcript chunks by lexical relevance to the query."""
    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    query_counts = Counter(query_tokens)
    chunks = db.scalars(
        select(TranscriptChunk).order_by(
            TranscriptChunk.source_file,
            TranscriptChunk.chunk_index,
        )
    ).all()

    scored = []

    for chunk in chunks:
        content_tokens = tokenize(chunk.content)
        if not content_tokens:
            continue

        content_counts = Counter(content_tokens)

        # Give more weight to repeated query terms, while limiting the
        # effect of repeated words inside one passage.
        score = sum(
            min(content_counts[token], 3) * query_count
            for token, query_count in query_counts.items()
        )

        if score > 0:
            scored.append(
                RetrievedChunk(
                    episode_title=chunk.episode_title,
                    guest=chunk.guest,
                    episode_date=chunk.episode_date,
                    source_file=chunk.source_file,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=float(score),
                )
            )

    scored.sort(key=lambda item: (-item.score, item.source_file, item.chunk_index))
    return scored[:max(1, min(top_k, 10))]
