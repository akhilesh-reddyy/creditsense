"""
Preprocessing utilities.

Functions used at both training time (in generate.py/train.py)
and inference time (in the API layer) to ensure train/serve consistency.

The rule: if a transformation happens at training, it MUST happen at inference.
Put it here so it can't drift.
"""

from __future__ import annotations
import numpy as np


def compute_emi(
    principal: float,
    annual_rate_pct: float,
    tenure_months: int,
) -> float:
    """
    Standard reducing-balance EMI formula.

    Args:
        principal: Loan amount in INR
        annual_rate_pct: Annual interest rate as percentage (e.g. 14.4 for 14.4%)
        tenure_months: Loan tenure in months

    Returns:
        Monthly EMI in INR
    """
    r = annual_rate_pct / 100 / 12
    if r == 0:
        return principal / tenure_months
    return principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)


def compute_emi_to_income(emi: float, monthly_income: float) -> float:
    """EMI as fraction of monthly income. Clipped to [0.05, 0.95]."""
    if monthly_income <= 0:
        return 0.95
    return float(np.clip(emi / monthly_income, 0.05, 0.95))


def compute_dti(
    proposed_emi: float,
    existing_emi_burden: float,
    monthly_income: float,
) -> float:
    """
    Total debt-to-income ratio including proposed loan.
    Clipped to [0.05, 1.5] — values above 1 indicate negative cash flow.
    """
    if monthly_income <= 0:
        return 1.5
    return float(np.clip((proposed_emi + existing_emi_burden) / monthly_income, 0.05, 1.5))


def normalise_cibil(score: int) -> float:
    """
    Normalise CIBIL to [0, 1] range.
    Not used by XGBoost (tree models are scale-invariant) but useful for
    linear models or neural network variants.
    """
    return (score - 300) / (900 - 300)


def validate_applicant_ratios(applicant: dict) -> list[str]:
    """
    Business-rule validation beyond Pydantic schema checks.
    Returns a list of warning strings (not errors — we score anyway but flag these).
    """
    warnings = []
    eti = applicant.get("emi_to_income_ratio", 0)
    dti = applicant.get("debt_to_income_ratio", 0)
    cibil = applicant.get("cibil_score", 750)
    inquiries = applicant.get("inquiries_last_6m", 0)

    if eti > 0.60:
        warnings.append(f"EMI-to-income ratio {eti:.0%} exceeds RBI guideline of 60%")
    if dti > 0.80:
        warnings.append(f"DTI {dti:.0%} is very high — borrower may be over-leveraged")
    if cibil < 600:
        warnings.append("CIBIL below 600 — most lenders require minimum 650")
    if inquiries >= 6:
        warnings.append(f"{inquiries} credit inquiries in 6 months signals credit-seeking behaviour")

    return warnings
