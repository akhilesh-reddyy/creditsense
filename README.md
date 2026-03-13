# CreditSense — Explainable Credit Risk Engine

> Real-time loan default prediction with SHAP-powered explanations and counterfactual recommendations. Built for Indian fintech lending teams who need to know *why* a borrower is risky, not just *that* they are.

---

## The Problem

Traditional credit scoring is a black box. A lender gets a number — 680 — and has no idea which factors drove it, whether the model is fair, or what the applicant could do to improve their standing. Regulators are increasingly demanding explainability (RBI's guidance on AI/ML models, 2023). CreditSense is the answer.

---

## What It Does

| Feature | Description |
|---|---|
| **Default Probability** | XGBoost model trained on 50,000 synthetic Indian loan applicant profiles |
| **Risk Band** | LOW / MODERATE / HIGH / CRITICAL with domain-tuned thresholds |
| **SHAP Explanations** | Top 5 risk drivers per applicant, with direction and magnitude |
| **Counterfactuals** | "Raise your CIBIL score by 50 points → reduces default risk by 8%" |
| **Batch Scoring** | Up to 100 applicants per request via `/score/batch` |
| **Audit Trail** | Every prediction includes latency, model version, and full SHAP breakdown |

---

## Architecture

```
┌─────────────────────────────────────────┐
│           React Dashboard               │
│  ApplicantForm → RiskGauge → SHAP       │
│  Waterfall → CounterfactualCards        │
└──────────────┬──────────────────────────┘
               │ HTTP (JSON)
┌──────────────▼──────────────────────────┐
│           FastAPI Backend               │
│  POST /api/v1/score                     │
│  POST /api/v1/score/batch               │
│  GET  /api/v1/health                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         CreditPredictor                 │
│  XGBClassifier (loaded once at startup) │
│  SHAP TreeExplainer                     │
│  Counterfactual Engine                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Model Artefacts                 │
│  model.json   — XGBoost booster         │
│  shap_background.npy — 500-row sample   │
│  feature_names.json                     │
│  metrics.json — AUROC / AUPRC           │
└─────────────────────────────────────────┘
```

---

## Tech Stack

**Backend:** Python 3.11 · FastAPI · XGBoost 2.0 · SHAP 0.45 · Pydantic v2

**Frontend:** React 18 · Vite · Tailwind CSS · Recharts

**Infrastructure:** Docker · Docker Compose · OpenAPI (auto-generated)

---

## Model Performance

Evaluated on a held-out 20% test set (10,000 applicants):

| Metric | Score |
|---|---|
| AUROC | ~0.89 |
| AUPRC | ~0.62 |
| Base default rate | ~12% |

> AUPRC is the right metric here — AUROC alone is misleading at 12% base rate.

---

## Run Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
python data/generate.py      # generates 50k training rows
python model/train.py        # trains model, saves artefacts (~60s)
uvicorn api.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

### Docker

```bash
docker-compose up --build
```

---

## API Quick Reference

### `POST /api/v1/score`

```json
// Request
{
  "age": 32, "monthly_income": 45000, "cibil_score": 710,
  "loan_amount": 500000, "loan_tenure_months": 36,
  "emi_to_income_ratio": 0.35, "debt_to_income_ratio": 0.45,
  "employment_type": 0, "years_employed": 4.5,
  "existing_loans": 1, "months_since_delinquency": 99,
  "inquiries_last_6m": 1, "payment_timing_score": 0.92,
  "partial_payment_ratio": 0.04
}

// Response
{
  "probability": 0.142,
  "band": "MODERATE",
  "score": 142,
  "top_factors": [{ "feature": "debt_to_income_ratio", "shap_value": 0.038, "direction": "increases_risk" }],
  "counterfactuals": [{ "display_name": "CIBIL Score", "suggested_value": 760, "risk_reduction": 0.082 }],
  "latency_ms": 12.4
}
```

---

## Key Engineering Decisions

**Why XGBoost over neural networks?** For tabular credit data with 14 features, gradient boosted trees consistently outperform NNs. More importantly, SHAP TreeExplainer is exact (not approximate) for tree models — each explanation runs in O(TLD) time. With neural networks you're stuck with KernelSHAP, which is ~100× slower.

**Why counterfactuals and not just explanations?** Explanations are backward-looking ("this is why your score is X"). Counterfactuals are forward-looking ("here's what to change"). For a lending product, this is what the relationship manager hands the applicant. It's also what regulators ask for when they want evidence that denials are actionable and not discriminatory.

**Why a stratified SHAP background dataset?** We oversample defaulters 4× in the 500-row background set so the explainer's baseline reflects the real decision boundary, not just the majority class distribution.

---

## License

MIT
