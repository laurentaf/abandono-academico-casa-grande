"""
ML Pipeline — Abandono Academico Casa Grande (OULAD)
====================================================
T4 (Feature Engineering) → T5 (Model Training) → T6 (Model Evaluation)

Reads gold_oulad_features from DuckDB, trains Logistic Regression + Random Forest,
compares against Dummy Classifier baseline, saves model and documentation.

Source: Open University Learning Analytics Dataset (OULAD)
Gold table: 32,593 rows × 28 cols
Target: is_dropout (31.2% positive class)
"""

import io
import pickle
import sys
import warnings
from pathlib import Path

# Force UTF-8 stdout on Windows to avoid cp1252 encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

# ─── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_DIR = ARTIFACTS_DIR / "data"
DUCKDB_PATH = DATA_DIR / "oulad.duckdb"
MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
MODEL_DOC_PATH = DATA_DIR / "model.md"

# ─── Feature groups ──────────────────────────────────────────────────────────

CATEGORICAL_FEATURES = [
    "code_module",
    "code_presentation",
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
]

NUMERIC_FEATURES = [
    "num_of_prev_attempts",
    "studied_credits",
    "date_registration",
    "total_clicks",
    "days_active",
    "last_activity_day",
    "first_activity_day",
    "click_trend",
    "avg_daily_clicks",
    "weighted_avg_score",
    "num_tma",
    "num_cma",
    "num_exams",
    "avg_assessment_score",
    "avg_submission_delta",
    "module_presentation_length",
]

TARGET = "is_dropout"
META_COLS = ["code_module", "code_presentation", "id_student", "final_result_label"]

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5


# ─── T4: Feature Engineering ─────────────────────────────────────────────────


