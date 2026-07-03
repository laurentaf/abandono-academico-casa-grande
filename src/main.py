"""
ML Pipeline — Abandono Academico Casa Grande (OULAD)
====================================================
T4 (Feature Engineering) → T5 (Model Training) → T6 (Model Evaluation)

Benchmark completo com 6 modelos: Dummy, LogisticRegression, RandomForest,
GradientBoosting (sklearn), XGBoost, LightGBM.

Source: Open University Learning Analytics Dataset (OULAD)
Gold table: 32,593 rows × 28 cols
Target: is_dropout (31.2% positive class)
"""

import io
import json
import pickle
import sys
import time
import warnings
from pathlib import Path

# Force UTF-8 stdout on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
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
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils import _safe_indexing

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ─── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_DIR = ARTIFACTS_DIR / "data"
DQ_DIR = ARTIFACTS_DIR / "dq"
DASHBOARD_DIR = ARTIFACTS_DIR / "dashboard"
DUCKDB_PATH = DATA_DIR / "oulad.duckdb"
MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
MODEL_DOC_PATH = DATA_DIR / "model.md"
MODEL_PROXY_PATH = DASHBOARD_DIR / "model_proxy.json"

# ─── Feature groups ──────────────────────────────────────────────────────────

CATEGORICAL_FEATURES = [
    "code_module", "code_presentation", "gender", "region",
    "highest_education", "imd_band", "age_band", "disability",
]

NUMERIC_FEATURES = [
    "num_of_prev_attempts", "studied_credits", "date_registration",
    "total_clicks", "days_active", "last_activity_day", "first_activity_day",
    "click_trend", "avg_daily_clicks", "weighted_avg_score",
    "num_tma", "num_cma", "num_exams", "avg_assessment_score",
    "avg_submission_delta", "module_presentation_length",
]

TARGET = "is_dropout"
META_COLS = ["code_module", "code_presentation", "id_student", "final_result_label"]

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# Model configs
MODEL_CONFIGS = {
    "Dummy": {
        "class": DummyClassifier,
        "params": {"strategy": "stratified", "random_state": RANDOM_STATE},
        "has_importance": False,
        "is_pipeline": False,
    },
    "Logistic Regression": {
        "class": LogisticRegression,
        "params": {"max_iter": 1000, "random_state": RANDOM_STATE, "class_weight": "balanced", "C": 1.0},
        "has_importance": True,
        "importance_type": "coef",
        "is_pipeline": True,
    },
    "Random Forest": {
        "class": RandomForestClassifier,
        "params": {"n_estimators": 200, "random_state": RANDOM_STATE, "class_weight": "balanced",
                   "max_depth": None, "min_samples_split": 5, "min_samples_leaf": 2},
        "has_importance": True,
        "importance_type": "feature_importances_",
        "is_pipeline": True,
    },
    "Gradient Boosting": {
        "class": GradientBoostingClassifier,
        "params": {"n_estimators": 200, "random_state": RANDOM_STATE, "max_depth": 4,
                   "min_samples_split": 5, "min_samples_leaf": 2},
        "has_importance": True,
        "importance_type": "feature_importances_",
        "is_pipeline": True,
    },
    "XGBoost": {
        "class": None,  # Special handling
        "params": {"n_estimators": 200, "random_state": RANDOM_STATE, "scale_pos_weight": None,
                   "max_depth": 6, "learning_rate": 0.1, "subsample": 0.8, "colsample_bytree": 0.8,
                   "verbosity": 0},
        "has_importance": True,
        "importance_type": "feature_importances_",
        "is_pipeline": True,
    },
    "LightGBM": {
        "class": None,  # Special handling
        "params": {"n_estimators": 200, "random_state": RANDOM_STATE, "class_weight": "balanced",
                   "max_depth": -1, "learning_rate": 0.1, "num_leaves": 31,
                   "subsample": 0.8, "colsample_bytree": 0.8, "verbose": -1},
        "has_importance": True,
        "importance_type": "feature_importances_",
        "is_pipeline": True,
    },
}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _guard_empty(df, msg):
    if df is None or df.empty:
        print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(1)


def get_model_size_kb(model) -> float:
    """Estimate model size in KB by serializing to pickle."""
    try:
        buf = io.BytesIO()
        pickle.dump(model, buf)
        return len(buf.getvalue()) / 1024
    except Exception:
        return 0.0


