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
- src/main.py (fetch_dataset, train_model, main)
- requirements.txt (pandas, scikit-learn, requests, dbt)
- data/dataset.parquet
- reports/model_metrics.md
- README.md

## Repo
https://github.com/laurentaf/abandono-academico-casa-grande
