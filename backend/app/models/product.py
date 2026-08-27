import uuid
from typing import Optional

from sqlalchemy import Numeric, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class InsuranceProduct(Base):
    __tablename__ = "insurance_products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 'term' | 'whole' | 'universal'
    min_coverage: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    max_coverage: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    term_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    premium_estimate: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