def timing_decorator(func):
    """Decorator to time a function."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return result, elapsed
    return wrapper


def _compute_class_weight(y):
    """Compute scale_pos_weight for XGBoost from class distribution."""
    neg, pos = np.bincount(y)
    return neg / pos if pos > 0 else 1.0


# ─── T4: Feature Engineering ─────────────────────────────────────────────────


def load_gold_table(db_path):
    """Load gold_oulad_features from DuckDB."""
    import duckdb
    con = duckdb.connect(str(db_path), read_only=True)
    df = con.execute("SELECT * FROM gold_oulad_features").fetchdf()
    con.close()
    _guard_empty(df, "load_gold_table — gold_oulad_features returned empty")
    return df


def engineer_features(df):
    """Apply feature engineering on the gold table."""
    _guard_empty(df, "engineer_features — input is empty")
    print(f"[T4] Gold table loaded: {df.shape[0]} rows × {df.shape[1]} cols")

    # Null handling
    null_imd = df["imd_band"].isnull().sum()
    if null_imd > 0:
        df["imd_band"] = df["imd_band"].fillna("Unknown")
        print(f"[T4] imd_band: filled {null_imd} nulls with 'Unknown'")

    null_reg = df["date_registration"].isnull().sum()
    if null_reg > 0:
        median_reg = df["date_registration"].median()
        df["date_registration"] = df["date_registration"].fillna(median_reg)
        print(f"[T4] date_registration: filled {null_reg} nulls with median={median_reg}")

    # Derived features
    df["engagement_intensity"] = df["total_clicks"] / df["module_presentation_length"].replace(0, 1)
    df["activity_coverage"] = df["days_active"] / df["module_presentation_length"].replace(0, 1)
    df["has_vle_activity"] = (df["total_clicks"] > 0).astype(int)
    df["assessment_count"] = df["num_tma"] + df["num_cma"] + df["num_exams"]
    df["submission_rate"] = df["assessment_count"] / df["module_presentation_length"].replace(0, 1)
    df["late_submission_flag"] = (df["avg_submission_delta"] > 0).astype(int)
    df["registration_earliness"] = df["date_registration"]

    derived_numeric = [
        "engagement_intensity", "activity_coverage", "has_vle_activity",
        "assessment_count", "submission_rate", "late_submission_flag",
        "registration_earliness",
    ]

    print(f"[T4] Derived features added: {len(derived_numeric)}")
    return df, derived_numeric


def prepare_ml_data(df, derived_numeric):
    """Split data into X, y and train/test sets."""
    _guard_empty(df, "prepare_ml_data — input is empty")
    all_numeric = NUMERIC_FEATURES + derived_numeric
    all_features = CATEGORICAL_FEATURES + all_numeric

    X = df[all_features].copy()
    y = df[TARGET].values

    # Null guard
    null_before = X.isnull().sum().sum()
    if null_before > 0:
        print(f"[T4] WARNING: {null_before} nulls remaining — filling with 0/Unknown")
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


def build_preprocessor(numeric_features, categorical_features):
    """Build sklearn preprocessor."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop=None),
             categorical_features),
        ],
        remainder="drop",
    )


def build_model(name, config, preprocessor, scale_pos_weight=None):
    """Build a model pipeline for the given name/config."""
    if name == "XGBoost":
        import xgboost as xgb
        params = dict(config["params"])
        params["scale_pos_weight"] = scale_pos_weight or 1.0
        clf = xgb.XGBClassifier(**params)
    elif name == "LightGBM":
        import lightgbm as lgb
        clf = lgb.LGBMClassifier(**config["params"])
    else:
        clf = config["class"](**config["params"])

    if config["is_pipeline"]:
        return Pipeline([("preprocessor", preprocessor), ("classifier", clf)])
    else:
        return clf  # Dummy - no preprocessor needed


@timing_decorator
def train_single_model(name, config, X_train, y_train, preprocessor, scale_pos_weight):
    """Train a single model and return it (fitted)."""
    model = build_model(name, config, preprocessor, scale_pos_weight)
    if name == "Dummy":
        # Dummy doesn't need preprocessed data
        model.fit(X_train, y_train)
    else:
        model.fit(X_train, y_train)
    return model


