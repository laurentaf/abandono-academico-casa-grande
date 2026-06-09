import os
import sys
from pathlib import Path

import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
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
SRC_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"

MODEL_PATH = SRC_DIR / "model.pkl"
METRICS_PATH = REPORTS_DIR / "model_metrics.md"

SUPPORTED_FORMATS = ("parquet", "json", "csv")
FILE_EXTENSIONS = {"parquet": ".parquet", "json": ".json", "csv": ".csv"}

# Schema esperado — usado pelos DQ checks
EXPECTED_COLUMNS = [
    "student_id",
    "timestamp",
    "course_name",
    "enrollment_status",
    "grade_point_average",
    "attendance_rate",
    "scholarship_percent",
]

SCHEMA_DTYPES = {
    "course_name": "object",
    "grade_point_average": "float64",
    "attendance_rate": "float64",
    "scholarship_percent": "float64",
}

BOUNDS = {
    "grade_point_average": (0.0, 4.0),
    "attendance_rate": (0.0, 100.0),
    "scholarship_percent": (0.0, 100.0),
}

GRAIN_KEY = ["student_id"]


# ─── I/O helpers ────────────────────────────────────────────────────────────


def _read_df(path: Path, fmt: str) -> pd.DataFrame:
    if fmt == "parquet":
        return pd.read_parquet(path)
    elif fmt == "csv":
        return pd.read_csv(path)
    elif fmt == "json":
        return pd.read_json(path)
    else:
        print(
            f"Erro: formato '{fmt}' nao suportado para leitura. Use um de: {SUPPORTED_FORMATS}",
            file=sys.stderr,
        )
        sys.exit(1)


def _guard_empty_df(df: pd.DataFrame, context: str) -> None:
    if df is None or df.empty:
        print(
            f"Erro: DataFrame vazio em: {context}. Verifique a fonte de dados e tente novamente.",
            file=sys.stderr,
        )
        sys.exit(1)


# ─── DQ baseline checks (DQ-01 a DQ-06) ────────────────────────────────────


def check_nulls(df: pd.DataFrame) -> dict:
    """DQ-01: Null profiling — conta e reporta nulls por coluna ANTES de qualquer transformacao."""
    nulls = df.isnull().sum()
    nulls_pct = (nulls / len(df) * 100).round(2)
    result = nulls[nulls > 0].to_dict()
    if result:
        pct_dict = {col: nulls_pct[col] for col in result}
        print(f"[DQ-01] Nulls encontrados: {result} ({pct_dict}%)")
    else:
        print("[DQ-01] Nenhum null encontrado.")
    return result


def check_columns(df: pd.DataFrame, expected: list[str]) -> bool:
    """DQ-02: Column existence — verifica que todas as colunas esperadas estao presentes."""
    missing = [c for c in expected if c not in df.columns]
    if missing:
        print(f"[DQ-02] Colunas ausentes: {missing}", file=sys.stderr)
        return False
    print(f"[DQ-02] Todas as {len(expected)} colunas presentes.")
    return True


def check_types(df: pd.DataFrame, schema: dict) -> list[str]:
    """DQ-03: Type validation — checa dtypes contra o schema declarado."""
    mismatches = []
    for col, expected_dtype in schema.items():
        if col in df.columns and str(df[col].dtype) != expected_dtype:
            mismatches.append(f"{col}: expected {expected_dtype}, got {df[col].dtype}")
    if mismatches:
        print(f"[DQ-03] Type mismatches: {mismatches}")
    else:
        print("[DQ-03] Todos os tipos conferem com o schema.")
    return mismatches


def check_duplicates(df: pd.DataFrame, key_cols: list[str]) -> int:
    """DQ-04: Duplicate detection — conta duplicatas na grain key (PK)."""
    dupes = df.duplicated(subset=key_cols).sum()
    print(f"[DQ-04] Duplicatas na PK {key_cols}: {dupes}")
    return dupes


def check_target_balance(df: pd.DataFrame, target_col: str) -> dict:
    """DQ-05: Target balance — loga distribuicao do target antes do treino."""
    counts = df[target_col].value_counts()
    pct = (counts / len(df) * 100).round(2).to_dict()
    print(f"[DQ-05] Target balance: {counts.to_dict()} ({pct}%)")
    return {"counts": counts.to_dict(), "pct": pct}


def check_bounds(df: pd.DataFrame, bounds: dict) -> list[str]:
    """DQ-06: Range/bounds check — valida que colunas numericas estao dentro do range esperado."""
    violations = []
    for col, (lo, hi) in bounds.items():
        if col in df.columns:
            oob = ((df[col] < lo) | (df[col] > hi)).sum()
            if oob > 0:
                violations.append(f"{col}: {oob} valores fora de [{lo}, {hi}]")
    if violations:
        print(f"[DQ-06] Bounds violations: {violations}")
    else:
        print("[DQ-06] Todos os valores dentro dos bounds esperados.")
    return violations


def run_dq_checks(df: pd.DataFrame) -> dict:
    """Executa os 6 DQ baseline checks e retorna resultados agregados."""
    results = {
        "nulls": check_nulls(df),
        "columns_ok": check_columns(df, EXPECTED_COLUMNS),
        "type_mismatches": check_types(df, SCHEMA_DTYPES),
        "duplicates": check_duplicates(df, GRAIN_KEY),
        "target_balance": check_target_balance(df, "enrollment_status"),
        "bounds_violations": check_bounds(df, BOUNDS),
    }
    return results


