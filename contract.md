# Contract — Abandono Acadêmico Casa Grande

## Brief
Pipeline de Previsão de Abandono Acadêmico, consumindo dataset via API DataMission.
Consome dataset via API DataMission, treina modelo de classificação
(scikit-learn) para prever enrollment_status, e gera relatórios de métricas.

## Needs
data, etl, ml, predictive-modeling, data-quality, dashboard

## Capabilities usadas
- LATADE (data, etl, data-quality) — ingestão, profiling, validação
- LAECON (ml, predictive-modeling) — modelo de classificação baseline
- LADESIGN (dashboard) — dashboard interativo com conclusões e simulação

## Deliverables
- src/main.py (fetch_dataset com formato parametrizado + HTTP handling, train_model, main)
- requirements.txt (pandas, scikit-learn, requests, pyarrow, dbt)
- data/raw.csv (dados crus exportados do parquet)
- artifacts/dashboard/index.html (dashboard interativo com simulação)
- README.md

## Notas Fase 2
- fetch_dataset agora aceita parametro `fmt` (parquet/json/csv)
- Tratamento de HTTP 4xx/5xx com sys.exit(1) e mensagem amigável
- Print registra tamanho do arquivo baixado em KB
- Dados crus salvos em data/raw.csv alem do dataset.parquet

## Notas Fase 4
- Dashboard self-contained (25.9KB HTML) com dark theme #1a1a2e
- Simulação interativa: sliders para CRA, attendance_rate, scholarship_percent
- Feature importance: CRA 35.2%, Attendance 29.8%, Scholarship 17.8%, Course 17.2%
- Métricas: Accuracy 66.5%, F1 0.152, Precision 0.28, Recall 0.10

## Repo
https://github.com/laurentaf/abandono-academico-casa-grande
