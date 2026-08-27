"""
Seed script — populates insurance_products with sample data.
Run: python seed_products.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.product import InsuranceProduct

SAMPLE_PRODUCTS = [
    # Term Life
    {
        "insurer_name": "SecureLife Insurance Co.",
        "product_name": "SecureLife Term 20",
        "product_type": "term",
        "min_coverage": 100_000,
        "max_coverage": 2_000_000,
        "term_years": 20,
        "premium_estimate": 45.00,
        "currency": "USD",
        "region": "United States",
        "description": "Level-premium term life insurance for 20 years. Simple, affordable death benefit protection for families.",
    },
    {
        "insurer_name": "SecureLife Insurance Co.",
        "product_name": "SecureLife Term 30",
        "product_type": "term",
        "min_coverage": 250_000,
        "max_coverage": 5_000_000,
        "term_years": 30,
        "premium_estimate": 75.00,
        "currency": "USD",
        "region": "United States",
        "description": "30-year term life policy with living benefit rider option. Ideal for long-term mortgage protection.",
    },
    {
        "insurer_name": "PrudentGuard Life",
        "product_name": "PrudentGuard Term Plus",
        "product_type": "term",
        "min_coverage": 50_000,
        "max_coverage": 1_000_000,
        "term_years": 10,
        "premium_estimate": 25.00,
        "currency": "USD",
        "region": "United States",
        "description": "10-year term policy with guaranteed renewable feature. Good for short-term income replacement needs.",
    },
    # Whole Life
    {
        "insurer_name": "Heritage Mutual Life",
        "product_name": "Heritage Whole Life",
        "product_type": "whole",
        "min_coverage": 50_000,
        "max_coverage": 1_000_000,
        "term_years": None,
        "premium_estimate": 220.00,
        "currency": "USD",
        "region": "United States",
        "description": "Permanent whole life policy with cash value accumulation. Premiums guaranteed never to increase.",
    },
    {
        "insurer_name": "Heritage Mutual Life",
        "product_name": "Heritage Whole Life Plus",
        "product_type": "whole",
        "min_coverage": 100_000,
        "max_coverage": 5_000_000,
        "term_years": None,
        "premium_estimate": 450.00,
        "currency": "USD",
        "region": "United States",
        "description": "Enhanced whole life with paid-up additions rider for accelerated cash value growth.",
    },
    # Universal Life
    {
        "insurer_name": "FlexLife Corporation",
        "product_name": "FlexLife Universal",
        "product_type": "universal",
        "min_coverage": 100_000,
        "max_coverage": 10_000_000,
        "term_years": None,
        "premium_estimate": 150.00,
        "currency": "USD",
        "region": "United States",
        "description": "Flexible universal life policy allowing premium and death benefit adjustments as your needs change.",
    },
    # International / USD
    {
        "insurer_name": "GlobalShield Re",
        "product_name": "GlobalShield Expat Term 20",
        "product_type": "term",
        "min_coverage": 100_000,
        "max_coverage": 3_000_000,
        "term_years": 20,
        "premium_estimate": 55.00,
        "currency": "USD",
        "region": "Global",
        "description": "Designed for expatriates and international workers. Coverage valid worldwide.",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(InsuranceProduct).count()
        if existing > 0:
            print(f"Already have {existing} products — skipping seed.")
            return
        for p in SAMPLE_PRODUCTS:
            db.add(InsuranceProduct(**p))
        db.commit()
        print(f"Seeded {len(SAMPLE_PRODUCTS)} insurance products.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
