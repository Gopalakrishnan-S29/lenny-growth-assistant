from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Artifact, ChatSession

router = APIRouter(prefix="/api/artifacts", tags=["Artifacts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ArtifactCreate(BaseModel):
    session_id: UUID
    title: str = Field(min_length=1, max_length=200)
    artifact_type: Literal["html", "markdown"]
    content: str = Field(min_length=1)


def artifact_response(item: Artifact):
    return {
        "id": str(item.id),
        "session_id": str(item.session_id),
        "title": item.title,
        "artifact_type": item.artifact_type,
        "content": item.content,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.post("")
def create_artifact(payload: ArtifactCreate, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(
        ChatSession.id == payload.session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")

    artifact = Artifact(
        session_id=payload.session_id,
        title=payload.title,
        artifact_type=payload.artifact_type,
        content=payload.content,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact_response(artifact)


@router.get("")
def list_artifacts(
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Artifact)
    if session_id:
        query = query.filter(Artifact.session_id == session_id)

    items = query.order_by(Artifact.created_at.desc()).all()
    return [artifact_response(item) for item in items]


@router.get("/{artifact_id}")
def get_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact_response(artifact)
