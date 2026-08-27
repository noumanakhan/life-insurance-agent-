from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.coverage import CoverageRequest, CoverageResponse
from app.services.calculator import calculate_coverage

router = APIRouter(prefix="/api", tags=["coverage"])


@router.post("/calculate-coverage", response_model=CoverageResponse)
def coverage_endpoint(
    payload: CoverageRequest,
    _user_id: str = Depends(get_current_user_id),
):
    """
    Deterministic coverage calculator.
    Math is computed by the pure Python function — never the LLM.
    """
    result = calculate_coverage(
        annual_income=payload.annual_income,
        income_replacement_years=payload.income_replacement_years,
        total_debt=payload.total_debt,
        available_savings=payload.available_savings,
        existing_life_insurance=payload.existing_life_insurance,
        real_discount_rate=payload.real_discount_rate,
    )

    return CoverageResponse(
        recommended_coverage=result["recommended_coverage"],
        breakdown=result["breakdown"],
        assumptions=result["assumptions"],
        currency=payload.currency or "USD",
    )