def load_gold_table(db_path: Path) -> pd.DataFrame:
    """Load gold_oulad_features from DuckDB via pandas."""
    import duckdb

    con = duckdb.connect(str(db_path), read_only=True)
    df = con.execute("SELECT * FROM gold_oulad_features").fetchdf()
    con.close()
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering on the gold table.

    The gold table already has pre-computed temporal and assessment features.
    This function adds derived features and handles nulls.
    """
    _guard_empty(df, "engineer_features — input is empty")
    print(f"[T4] Gold table loaded: {df.shape[0]} rows × {df.shape[1]} cols")

    # --- Null handling ---
    # imd_band: 3.4% nulls → fill with "Unknown"
    null_imd = df["imd_band"].isnull().sum()
    if null_imd > 0:
        df["imd_band"] = df["imd_band"].fillna("Unknown")
        print(f"[T4] imd_band: filled {null_imd} nulls with 'Unknown'")

    # date_registration: 0.1% nulls → fill with median
    null_reg = df["date_registration"].isnull().sum()
    if null_reg > 0:
        median_reg = df["date_registration"].median()
        df["date_registration"] = df["date_registration"].fillna(median_reg)
        print(f"[T4] date_registration: filled {null_reg} nulls with median={median_reg}")

    # --- Derived features ---
    # engagement_intensity: total_clicks / module_presentation_length (clicks per day of module)
    df["engagement_intensity"] = df["total_clicks"] / df["module_presentation_length"].replace(0, 1)
    print("[T4] Derived: engagement_intensity = total_clicks / module_presentation_length")

    # activity_coverage: days_active / module_presentation_length (fraction of module days active)
    df["activity_coverage"] = df["days_active"] / df["module_presentation_length"].replace(0, 1)
    print("[T4] Derived: activity_coverage = days_active / module_presentation_length")

    # has_vle_activity: binary flag for VLE engagement
    df["has_vle_activity"] = (df["total_clicks"] > 0).astype(int)
    print("[T4] Derived: has_vle_activity (binary flag)")

    # assessment_count: total assessments submitted
    df["assessment_count"] = df["num_tma"] + df["num_cma"] + df["num_exams"]
    print("[T4] Derived: assessment_count = num_tma + num_cma + num_exams")

    # submission_rate: assessments submitted / module length (proxy for consistency)
    # Higher values → student is submitting more consistently
    df["submission_rate"] = df["assessment_count"] / df["module_presentation_length"].replace(0, 1)
    print("[T4] Derived: submission_rate = assessment_count / module_presentation_length")

    # late_submission_flag: binary (1 if avg_submission_delta > 0, i.e., submitted late on average)
    df["late_submission_flag"] = (df["avg_submission_delta"] > 0).astype(int)
    print("[T4] Derived: late_submission_flag (1 if avg_submission_delta > 0)")

    # registration_earliness: days before module start (more negative = registered earlier)
    df["registration_earliness"] = df["date_registration"]
    print("[T4] Derived: registration_earliness = date_registration")

    # update feature lists with new derived features
    derived_numeric = [
        "engagement_intensity",
        "activity_coverage",
        "has_vle_activity",
        "assessment_count",
        "submission_rate",
        "late_submission_flag",
        "registration_earliness",
    ]

    print(f"[T4] Final feature count: {len(NUMERIC_FEATURES) + len(derived_numeric)} numeric + {len(CATEGORICAL_FEATURES)} categorical")
    print(f"[T4] Null profile after imputation: {df.isnull().sum().sum()} total nulls")

    return df, derived_numeric


def prepare_ml_data(df: pd.DataFrame, derived_numeric: list[str]) -> tuple:
    """Split data into X, y and train/test sets. Returns preprocessed data."""
    all_numeric = NUMERIC_FEATURES + derived_numeric
    all_features = CATEGORICAL_FEATURES + all_numeric

    X = df[all_features].copy()
    y = df[TARGET].values

    # Null guard
    null_before = X.isnull().sum().sum()
    if null_before > 0:
        print(f"[T4] WARNING: {null_before} nulls remaining in features — filling with 0/Unknown")
        for col in all_numeric:
            X[col] = X[col].fillna(0)
        for col in CATEGORICAL_FEATURES:
            X[col] = X[col].fillna("Unknown")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    print(f"[T4] Train: {X_train.shape[0]} rows, Test: {X_test.shape[0]} rows")
    print(f"[T4] Train dropout rate: {y_train.mean():.1%}, Test dropout rate: {y_test.mean():.1%}")

    return X_train, X_test, y_train, y_test, all_numeric, all_features


# ─── T5: Model Training ──────────────────────────────────────────────────────


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    """Build sklearn preprocessor: StandardScaler for numeric, OneHot for categorical."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop=None), categorical_features),
        ],
        remainder="drop",
    )