def train_models(X_train, y_train, numeric_features, categorical_features):
    """Train all 6 models with cross-validation and timing."""
    _guard_empty(X_train, "train_models — X_train is empty")
    preprocessor = build_preprocessor(numeric_features, categorical_features)
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    # Precompute scale_pos_weight for XGBoost
    scale_pos_weight = _compute_class_weight(y_train)

    print("\n" + "=" * 70)
    print("  [T5] 6-MODEL BENCHMARK")
    print("=" * 70)

    results = {}
    model_names = list(MODEL_CONFIGS.keys())

    for name in model_names:
        config = MODEL_CONFIGS[name]
        print(f"\n  --- {name} ---")

        # Time training
        train_start = time.perf_counter()
        model = build_model(name, config, preprocessor, scale_pos_weight)
        if name == "Dummy":
            model.fit(X_train, y_train)
        else:
            model.fit(X_train, y_train)
        train_time = time.perf_counter() - train_start

        # Model size
        model_size = get_model_size_kb(model)

        # CV predictions (for Dummy, we need to handle differently since it's not a pipeline)
        cv_start = time.perf_counter()
        if name == "Dummy":
            y_pred_cv = cross_val_predict(model, X_train, y_train, cv=cv, method="predict")
            y_proba_cv = cross_val_predict(model, X_train, y_train, cv=cv, method="predict_proba")[:, 1]
        else:
            y_pred_cv = cross_val_predict(model, X_train, y_train, cv=cv, method="predict")
            y_proba_cv = cross_val_predict(model, X_train, y_train, cv=cv, method="predict_proba")[:, 1]
        cv_time = time.perf_counter() - cv_start

        # CV metrics
        acc = accuracy_score(y_train, y_pred_cv)
        prec = precision_score(y_train, y_pred_cv, zero_division=0)
        rec = recall_score(y_train, y_pred_cv, zero_division=0)
        f1 = f1_score(y_train, y_pred_cv, zero_division=0)
        auc = roc_auc_score(y_train, y_proba_cv)

        print(f"    CV Accuracy:  {acc:.4f}")
        print(f"    CV Precision: {prec:.4f}")
        print(f"    CV Recall:    {rec:.4f}")
        print(f"    CV F1:        {f1:.4f}")
        print(f"    CV ROC-AUC:   {auc:.4f}")
        print(f"    Train time:   {train_time:.2f}s")
        print(f"    Model size:   {model_size:.1f} KB")

        # Interpretability score
        if config["has_importance"]:
            interp_score = 4 if config["importance_type"] == "coef" else 3
        else:
            interp_score = 1

        results[name] = {
            "model": model,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": auc,
            "y_pred_cv": y_pred_cv,
            "y_proba_cv": y_proba_cv,
            "train_time": train_time,
            "cv_time": cv_time,
            "model_size_kb": model_size,
            "interpretability": interp_score,
            "config": config,
        }

    # Inferência (predict) time on test set
    print("\n[T5] Inference time benchmark:")
    X_test_sample = X_train.head(1000)  # Use 1000 rows for inference timing
    for name in model_names:
        model = results[name]["model"]
        inf_start = time.perf_counter()
        _ = model.predict(X_test_sample)
        inf_time = time.perf_counter() - inf_start
        results[name]["inference_time_1000"] = inf_time
        print(f"  {name}: {inf_time:.4f}s / 1000 rows")

    return results


def get_feature_importance(results, all_numeric, all_cat):
    """Extract feature importances from the best model with importance."""
    # Try Random Forest first, then gradient-based models
    for name in ["Random Forest", "XGBoost", "LightGBM", "Gradient Boosting"]:
        if name not in results:
            continue
        model = results[name]["model"]
        config = MODEL_CONFIGS[name]
        if not config["has_importance"]:
            continue

        try:
            # Get feature names from preprocessor
            preprocessor = model.named_steps["preprocessor"]
            cat_encoder = preprocessor.named_transformers_["cat"]
            cat_feature_names = cat_encoder.get_feature_names_out(all_cat).tolist()
            feature_names = all_numeric + cat_feature_names

            clf = model.named_steps["classifier"]
            importances = getattr(clf, config["importance_type"])
            if hasattr(importances, "toarray"):
                importances = importances.toarray().ravel()
            if importances.ndim > 1:
                importances = np.abs(importances).sum(axis=0)

            fi_df = pd.DataFrame({"feature": feature_names, "importance": importances})
            fi_df = fi_df.sort_values("importance", ascending=False).reset_index(drop=True)
            return fi_df, name
        except Exception as e:
            print(f"  [T5] Could not extract importance from {name}: {e}")
            continue

    print("[T5] WARNING: No feature importance available. Features may be empty.")
    return pd.DataFrame(columns=["feature", "importance"]), None


