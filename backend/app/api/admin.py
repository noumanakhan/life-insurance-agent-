"""
Admin endpoints — document ingestion and management.
Phase 4.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.policy import PolicyDocument
from app.services.rag import ingest_document

router = APIRouter(prefix="/api/admin", tags=["admin"])


class DocumentInfo(BaseModel):
    id: str
    insurer_name: Optional[str]
    title: Optional[str]
    source_url: Optional[str]
    chunk_count: int
    uploaded_at: str


def _require_admin(user_id: str = Depends(get_current_user_id), db: DBSession = Depends(get_db)) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user_id


@router.post("/ingest-document", status_code=status.HTTP_201_CREATED)
async def ingest_document_endpoint(
    file: UploadFile = File(...),
    insurer_name: str = Form(...),
    title: str = Form(...),
    source_url: Optional[str] = Form(None),
    _admin: str = Depends(_require_admin),
    db: DBSession = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    doc = ingest_document(
        db=db,
        pdf_bytes=pdf_bytes,
        insurer_name=insurer_name,
        title=title,
        source_url=source_url,
    )

    return {
        "message": "Document ingested successfully",
        "document_id": str(doc.id),
        "chunk_count": len(doc.chunks),
    }


@router.get("/documents", response_model=list[DocumentInfo])
def list_documents(
    _admin: str = Depends(_require_admin),
    db: DBSession = Depends(get_db),
):
    docs = db.query(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).all()
    return [
        DocumentInfo(
            id=str(d.id),
            insurer_name=d.insurer_name,
            title=d.title,
            source_url=d.source_url,
            chunk_count=len(d.chunks),
            uploaded_at=d.uploaded_at.isoformat(),
        )
        for d in docs
    ]
