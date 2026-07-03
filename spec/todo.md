# TODO — Abandono Academico Casa Grande (OULAD)

---

## Stage 0: SDD Scaffold (Missao 0)
- [x] Criar estrutura de pastas (src, data, artifacts, spec)
- [x] Criar constitution, contract, README, ADR template, harness template, bootstrap spec
- [x] design-direction.md (projeto tem need: dashboard)

## Stage 1: Ingestao OULAD + Feature Engineering (T1-T3)
- [x] Baixar e extrair 7 CSVs OULAD em data/oulad/
- [x] Ingerir CSVs para DuckDB bronze (7 tabelas, 10.9M rows)
- [x] Criar silver deduplicados (2 tabelas)
- [x] Gerar gold_oulad_features (32.593 rows x 26 cols)
- [x] Executar 6 DQ baseline checks — todos PASS
- [x] Documentar ETL em artifacts/data/etl_oulad.sql

## Stage 2: Modelo Preditivo + Avaliacao (T4-T6)
- [x] Feature engineering (derived features + null handling)
- [x] Treinar RF + LR + Dummy baseline (5-fold CV)
- [x] Avaliar no test set: RF 87.5% acc, 93.7% recall, 0.954 ROC-AUC
- [x] Testes estatisticos: RF vs Dummy p=0.001 (sig), RF vs LR p=0.084 (ns)
- [x] Salvar modelo em src/model.pkl
- [x] Documentar em artifacts/data/model.md

## Stage 3: ETL SQL + Documentacao
- [x] artifacts/data/etl_oulad.sql com pipeline bronze→silver→gold
- [x] artifacts/data/model.md com schema, metricas, feature importance

## Stage 4: Dashboard + Simulação
- [x] Dashboard interativo em artifacts/dashboard/index.html
- [x] Dashboard atualizado para OULAD (métricas, features, sliders)
- [x] **PONTO 2 — Dashboard com meta configurável + 3 sliders + esforço por indicador**
  - [x] Slider de meta (5%–50%, default 20%) + Gap visual (barra/marker)
  - [x] 3 sliders (last_activity_day, assessment_count, submission_rate) com impacto local e esforço p/ meta
  - [x] Risk ring com probabilidade atual + cor (verde < 20%, amarelo 20–40%, vermelho > 40%)
  - [x] Esforço total padronizado + interpretação (baixo/médio/alto)
  - [x] Feature importance (top 10 XGBoost) — bar chart horizontal
  - [x] Comparativo de 6 modelos (tabela ROC-AUC, Recall, Tempo, Prós/Contras)
  - [x] Conclusões e Ações (3 bullets de conclusions-and-actions.md)
  - [x] 3 disclaimers (correlação, OULAD, proxy linear)
  - [x] ADR-004 documentando decisão do proxy linear vs RF completo
