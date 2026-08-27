"""
Chat API — session management + Gemini agent with tool-calling.

Covers Phase 2 (basic chat) and Phase 3 (tool calling + profile extraction).
"""
from __future__ import annotations
import json
import uuid
from typing import Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.session import Session as ChatSession, Message
from app.models.profile import ClientProfile
from app.models.product import InsuranceProduct
from app.schemas.chat import (
    ChatRequest, ChatResponse, SessionCreateRequest, SessionResponse,
    MessageResponse, ProfileResponse, ToolCallInfo,
)
from app.services.calculator import calculate_coverage
from app.services.rag import search_policy
from app.services.gemini_client import get_chat_model, SYSTEM_INSTRUCTION

router = APIRouter(prefix="/api", tags=["chat"])

# ── Tool definitions for Gemini function calling ─────────────────────────────

TOOLS = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="calculate_coverage",
                description=(
                    "Calculate recommended life insurance coverage using the client's "
                    "financial profile. Call this once you have annual_income, dependents, "
                    "total_debt, available_savings, and existing_life_insurance."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "annual_income": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Gross annual income"),
                        "income_replacement_years": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Years of income to replace (default 10)"),
                        "total_debt": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Total outstanding debt"),
                        "available_savings": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Available liquid savings"),
                        "existing_life_insurance": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Existing life insurance death benefit"),
                        "real_discount_rate": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Real discount rate (default 0.02)"),
                    },
                    required=["annual_income", "total_debt", "available_savings", "existing_life_insurance"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="search_policy_documents",
                description=(
                    "Search ingested insurance policy documents to answer questions about "
                    "coverage terms, exclusions, riders, or conditions. Always use this "
                    "before answering any policy-specific factual question."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "question": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "insurer_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="Optional insurer to narrow search"),
                    },
                    required=["question"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="recommend_products",
                description=(
                    "Find matching insurance products from the product catalog based on "
                    "required coverage amount, region, and currency."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "min_coverage": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                        "region": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "currency": genai.protos.Schema(type=genai.protos.Type.STRING),
                    },
                    required=["min_coverage"],
                ),
            ),
        ]
    )
]


# ── Tool execution ────────────────────────────────────────────────────────────

def _execute_tool(
    name: str,
    args: dict,
    db: DBSession,
    session_id: uuid.UUID,
) -> tuple[dict, bool]:
    """
    Execute a tool call and return (result_dict, profile_updated).
    """
    profile_updated = False

    if name == "calculate_coverage":
        # Extract and persist profile fields
        _update_profile(db, session_id, args)
        profile_updated = True
        result = calculate_coverage(
            annual_income=float(args.get("annual_income", 0)),
            income_replacement_years=int(args.get("income_replacement_years", 10)),
            total_debt=float(args.get("total_debt", 0)),
            available_savings=float(args.get("available_savings", 0)),
            existing_life_insurance=float(args.get("existing_life_insurance", 0)),
            real_discount_rate=float(args.get("real_discount_rate", 0.02)),
        )
        return result, profile_updated

    elif name == "search_policy_documents":
        chunks = search_policy(
            db=db,
            question=args["question"],
            insurer_name=args.get("insurer_name"),
        )
        if not chunks:
            return {"answer_context": "No relevant policy documents found.", "citations": []}, False
        context_text = "\n\n".join(
            f"[Doc: {c['document_title']}, Page {c['page_number']}]\n{c['content']}"
            for c in chunks
        )
        citations = [
            {"document": c["document_title"], "page": c["page_number"], "excerpt": c["content"][:200]}
            for c in chunks
        ]
        return {"answer_context": context_text, "citations": citations}, False

    elif name == "recommend_products":
        products = (
            db.query(InsuranceProduct)
            .filter(
                InsuranceProduct.min_coverage <= float(args.get("min_coverage", 0)),
            )
            .all()
        )
        if args.get("region"):
            products = [p for p in products if p.region and args["region"].lower() in p.region.lower()]
        if args.get("currency"):
            products = [p for p in products if p.currency == args["currency"]]
        return {
            "products": [
                {
                    "insurer": p.insurer_name,
                    "product": p.product_name,
                    "type": p.product_type,
                    "min_coverage": float(p.min_coverage or 0),
                    "max_coverage": float(p.max_coverage or 0),
                    "term_years": p.term_years,
                    "premium_estimate": float(p.premium_estimate or 0),
                    "currency": p.currency,
                    "description": p.description,
                }
                for p in products[:5]  # cap at 5
            ]
        }, False

    return {"error": f"Unknown tool: {name}"}, False