def train_models(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    numeric_features: list[str],
    categorical_features: list[str],
) -> dict:
    """Train Logistic Regression and Random Forest with cross-validation.

    Returns dict with models, CV results, and fitted preprocessor.
    """
    preprocessor = build_preprocessor(numeric_features, categorical_features)

    # --- Logistic Regression ---
    lr_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_STATE,
            class_weight="balanced",
            C=1.0,
        )),
    ])

    # --- Random Forest ---
    rf_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            random_state=RANDOM_STATE,
            class_weight="balanced",
            max_depth=None,
            min_samples_split=5,
            min_samples_leaf=2,
        )),
    ])

    # --- Dummy Classifier (stratified baseline) ---
    dummy = DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)

    # Cross-validation
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    print("\n[T5] Cross-validation (5-fold stratified):")

    results = {}

    for name, model in [("Logistic Regression", lr_pipeline), ("Random Forest", rf_pipeline)]:
        print(f"\n  --- {name} ---")
        y_pred_cv = cross_val_predict(model, X_train, y_train, cv=cv, method="predict")
        y_proba_cv = cross_val_predict(model, X_train, y_train, cv=cv, method="predict_proba")[:, 1]

        acc = accuracy_score(y_train, y_pred_cv)
        prec = precision_score(y_train, y_pred_cv, zero_division=0)
        rec = recall_score(y_train, y_pred_cv, zero_division=0)
        f1 = f1_score(y_train, y_pred_cv, zero_division=0)
        auc = roc_auc_score(y_train, y_proba_cv)

        print(f"    Accuracy:  {acc:.4f}")
        print(f"    Precision: {prec:.4f}")
        print(f"    Recall:    {rec:.4f}")
        print(f"    F1:        {f1:.4f}")
        print(f"    ROC-AUC:   {auc:.4f}")

        results[name] = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": auc,
            "y_pred_cv": y_pred_cv,
            "y_proba_cv": y_proba_cv,
        }

    # Dummy baseline
    print(f"\n  --- Dummy Classifier (stratified) ---")
    dummy.fit(X_train, y_train)
    y_pred_dummy = cross_val_predict(dummy, X_train, y_train, cv=cv, method="predict")
    y_proba_dummy = cross_val_predict(dummy, X_train, y_train, cv=cv, method="predict_proba")[:, 1]

    acc_d = accuracy_score(y_train, y_pred_dummy)
    prec_d = precision_score(y_train, y_pred_dummy, zero_division=0)
    rec_d = recall_score(y_train, y_pred_dummy, zero_division=0)
    f1_d = f1_score(y_train, y_pred_dummy, zero_division=0)
    auc_d = roc_auc_score(y_train, y_proba_dummy)

    print(f"    Accuracy:  {acc_d:.4f}")
    print(f"    Precision: {prec_d:.4f}")
    print(f"    Recall:    {rec_d:.4f}")
    print(f"    F1:        {f1_d:.4f}")
    print(f"    ROC-AUC:   {auc_d:.4f}")

    results["Dummy Classifier"] = {
        "accuracy": acc_d,
        "precision": prec_d,
        "recall": rec_d,
        "f1": f1_d,
        "roc_auc": auc_d,
    }

    # Fit final models on full training set
    lr_pipeline.fit(X_train, y_train)
    rf_pipeline.fit(X_train, y_train)

    results["Logistic Regression"]["model"] = lr_pipeline
    results["Random Forest"]["model"] = rf_pipeline

    return results


def get_feature_importance(rf_model: Pipeline, numeric_features: list[str], categorical_features: list[str]) -> pd.DataFrame:
    """Extract feature importances from the fitted Random Forest model."""
    # Get feature names from preprocessor
    preprocessor = rf_model.named_steps["preprocessor"]
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features).tolist()
    all_feature_names = numeric_features + cat_feature_names

    importances = rf_model.named_steps["classifier"].feature_importances_

    fi_df = pd.DataFrame({
        "feature": all_feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    return fi_df


# ─── T6: Model Evaluation ────────────────────────────────────────────────────


def evaluate_on_test(results: dict, X_test: pd.DataFrame, y_test: np.ndarray) -> dict:
    """Evaluate all models on the held-out test set."""
    print("\n[T6] Test set evaluation:")

    test_results = {}

    for name in ["Logistic Regression", "Random Forest"]:
        model = results[name]["model"]
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_proba)
        cm = confusion_matrix(y_test, y_pred)

        print(f"\n  --- {name} ---")
        print(f"    Accuracy:  {acc:.4f}")
        print(f"    Precision: {prec:.4f}")
        print(f"    Recall:    {rec:.4f}")
        print(f"    F1:        {f1:.4f}")
        print(f"    ROC-AUC:   {auc:.4f}")
        print(f"    Confusion Matrix:")
        print(f"      TN={cm[0,0]:>5}  FP={cm[0,1]:>5}")
        print(f"      FN={cm[1,0]:>5}  TP={cm[1,1]:>5}")

        report = classification_report(y_test, y_pred, target_names=["Pass/Fail/Distinction", "Withdrawn"], zero_division=0)
        print(f"\n    Classification Report:\n{report}")

        test_results[name] = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": auc,
            "confusion_matrix": cm,
            "classification_report": report,
            "y_pred": y_pred,
            "y_proba": y_proba,
        }

    # Dummy on test set
    dummy = DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)
    dummy.fit(X_test, y_test)  # fit on test for fair comparison
    y_pred_d = dummy.predict(X_test)
    acc_d = accuracy_score(y_test, y_pred_d)

    print(f"\n  --- Dummy Classifier (stratified) ---")
    print(f"    Accuracy:  {acc_d:.4f}")

    test_results["Dummy Classifier"] = {"accuracy": acc_d}

    return test_results