# ─── Preprocessamento ───────────────────────────────────────────────────────


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa nulls (drop + logging) e encodes categoricals via pandas.

    Nao usa sklearn.LabelEncoder (removido na Fase 3 — ver ADR-002).
    """
    _guard_empty_df(df, "preprocess_data — DataFrame de entrada vazio")

    # Null profiling antes da limpeza (check ja rodou, mas logamos o que sera removido)
    nulls_before = df.isnull().sum()
    total_nulls = nulls_before.sum()
    if total_nulls > 0:
        null_cols = nulls_before[nulls_before > 0].to_dict()
        print(f"[preprocess] Removendo {total_nulls} nulls de: {null_cols}")
        df = df.dropna().reset_index(drop=True)
        print(f"[preprocess] Apos dropna: {len(df)} rows restantes")
    else:
        print("[preprocess] Nenhum null para remover.")

    # Target encoding
    df["target"] = (df["enrollment_status"] == "SUSPENDED").astype(int)

    # Categorical encoding via pandas .cat.codes
    # Preserva mapping para inspecao e nao introduz ordinalidade artificial
    df["course_name"] = df["course_name"].astype("category")
    course_mapping = dict(enumerate(df["course_name"].cat.categories))
    df["course_name_enc"] = df["course_name"].cat.codes
    print(f"[preprocess] course_name encoded via .cat.codes — {len(course_mapping)} categorias: {course_mapping}")

    return df


# ─── Fetch dataset ──────────────────────────────────────────────────────────


def fetch_dataset(
    project_id: str = PROJECT_ID,
    fmt: str = "parquet",
    token: str | None = None,
) -> tuple[bytes, Path]:
    """Baixa o dataset da API e retorna (conteudo_bruto, caminho_do_arquivo)."""
    if fmt not in SUPPORTED_FORMATS:
        print(
            f"Erro: formato '{fmt}' nao suportado. Use um de: {SUPPORTED_FORMATS}",
            file=sys.stderr,
        )
        sys.exit(1)

    if token is None:
        token = os.environ.get("DATAMISSION_APIKEY")
    if not token:
        print(
            "Erro: DATAMISSION_APIKEY nao encontrada. Defina a variavel de ambiente ou passe o token explicitamente.",
            file=sys.stderr,
        )
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


# ─── Model training ─────────────────────────────────────────────────────────


def train_model(df: pd.DataFrame) -> dict:
    """Treina RandomForestClassifier no DataFrame pre-processado.

    Recebe df JA preprocessado (com colunas target e course_name_enc).
    """
    _guard_empty_df(df, "train_model — DataFrame de entrada vazio")

    feature_cols = [
        "course_name_enc",
        "grade_point_average",
        "attendance_rate",
        "scholarship_percent",
    ]

    X = df[feature_cols]
    y = df["target"]

    _guard_empty_df(pd.DataFrame(X), "train_model — features vazias apos selecao")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    clf.fit(X_train, y_train)

    # Salvar modelo + mapping de categorias no mesmo pickle
    course_categories = dict(enumerate(df["course_name"].cat.categories))
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(
            {"model": clf, "course_categories": course_categories},
            f,
        )

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
    print(f"Accuracy: {metrics['accuracy']}")
    print(f"Precision: {metrics['precision']}")
    print(f"Recall: {metrics['recall']}")
    print(f"F1: {metrics['f1']}")

    return metrics


# ─── Metrics output ─────────────────────────────────────────────────────────


def _save_metrics(metrics: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    content = f"""# Model Metrics — Pipeline Abandono Academico

## Classificador Baseline (RandomForestClassifier)

| Metric    | Value  |
|-----------|--------|
| Accuracy  | {metrics['accuracy']} |
| Precision | {metrics['precision']} |
| Recall    | {metrics['recall']} |
| F1 Score  | {metrics['f1']} |

## Classification Report

```
{metrics['classification_report']}
```

---
_Generated automatically by `src/main.py`._
"""
    METRICS_PATH.write_text(content, encoding="utf-8")
    print(f"Metricas salvas em {METRICS_PATH}")


# ─── Pipeline principal ─────────────────────────────────────────────────────


def main() -> None:
    fmt = "parquet"
    print("=== Pipeline Abandono Academico — Fase 3 ===")

    # Step 1: Fetch dataset
    print("\n[1/6] Baixando dataset...")
    raw_content, data_path = fetch_dataset(fmt=fmt)

    # Step 2: Save raw CSV
    print("\n[2/6] Salvando dados crus em raw.csv...")
    df_raw = _read_df(data_path, fmt)
    raw_csv_path = DATA_DIR / "raw.csv"
    raw_csv_path.write_text(df_raw.to_csv(index=False), encoding="utf-8")
    csv_size_kb = raw_csv_path.stat().st_size / 1024
    print(
        f"Dados crus salvos em {raw_csv_path} — {csv_size_kb:.1f} KB, "
        f"{len(df_raw)} rows, {len(df_raw.columns)} cols"
    )

    # Step 3: DQ baseline checks (ANTES de qualquer transformacao)
    print("\n[3/6] Executando DQ baseline checks...")
    dq_results = run_dq_checks(df_raw)

    # Step 4: Preprocessamento (limpa nulls, encodes categoricals)
    print("\n[4/6] Preprocessando dados...")
    df_clean = preprocess_data(df_raw.copy())

    # Step 5: Treinamento
    print("\n[5/6] Treinando modelo...")
    metrics = train_model(df_clean)

    # Step 6: Metricas
    print("\n[6/6] Salvando metricas...")
    _save_metrics(metrics)

    print("\n=== Pipeline concluido com sucesso ===")


if __name__ == "__main__":
    main()