def _update_profile(db: DBSession, session_id: uuid.UUID, args: dict):
    profile = db.query(ClientProfile).filter(ClientProfile.session_id == session_id).first()
    if not profile:
        profile = ClientProfile(session_id=session_id)
        db.add(profile)
    if "annual_income" in args:
        profile.annual_income = args["annual_income"]
    if "total_debt" in args:
        profile.total_debt = args["total_debt"]
    if "available_savings" in args:
        profile.available_savings = args["available_savings"]
    if "existing_life_insurance" in args:
        profile.existing_life_insurance = args["existing_life_insurance"]
    if "income_replacement_years" in args:
        profile.income_replacement_years = args["income_replacement_years"]
    db.flush()


# ── Session endpoints ─────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: DBSession = Depends(get_db),
):
    session = ChatSession(user_id=uuid.UUID(user_id), title=payload.title or "New Conversation")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: DBSession = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or str(session.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages


@router.get("/sessions/{session_id}/profile", response_model=Optional[ProfileResponse])
def get_profile(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: DBSession = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or str(session.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    profile = db.query(ClientProfile).filter(ClientProfile.session_id == session_id).first()
    return profile


# ── Main chat endpoint ────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: DBSession = Depends(get_db),
):
    # Verify session ownership
    session = db.query(ChatSession).filter(ChatSession.id == payload.session_id).first()
    if not session or str(session.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Persist user message
    user_msg = Message(session_id=session.id, role="user", content=payload.message)
    db.add(user_msg)
    db.flush()

    # Build conversation history for Gemini
    history_rows = (
        db.query(Message)
        .filter(Message.session_id == session.id, Message.role.in_(["user", "assistant"]))
        .order_by(Message.created_at)
        .all()
    )
    # Exclude the message we just inserted (it will be sent as the new message)
    history = [
        {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
        for m in history_rows[:-1]  # last one is the current user message
    ]

    # Call Gemini with function calling tools
    model = get_chat_model(tools=TOOLS)
    chat_session = model.start_chat(history=history)

    tool_calls_info: list[ToolCallInfo] = []
    profile_updated = False
    final_reply = ""

    # Agentic loop: handle multi-step tool calls
    current_message = payload.message
    for _turn in range(5):  # max 5 tool-call rounds
        try:
            response = chat_session.send_message(current_message)
        except Exception as e:
            final_reply = f"I'm having trouble connecting right now. Please try again in a moment. (Error: {type(e).__name__})"
            break

        # Check if Gemini wants to call a tool
        part = response.candidates[0].content.parts[0] if response.candidates else None
        if part and hasattr(part, "function_call") and part.function_call.name:
            fc = part.function_call
            tool_name = fc.name
            tool_args = dict(fc.args)

            tool_result, p_updated = _execute_tool(tool_name, tool_args, db, session.id)
            profile_updated = profile_updated or p_updated

            tool_calls_info.append(ToolCallInfo(name=tool_name, args=tool_args, result=tool_result))

            # Feed tool result back to the model
            current_message = genai.protos.Content(
                parts=[genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=tool_name,
                        response={"result": tool_result},
                    )
                )],
                role="tool",
            )
        else:
            # LLM produced a text response — we're done
            final_reply = response.text
            break

    if not final_reply:
        final_reply = "I've gathered the information. Is there anything else you'd like to know?"

    # Persist assistant reply
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=final_reply,
        tool_calls_json=json.dumps([tc.model_dump() for tc in tool_calls_info]) if tool_calls_info else None,
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        reply=final_reply,
        session_id=session.id,
        profile_updated=profile_updated,
        tool_calls=tool_calls_info,
    )