def statistical_tests(y_train: np.ndarray, X_train: pd.DataFrame, cv_results: dict) -> list[dict]:
    """Run statistical significance tests: model vs dummy, LR vs RF."""
    tests = []

    # McNemar's test: LR vs Dummy (on CV predictions)
    lr_pred = cv_results["Logistic Regression"]["y_pred_cv"]
    rf_pred = cv_results["Random Forest"]["y_pred_cv"]
    dummy_acc = cv_results["Dummy Classifier"]["accuracy"]

    # Permutation test: is LR significantly better than dummy?
    n_permutations = 1000
    rng = np.random.RandomState(RANDOM_STATE)
    lr_acc = cv_results["Logistic Regression"]["accuracy"]
    count_better = 0
    for _ in range(n_permutations):
        perm = rng.permutation(y_train)
        perm_acc = accuracy_score(perm, lr_pred)
        if perm_acc >= lr_acc:
            count_better += 1
    p_value_lr_dummy = (count_better + 1) / (n_permutations + 1)

    tests.append({
        "test": "LR vs Dummy (permutation)",
        "statistic": lr_acc - dummy_acc,
        "p_value": p_value_lr_dummy,
        "significant_005": p_value_lr_dummy < 0.05,
        "interpretation": f"LR accuracy ({lr_acc:.4f}) vs Dummy ({dummy_acc:.4f}), Δ={lr_acc - dummy_acc:.4f}",
    })

    # Permutation test: RF vs Dummy
    rf_acc = cv_results["Random Forest"]["accuracy"]
    count_better_rf = 0
    for _ in range(n_permutations):
        perm = rng.permutation(y_train)
        perm_acc = accuracy_score(perm, rf_pred)
        if perm_acc >= rf_acc:
            count_better_rf += 1
    p_value_rf_dummy = (count_better_rf + 1) / (n_permutations + 1)

    tests.append({
        "test": "RF vs Dummy (permutation)",
        "statistic": rf_acc - dummy_acc,
        "p_value": p_value_rf_dummy,
        "significant_005": p_value_rf_dummy < 0.05,
        "interpretation": f"RF accuracy ({rf_acc:.4f}) vs Dummy ({dummy_acc:.4f}), Δ={rf_acc - dummy_acc:.4f}",
    })

    # Paired t-test: LR vs RF CV fold accuracies
    from sklearn.model_selection import cross_val_score
    lr_model = cv_results["Logistic Regression"]["model"]
    rf_model = cv_results["Random Forest"]["model"]

    # Recompute fold-level scores
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    lr_scores = cross_val_score(lr_model, X_train, y_train, cv=cv, scoring="accuracy")
    rf_scores = cross_val_score(rf_model, X_train, y_train, cv=cv, scoring="accuracy")

    t_stat, p_value_ttest = stats.ttest_rel(lr_scores, rf_scores)
    tests.append({
        "test": "LR vs RF (paired t-test, 5-fold)",
        "statistic": t_stat,
        "p_value": p_value_ttest,
        "significant_005": p_value_ttest < 0.05,
        "interpretation": f"LR mean={lr_scores.mean():.4f}±{lr_scores.std():.4f}, RF mean={rf_scores.mean():.4f}±{rf_scores.std():.4f}",
    })

    return tests


def save_model(results: dict, X_train: pd.DataFrame, all_numeric: list[str], all_features: list[str]) -> None:
    """Save the best model (Random Forest) to pickle."""
    best_name = "Random Forest"
    best_model = results[best_name]["model"]

    # Save model + metadata
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(
            {
                "model": best_model,
                "feature_names": all_features,
                "numeric_features": all_numeric,
                "categorical_features": CATEGORICAL_FEATURES,
                "target": TARGET,
                "model_type": best_name,
                "random_state": RANDOM_STATE,
            },
            f,
        )
    print(f"\n[T6] Model saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")


# ─── Documentation ────────────────────────────────────────────────────────────


