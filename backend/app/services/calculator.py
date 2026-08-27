"""
Life Insurance Coverage Calculator
===================================
Deterministic present-value-of-annuity based coverage formula.
Math is NEVER delegated to the LLM — this module is the single source of truth.
"""


def calculate_coverage(
    annual_income: float,
    income_replacement_years: int,
    total_debt: float,
    available_savings: float,
    existing_life_insurance: float,
    real_discount_rate: float = 0.02,
) -> dict:
    """
    Calculate recommended life insurance coverage.

    Formula:
        discounted_income = annual_income * annuity_factor
        annuity_factor    = (1 - (1+r)^-n) / r   [or n when r == 0]
        assets_offset     = available_savings + existing_life_insurance
        recommended       = max(0, discounted_income + total_debt - assets_offset)

    Args:
        annual_income:            Gross annual income in local currency.
        income_replacement_years: Number of years income should be replaced (n).
        total_debt:               All outstanding debt (mortgage, loans, etc.).
        available_savings:        Liquid savings / investments the family can use.
        existing_life_insurance:  Sum of all current life insurance death benefits.
        real_discount_rate:       Real discount rate (default 2 % = 0.02).

    Returns:
        dict with keys:
            - recommended_coverage (float)
            - breakdown (dict)
            - assumptions (dict)
    """
    if annual_income < 0:
        raise ValueError("annual_income must be non-negative")
    if income_replacement_years < 0:
        raise ValueError("income_replacement_years must be non-negative")
    if real_discount_rate < 0:
        raise ValueError("real_discount_rate must be non-negative")

    r = real_discount_rate
    n = income_replacement_years

    if r <= 0 or n == 0:
        annuity_factor = float(n)
        discounted_income = annual_income * n
    else:
        annuity_factor = (1 - (1 + r) ** (-n)) / r
        discounted_income = annual_income * annuity_factor

    assets_offset = available_savings + existing_life_insurance
    raw_recommended = discounted_income + total_debt - assets_offset
    recommended = max(0.0, raw_recommended)

    return {
        "recommended_coverage": round(recommended, 2),
        "breakdown": {
            "discounted_income_replacement": round(discounted_income, 2),
            "annuity_factor": round(annuity_factor, 4),
            "total_debt": round(total_debt, 2),
            "assets_offset": round(-assets_offset, 2),
            "raw_before_floor": round(raw_recommended, 2),
        },
        "assumptions": {
            "income_replacement_years": n,
            "real_discount_rate": r,
        },
    }
