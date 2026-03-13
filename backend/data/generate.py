"""
Synthetic Indian loan applicant data generator.

Generates statistically realistic training data with:
- Correlated features (e.g. high DTI → higher default rate)
- India-specific field distributions (income bands, CIBIL score ranges)
- Behavioral signals (payment timing, partial payment history)
- Class imbalance matching real-world loan books (~12% default rate)
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
N_SAMPLES = 50_000
DEFAULT_RATE = 0.12

rng = np.random.default_rng(SEED)


def _clip(arr, lo, hi):
    return np.clip(arr, lo, hi)


def generate(n: int = N_SAMPLES) -> pd.DataFrame:
    # ── Core applicant profile ────────────────────────────────────────────
    age = rng.integers(21, 62, n)

    # Monthly income in INR — log-normal, median ~35k
    income = rng.lognormal(mean=10.6, sigma=0.55, size=n).astype(int)
    income = _clip(income, 8_000, 500_000)

    # CIBIL score (300–900); higher income → slightly higher score
    cibil_base = 550 + (income / 500_000) * 200
    cibil = _clip(
        (cibil_base + rng.normal(0, 60, n)).astype(int), 300, 900
    )

    # Loan amount (1L – 50L INR)
    loan_amount = _clip(
        rng.lognormal(mean=13.1, sigma=0.8, size=n).astype(int),
        100_000,
        5_000_000,
    )

    loan_tenure_months = rng.choice([12, 24, 36, 48, 60, 84], n)

    # EMI-to-income ratio (higher → riskier)
    monthly_rate = 0.012  # ~14.4% annual
    emi = loan_amount * monthly_rate / (1 - (1 + monthly_rate) ** -loan_tenure_months)
    emi_to_income = _clip(emi / income, 0.05, 0.95)

    # Existing loans outstanding
    existing_loans = rng.integers(0, 5, n)

    # Debt-to-income ratio
    existing_emi_burden = income * rng.uniform(0, 0.4, n)
    dti = _clip((emi + existing_emi_burden) / income, 0.05, 1.2)

    # Employment type: 0=salaried, 1=self-employed, 2=business owner
    employment_type = rng.choice([0, 1, 2], n, p=[0.55, 0.30, 0.15])

    # Years at current job
    years_employed = _clip(rng.exponential(scale=4, size=n), 0, 35)

    # ── Behavioral signals ────────────────────────────────────────────────
    # Payment timing score: 1.0 = always on time, 0.0 = always late
    payment_timing_score = _clip(rng.beta(a=6, b=2, size=n), 0, 1)

    # Partial payment ratio: fraction of EMIs paid partially (not full)
    partial_payment_ratio = _clip(rng.beta(a=1.5, b=8, size=n), 0, 1)

    # Months since last delinquency (99 = never delinquent)
    never_delinquent = rng.random(n) > 0.35
    months_since_delinquency = np.where(
        never_delinquent, 99, rng.integers(1, 48, n)
    )

    # Number of hard credit inquiries in last 6 months
    inquiries_6m = rng.integers(0, 8, n)

    # ── Default label ─────────────────────────────────────────────────────
    # Logistic-ish score combining real risk factors
    risk_logit = (
        -4.5
        + 0.03 * (750 - cibil) / 100          # low CIBIL = bad
        + 2.5 * dti                              # high DTI = bad
        + 1.8 * emi_to_income                    # high EMI burden = bad
        + 0.4 * existing_loans                   # more loans = riskier
        + 0.3 * (employment_type == 1)           # self-employed slightly riskier
        - 0.8 * payment_timing_score             # good payment history = good
        + 1.2 * partial_payment_ratio            # partial payments = bad
        + 0.05 * np.where(months_since_delinquency < 99, 48 - months_since_delinquency, 0)
        + 0.2 * inquiries_6m                     # many inquiries = bad
        - 0.02 * years_employed                  # stability is good
    )
    default_prob = 1 / (1 + np.exp(-risk_logit))
    # Add noise and re-scale so actual default rate ≈ DEFAULT_RATE
    noise = rng.normal(0, 0.05, n)
    default_prob = _clip(default_prob + noise, 0.01, 0.99)
    labels = (default_prob > rng.random(n)).astype(int)

    df = pd.DataFrame({
        "age": age,
        "monthly_income": income,
        "cibil_score": cibil,
        "loan_amount": loan_amount,
        "loan_tenure_months": loan_tenure_months,
        "emi_to_income_ratio": emi_to_income.round(4),
        "existing_loans": existing_loans,
        "debt_to_income_ratio": dti.round(4),
        "employment_type": employment_type,
        "years_employed": years_employed.round(1),
        "payment_timing_score": payment_timing_score.round(4),
        "partial_payment_ratio": partial_payment_ratio.round(4),
        "months_since_delinquency": months_since_delinquency,
        "inquiries_last_6m": inquiries_6m,
        "defaulted": labels,
    })

    actual_rate = labels.mean()
    print(f"Generated {n:,} samples | Default rate: {actual_rate:.2%}")
    return df


if __name__ == "__main__":
    out_path = Path(__file__).parent / "loan_data.csv"
    df = generate()
    df.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")
    print(df.describe().T[["mean", "std", "min", "max"]].round(2).to_string())
