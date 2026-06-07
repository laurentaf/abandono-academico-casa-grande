# Data Quality Checks — Abandono Acadêmico Casa Grande

## Guards implementados (Fase 1)

### 1. DataFrame vazio (`_guard_empty_df`)
- **Local:** `src/main.py:36-39`
- **Regra:** Se `df.empty`, imprime mensagem amigável em stderr e chama `sys.exit(1)`.
- **Pontos de chamada:** após `fetch_dataset` (L74), após `train_model` (L85), após predição (L98).
- **Nota:** Fase 1 usa `sys.exit(1)` + stderr (conforme padroes-entrega.md P0); Fase 2 pode evoluir para logging estruturado.

### 2. Colunas obrigatórias
- **Regra implícita:** `fetch_dataset` lê parquet com `read_parquet()` e espera as 7 colunas do schema.
- **Check:** se coluna ausente, pandas levanta `KeyError` natural.
- **TODO Fase 2:** validação explícita com `assert col in df.columns`.

### 3. Tipos esperados
- **Regra implícita:** LabelEncoder requer string/bool; features numéricas requerem float/int.
- **Check:** pandas infere tipos do parquet; sklearn falha graciosamente se tipo incorreto.
- **TODO Fase 2:** `df.dtypes` check explícito.

### 4. Target balance
- **Regra:** `class_weight="balanced"` no RandomForest compensa desbalanceamento.
- **Check:** Fase 1 não loga distribuição de classes; Fase 2 deve imprimir `value_counts(normalize=True)`.

## Regras de qualidade (DQ) — checklist

| ID | Regra | Severidade | Status |
|----|-------|------------|--------|
| DQ-01 | DataFrame não vazio após fetch | CRITICAL | implementado |
| DQ-02 | 7 colunas presentes no schema | HIGH | implícito (TODO F2) |
| DQ-03 | Tipos corretos por coluna | MEDIUM | implícito (TODO F2) |
| DQ-04 | Target balance verificado | MEDIUM | parcial (class_weight) |
| DQ-05 | Nenhum NULL em features | HIGH | implícito (TODO F2) |

## Owner
Laurent (data-architect)
