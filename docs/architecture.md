# CreditSense — Architecture

## Overview

CreditSense is a three-layer system: a React SPA, a FastAPI backend, and an ML inference engine. All three are stateless (model artefacts are loaded once at startup and held in memory) so horizontal scaling is trivial.

## Request Lifecycle

```
1. User fills ApplicantForm in React
2. useScore hook POSTs to /api/v1/score
3. FastAPI validates request with Pydantic (400 on invalid input)
4. ScoringService applies loan-type specific band overrides
5. CreditPredictor runs XGBoost inference (~2ms)
6. SHAP TreeExplainer computes per-feature contributions (~10ms)
7. Counterfactual engine iterates over 8 mutable features, simulates changes
8. Response: probability + band + top_factors + counterfactuals + latency
9. React renders RiskGauge (SVG arc), ShapWaterfall (bars), CounterfactualCards
```

Total round-trip: ~15–25ms (excluding network).

## ML Pipeline

### Training (`model/train.py`)

```
Raw data (50k rows)
  → train/val/test split (80/12/8, stratified)
  → XGBClassifier (400 estimators, early stopping on val AUC)
  → Saved as model.json (XGBoost native format — faster than pickle)

Background dataset
  → 500 stratified samples from train set
  → Defaulters oversampled 4× (so SHAP baselines are calibrated)
  → Saved as shap_background.npy
```

### Inference (`model/predictor.py`)

```
Input dict (14 features)
  → np.array (float32)
  → XGBClassifier.predict_proba → scalar probability
  → SHAP TreeExplainer.shap_values → array of 14 SHAP values
  → Top 5 by |shap_value| → ShapFactor list
  → Counterfactual loop (8 features × simulate change → new probability)
  → RiskScore dataclass
```

### Why TreeExplainer over KernelSHAP?

TreeExplainer is exact for tree models. KernelSHAP approximates via sampling — it works for any model but is 50–100× slower and adds variance. At <20ms per call with TreeExplainer, we can run SHAP synchronously on every prediction without queueing.

## Data Model

### Features

| Feature | Type | India-Specific Note |
|---|---|---|
| `cibil_score` | int 300–900 | Indian credit bureau score (vs US FICO 300–850) |
| `monthly_income` | float INR | Log-normal distribution, median ~₹35k |
| `emi_to_income_ratio` | float 0–1 | RBI guideline: should not exceed 60% |
| `debt_to_income_ratio` | float 0–1.5 | Can exceed 1.0 — signals negative cash flow |
| `months_since_delinquency` | int 0–99 | 99 = never delinquent (sentinel value) |
| `payment_timing_score` | float 0–1 | Behavioral signal — not available in traditional credit files |
| `partial_payment_ratio` | float 0–1 | Behavioral signal — fraction of EMIs paid partially |
| `employment_type` | enum 0/1/2 | Salaried/Self-employed/Business owner |

### Risk Bands

| Band | Probability | Decision Guidance |
|---|---|---|
| LOW | < 15% | Standard rates, auto-approve |
| MODERATE | 15–35% | Manual review, consider co-applicant |
| HIGH | 35–60% | Manual underwriting, collateral required |
| CRITICAL | > 60% | Decline or escalate to credit committee |

Thresholds are tuned per loan type in `services/scoring_service.py`. Business loans use a stricter CRITICAL threshold (50% instead of 60%) due to higher loss-given-default.

## Explainability Design

### SHAP Values

A SHAP value for feature `f` in prediction `x` answers: "How much did `f` shift the prediction away from the expected value?" Positive = pushed toward default, negative = pushed away.

Example output for a MODERATE-risk applicant:
```
debt_to_income_ratio:  +0.038  (increases risk)
cibil_score:           -0.031  (decreases risk — good CIBIL)
payment_timing_score:  -0.019  (decreases risk — consistent payments)
inquiries_last_6m:     +0.012  (increases risk — recent credit seeking)
existing_loans:        +0.008  (increases risk — already leveraged)
```

### Counterfactuals

For each of 8 mutable features, we simulate a single-step change (e.g. CIBIL +50) and re-run inference. The resulting probability drop is the `risk_reduction`. We surface the top 4 by impact.

This is intentionally simple — single-feature isolation, not joint optimisation. A Wachter-style recourse algorithm would be more theoretically correct but produces suggestions that are harder to explain to non-technical users ("increase CIBIL by 47.3 points and reduce DTI by 0.12 simultaneously").

## Scaling Considerations

The current design is single-process. For production scale:

- **Model serving**: Replace `get_predictor()` singleton with a proper model server (TorchServe, Triton, or just a gunicorn multi-worker setup)
- **SHAP caching**: For batch scoring, cache SHAP explainer.expected_value (it's constant per model version)
- **Async batch**: The `/score/batch` endpoint runs synchronously. For >100 applicants, push to a Celery/RQ queue and poll for results
- **Feature store**: `payment_timing_score` and `partial_payment_ratio` are behavioral signals that should be pulled from a feature store at inference time, not submitted by the API caller
