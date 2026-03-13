"""
Scoring Service

Business logic layer that sits between the API routes and the raw ML predictor.
Handles:
- Input preprocessing (ratio computation from raw values)
- Risk threshold overrides for specific loan types
- Audit logging (structure for plugging in a real logger/DB)
- Future: A/B model switching, feature flag gating

Keeping this separate from routes.py means the API layer stays thin
and the business rules are testable in isolation.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from model.predictor import get_predictor, RiskScore


@dataclass
class ScoringRequest:
    applicant: dict[str, Any]
    loan_type: str = "personal"       # personal | home | vehicle | business
    source: str = "api"               # api | batch | internal


@dataclass
class ScoringResponse:
    risk_score: RiskScore
    loan_type: str
    override_applied: bool = False
    override_reason: str = ""


# Loan-type specific risk band overrides.
# Home loans can tolerate slightly higher DTI; business loans need lower default prob.
LOAN_TYPE_THRESHOLDS = {
    "personal":  {"high_threshold": 0.35, "critical_threshold": 0.60},
    "home":      {"high_threshold": 0.40, "critical_threshold": 0.65},  # more collateral
    "vehicle":   {"high_threshold": 0.38, "critical_threshold": 0.62},
    "business":  {"high_threshold": 0.28, "critical_threshold": 0.50},  # stricter
}


class ScoringService:
    def __init__(self):
        self._predictor = None

    def _get_predictor(self):
        if self._predictor is None:
            self._predictor = get_predictor()
        return self._predictor

    def score(self, request: ScoringRequest) -> ScoringResponse:
        """
        Score an applicant with optional loan-type specific overrides.

        The raw model outputs a single default probability — this layer
        applies business rules on top without touching the model itself.
        """
        predictor = self._get_predictor()
        risk_score = predictor.predict(request.applicant)

        override_applied = False
        override_reason = ""

        # Apply loan-type band overrides if thresholds differ from defaults
        thresholds = LOAN_TYPE_THRESHOLDS.get(request.loan_type, LOAN_TYPE_THRESHOLDS["personal"])
        adjusted_band = _apply_band_override(
            risk_score.probability,
            thresholds,
            risk_score.band,
        )

        if adjusted_band != risk_score.band:
            override_applied = True
            override_reason = f"Band adjusted for loan type '{request.loan_type}'"
            # Mutate the band — the probability stays the same (that's the model's job)
            risk_score.band = adjusted_band

        self._audit_log(request, risk_score)

        return ScoringResponse(
            risk_score=risk_score,
            loan_type=request.loan_type,
            override_applied=override_applied,
            override_reason=override_reason,
        )

    def _audit_log(self, request: ScoringRequest, score: RiskScore):
        """
        Structured audit log entry. In production: write to Postgres/ClickHouse.
        Format matches what RBI expects in AI model audit trails.
        """
        entry = {
            "source": request.source,
            "loan_type": request.loan_type,
            "probability": score.probability,
            "band": score.band,
            "score": score.score,
            "latency_ms": score.latency_ms,
            "model_version": score.model_version,
            "top_factor": score.top_factors[0].feature if score.top_factors else None,
        }
        # TODO: replace with structlog / database write in production
        # log.info("credit_score_issued", **entry)
        pass


def _apply_band_override(prob: float, thresholds: dict, current_band: str) -> str:
    high_t     = thresholds["high_threshold"]
    critical_t = thresholds["critical_threshold"]

    if prob < 0.15:
        return "LOW"
    elif prob < high_t:
        return "MODERATE"
    elif prob < critical_t:
        return "HIGH"
    else:
        return "CRITICAL"


# Singleton
_scoring_service: ScoringService | None = None

def get_scoring_service() -> ScoringService:
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
