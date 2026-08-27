"""
Products endpoint — catalog search and seed data.
Phase 5.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.product import InsuranceProduct

router = APIRouter(prefix="/api", tags=["products"])


class ProductResponse(BaseModel):
    id: str
    insurer_name: Optional[str]
    product_name: Optional[str]
    product_type: Optional[str]
    min_coverage: Optional[float]
    max_coverage: Optional[float]
    term_years: Optional[int]
    premium_estimate: Optional[float]
    currency: str
    region: Optional[str]
    description: Optional[str]


@router.get("/products", response_model=list[ProductResponse])
def get_products(
    min_coverage: Optional[float] = Query(None, description="Minimum coverage needed"),
    region: Optional[str] = Query(None),
    currency: str = Query("USD"),
    _user_id: str = Depends(get_current_user_id),
    db: DBSession = Depends(get_db),
):
    query = db.query(InsuranceProduct).filter(InsuranceProduct.currency == currency)

    if min_coverage is not None:
        # Products whose max_coverage >= what the user needs
        query = query.filter(InsuranceProduct.max_coverage >= min_coverage)

    if region:
        query = query.filter(InsuranceProduct.region.ilike(f"%{region}%"))

    products = query.order_by(InsuranceProduct.premium_estimate).limit(10).all()

    return [
        ProductResponse(
            id=str(p.id),
            insurer_name=p.insurer_name,
            product_name=p.product_name,
            product_type=p.product_type,
            min_coverage=float(p.min_coverage) if p.min_coverage else None,
            max_coverage=float(p.max_coverage) if p.max_coverage else None,
            term_years=p.term_years,
            premium_estimate=float(p.premium_estimate) if p.premium_estimate else None,
            currency=p.currency,
            region=p.region,
            description=p.description,
        )
        for p in products
    ]
