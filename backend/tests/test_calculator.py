"""
Unit tests for the deterministic coverage calculator.
Run: pytest tests/test_calculator.py -v
"""
import pytest
from app.services.calculator import calculate_coverage


class TestCalculateCoverage:

    def test_basic_case(self):
        """Standard middle-income scenario."""
        result = calculate_coverage(
            annual_income=80_000,
            income_replacement_years=10,
            total_debt=150_000,
            available_savings=30_000,
            existing_life_insurance=50_000,
            real_discount_rate=0.02,
        )
        assert result["recommended_coverage"] > 0
        # annuity factor at 2% for 10 years ≈ 8.9826
        assert abs(result["breakdown"]["annuity_factor"] - 8.9826) < 0.001
        assert "discounted_income_replacement" in result["breakdown"]

    def test_zero_discount_rate(self):
        """When rate is 0, discounted income = income * years."""
        result = calculate_coverage(
            annual_income=60_000,
            income_replacement_years=10,
            total_debt=0,
            available_savings=0,
            existing_life_insurance=0,
            real_discount_rate=0.0,
        )
        assert result["breakdown"]["discounted_income_replacement"] == 600_000.0
        assert result["breakdown"]["annuity_factor"] == 10.0

    def test_zero_income_replacement_years(self):
        """0 replacement years → income component is 0, only debt remains."""
        result = calculate_coverage(
            annual_income=100_000,
            income_replacement_years=0,
            total_debt=200_000,
            available_savings=0,
            existing_life_insurance=0,
        )
        assert result["breakdown"]["discounted_income_replacement"] == 0.0
        assert result["recommended_coverage"] == 200_000.0

    def test_coverage_floored_at_zero(self):
        """Assets > (income + debt) → recommended coverage is 0, not negative."""
        result = calculate_coverage(
            annual_income=50_000,
            income_replacement_years=10,
            total_debt=0,
            available_savings=1_000_000,
            existing_life_insurance=500_000,
            real_discount_rate=0.02,
        )
        assert result["recommended_coverage"] == 0.0
        assert result["breakdown"]["raw_before_floor"] < 0

    def test_no_debt_no_savings(self):
        """Pure income-replacement scenario."""
        result = calculate_coverage(
            annual_income=100_000,
            income_replacement_years=10,
            total_debt=0,
            available_savings=0,
            existing_life_insurance=0,
            real_discount_rate=0.02,
        )
        expected = round(100_000 * ((1 - (1.02) ** -10) / 0.02), 2)
        assert result["recommended_coverage"] == expected

    def test_existing_insurance_reduces_coverage(self):
        """Existing coverage reduces recommended amount proportionally."""
        without = calculate_coverage(
            annual_income=80_000, income_replacement_years=10,
            total_debt=100_000, available_savings=0, existing_life_insurance=0,
        )
        with_existing = calculate_coverage(
            annual_income=80_000, income_replacement_years=10,
            total_debt=100_000, available_savings=0, existing_life_insurance=200_000,
        )
        assert with_existing["recommended_coverage"] < without["recommended_coverage"]

    def test_negative_income_raises(self):
        with pytest.raises(ValueError, match="annual_income"):
            calculate_coverage(-1000, 10, 0, 0, 0)

    def test_negative_replacement_years_raises(self):
        with pytest.raises(ValueError, match="income_replacement_years"):
            calculate_coverage(50_000, -1, 0, 0, 0)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="real_discount_rate"):
            calculate_coverage(50_000, 10, 0, 0, 0, real_discount_rate=-0.01)

    def test_return_structure(self):
        """Response always has all required keys."""
        result = calculate_coverage(70_000, 15, 200_000, 10_000, 50_000)
        assert "recommended_coverage" in result
        assert "breakdown" in result
        assert "assumptions" in result
        bd = result["breakdown"]
        assert all(k in bd for k in [
            "discounted_income_replacement", "annuity_factor",
            "total_debt", "assets_offset", "raw_before_floor"
        ])
        assert result["assumptions"]["income_replacement_years"] == 15
