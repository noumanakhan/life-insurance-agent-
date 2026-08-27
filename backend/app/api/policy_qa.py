"""
Policy Q&A endpoint — RAG grounded answers with citations.
Phase 4.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.rag import search_policy
from app.services.gemini_client import get_chat_model

router = APIRouter(prefix="/api", tags=["policy-qa"])

GROUNDED_PROMPT = """You are a precise life insurance policy analyst.

Answer the following question using ONLY the provided policy document context below.
- If the context contains relevant information, answer clearly and cite the document and page number.
- If the context does NOT contain relevant information to answer the question, respond exactly with:
  "I don't have specific information about that in the ingested policy documents. Please refer to the insurer directly."
- Do NOT use your own training knowledge to fill gaps.
- Always end with: "Source: [Document Title], Page [N]" for each piece of information cited.

Context:
{context}

Question: {question}
"""


class PolicyQARequest(BaseModel):
    question: str
    insurer_name: Optional[str] = None


class Citation(BaseModel):
    document: str
    page: Optional[int]
    excerpt: str


class PolicyQAResponse(BaseModel):
    answer: str
    citations: list[Citation]
    disclaimer: str = (
        "This is educational guidance only, not licensed financial advice. "
        "Verify with a qualified professional."
    )


@router.post("/policy-qa", response_model=PolicyQAResponse)
def policy_qa(
    payload: PolicyQARequest,
    _user_id: str = Depends(get_current_user_id),
    db: DBSession = Depends(get_db),
):
    chunks = search_policy(db=db, question=payload.question, insurer_name=payload.insurer_name)

    if not chunks:
        return PolicyQAResponse(
            answer="I don't have specific information about that in the ingested policy documents. Please refer to the insurer directly.",
            citations=[],
        )

    context = "\n\n".join(
        f"[{c['document_title']}, Page {c['page_number']}]\n{c['content']}"
        for c in chunks
    )
    prompt = GROUNDED_PROMPT.format(context=context, question=payload.question)

    model = get_chat_model()  # no tools needed here
    response = model.generate_content(prompt)

    citations = [
        Citation(
            document=c["document_title"] or "Unknown",
            page=c["page_number"],
            excerpt=c["content"][:300],
        )
        for c in chunks
    ]

    return PolicyQAResponse(answer=response.text, citations=citations)
