"""
CreditSense API routes.

Endpoints:
  POST /score              — single applicant risk score
  POST /score/batch        — up to 100 applicants at once
  GET  /health             — liveness + model status
  GET  /metrics            — model performance metrics from training
  GET  /features           — feature metadata (for UI dropdowns)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.schemas import (
    ApplicantInput,
    BatchApplicantInput,
    BatchRiskScoreResponse,
    HealthResponse,
    RiskScoreResponse,
)
from model.predictor import get_predictor, ShapFactor, Counterfactual

router = APIRouter()

ARTEFACT_DIR = Path(__file__).parent.parent / "model" / "artefacts"


def _score_to_response(score) -> dict:
    return RiskScoreResponse(
        probability=score.probability,
        band=score.band,
        band_description=score.band_description,
        score=score.score,
        top_factors=[
            {
                "feature": f.feature,
                "display_name": f.display_name,
                "value": f.value,
                "shap_value": f.shap_value,
                "direction": f.direction,
                "magnitude": f.magnitude,
            }
            for f in score.top_factors
        ],
        counterfactuals=[
            {
                "feature": c.feature,
                "display_name": c.display_name,
                "current_value": c.current_value,
                "suggested_value": c.suggested_value,
                "risk_reduction": c.risk_reduction,
                "formatted_change": c.formatted_change,
            }
            for c in score.counterfactuals
        ],
        latency_ms=score.latency_ms,
        model_version=score.model_version,
    )


@router.post("/score", response_model=RiskScoreResponse, tags=["Scoring"])
async def score_applicant(body: ApplicantInput):
    """
    Score a single loan applicant.

    Returns:
    - **probability**: raw default probability (0–1)
    - **band**: risk tier (LOW / MODERATE / HIGH / CRITICAL)
    - **top_factors**: top 5 SHAP drivers with direction and magnitude
    - **counterfactuals**: actionable changes to reduce risk score
    """
    predictor = get_predictor()
    try:
        result = predictor.predict(body.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    return _score_to_response(result)


@router.post("/score/batch", response_model=BatchRiskScoreResponse, tags=["Scoring"])
async def score_batch(body: BatchApplicantInput):
    """Score up to 100 applicants in a single request."""
    predictor = get_predictor()
    t0 = time.perf_counter()
    results = []
    for applicant in body.applicants:
        try:
            result = predictor.predict(applicant.model_dump())
            results.append(_score_to_response(result))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed on applicant: {str(e)}"
            )
    total_ms = round((time.perf_counter() - t0) * 1000, 2)
    return BatchRiskScoreResponse(results=results, total_latency_ms=total_ms)


@router.get("/health", response_model=HealthResponse, tags=["Ops"])
async def health():
    """Liveness check with model status."""
    try:
        predictor = get_predictor()
        loaded = predictor._loaded
    except Exception:
        loaded = False
    return HealthResponse(status="ok", model_loaded=loaded, version="1.0.0")


@router.get("/metrics", tags=["Ops"])
async def model_metrics():
    """Return hold-out evaluation metrics from training run."""
    metrics_path = ARTEFACT_DIR / "metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Metrics not found. Run model/train.py first.")
    return JSONResponse(json.loads(metrics_path.read_text()))


@router.get("/features", tags=["Schema"])
async def feature_metadata():
    """
    Return feature schema — useful for UI form generation and documentation.
    """
    return {
        "features": [
            {"key": "age",                      "label": "Age",                        "type": "int",   "min": 18,   "max": 75,   "unit": "years"},
            {"key": "monthly_income",           "label": "Monthly Income",             "type": "float", "min": 8000, "max": 500000, "unit": "INR"},
            {"key": "cibil_score",              "label": "CIBIL Score",                "type": "int",   "min": 300,  "max": 900,  "unit": ""},
            {"key": "loan_amount",              "label": "Loan Amount",                "type": "float", "min": 100000, "max": 5000000, "unit": "INR"},
            {"key": "loan_tenure_months",       "label": "Loan Tenure",                "type": "int",   "min": 6,    "max": 120,  "unit": "months"},
            {"key": "emi_to_income_ratio",      "label": "EMI-to-Income Ratio",        "type": "float", "min": 0,    "max": 1,    "unit": "%"},
            {"key": "debt_to_income_ratio",     "label": "Debt-to-Income Ratio",       "type": "float", "min": 0,    "max": 1.5,  "unit": "%"},
            {"key": "employment_type",          "label": "Employment Type",            "type": "enum",  "options": [{"value": 0, "label": "Salaried"}, {"value": 1, "label": "Self-Employed"}, {"value": 2, "label": "Business Owner"}]},
            {"key": "years_employed",           "label": "Years at Current Job",       "type": "float", "min": 0,    "max": 40,   "unit": "years"},
            {"key": "existing_loans",           "label": "Existing Loans",             "type": "int",   "min": 0,    "max": 20,   "unit": ""},
            {"key": "months_since_delinquency", "label": "Months Since Delinquency",   "type": "int",   "min": 0,    "max": 99,   "unit": "months (99 = never)"},
            {"key": "inquiries_last_6m",        "label": "Credit Inquiries (6m)",      "type": "int",   "min": 0,    "max": 20,   "unit": ""},
            {"key": "payment_timing_score",     "label": "Payment Timing Score",       "type": "float", "min": 0,    "max": 1,    "unit": "0–1"},
            {"key": "partial_payment_ratio",    "label": "Partial Payment Ratio",      "type": "float", "min": 0,    "max": 1,    "unit": "0–1"},
        ]
    }