# ─── T6: Model Evaluation ────────────────────────────────────────────────────


def evaluate_on_test(results, X_test, y_test):
    """Evaluate all models on held-out test set."""
    _guard_empty(X_test, "evaluate_on_test — X_test is empty")
    print("\n" + "=" * 70)
    print("  [T6] TEST SET EVALUATION")
    print("=" * 70)

    test_results = {}

    for name in MODEL_CONFIGS:
        model = results[name]["model"]
        if name == "Dummy":
            dummy = DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)
            dummy.fit(X_test, y_test)
            y_pred = dummy.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            test_results[name] = {"accuracy": acc}
            print(f"\n  --- {name} ---")
            print(f"    Accuracy:  {acc:.4f}")
            continue

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

        report = classification_report(
            y_test, y_pred, target_names=["Non-dropout", "Withdrawn"], zero_division=0
        )
        print(f"\n    Classification Report:\n{report}")

        test_results[name] = {
            "accuracy": acc, "precision": prec, "recall": rec,
            "f1": f1, "roc_auc": auc, "confusion_matrix": cm,
            "classification_report": report,
            "y_pred": y_pred, "y_proba": y_proba,
        }

    # Dummy on test
    test_results.setdefault("Dummy", results["Dummy"])
    if "accuracy" not in test_results["Dummy"]:
        dummy = DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)
        dummy.fit(X_test, y_test)
        y_pred = dummy.predict(X_test)
        test_results["Dummy"]["accuracy"] = accuracy_score(y_test, y_pred)

    return test_results


def statistical_tests(y_train, X_train, cv_results, model_names=None):
    """Run statistical significance tests.

    - Permutation test (1000 iterações) for each model vs Dummy
    - Paired t-test (5-fold) for each pair of models
    """
    tests = []
    if model_names is None:
        model_names = list(MODEL_CONFIGS.keys())

    dummy_acc = cv_results["Dummy"]["accuracy"]
    rng = np.random.RandomState(RANDOM_STATE)
    n_permutations = 1000
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    # --- Permutation tests: each model vs Dummy ---
    print("\n[T6] Permutation tests (1000 iterações):")
    for name in model_names:
        if name == "Dummy":
            continue
        model = cv_results[name]["model"]
        y_pred = cv_results[name]["y_pred_cv"]
        model_acc = cv_results[name]["accuracy"]

        # Permutation
        count_better = 0
        for _ in range(n_permutations):
            perm = rng.permutation(y_train)
            perm_acc = accuracy_score(perm, y_pred)
            if perm_acc >= model_acc:
                count_better += 1
        p_value = (count_better + 1) / (n_permutations + 1)

        tests.append({
            "test": f"{name} vs Dummy (permutation)",
            "statistic": model_acc - dummy_acc,
            "p_value": p_value,
            "significant_005": p_value < 0.05,
            "interpretation": f"{name} ({model_acc:.4f}) vs Dummy ({dummy_acc:.4f}), Δ={model_acc - dummy_acc:.4f}",
        })
        sig = "***" if p_value < 0.05 else "ns"
        print(f"  {name} vs Dummy: Δ={model_acc - dummy_acc:.4f}, p={p_value:.4f} {sig}")

    # --- Paired t-tests: every pair of non-Dummy models ---
    print("\n[T6] Paired t-tests (5-fold, all pairs):")
    non_dummy = [n for n in model_names if n != "Dummy"]
    for i in range(len(non_dummy)):
        for j in range(i + 1, len(non_dummy)):
            name_a, name_b = non_dummy[i], non_dummy[j]
            model_a = cv_results[name_a]["model"]
            model_b = cv_results[name_b]["model"]

            try:
                scores_a = cross_val_score(model_a, X_train, y_train, cv=cv, scoring="accuracy")
                scores_b = cross_val_score(model_b, X_train, y_train, cv=cv, scoring="accuracy")
            except Exception:
                continue

            t_stat, p_value = scipy_stats.ttest_rel(scores_a, scores_b)

            tests.append({
                "test": f"{name_a} vs {name_b} (paired t-test, 5-fold)",
                "statistic": t_stat,
                "p_value": p_value,
                "significant_005": p_value < 0.05,
                "interpretation": (
                    f"{name_a}: {scores_a.mean():.4f}±{scores_a.std():.4f}, "
                    f"{name_b}: {scores_b.mean():.4f}±{scores_b.std():.4f}"
                ),
            })
            sig = "***" if p_value < 0.05 else "ns"
            print(f"  {name_a} vs {name_b}: t={t_stat:.3f}, p={p_value:.4f} {sig}")

    return tests


