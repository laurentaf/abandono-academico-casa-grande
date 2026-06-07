# Contract — Abandono Acadêmico Casa Grande

## Brief
Pipeline de Previsão de Abandono Acadêmico para a Universidade Casa Grande.
Consome dataset via API DataMission, treina modelo de classificação
(scikit-learn) para prever enrollment_status, e gera relatórios de métricas.

## Needs
data, etl, ml, predictive-modeling, data-quality

## Capabilities usadas
- LATADE (data, etl, data-quality) — ingestão, profiling, validação
- LAECON (ml, predictive-modeling) — modelo de classificação baseline

## Deliverables
- src/main.py (fetch_dataset com formato parametrizado + HTTP handling, train_model, main)
- requirements.txt (pandas, scikit-learn, requests, pyarrow, dbt)
- data/raw.csv (dados crus exportados do parquet)
- README.md

## Notas Fase 2
- fetch_dataset agora aceita parametro `fmt` (parquet/json/csv)
- Tratamento de HTTP 4xx/5xx com sys.exit(1) e mensagem amigável
- Print registra tamanho do arquivo baixado em KB
- Dados crus salvos em data/raw.csv alem do dataset.parquet

## Repo
https://github.com/laurentaf/abandono-academico-casa-grande
