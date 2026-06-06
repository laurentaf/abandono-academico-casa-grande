import os
import sys
from pathlib import Path

import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)
import pickle


PROJECT_ID = "2e4ce469-1a75-45fb-a41e-160196c7b989"
API_BASE = "https://api.datamission.com.br"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

DATA_PATH = DATA_DIR / "dataset.parquet"
MODEL_PATH = MODELS_DIR / "model.pkl"
METRICS_PATH = REPORTS_DIR / "model_metrics.md"


def _guard_empty_df(df: pd.DataFrame, context: str) -> None:
    if df is None or df.empty:
        raise ValueError(f"DataFrame vazio em: {context}. Abortando para evitar IndexError.")


def fetch_dataset(project_id: str = PROJECT_ID, token: str | None = None) -> Path:
    if token is None:
        token = os.environ.get("DATAMISSION_APIKEY")
    if not token:
        raise EnvironmentError(
            "DATAMISSION_APIKEY nao encontrada. Defina a variavel de ambiente ou passe o token explicitamente."
        )

    url = f"{API_BASE}/projects/{project_id}/dataset?format=parquet"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_bytes(response.content)

    df = pd.read_parquet(DATA_PATH)
    _guard_empty_df(df, "fetch_dataset — dataset baixado esta vazio")

    print(f"Dataset salvo em {DATA_PATH} — {len(df)} rows, {len(df.columns)} cols")
    return DATA_PATH


def train_model(data_path: Path = DATA_PATH) -> dict:
    df = pd.read_parquet(data_path)
    _guard_empty_df(df, "train_model — dataset carregado esta vazio")

    target_col = "enrollment_status"
    feature_cols = ["course_name", "grade_point_average", "attendance_rate", "scholarship_percent"]

    df["target"] = (df[target_col] == "SUSPENDED").astype(int)

    le_course = LabelEncoder()
    df["course_name_enc"] = le_course.fit_transform(df["course_name"])

    X = df[["course_name_enc", "grade_point_average", "attendance_rate", "scholarship_percent"]]
    y = df["target"]

    _guard_empty_df(pd.DataFrame(X), "train_model — features vazias apos preprocessamento")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    clf.fit(X_train, y_train)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": clf, "label_encoder": le_course}, f)

    y_pred = clf.predict(X_test)

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "classification_report": classification_report(
            y_test, y_pred, target_names=["nao-abandono", "abandono"], zero_division=0
        ),
    }

    print(f"Modelo salvo em {MODEL_PATH}")
    print(f"Accuracy:  {metrics['accuracy']}")
    print(f"Precision: {metrics['precision']}")
    print(f"Recall:    {metrics['recall']}")
    print(f"F1:        {metrics['f1']}")

    return metrics


def _save_metrics(metrics: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    content = f"""# Model Metrics — Pipeline Abandono Academico

## Classificador Baseline (RandomForestClassifier)

| Metric     | Value  |
|------------|--------|
| Accuracy   | {metrics['accuracy']} |
| Precision  | {metrics['precision']} |
| Recall     | {metrics['recall']}   |
| F1 Score   | {metrics['f1']}       |

## Classification Report

```
{metrics['classification_report']}
```

---
_Generated automatically by `src/main.py`._
"""
    METRICS_PATH.write_text(content, encoding="utf-8")
    print(f"Metricas salvas em {METRICS_PATH}")


def main() -> None:
    print("=== Pipeline Abandono Academico — Fase 1 ===")

    print("\n[1/3] Baixando dataset...")
    data_path = fetch_dataset()

    print("\n[2/3] Treinando modelo...")
    metrics = train_model(data_path)

    print("\n[3/3] Salvando metricas...")
    _save_metrics(metrics)

    print("\n=== Pipeline concluido com sucesso ===")


if __name__ == "__main__":
    main()
