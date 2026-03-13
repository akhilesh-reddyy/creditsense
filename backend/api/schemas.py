"""
API schemas — all request/response shapes with validation.
"""

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator


# ── Request ───────────────────────────────────────────────────────────────────

class ApplicantInput(BaseModel):
    """Loan applicant profile submitted for risk scoring."""

    # Demographics
    age: int = Field(..., ge=18, le=75, description="Applicant age in years")

    # Financial profile
    monthly_income: float = Field(..., gt=0, description="Gross monthly income in INR")
    cibil_score: int = Field(..., ge=300, le=900, description="CIBIL credit score")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount in INR")
    loan_tenure_months: int = Field(..., ge=6, le=120, description="Loan tenure in months")

    # Ratios (computed by caller or derived from income/EMI)
    emi_to_income_ratio: float = Field(..., ge=0, le=1, description="Monthly EMI ÷ income")
    debt_to_income_ratio: float = Field(..., ge=0, description="Total debt obligations ÷ income")

    # Employment
    employment_type: int = Field(
        ..., ge=0, le=2,
        description="0=salaried, 1=self-employed, 2=business owner"
    )
    years_employed: float = Field(..., ge=0, le=50)

    # Credit history
    existing_loans: int = Field(..., ge=0, le=20, description="Number of active loans")
    months_since_delinquency: int = Field(
        ..., ge=0, le=99,
        description="Months since last missed payment. Use 99 if never delinquent."
    )
    inquiries_last_6m: int = Field(..., ge=0, le=20, description="Hard credit pulls in last 6 months")

    # Behavioral signals
    payment_timing_score: float = Field(
        ..., ge=0, le=1,
        description="Historical on-time payment ratio (1.0 = always on time)"
    )
    partial_payment_ratio: float = Field(
        ..., ge=0, le=1,
        description="Fraction of EMIs paid partially rather than in full"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "age": 32,
            "monthly_income": 45000,
            "cibil_score": 710,
            "loan_amount": 500000,
            "loan_tenure_months": 36,
            "emi_to_income_ratio": 0.35,
            "debt_to_income_ratio": 0.45,
            "employment_type": 0,
            "years_employed": 4.5,
            "existing_loans": 1,
            "months_since_delinquency": 99,
            "inquiries_last_6m": 1,
            "payment_timing_score": 0.92,
            "partial_payment_ratio": 0.04,
        }
    }}


# ── Response sub-models ───────────────────────────────────────────────────────

class ShapFactorResponse(BaseModel):
    feature: str
    display_name: str
    value: float
    shap_value: float
    direction: Literal["increases_risk", "decreases_risk"]
    magnitude: Literal["high", "medium", "low"]


class CounterfactualResponse(BaseModel):
    feature: str
    display_name: str
    current_value: float
    suggested_value: float
    risk_reduction: float
    formatted_change: str


class RiskScoreResponse(BaseModel):
    """Full credit risk assessment result."""
    probability: float = Field(..., description="Default probability (0–1)")
    band: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]
    band_description: str
    score: int = Field(..., description="Risk score 0–1000 (higher = riskier)")
    top_factors: list[ShapFactorResponse]
    counterfactuals: list[CounterfactualResponse]
    latency_ms: float
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str


class BatchApplicantInput(BaseModel):
    applicants: list[ApplicantInput] = Field(..., max_length=100)


class BatchRiskScoreResponse(BaseModel):
    results: list[RiskScoreResponse]
    total_latency_ms: float
