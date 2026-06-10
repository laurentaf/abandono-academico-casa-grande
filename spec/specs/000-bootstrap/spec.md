# SPEC-000: Bootstrap — Abandono Academico Casa Grande

**Status:** ACEITO
**Version:** 2.0 (OULAD migration)
**Authors:** Laurent
**Owner:** Laurent

---

## Contexto

Pipeline de previsao de abandono academico, utilizando o Open University Learning Analytics Dataset (OULAD).
Dataset: 32.593 estudantes, 7 modulos, 22 apresentacoes (2013-2014), publicado em Nature Scientific Data (CC-BY 4.0).
Tabelas: studentInfo, studentRegistration, studentAssessment, studentVle, assessments, courses, vle.
Target: final_result binarizado (Withdrawn=1, demais=0), 31.2% classe positiva.

## Decisao inicial

- Stack: Python (pandas, scikit-learn, duckdb, scipy, pyarrow)
- Ingestao: 7 OULAD CSVs → DuckDB (bronze/silver/gold medallion pipeline)
- Modelagem: RandomForestClassifier + Logistic Regression + Dummy baseline
- 4 estagios: ingestao → feature engineering → treinamento → dashboard

## Criterios de pronto

- [x] src/main.py com pipeline E2E (DuckDB load → DQ → features → train → evaluate)
- [x] requirements.txt com pandas, scikit-learn, duckdb, scipy, pyarrow
- [x] Modelo treinado e salvo em src/model.pkl
- [x] Metricas documentadas em artifacts/data/model.md
- [x] Dashboard interativo em artifacts/dashboard/index.html