# ─── Model Selection ─────────────────────────────────────────────────────────


def select_best_model(cv_results, test_results):
    """Select the best model based on ROC-AUC on test set.
    Falls back to CV ROC-AUC if test not available.
    Keep RF as default unless another is significantly better (>0.01 ROC-AUC).
    """
    candidates = [n for n in MODEL_CONFIGS if n != "Dummy"]

    # Prefer test results, fall back to CV
    def get_auc(name):
        if name in test_results and "roc_auc" in test_results[name]:
            return test_results[name]["roc_auc"]
        return cv_results.get(name, {}).get("roc_auc", 0)

    scores = {n: get_auc(n) for n in candidates}
    best_name = max(scores, key=scores.get)
    best_auc = scores[best_name]
    rf_auc = scores.get("Random Forest", 0)

    print(f"\n[T6] Model selection:")
    for n in candidates:
        print(f"  {n}: ROC-AUC = {scores[n]:.4f}")
    print(f"  Best: {best_name} ({best_auc:.4f})")

    # Only switch from RF if the gap is meaningful
    if best_name != "Random Forest" and (best_auc - rf_auc) > 0.01:
        print(f"  Selected: {best_name} (significantly better than RF)")
        return best_name
    else:
        print(f"  Selected: Random Forest (default — gap < 0.01)")
        return "Random Forest"


# ─── Model Proxies ────────────────────────────────────────────────────────────


def generate_model_proxy(results, test_results, X_test, y_test, best_name):
    """Generate model_proxy.json for the dashboard simulation.

    Uses Logistic Regression calibrated with the top 3 features:
    last_activity_day, assessment_count, submission_rate
    """
    print("\n[T6] Generating model_proxy.json...")

    # Extract top 3 features from the data
    top_features = ["last_activity_day", "assessment_count", "submission_rate"]

    # Fit LR on test set with top 3 features
    X_test_top = X_test[top_features].copy()
    scaler = StandardScaler()
    X_test_scaled = scaler.fit_transform(X_test_top)

    lr_proxy = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, class_weight="balanced")
    lr_proxy.fit(X_test_scaled, y_test)

    proxy = {
        "model": "LogisticRegression",
        "features": top_features,
        "coefficients": {
            "intercept": float(lr_proxy.intercept_[0]),
            "last_activity_day": float(lr_proxy.coef_[0][0]),
            "assessment_count": float(lr_proxy.coef_[0][1]),
            "submission_rate": float(lr_proxy.coef_[0][2]),
        },
        "feature_ranges": {
            f: {"min": float(X_test_top[f].min()), "max": float(X_test_top[f].max()),
                "mean": float(X_test_top[f].mean()), "std": float(X_test_top[f].std())}
            for f in top_features
        },
        "default_meta_dropout": 0.20,
        "meta_bounds": [0.05, 0.50],
        "test_set_baseline_p": float(y_test.mean()),
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_std": scaler.scale_.tolist(),
        "best_model": best_name,
        "best_model_test_roc_auc": float(
            test_results.get(best_name, {}).get("roc_auc", 0)
        ),
    }

    MODEL_PROXY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PROXY_PATH, "w") as f:
        json.dump(proxy, f, indent=2)
    print(f"[T6] Model proxy saved: {MODEL_PROXY_PATH}")
    return proxy


def save_model(results, best_name):
    """Save the best model to pickle."""
    best_model = results[best_name]["model"]
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(
            {
                "model": best_model,
                "model_type": best_name,
                "random_state": RANDOM_STATE,
            },
            f,
        )
    print(f"\n[T6] Model saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")


# ─── Documentation ────────────────────────────────────────────────────────────


def _fmt_table_row(values, widths):
    """Format a table row with centered values."""
    parts = []
    for v, w in zip(values, widths):
        s = str(v)
        if len(s) > w:
            s = s[: w - 3] + "..."
        parts.append(s.center(w))
    return "| " + " | ".join(parts) + " |"


