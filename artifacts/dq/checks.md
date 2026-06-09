# Data Quality Checks — Abandono Acadêmico Casa Grande

## DQ baseline checks (DQ-01 a DQ-06) — Fase 3

Conforme `knowledge/data-quality-baseline.md` §4.1 (LACOUNCIL d6c79133, 2026-06-09).
Todos os 6 checks rodam **após fetch** e **antes** de qualquer transformação.

| ID | Check | Severidade | Status | Detalhe |
|----|-------|------------|--------|---------|
| DQ-01 | Null profiling | HIGH | implementado | `check_nulls(df)` — conta nulls por coluna antes de drop; próximo estágio (preprocess) faz limpeza |
| DQ-02 | Column existence | HIGH | implementado | `check_columns(df, EXPECTED_COLUMNS)` — assert explícito das 7 colunas do schema |
| DQ-03 | Type validation | MEDIUM | implementado | `check_types(df, SCHEMA_DTYPES)` — valida dtypes contra schema declarado |
| DQ-04 | Duplicate detection | MEDIUM | implementado | `check_duplicates(df, GRAIN_KEY)` — PK: student_id |
| DQ-05 | Target balance | HIGH | implementado | `check_target_balance(df, "enrollment_status")` — loga distribuição antes do treino |
| DQ-06 | Range/bounds check | HIGH | implementado | `check_bounds(df, BOUNDS)` — GPA 0-4, attendance 0-100, scholarship 0-100 |

### Severidade HIGH para DQ-01, DQ-02, DQ-05, DQ-06

- **DQ-01 (Null profiling)**: HIGH porque Fase 3 faz limpeza de nulls em `preprocess_data()` — o check informa o que será removido.
- **DQ-02 (Column existence)**: HIGH porque `preprocess_data()` seleciona features por nome — coluna ausente = KeyError tarde.
- **DQ-05 (Target balance)**: HIGH porque próximo estágio treina modelo — treinar em 90/10 sem saber é risco.
- **DQ-06 (Range/bounds)**: HIGH porque valores impossíveis (GPA 999) propagariam silenciosamente pelo RandomForest.

## Schema de referência

```python
EXPECTED_COLUMNS = [
    "student_id", "timestamp", "course_name",
    "enrollment_status", "grade_point_average",
    "attendance_rate", "scholarship_percent",
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
```

## Guard P0 (DataFrame vazio) — preservado

- **Função:** `_guard_empty_df(df, context)` — se `df.empty`, imprime em stderr e `sys.exit(1)`.
- **Pontos de chamada:** fetch_dataset, preprocess_data, train_model.
- **Nota:** Fase 1 usava `sys.exit(1)` + stderr (conforme padroes-entrega.md P0); Fase 3 preserva o mesmo comportamento.

## Implementação em src/main.py

Cada check é uma função simples em `src/main.py`, chamada por `run_dq_checks(df)`:

```
fetch_dataset → [DQ checks] → preprocess_data → train_model → metrics
```

Os resultados dos checks são logados no console com prefixo `[DQ-NN]` para rastreabilidade.

## Owner

Laurent (data-architect)
