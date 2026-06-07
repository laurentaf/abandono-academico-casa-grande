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

MODEL_PATH = MODELS_DIR / "model.pkl"
METRICS_PATH = REPORTS_DIR / "model_metrics.md"

SUPPORTED_FORMATS = ("parquet", "json", "csv")

FILE_EXTENSIONS = {"parquet": ".parquet", "json": ".json", "csv": ".csv"}


def _read_df(path: Path, fmt: str) -> pd.DataFrame:
    if fmt == "parquet":
        return pd.read_parquet(path)
    elif fmt == "csv":
        return pd.read_csv(path)
    elif fmt == "json":
        return pd.read_json(path)
    else:
        print(f"Erro: formato '{fmt}' nao suportado para leitura. Use um de: {SUPPORTED_FORMATS}", file=sys.stderr)
        sys.exit(1)


def _guard_empty_df(df: pd.DataFrame, context: str) -> None:
    if df is None or df.empty:
        print(f"Erro: DataFrame vazio em: {context}. Verifique a fonte de dados e tente novamente.", file=sys.stderr)
        sys.exit(1)


def fetch_dataset(project_id: str = PROJECT_ID, fmt: str = "parquet", token: str | None = None) -> tuple[bytes, Path]:
    """Baixa o dataset da API e retorna (conteudo_bruto, caminho_do_arquivo).

    O chamador decide o que fazer com os bytes — salvar como raw.csv, etc.
    """
    if fmt not in SUPPORTED_FORMATS:
        print(f"Erro: formato '{fmt}' nao suportado. Use um de: {SUPPORTED_FORMATS}", file=sys.stderr)
        sys.exit(1)

    if token is None:
        token = os.environ.get("DATAMISSION_APIKEY")
    if not token:
        print("Erro: DATAMISSION_APIKEY nao encontrada. Defina a variavel de ambiente ou passe o token explicitamente.", file=sys.stderr)
        sys.exit(1)

    url = f"{API_BASE}/projects/{project_id}/dataset?format={fmt}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, timeout=60)

    if response.status_code >= 400:
        reason = response.text[:200] if response.text else "(sem corpo)"
        print(
            f"Erro: API retornou HTTP {response.status_code} ao buscar dataset. "
            f"Resposta: {reason}",
            file=sys.stderr,
        )
        sys.exit(1)

    file_size_kb = len(response.content) / 1024
    print(f"Dataset baixado: {file_size_kb:.1f} KB (formato={fmt}, HTTP {response.status_code})")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ext = FILE_EXTENSIONS[fmt]
    data_path = DATA_DIR / f"dataset{ext}"
    data_path.write_bytes(response.content)

    df = _read_df(data_path, fmt)
    _guard_empty_df(df, "fetch_dataset — dataset baixado esta vazio")

    return response.content, data_path


def train_model(data_path: Path, fmt: str = "parquet") -> dict:
    df = _read_df(data_path, fmt)
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
    fmt = "parquet"
    print("=== Pipeline Abandono Academico — Fase 2 ===")

    print("\n[1/4] Baixando dataset...")
    raw_content, data_path = fetch_dataset(fmt=fmt)

    print("\n[2/4] Salvando dados crus em raw.csv...")
    df_raw = _read_df(data_path, fmt)
    raw_csv_path = DATA_DIR / "raw.csv"
    raw_csv_path.write_text(df_raw.to_csv(index=False), encoding="utf-8")
    csv_size_kb = raw_csv_path.stat().st_size / 1024
    print(f"Dados crus salvos em {raw_csv_path} — {csv_size_kb:.1f} KB, {len(df_raw)} rows, {len(df_raw.columns)} cols")

    print("\n[3/4] Treinando modelo...")
    metrics = train_model(data_path, fmt=fmt)

    print("\n[4/4] Salvando metricas...")
    _save_metrics(metrics)

    print("\n=== Pipeline concluido com sucesso ===")


if __name__ == "__main__":
    main()