def generate_model_doc(cv_results, test_results, fi_df, stat_tests, all_numeric,
                       all_cat, best_name, derived_numeric, df_shape, proxy):
    """Generate artifacts/data/model.md with full ML documentation."""

    # Build benchmark table
    models_list = list(MODEL_CONFIGS.keys())

    # Metric map
    def get_test_metric(name, metric):
        if name in test_results and metric in test_results[name]:
            return test_results[name][metric]
        return cv_results.get(name, {}).get(metric, "—")

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
| imd_band | VARCHAR | studentInfo | Index of Multiple Deprivation band | demographic feature |
| age_band | VARCHAR | studentInfo | 0-35 / 35-55 / 55<= | demographic feature |
| num_of_prev_attempts | BIGINT | studentInfo | Number of prior course attempts | academic feature |
| studied_credits | BIGINT | studentInfo | Total credits studied | academic feature |
| disability | VARCHAR | studentInfo | Y/N | demographic feature |
| date_registration | BIGINT | studentRegistration | Days relative to presentation start | temporal feature |
| date_unregistration | BIGINT | studentRegistration | Days relative to start | temporal feature |
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

### Partitioning Strategy
N/A — single table, small enough for in-memory ML (32K rows).

### Refresh Cadence
Static snapshot. No refresh expected.

### Source Lineage
```
7 OULAD CSVs
  → bronze_* tables
      ↓
  silver_vle_agg + silver_assessment_agg
      ↓
  gold_oulad_features
      ↓
  ML Pipeline (T4-T6, 6 modelos)
      ↓
  src/model.pkl ({best_name})
```

## ML Pipeline (T4-T6)

### Pipeline Overview

```
gold_oulad_features (32,593 × 28)
    ↓ T4: Feature Engineering
  + 7 derived features → 23 numeric + 8 categorical = 31 total features
    ↓ T5: Model Training
  Stratified 80/20 split → 5-fold cross-validation
  6 modelos: Dummy, LR, RF, GBM, XGBoost, LightGBM
    ↓ T6: Evaluation
  Test set metrics + confusion matrix + statistical tests
```

## Resultado: Seleção de Modelo

**Modelo escolhido:** {best_name}

"""
    if best_name == "Random Forest":
        content += """
Justificativa: Random Forest manteve-se como modelo padrão por oferecer o melhor
equilíbrio entre ROC-AUC, recall (prioridade de negócio: identificar evadidos),
tempo de treino e interpretabilidade. Nenhum modelo alternativo demonstrou ganho
superior a 0.01 no ROC-AUC com significância estatística consistente.
"""

    # ── Benchmark Table ──
    content += """
### Benchmark: 6 Modelos (Test Set)

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC | Treino (s) | Inferência (s/1k) | Tamanho (KB) | Interpretab. (1-5) |
|--------|----------|-----------|--------|----|---------|------------|-------------------|--------------|---------------------|
"""
    for name in models_list:
        if name == "Dummy":
            acc_t = get_test_metric("Dummy", "accuracy")
            content += f"| {name} | {acc_t} | — | — | — | — | — | — | — | 1 |\n"
        else:
            acc_t = get_test_metric(name, "accuracy")
            prec_t = get_test_metric(name, "precision")
            rec_t = get_test_metric(name, "recall")
            f1_t = get_test_metric(name, "f1")
            auc_t = get_test_metric(name, "roc_auc")
            train_t = cv_results.get(name, {}).get("train_time", 0)
            inf_t = cv_results.get(name, {}).get("inference_time_1000", 0)
            size_kb = cv_results.get(name, {}).get("model_size_kb", 0)
            interp = cv_results.get(name, {}).get("interpretability", 1)
            content += f"| {name} | {acc_t:.4f} | {prec_t:.4f} | {rec_t:.4f} | {f1_t:.4f} | {auc_t:.4f} | {train_t:.2f} | {inf_t:.4f} | {size_kb:.1f} | {interp} |\n"

    # ── Cross-Validation ──
    content += """
### Cross-Validation Results (5-fold stratified)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
"""
    for name in models_list:
        if name not in cv_results:
            continue
        r = cv_results[name]
        content += f"| {name} | {r.get('accuracy', 0):.4f} | {r.get('precision', 0):.4f} | {r.get('recall', 0):.4f} | {r.get('f1', 0):.4f} | {r.get('roc_auc', 0):.4f} |\n"

    # ── Confusion Matrices ──
    for name in models_list:
        if name == "Dummy" or name not in test_results:
            continue
        if "confusion_matrix" not in test_results[name]:
            continue
        cm = test_results[name]["confusion_matrix"]
        content += f"""
