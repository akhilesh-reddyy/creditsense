"""
CreditSense Predictor

Loads trained artefacts once at startup (singleton pattern) and exposes:
  - predict(applicant) → RiskScore with probability, band, SHAP explanations
  - counterfactuals(applicant) → list of actionable changes to reduce risk

SHAP TreeExplainer is fast enough for synchronous API use (~5–20ms per call).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import shap
import xgboost as xgb

ARTEFACT_DIR = Path(__file__).parent / "artefacts"

# ── Domain thresholds (tuned for ~12% base default rate) ─────────────────────
RISK_BANDS = [
    (0.00, 0.15, "LOW",      "Low risk — eligible for standard rates"),
    (0.15, 0.35, "MODERATE", "Moderate risk — may need co-applicant or collateral"),
    (0.35, 0.60, "HIGH",     "High risk — manual underwriting recommended"),
    (0.60, 1.00, "CRITICAL", "Very high risk — decline or escalate"),
]

# How much each feature must move to be worth mentioning in counterfactuals
COUNTERFACTUAL_DELTAS = {
    "cibil_score":             {"direction": "up",   "step": 50,   "label": "CIBIL score",            "unit": "points",  "format": "int"},
    "debt_to_income_ratio":    {"direction": "down", "step": 0.10, "label": "Debt-to-income ratio",   "unit": "",        "format": "pct"},
    "emi_to_income_ratio":     {"direction": "down", "step": 0.05, "label": "EMI-to-income ratio",    "unit": "",        "format": "pct"},
    "payment_timing_score":    {"direction": "up",   "step": 0.15, "label": "Payment timing score",   "unit": "",        "format": "pct"},
    "inquiries_last_6m":       {"direction": "down", "step": 2,    "label": "Credit inquiries (6m)",  "unit": "",        "format": "int"},
    "existing_loans":          {"direction": "down", "step": 1,    "label": "Existing loans",         "unit": "",        "format": "int"},
    "partial_payment_ratio":   {"direction": "down", "step": 0.10, "label": "Partial payment ratio",  "unit": "",        "format": "pct"},
    "months_since_delinquency":{"direction": "up",   "step": 12,   "label": "Months since delinquency","unit": "months", "format": "int"},
}


@dataclass
class ShapFactor:
    feature: str
    display_name: str
    value: float
    shap_value: float
    direction: str       # "increases_risk" | "decreases_risk"
    magnitude: str       # "high" | "medium" | "low"


@dataclass
class Counterfactual:
    feature: str
    display_name: str
    current_value: float
    suggested_value: float
    risk_reduction: float   # absolute probability drop
    formatted_change: str


@dataclass
class RiskScore:
    probability: float
    band: str
    band_description: str
    score: int              # 0–1000 scaled, higher = riskier
    top_factors: list[ShapFactor]
    counterfactuals: list[Counterfactual]
    latency_ms: float
    model_version: str = "1.0.0"


FEATURE_DISPLAY = {
    "age": "Age",
    "monthly_income": "Monthly Income",
    "cibil_score": "CIBIL Score",
    "loan_amount": "Loan Amount",
    "loan_tenure_months": "Loan Tenure",
    "emi_to_income_ratio": "EMI-to-Income Ratio",
    "existing_loans": "Existing Loans",
    "debt_to_income_ratio": "Debt-to-Income Ratio",
    "employment_type": "Employment Type",
    "years_employed": "Years Employed",
    "payment_timing_score": "Payment Timing Score",
    "partial_payment_ratio": "Partial Payment Ratio",
    "months_since_delinquency": "Months Since Delinquency",
    "inquiries_last_6m": "Credit Inquiries (6m)",
}


class CreditPredictor:
    def __init__(self):
        self._model: xgb.XGBClassifier | None = None
        self._explainer: shap.TreeExplainer | None = None
        self._feature_names: list[str] = []
        self._loaded = False

    def load(self):
        """Load artefacts from disk. Called once at API startup."""
        if self._loaded:
            return

        self._feature_names = json.loads(
            (ARTEFACT_DIR / "feature_names.json").read_text()
        )

        self._model = xgb.XGBClassifier()
        self._model.load_model(str(ARTEFACT_DIR / "model.json"))

        background = np.load(ARTEFACT_DIR / "shap_background.npy")
        self._explainer = shap.TreeExplainer(
            self._model,
            data=background,
            feature_names=self._feature_names,
            model_output="probability",
        )

        self._loaded = True

    def _to_array(self, applicant: dict[str, Any]) -> np.ndarray:
        return np.array(
            [[applicant[f] for f in self._feature_names]], dtype=np.float32
        )

    def predict(self, applicant: dict[str, Any]) -> RiskScore:
        assert self._loaded, "Call load() before predict()"
        t0 = time.perf_counter()

        X = self._to_array(applicant)

        # ── Probability ───────────────────────────────────────────────────
        prob = float(self._model.predict_proba(X)[0, 1])

        # ── Risk band ─────────────────────────────────────────────────────
        band, band_desc = "UNKNOWN", ""
        for lo, hi, b, desc in RISK_BANDS:
            if lo <= prob < hi:
                band, band_desc = b, desc
                break

        # ── SHAP values ───────────────────────────────────────────────────
        shap_vals = self._explainer.shap_values(X)[0]  # shape (n_features,)
        abs_shap = np.abs(shap_vals)
        top_idx = np.argsort(abs_shap)[::-1][:5]

        top_factors = []
        for i in top_idx:
            sv = float(shap_vals[i])
            magnitude = (
                "high" if abs(sv) > 0.05 else
                "medium" if abs(sv) > 0.02 else
                "low"
            )
            top_factors.append(ShapFactor(
                feature=self._feature_names[i],
                display_name=FEATURE_DISPLAY.get(self._feature_names[i], self._feature_names[i]),
                value=float(X[0, i]),
                shap_value=sv,
                direction="increases_risk" if sv > 0 else "decreases_risk",
                magnitude=magnitude,
            ))

        # ── Counterfactuals ───────────────────────────────────────────────
        counterfactuals = self._compute_counterfactuals(applicant, X, prob)

        latency = (time.perf_counter() - t0) * 1000

        return RiskScore(
            probability=round(prob, 4),
            band=band,
            band_description=band_desc,
            score=int(prob * 1000),
            top_factors=top_factors,
            counterfactuals=counterfactuals,
            latency_ms=round(latency, 2),
        )

    def _compute_counterfactuals(
        self,
        applicant: dict[str, Any],
        X_orig: np.ndarray,
        prob_orig: float,
    ) -> list[Counterfactual]:
        results = []

        for feat, cfg in COUNTERFACTUAL_DELTAS.items():
            if feat not in self._feature_names:
                continue

            feat_idx = self._feature_names.index(feat)
            current = float(X_orig[0, feat_idx])
            direction = cfg["direction"]
            step = cfg["step"]

            suggested = (
                current + step if direction == "up" else current - step
            )
            # Clamp to sensible domain
            suggested = max(0, suggested)

            X_cf = X_orig.copy()
            X_cf[0, feat_idx] = suggested
            prob_cf = float(self._model.predict_proba(X_cf)[0, 1])
            reduction = prob_orig - prob_cf

            if reduction < 0.01:  # not worth mentioning
                continue

            # Format the suggested value
            fmt = cfg["format"]
            unit = cfg["unit"]
            if fmt == "pct":
                change_str = f"{suggested:.0%}"
            elif fmt == "int":
                change_str = f"{int(suggested):,} {unit}".strip()
            else:
                change_str = f"{suggested:.2f} {unit}".strip()

            results.append(Counterfactual(
                feature=feat,
                display_name=cfg["label"],
                current_value=round(current, 4),
                suggested_value=round(suggested, 4),
                risk_reduction=round(reduction, 4),
                formatted_change=change_str,
            ))

        # Sort by biggest risk reduction first
        results.sort(key=lambda c: c.risk_reduction, reverse=True)
        return results[:4]


@lru_cache(maxsize=1)
def get_predictor() -> CreditPredictor:
    p = CreditPredictor()
    p.load()
    return p
