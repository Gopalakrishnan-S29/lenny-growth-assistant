
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import ChatSession, Message
from app.db.session import get_db


router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)
    user_id: str | None = Field(default=None, max_length=200)


class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=100000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    message_metadata: dict = Field(
        default_factory=dict,
        validation_alias="message_metadata",
    )
    created_at: datetime


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    user_id: str | None
    created_at: datetime
    updated_at: datetime


class SessionDetail(SessionResponse):
    messages: list[MessageResponse]


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title must not be empty.")

    session = ChatSession(title=title, user_id=payload.user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 100.")
    if offset < 0:
        raise HTTPException(status_code=422, detail="Offset cannot be negative.")

    statement = (
        select(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    statement = (
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    session = db.scalar(statement)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    return session


@router.post(
    "/{session_id}/messages",
    response_model=MessageResponse,
    status_code=201,
)
def add_message(
    session_id: uuid.UUID,
    payload: MessageCreate,
    db: Session = Depends(get_db),
):
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    message = Message(
        session_id=session_id,
        role=payload.role,
        content=payload.content,
    )
    session.updated_at = datetime.now(timezone.utc)

    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    db.delete(session)
    db.commit()
    return Response(status_code=204)
