# ADR-001: Classificador Baseline com RandomForestClassifier

## Status
Accepted

## Context
Precisamos de um modelo preditivo para identificar estudantes em risco de abandono academico na Universidade Casa Grande. O dataset possui 1000 registros com 7 colunas (student_id, timestamp, course_name, enrollment_status, grade_point_average, attendance_rate, scholarship_percent). O target e binario: SUSPENDED = 1 (abandono), demais status = 0.

Esta e a Fase 1 do pipeline, onde o objetivo e estabelecer uma baseline funcional antes de iterar com modelos mais sofisticados.

## Decision
Usar **RandomForestClassifier** (sklearn) como classificador baseline com as seguintes configuracoes:
- `n_estimators=100` — numero suficiente para estabilidade sem custo computacional excessivo
- `class_weight="balanced"` — compensa o desbalanceamento esperado entre SUSPENDED e demais classes
- `random_state=42` — reprodutibilidade
- Features: course_name (LabelEncoder), grade_point_average, attendance_rate, scholarship_percent
- Split: 80/20 stratificado

## Alternatives

### A) Logistic Regression
Mais interpretavel e rapido, mas desempenho inferior com features categoricas encodadas e relacoes nao-lineares (e.g., interacao entre GPA e attendance_rate). Melhor como comparacao na Fase 2.

### B) Gradient Boosting (XGBoost/LightGBM)
Maior poder preditivo, mas adiciona dependencia extra e complexidade de tuning inadequada para uma baseline. Candidato para Fase 2 ou 3.

### C) SVM
Sensivel a escala e a hiperparametros; requer preprocessing mais elaborado (StandardScaler). Custo-beneficio ruim para baseline.

## Consequences
+ Baseline funcional rapidamente, com pouco tuning
+ RandomForest e robusto a outliers e features com escalas diferentes
+ `class_weight="balanced"` mitiga viés do desbalanceamento sem SMOTE
+ feature_importances_ disponivel para analise interpretativa na Fase 2
- Nao e tao interpretavel quanto Logistic Regression
- Pode overfittar com 1000 registros se nao monitorado
- LabelEncoder em course_name introduz ordinalidade artificial — target encoding pode ser melhor na Fase 2
