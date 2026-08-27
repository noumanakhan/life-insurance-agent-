from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel


# ── Session ───────────────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Message ───────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    tool_calls_json: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: UUID
    message: str


class ToolCallInfo(BaseModel):
    name: str
    args: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    reply: str
    session_id: UUID
    profile_updated: bool = False
    tool_calls: list[ToolCallInfo] = []


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    session_id: UUID
    age: Optional[int]
    annual_income: Optional[float]
    dependents: Optional[int]
    total_debt: Optional[float]
    available_savings: Optional[float]
    existing_life_insurance: Optional[float]
    income_replacement_years: int
    currency: str

    model_config = {"from_attributes": True}
