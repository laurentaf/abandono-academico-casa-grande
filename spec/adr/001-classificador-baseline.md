# ADR-001: Classificador Baseline com RandomForestClassifier

## Status
**Superseded** por ADR-003 (dados sem valor preditivo)

## Context
Precisamos de um modelo preditivo para identificar estudantes em risco de abandono academico. O dataset possui 1000 registros com 7 colunas (student_id, timestamp, course_name, enrollment_status, grade_point_average, attendance_rate, scholarship_percent). O target e binario: SUSPENDED = 1 (abandono), demais status = 0.

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

## Post-Mortem (Fase 4 — Analise Estatistica Completa)

**Data:** 2026-06-09
**Veredicto:** Dataset sem valor preditivo. Modelo é puro ruído estatístico.

### Resultados-chave

| Teste | Resultado | Conclusão |
|-------|-----------|-----------|
| Accuracy vs Dummy | 66.5% < 75.1% (dummy) | Modelo PIOR que chutar |
| Cross-validation (5-fold) | 62.9% ± 2.2% | Instável e baixo |
| CRA: t-test (SUSPENDED vs outros) | p=0.594, d=0.039 | **Não significativo** |
| Presença: t-test | p=0.309, d=0.075 | **Não significativo** |
| Bolsa: t-test | p=0.032, d=-0.158 | Significativo mas fraco |
| Curso: Chi-square | p=0.138, V=0.074 | **Não significativo** |
| CRA bins: Chi-square | p=0.274 | **Não significativo** |
| CRA 3.5 vs 4.0: Fisher | p=0.790 | **Não significativo** |

### Target SUSPENDED é problemático
- SUSPENDED tem CRA **maior** (5.06) que ACTIVE (4.73) — contradiz premissa
- SUSPENDED e DROPPED são indistinguíveis (p=0.58)
- Ordem observada: GRAD(5.19) > SUSP(5.06) > DROP(4.92) > ACT(4.73) — caótica

### Target DROPPED também falha
- Sem SUSPENDED: accuracy 55.1% vs 63.4% dummy → -8.3pp
- CRA p=0.83, Presença p=0.12, Bolsa p=0.43 — nada significativo
- CRA bins Chi2 p=0.80 — completamente aleatório

### Conclusão
O dataset da DataMission com estas 4 features é **estatisticamente inútil** para prever abandono. As variáveis são ruído uniforme em relação a qualquer combinação de target. Dataset didático, não adequado para modelo preditivo real.