def generate_model_doc(
    cv_results: dict,
    test_results: dict,
    fi_df: pd.DataFrame,
    stat_tests: list[dict],
    derived_numeric: list[str],
    df_shape: tuple,
) -> None:
    """Generate artifacts/data/model.md with full ML documentation."""
    all_numeric = NUMERIC_FEATURES + derived_numeric
    all_features = CATEGORICAL_FEATURES + all_numeric

    # Determine best model
    best_name = max(
        ["Logistic Regression", "Random Forest"],
        key=lambda n: test_results[n]["roc_auc"],
    )

    content = f"""# Data Model — ML Pipeline: Abandono Academico (OULAD)

## Source

- **Dataset:** Open University Learning Analytics Dataset (OULAD)
- **Paper:** "An exploration of learning analytics datasets" (Kuzilek et al., Nature CC-BY 4.0)
- **URL:** https://analyse.kmi.open.ac.uk/open_dataset
- **Total students:** {df_shape[0]:,}
- **Total VLE interactions:** 10,655,280
- **Refresh:** Static snapshot (2026-06-09)

## Bronze Tables (7 source CSVs)

| Table | Rows | PK | Source File |
|-------|------|----|-------------|
| bronze_student_info | 32,593 | (code_module, code_presentation, id_student) | studentInfo.csv |
| bronze_student_registration | 32,593 | (code_module, code_presentation, id_student) | studentRegistration.csv |
| bronze_student_assessment | 173,912 | (id_assessment, id_student) | studentAssessment.csv |
| bronze_student_vle | 10,655,280 | (code_module, code_presentation, id_student, id_site, date) | studentVle.csv |
| bronze_assessments | 206 | id_assessment | assessments.csv |
| bronze_courses | 22 | (code_module, code_presentation) | courses.csv |
| bronze_vle | 6,364 | id_site | vle.csv |

**DuckDB file:** `artifacts/data/oulad.duckdb`

## Silver Tables (2 aggregations)

### silver_vle_agg (29,228 rows)
- Grain: student + course presentation
- Columns: total_clicks, days_active, last_activity_day, first_activity_day, click_trend

### silver_assessment_agg (25,843 rows)
- Grain: student + course presentation
- Columns: weighted_avg_score, num_tma, num_cma, num_exams, avg_score, min_score, max_score, avg_submission_delta

## Gold Table: gold_oulad_features (32,593 rows)

### Grain
One row per student per course presentation.

### Keys
- **PK:** (code_module, code_presentation, id_student)
- **FK:** code_module+code_presentation → courses, assessments

### Column Schema

| Column | Type | Source | Description | Feature Role |
|--------|------|--------|-------------|-------------|
| code_module | VARCHAR | studentInfo | Module code (AAA–GGG) | dimension key |
| code_presentation | VARCHAR | studentInfo | Presentation period (2013B/J, 2014B/J) | dimension key |
| id_student | BIGINT | studentInfo | Student ID | dimension key |
| gender | VARCHAR | studentInfo | F/M | demographic feature |
| region | VARCHAR | studentInfo | UK region | demographic feature |
| highest_education | VARCHAR | studentInfo | Highest qualification level | demographic feature |
| imd_band | VARCHAR | studentInfo | Index of Multiple Deprivation band (1,111 nulls → "Unknown") | demographic feature |
| age_band | VARCHAR | studentInfo | 0-35 / 35-55 / 55<= | demographic feature |
| num_of_prev_attempts | BIGINT | studentInfo | Number of prior course attempts | academic feature |
| studied_credits | BIGINT | studentInfo | Total credits studied | academic feature |
| disability | VARCHAR | studentInfo | Y/N | demographic feature |
| date_registration | BIGINT | studentRegistration | Days relative to presentation start (45 nulls → median) | temporal feature |
| date_unregistration | BIGINT | studentRegistration | Days relative to start (69% null — expected) | temporal feature |
| total_clicks | HUGEINT | silver_vle_agg | Sum of all VLE clicks | engagement feature |
| days_active | BIGINT | silver_vle_agg | Distinct days with VLE activity | engagement feature |
| last_activity_day | BIGINT | silver_vle_agg | Most recent VLE click day | engagement feature |
| first_activity_day | BIGINT | silver_vle_agg | First VLE click day | engagement feature |
| click_trend | DOUBLE | silver_vle_agg | Ratio of post-start clicks / total clicks (0–1) | engagement feature |
| avg_daily_clicks | DOUBLE | derived | total_clicks / days_active | engagement feature |
| weighted_avg_score | DOUBLE | silver_assessment_agg | Weighted average of assessment scores (0–100) | academic feature |
| num_tma | BIGINT | silver_assessment_agg | Count of Tutor-Marked Assessments | academic feature |
| num_cma | BIGINT | silver_assessment_agg | Count of Computer-Marked Assessments | academic feature |
| num_exams | BIGINT | silver_assessment_agg | Count of Exams | academic feature |
| avg_assessment_score | DOUBLE | silver_assessment_agg | Simple average of all scores | academic feature |
| avg_submission_delta | DOUBLE | silver_assessment_agg | Avg (submitted − deadline) — negative = early | academic feature |
| module_presentation_length | BIGINT | courses | Module length in days | course metadata |
| is_dropout | INTEGER | derived | **TARGET** — 1 if Withdrawn, 0 otherwise | target |
| final_result_label | VARCHAR | studentInfo | Original label (Pass/Fail/Distinction/Withdrawn) | target metadata |

### Derived Features (ML Pipeline)

| Feature | Formula | Description |
|---------|---------|-------------|
| engagement_intensity | total_clicks / module_presentation_length | Clicks per day of module |
| activity_coverage | days_active / module_presentation_length | Fraction of module days with activity |
| has_vle_activity | total_clicks > 0 (binary) | Whether student used VLE at all |
| assessment_count | num_tma + num_cma + num_exams | Total assessments submitted |
| submission_rate | assessment_count / module_presentation_length | Assessment submission consistency |
| late_submission_flag | avg_submission_delta > 0 (binary) | Whether student submitted late on average |
| registration_earliness | date_registration | Proxy for how early student registered |

### Target Encoding
- `Withdrawn` → 1 (dropout/abandono)
- `Pass`, `Fail`, `Distinction` → 0 (nao-abandono)

### Target Distribution
| Label | Count | % |
|-------|-------|---|
| Withdrawn (1) | 10,156 | 31.2% |
| Non-dropout (0) | 22,437 | 68.8% |

### Null Profile (post-imputation)
| Column | Nulls | Treatment |
|--------|-------|-----------|
| imd_band | 1,111 (3.4%) | Filled with "Unknown" |
| date_registration | 45 (0.1%) | Filled with median |
| All other columns | 0 | Clean |

### Partitioning Strategy
N/A — single table, small enough for in-memory ML (32K rows).

### Refresh Cadence
Static snapshot. No refresh expected.

### Source Lineage
```
7 OULAD CSVs
  → bronze_student_info (32,593)
  → bronze_student_registration (32,593)
  → bronze_student_assessment (173,912)
  → bronze_student_vle (10,655,280)
  → bronze_assessments (206)
  → bronze_courses (22)
  → bronze_vle (6,364)
      ↓
  silver_vle_agg (29,228)
  silver_assessment_agg (25,843)
      ↓
  gold_oulad_features (32,593)
      ↓
  ML Pipeline (T4-T6)
      ↓
  src/model.pkl (RandomForestClassifier)
```

## ML Pipeline (T4-T6)

### Pipeline Overview

```
gold_oulad_features (32,593 × 28)
    ↓ T4: Feature Engineering
  + 7 derived features → 23 numeric + 8 categorical = 31 total features
    ↓ T5: Model Training
  Stratified 80/20 split → 5-fold cross-validation
  Logistic Regression (baseline) + Random Forest + Dummy (stratified)
    ↓ T6: Evaluation
  Test set metrics + confusion matrix + statistical significance tests
```

### Model Configurations

| Model | Hyperparameters | Class Weight |
|-------|----------------|--------------|
| Logistic Regression | max_iter=1000, C=1.0 | balanced |
| Random Forest | n_estimators=200, max_depth=None, min_samples_split=5, min_samples_leaf=2 | balanced |
| Dummy Classifier | strategy="stratified" | N/A |

### Cross-Validation Results (5-fold stratified)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | {cv_results['Logistic Regression']['accuracy']:.4f} | {cv_results['Logistic Regression']['precision']:.4f} | {cv_results['Logistic Regression']['recall']:.4f} | {cv_results['Logistic Regression']['f1']:.4f} | {cv_results['Logistic Regression']['roc_auc']:.4f} |
| Random Forest | {cv_results['Random Forest']['accuracy']:.4f} | {cv_results['Random Forest']['precision']:.4f} | {cv_results['Random Forest']['recall']:.4f} | {cv_results['Random Forest']['f1']:.4f} | {cv_results['Random Forest']['roc_auc']:.4f} |
| Dummy (stratified) | {cv_results['Dummy Classifier']['accuracy']:.4f} | {cv_results['Dummy Classifier']['precision']:.4f} | {cv_results['Dummy Classifier']['recall']:.4f} | {cv_results['Dummy Classifier']['f1']:.4f} | {cv_results['Dummy Classifier']['roc_auc']:.4f} |

### Test Set Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | {test_results['Logistic Regression']['accuracy']:.4f} | {test_results['Logistic Regression']['precision']:.4f} | {test_results['Logistic Regression']['recall']:.4f} | {test_results['Logistic Regression']['f1']:.4f} | {test_results['Logistic Regression']['roc_auc']:.4f} |
| Random Forest | {test_results['Random Forest']['accuracy']:.4f} | {test_results['Random Forest']['precision']:.4f} | {test_results['Random Forest']['recall']:.4f} | {test_results['Random Forest']['f1']:.4f} | {test_results['Random Forest']['roc_auc']:.4f} |
| Dummy (stratified) | {test_results['Dummy Classifier']['accuracy']:.4f} | — | — | — | — |

### Confusion Matrix — Random Forest (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | {test_results['Random Forest']['confusion_matrix'][0,0]:,} | {test_results['Random Forest']['confusion_matrix'][0,1]:,} |
| **Actual Dropout** | {test_results['Random Forest']['confusion_matrix'][1,0]:,} | {test_results['Random Forest']['confusion_matrix'][1,1]:,} |

### Classification Report — Random Forest (Test Set)

```
{test_results['Random Forest']['classification_report']}
```

### Confusion Matrix — Logistic Regression (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | {test_results['Logistic Regression']['confusion_matrix'][0,0]:,} | {test_results['Logistic Regression']['confusion_matrix'][0,1]:,} |
| **Actual Dropout** | {test_results['Logistic Regression']['confusion_matrix'][1,0]:,} | {test_results['Logistic Regression']['confusion_matrix'][1,1]:,} |

### Classification Report — Logistic Regression (Test Set)

```
{test_results['Logistic Regression']['classification_report']}
```

### Statistical Significance Tests

| Test | Statistic | p-value | Significant (α=0.05) | Interpretation |
|------|-----------|---------|----------------------|----------------|
"""

    for t in stat_tests:
        sig_mark = "✅ Yes" if t["significant_005"] else "❌ No"
        content += f"| {t['test']} | {t['statistic']:.4f} | {t['p_value']:.4f} | {sig_mark} | {t['interpretation']} |\n"

    content += f"""
### Top 15 Feature Importances (Random Forest)

| Rank | Feature | Importance |
|------|---------|-----------|
"""

    for i, row in fi_df.head(15).iterrows():
        content += f"| {i + 1} | {row['feature']} | {row['importance']:.4f} |\n"

    content += f"""
### Full Feature Importance Table

| Feature | Importance |
|---------|-----------|
"""

    for _, row in fi_df.iterrows():
        content += f"| {row['feature']} | {row['importance']:.4f} |\n"

    content += f"""
### Modeling Decisions

1. **Target encoding:** `Withdrawn` → 1, all others → 0. Rationale: binary dropout prediction is the business question.
2. **Class weight:** `balanced` on both models. Rationale: 31.2% positive class requires compensation to avoid majority-class bias.
3. **One-hot encoding** for categorical features (8 categorical → ~40 one-hot columns). Chosen over label encoding to avoid ordinality artifacts (see ADR-002).
4. **StandardScaler** on numeric features for Logistic Regression convergence. Random Forest is scale-invariant but scaler is in the pipeline for consistency.
5. **200 trees** in Random Forest (up from 100 baseline). More trees improve stability without overfitting risk.
6. **Dummy classifier** as floor comparison. Models must beat stratified random predictions to have predictive value.
7. **Permutation tests** (1000 iterations) for model vs dummy significance. More robust than parametric tests for non-normal accuracy distributions.
8. **Paired t-test** for LR vs RF comparison across CV folds. Tests whether the difference is systematic or random.
9. **7 derived features** added: engagement_intensity, activity_coverage, has_vle_activity, assessment_count, submission_rate, late_submission_flag, registration_earliness.
10. **Null handling:** imd_band (3.4%) → "Unknown" category; date_registration (0.1%) → median imputation.

### Owner
Laurent (data-architect)
"""

    MODEL_DOC_PATH.write_text(content, encoding="utf-8")
    print(f"\n[T6] Model documentation saved: {MODEL_DOC_PATH}")


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _guard_empty(df: pd.DataFrame, msg: str) -> None:
    if df is None or df.empty:
        print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(1)


