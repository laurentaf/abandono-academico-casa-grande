# Contract — Abandono Academico Casa Grande

## Brief

Pipeline de Previsao de Abandono Academico utilizando o Open University Learning Analytics Dataset (OULAD) — dataset real com 32.593 estudantes, publicado em Nature Scientific Data (Kuzilek et al., 2017, CC-BY 4.0). O pipeline cobre ingestao de 7 tabelas OULAD, feature engineering, treinamento de modelo preditivo (Random Forest 87.5% accuracy, 93.7% recall), e dashboard interativo com simulacao.

## Needs

data, etl, ml, predictive-modeling, data-quality, dashboard

## Capabilities usadas

- LATADE (data, etl, data-quality) — ingestao CSV, agregacoes bronze/silver/gold, DQ baseline 6 checks
- LAECON (ml, predictive-modeling) — modelo de classificacao baseline (fallback para scikit-learn direto, laecon em BASIC)
- LADESIGN (dashboard) — dashboard interativo com conclusoes e simulacao

## Deliverables

- src/main.py (pipeline E2E: DuckDB load → feature engineering → DQ checks → train → evaluate)
- src/model.pkl (RandomForestClassifier treinado, class_weight=balanced, 200 estimators)
- requirements.txt (pandas, scikit-learn, duckdb, scipy, pyarrow)
- artifacts/data/model.md (schema + ML results)
- artifacts/data/etl_oulad.sql (SQL reprodutivel do pipeline ETL)
- artifacts/data/oulad.duckdb (DuckDB com 7 bronze + 2 silver + 1 gold tabelas)
- artifacts/dq/checks.md (6 DQ baseline checks documentados)
- artifacts/dashboard/index.html (dashboard interativo com simulacao)
- README.md

## Notas OULAD

- Dataset: Open University Learning Analytics Dataset (32.593 alunos, 7 modulos, 22 apresentacoes, 2013-2014)
- Target: final_result binarizado (Withdrawn=1, demais=0), 31.2% classe positiva
- Features: 26 colunas no gold (demografia + VLE engagement + assessment scores + 7 features derivadas)
- Modelo: RandomForest 87.5% accuracy, 93.7% recall (dropout), 0.954 ROC-AUC
- Significancia estatistica: RF vs Dummy p=0.001; RF vs LR p=0.084 (nao significativo)
- Top feature: last_activity_day (20.2% importancia) — estudantes que param de interagir cedo tem maior risco

## Repo

https://github.com/laurentaf/abandono-academico-casa-grande
