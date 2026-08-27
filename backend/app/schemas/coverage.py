from typing import Optional
from pydantic import BaseModel, Field


class CoverageRequest(BaseModel):
    annual_income: float = Field(..., ge=0, description="Gross annual income")
    income_replacement_years: int = Field(10, ge=0, le=50)
    total_debt: float = Field(0.0, ge=0)
    available_savings: float = Field(0.0, ge=0)
    existing_life_insurance: float = Field(0.0, ge=0)
    real_discount_rate: float = Field(0.02, ge=0, le=0.20)
    currency: Optional[str] = Field("USD", max_length=10)


class CoverageBreakdown(BaseModel):
    discounted_income_replacement: float
    annuity_factor: float
    total_debt: float
    assets_offset: float
    raw_before_floor: float


class CoverageAssumptions(BaseModel):
    income_replacement_years: int
    real_discount_rate: float


class CoverageResponse(BaseModel):
    recommended_coverage: float
    breakdown: CoverageBreakdown
    assumptions: CoverageAssumptions
    currency: str
    disclaimer: str = (
        "This is educational guidance only, not licensed financial advice. "
        "Verify with a qualified professional before making any insurance decisions."
    )