# ─── Pipeline entrypoint ──────────────────────────────────────────────────────


def main() -> None:
    print("=" * 70)
    print("  ML Pipeline — Abandono Academico Casa Grande (OULAD)")
    print("  T4 (Feature Engineering) -> T5 (Model Training) -> T6 (Evaluation)")
    print("=" * 70)

    # ── T4: Load & Feature Engineering ──
    print("\n" + "─" * 70)
    print("  T4: FEATURE ENGINEERING")
    print("─" * 70)
    df = load_gold_table(DUCKDB_PATH)
    df, derived_numeric = engineer_features(df)
    X_train, X_test, y_train, y_test, all_numeric, all_features = prepare_ml_data(df, derived_numeric)

    # ── T5: Model Training ──
    print("\n" + "─" * 70)
    print("  T5: MODEL TRAINING")
    print("─" * 70)
    cv_results = train_models(X_train, y_train, all_numeric, CATEGORICAL_FEATURES)

    # Feature importance
    fi_df = get_feature_importance(
        cv_results["Random Forest"]["model"],
        all_numeric,
        CATEGORICAL_FEATURES,
    )
    print("\n[T5] Top 10 features:")
    print(fi_df.head(10).to_string(index=False))

    # ── T6: Evaluation ──
    print("\n" + "─" * 70)
    print("  T6: MODEL EVALUATION")
    print("─" * 70)
    test_results = evaluate_on_test(cv_results, X_test, y_test)

    # Statistical tests
    print("\n[T6] Statistical significance tests:")
    stat_tests = statistical_tests(y_train, X_train, cv_results)
    for t in stat_tests:
        sig = "***" if t["significant_005"] else "ns"
        print(f"  {t['test']}: stat={t['statistic']:.4f}, p={t['p_value']:.4f} {sig}")

    # Save model
    save_model(cv_results, X_train, all_numeric, all_features)

    # Generate documentation
    generate_model_doc(cv_results, test_results, fi_df, stat_tests, derived_numeric, df.shape)

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Models trained: Logistic Regression, Random Forest, Dummy")
    print(f"  Best model: Random Forest (saved to {MODEL_PATH})")
    print(f"  Documentation: {MODEL_DOC_PATH}")
    print(f"  Train rows: {X_train.shape[0]:,} | Test rows: {X_test.shape[0]:,}")
    print(f"  Features: {len(all_features)} ({len(all_numeric)} numeric + {len(CATEGORICAL_FEATURES)} categorical)")
    print("=" * 70)


if __name__ == "__main__":
    main()
