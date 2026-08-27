"""
Gemini Client — thin wrapper around google-generativeai.
Handles:
  - Simple chat completions (no tools)
  - Function-calling chat (Phase 3)
  - Text embeddings (Phase 4 RAG)
"""
from typing import Any, Optional
import google.generativeai as genai

from app.core.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.google_api_key)

# ── Model constants ───────────────────────────────────────────────────────────
CHAT_MODEL = "gemini-2.5-flash"
EMBED_MODEL = "models/embedding-001"

SYSTEM_INSTRUCTION = """You are a conservative, helpful life insurance advisor assistant.

Rules:
1. Never calculate coverage numbers yourself — always call `calculate_coverage` once you have 
   the required profile fields (annual_income, income_replacement_years, total_debt, 
   available_savings, existing_life_insurance). If fields are missing, ask the user for them 
   conversationally, one or two at a time — don't overwhelm with a long form-like list.
2. Never answer policy-specific factual questions (coverage, exclusions, riders, claims process) 
   from your own knowledge — always call `search_policy_documents` first and ground your answer 
   in the returned context. If no relevant context is found, say so honestly.
3. When recommending products, call `recommend_products` — don't invent product names, prices, 
   or insurers.
4. Keep responses concise, plain-language, and free of jargon unless the user asks for detail.
5. Always disclose: "This is educational guidance, not licensed financial advice — verify with 
   a qualified professional."
6. Maintain conversation memory of the client profile across turns within a session.
"""


def get_chat_model(tools: Optional[list] = None) -> genai.GenerativeModel:
    """Return a GenerativeModel instance, optionally with tools bound."""
    return genai.GenerativeModel(
        model_name=CHAT_MODEL,
        system_instruction=SYSTEM_INSTRUCTION,
        tools=tools or [],
    )


def embed_text(text: str) -> list[float]:
    """Embed a single text string using Gemini embedding-001 (768 dims)."""
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


def embed_document_chunk(text: str) -> list[float]:
    """Embed a document chunk (use retrieval_document task type for RAG)."""
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]
