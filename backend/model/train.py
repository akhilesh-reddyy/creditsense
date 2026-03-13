"""
Train XGBoost default-risk model and persist artefacts for inference.

Outputs (saved to backend/model/artefacts/):
  model.json          — XGBoost booster
  scaler.pkl          — StandardScaler (for future numeric features)
  shap_background.npy — 500-row background dataset for SHAP TreeExplainer
  feature_names.json  — ordered feature list
  metrics.json        — hold-out eval metrics
"""

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ARTEFACT_DIR = Path(__file__).parent / "artefacts"
DATA_PATH = Path(__file__).parent.parent / "data" / "loan_data.csv"
SEED = 42


FEATURES = [
    "age",
    "monthly_income",
    "cibil_score",
    "loan_amount",
    "loan_tenure_months",
    "emi_to_income_ratio",
    "existing_loans",
    "debt_to_income_ratio",
    "employment_type",
    "years_employed",
    "payment_timing_score",
    "partial_payment_ratio",
    "months_since_delinquency",
    "inquiries_last_6m",
]

XGB_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": ["logloss", "auc"],
    "max_depth": 6,
    "learning_rate": 0.05,
    "n_estimators": 400,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 20,
    "gamma": 1.0,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "scale_pos_weight": 7,   # handles ~12% default rate imbalance
    "random_state": SEED,
    "tree_method": "hist",
    "early_stopping_rounds": 30,
}


def train():
    ARTEFACT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data…")
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES]
    y = df["defaulted"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.15, stratify=y_train, random_state=SEED
    )

    print(f"Train: {len(X_tr):,}  Val: {len(X_val):,}  Test: {len(X_test):,}")

    # ── Train ────────────────────────────────────────────────────────────
    model = xgb.XGBClassifier(**XGB_PARAMS, verbosity=0)
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # ── Evaluate ─────────────────────────────────────────────────────────
    probs = model.predict_proba(X_test)[:, 1]
    auroc = roc_auc_score(y_test, probs)
    auprc = average_precision_score(y_test, probs)
    print(f"AUROC: {auroc:.4f}  AUPRC: {auprc:.4f}")

    metrics = {"auroc": round(auroc, 4), "auprc": round(auprc, 4), "n_test": len(X_test)}
    (ARTEFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # ── SHAP background ──────────────────────────────────────────────────
    # 500 stratified samples from train set — used by TreeExplainer
    bg_idx = (
        X_train.sample(n=500, random_state=SEED, weights=(y_train * 4 + 1)).index
    )
    background = X_train.loc[bg_idx].values
    np.save(ARTEFACT_DIR / "shap_background.npy", background)

    # ── Persist ──────────────────────────────────────────────────────────
    model.save_model(str(ARTEFACT_DIR / "model.json"))
    scaler = StandardScaler().fit(X_train)
    joblib.dump(scaler, ARTEFACT_DIR / "scaler.pkl")
    (ARTEFACT_DIR / "feature_names.json").write_text(json.dumps(FEATURES, indent=2))

    print(f"Artefacts saved to {ARTEFACT_DIR}")
    return model


if __name__ == "__main__":
    train()
