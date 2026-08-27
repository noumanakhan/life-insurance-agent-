import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, unique=True
    )
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    annual_income: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    dependents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_debt: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    available_savings: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    existing_life_insurance: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    income_replacement_years: Mapped[int] = mapped_column(Integer, default=10)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
