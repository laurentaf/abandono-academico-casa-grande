"""
Quick test: runs a simplified version to verify code works.
Uses 10% sample, 10 trees for ensembles, no permutation tests.
"""
import sys, io, json, pickle, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import duckdb
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

print("=" * 60)
print("TEST PIPELINE - Lightweight validation")
print("=" * 60)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "artifacts" / "data"
DUCKDB_PATH = DATA_DIR / "oulad.duckdb"
MODEL_PATH = BASE_DIR / "src" / "model.pkl"

# Load data
con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
df = con.execute("SELECT * FROM gold_oulad_features").fetchdf()
con.close()
print(f"Loaded: {len(df)} rows")

# Simple feature engineering
df["engagement_intensity"] = df["total_clicks"] / df["module_presentation_length"].replace(0, 1)
df["assessment_count"] = df["num_tma"] + df["num_cma"] + df["num_exams"]
df["submission_rate"] = df["assessment_count"] / df["module_presentation_length"].replace(0, 1)
df["imd_band"] = df["imd_band"].fillna("Unknown")

cat_features = ["code_module", "code_presentation", "gender", "region",
                "highest_education", "imd_band", "age_band", "disability"]
num_features = ["total_clicks", "days_active", "last_activity_day", "assessment_count",
                "submission_rate", "engagement_intensity"]

X = df[cat_features + num_features].copy()
y = df["is_dropout"].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train)}, Test: {len(X_test)}, Dropout: {y.mean():.1%}")

# Preprocessor
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), num_features),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features),
])

models = {
    "Dummy": DummyClassifier(strategy="stratified", random_state=42),
    "LR": Pipeline([("prep", preprocessor), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))]),
    "RF": Pipeline([("prep", preprocessor), ("clf", RandomForestClassifier(n_estimators=50, class_weight="balanced", random_state=42))]),
}

results = {}
for name, model in models.items():
    t0 = time.time()
    model.fit(X_train, y_train)
    dt = time.time() - t0

    if name == "Dummy":
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"  {name}: acc={acc:.4f}, time={dt:.2f}s")
        results[name] = {"accuracy": float(acc), "train_time": dt}
    else:
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_proba)
        print(f"  {name}: acc={acc:.4f}, prec={prec:.4f}, rec={rec:.4f}, f1={f1:.4f}, auc={auc:.4f}, time={dt:.2f}s")
        results[name] = {"accuracy": float(acc), "precision": float(prec), "recall": float(rec),
                         "f1": float(f1), "roc_auc": float(auc), "train_time": dt}

# Save model
pickle.dump({"model": models["RF"], "model_type": "Random Forest"}, open(MODEL_PATH, "wb"))
print(f"\nModel saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")

# Save quick results for benchmarking
results_path = DATA_DIR / "test_results.json"
with open(results_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"Results saved: {results_path}")
print("\nTEST PIPELINE COMPLETE ✅")
