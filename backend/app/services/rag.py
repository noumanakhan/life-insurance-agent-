"""
RAG Service — document ingestion and semantic retrieval.
Phase 4 implementation.
"""
from __future__ import annotations
import io
import re
from typing import Optional

import pdfplumber
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.policy import PolicyDocument, PolicyChunk
from app.services.gemini_client import embed_document_chunk, embed_text

CHUNK_SIZE = 600       # target characters per chunk
CHUNK_OVERLAP = 100    # overlap between consecutive chunks
TOP_K = 5              # number of chunks to retrieve


def _chunk_text(text_content: str) -> list[str]:
    """Split text into overlapping chunks of ~CHUNK_SIZE characters."""
    text_content = re.sub(r"\s+", " ", text_content).strip()
    chunks = []
    start = 0
    while start < len(text_content):
        end = min(start + CHUNK_SIZE, len(text_content))
        chunks.append(text_content[start:end])
        if end == len(text_content):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def ingest_document(
    db: Session,
    pdf_bytes: bytes,
    insurer_name: str,
    title: str,
    source_url: Optional[str] = None,
) -> PolicyDocument:
    """
    Full ingestion pipeline:
        PDF bytes → extract text → chunk → embed → store in DB
    """
    # 1. Store document metadata
    doc = PolicyDocument(insurer_name=insurer_name, title=title, source_url=source_url)
    db.add(doc)
    db.flush()  # get doc.id without committing

    # 2. Extract text page-by-page
    all_chunks: list[PolicyChunk] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                continue
            for chunk_text in _chunk_text(page_text):
                if not chunk_text.strip():
                    continue
                embedding = embed_document_chunk(chunk_text)
                chunk = PolicyChunk(
                    document_id=doc.id,
                    content=chunk_text,
                    page_number=page_num,
                    embedding=embedding,
                )
                all_chunks.append(chunk)

    db.add_all(all_chunks)
    db.commit()
    db.refresh(doc)
    return doc


def search_policy(
    db: Session,
    question: str,
    insurer_name: Optional[str] = None,
    top_k: int = TOP_K,
) -> list[dict]:
    """
    Embed the question, run cosine similarity search, return top chunks with metadata.
    Returns list of dicts: {content, page_number, document_title, insurer_name, score}
    """
    query_embedding = embed_text(question)
    # Format as pgvector literal
    vec_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"

    filters = ""
    if insurer_name:
        filters = f"AND pd.insurer_name ILIKE :insurer"

    sql = text(f"""
        SELECT
            pc.content,
            pc.page_number,
            pd.title AS document_title,
            pd.insurer_name,
            1 - (pc.embedding <=> :embedding::vector) AS similarity
        FROM policy_chunks pc
        JOIN policy_documents pd ON pd.id = pc.document_id
        WHERE pc.embedding IS NOT NULL
        {filters}
        ORDER BY pc.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    params: dict = {"embedding": vec_literal, "top_k": top_k}
    if insurer_name:
        params["insurer"] = f"%{insurer_name}%"

    rows = db.execute(sql, params).fetchall()
    return [
        {
            "content": row.content,
            "page_number": row.page_number,
            "document_title": row.document_title,
            "insurer_name": row.insurer_name,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