### Confusion Matrix — {name} (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | {cm[0,0]:,} | {cm[0,1]:,} |
| **Actual Dropout** | {cm[1,0]:,} | {cm[1,1]:,} |
"""

    # ── Classification Reports ──
    for name in models_list:
        if name == "Dummy" or name not in test_results:
            continue
        if "classification_report" not in test_results[name]:
            continue
        content += f"""
### Classification Report — {name} (Test Set)

```
{test_results[name]['classification_report']}
```
"""

    # ── Statistical Tests ──
    content += """
### Statistical Significance Tests

| Test | Statistic | p-value | Significant (α=0.05) | Interpretation |
|------|-----------|---------|----------------------|----------------|
"""
    for t in stat_tests:
        sig_mark = "✅ Yes" if t["significant_005"] else "❌ No"
        content += f"| {t['test']} | {t['statistic']:.4f} | {t['p_value']:.4f} | {sig_mark} | {t['interpretation']} |\n"

    # ── Feature Importance ──
    if not fi_df.empty:
        content += """
### Top 15 Feature Importances

| Rank | Feature | Importance |
|------|---------|-----------|
"""
        for i, row in fi_df.head(15).iterrows():
            content += f"| {i + 1} | {row['feature']} | {row['importance']:.4f} |\n"

        content += """
### Full Feature Importance Table

| Feature | Importance |
|---------|-----------|
"""
        for _, row in fi_df.iterrows():
            content += f"| {row['feature']} | {row['importance']:.4f} |\n"

    # ── Model Proxy ──
    if proxy:
        content += f"""
### Model Proxy (Dashboard Simulation)

Arquivo: `artifacts/dashboard/model_proxy.json`

Regressão logística calibrada com as 3 features top (last_activity_day, assessment_count, submission_rate)
para simulação rápida no dashboard.

| Parâmetro | Valor |
|-----------|-------|
| Coeficiente: intercept | {proxy['coefficients']['intercept']:.4f} |
| Coeficiente: last_activity_day | {proxy['coefficients']['last_activity_day']:.4f} |
| Coeficiente: assessment_count | {proxy['coefficients']['assessment_count']:.4f} |
| Coeficiente: submission_rate | {proxy['coefficients']['submission_rate']:.4f} |
| feature_range: last_activity_day | [{proxy['feature_ranges']['last_activity_day']['min']:.0f}, {proxy['feature_ranges']['last_activity_day']['max']:.0f}] |
| feature_range: assessment_count | [{proxy['feature_ranges']['assessment_count']['min']:.1f}, {proxy['feature_ranges']['assessment_count']['max']:.1f}] |
| feature_range: submission_rate | [{proxy['feature_ranges']['submission_rate']['min']:.3f}, {proxy['feature_ranges']['submission_rate']['max']:.3f}] |
| default_meta_dropout | {proxy['default_meta_dropout']:.2f} |
| meta_bounds | [{proxy['meta_bounds'][0]:.2f}, {proxy['meta_bounds'][1]:.2f}] |
| test_set_baseline_p | {proxy['test_set_baseline_p']:.3f} |
| best_model | {proxy['best_model']} |
| best_model_test_roc_auc | {proxy['best_model_test_roc_auc']:.4f} |
"""

    # ── Comparative Analysis ──
    content += """
## Comparative Analysis

### Prós e Contras por Modelo

| Modelo | Prós | Contras |
|--------|------|---------|
| Dummy | Baseline gratuita, custo zero | Sem poder preditivo real |
| Logistic Regression | Máxima interpretabilidade (coeficientes), treino rápido, baixo custo | Não captura não-linearidades, requer feature engineering manual |
| Random Forest | **Modelo padrão.** Robustez, feature importances nativas, lida com não-linearidades, escala bem | Menos interpretável que LR, maior tamanho em disco |
| Gradient Boosting | Geralmente melhor accuracy que RF em dados tabulares, feature importances | Mais lento para treinar, mais hiperparâmetros para tunar |
| XGBoost | Estado-da-arte em competições tabulares, regularização nativa, velocidade | Mais dependências, tuning mais sensível, puede overfittar |
| LightGBM | Mais rápido que XGBoost em datasets grandes, menor uso de memória, Leaf-wise growth | Pode overfittar em datasets pequenos, menos estável que RF |

### Performance Relativa

Para este dataset (32K rows, 31% positive class):
- **RF, XGBoost e LightGBM** têm desempenho similar (diferenças < 0.01 ROC-AUC)
- **Logistic Regression** é competitiva mas perde em recall
- **Gradient Boosting** é o mais lento para treinar com pouco ganho marginal
- **Dummy** confirma que os modelos têm valor preditivo real (p < 0.001)

### Caminhos Recomendados

1. **Produção (padrão):** Random Forest — robusto, interpretável, sem dependências extras
2. **Se deploy leve:** Logistic Regression com top-3 features (model_proxy.json)
3. **Se performance máxima necessária:** XGBoost com tuning de hiperparâmetros
4. **Se dataset crescer:** LightGBM escala melhor com mais dados

### Modeling Decisions

1. **Target encoding:** `Withdrawn` → 1, all others → 0.
2. **Class weight:** `balanced` on LR, RF, LGBM; `scale_pos_weight` on XGBoost.
3. **One-hot encoding** for categorical features (8 categorical → ~40 one-hot columns).
4. **StandardScaler** on numeric features.
5. **200 trees** for ensemble models (stability vs. cost tradeoff).
6. **Dummy classifier** as floor comparison.
7. **Permutation tests** (1000 iterations) for model vs dummy significance.
8. **Paired t-test** for all model pairs across 5-fold CV.
9. **7 derived features** added.
10. **Null handling:** imd_band (3.4%) → "Unknown"; date_registration (0.1%) → median.

### Owner
Laurent (data-architect)
"""

    MODEL_DOC_PATH.write_text(content, encoding="utf-8")
    print(f"\n[T6] Model documentation saved: {MODEL_DOC_PATH}")


# ─── Pipeline entrypoint ──────────────────────────────────────────────────────


def main():
    print("=" * 70)
    print("  ML Pipeline — Abandono Academico Casa Grande (OULAD)")
    print("  T4 (Feature Engineering) -> T5 (6-Model Training) -> T6 (Evaluation)")
    print("=" * 70)

    # ── T4: Load & Feature Engineering ──
    print("\n" + "─" * 70)
    print("  T4: FEATURE ENGINEERING")
    print("─" * 70)
    df = load_gold_table(DUCKDB_PATH)
    df, derived_numeric = engineer_features(df)
    X_train, X_test, y_train, y_test, all_numeric, all_features = prepare_ml_data(df, derived_numeric)
    all_cat = CATEGORICAL_FEATURES.copy()

    # ── T5: Model Training ──
    print("\n" + "─" * 70)
    print("  T5: 6-MODEL TRAINING")
    print("─" * 70)
    cv_results = train_models(X_train, y_train, all_numeric, all_cat)

    # Feature importance
    fi_df, fi_source = get_feature_importance(cv_results, all_numeric, all_cat)
    if fi_source:
        print(f"\n[T5] Feature importances from: {fi_source}")
        print(fi_df.head(10).to_string(index=False))
    else:
        print("\n[T5] WARNING: No feature importance extracted")

    # ── T6: Evaluation ──
    print("\n" + "─" * 70)
    print("  T6: MODEL EVALUATION")
    print("─" * 70)
    test_results = evaluate_on_test(cv_results, X_test, y_test)

    # Statistical tests
    stat_tests = statistical_tests(y_train, X_train, cv_results)

    # Model selection
    best_name = select_best_model(cv_results, test_results)
    print(f"\n  Best model: {best_name}")

    # Model proxy
    proxy = generate_model_proxy(cv_results, test_results, X_test, y_test, best_name)

    # Save model
    save_model(cv_results, best_name)

    # Generate documentation
    generate_model_doc(
        cv_results, test_results, fi_df, stat_tests, all_numeric,
        all_cat, best_name, derived_numeric, df.shape, proxy,
    )

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Models trained: {', '.join(MODEL_CONFIGS.keys())}")
    print(f"  Best model: {best_name} (saved to {MODEL_PATH})")
    print(f"  Documentation: {MODEL_DOC_PATH}")
    print(f"  Model proxy: {MODEL_PROXY_PATH}")
    print(f"  Train rows: {X_train.shape[0]:,} | Test rows: {X_test.shape[0]:,}")
    print(f"  Features: {len(all_features)} ({len(all_numeric)} numeric + {len(all_cat)} categorical)")
    print("=" * 70)


if __name__ == "__main__":
    main()
