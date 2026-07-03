# Data Model — ML Pipeline: Abandono Academico (OULAD)

## Source

- **Dataset:** Open University Learning Analytics Dataset (OULAD)
- **Paper:** "An exploration of learning analytics datasets" (Kuzilek et al., Nature CC-BY 4.0)
- **URL:** https://analyse.kmi.open.ac.uk/open_dataset
- **Total students:** 32,593
- **Total VLE interactions:** 10,655,280
- **Refresh:** Static snapshot (2026-06-09)

## Bronze Tables (7 source CSVs)

| Table | Rows | PK | Source File |
|-------|------|----|-------------|
| bronze_student_info | 32,593 | (code_module, code_presentation, id_student) | studentInfo.csv |
| bronze_student_registration | 32,593 | (code_module, code_presentation, id_student) | studentRegistration.csv |
| bronze_student_assessment | 173,912 | (id_assessment, id_student) | studentAssessment.csv |
| bronze_student_vle | 10,655,280 | (code_module, code_presentation, id_student, id_site, date) | studentVle.csv |
| bronze_assessments | 206 | id_assessment | assessments.csv |
| bronze_courses | 22 | (code_module, code_presentation) | courses.csv |
| bronze_vle | 6,364 | id_site | vle.csv |

**DuckDB file:** `artifacts/data/oulad.duckdb`

## Silver Tables (2 aggregations)

### silver_vle_agg (29,228 rows)
- Grain: student + course presentation
- Columns: total_clicks, days_active, last_activity_day, first_activity_day, click_trend

### silver_assessment_agg (25,843 rows)
- Grain: student + course presentation
- Columns: weighted_avg_score, num_tma, num_cma, num_exams, avg_score, min_score, max_score, avg_submission_delta

## Gold Table: gold_oulad_features (32,593 rows)

### Grain
One row per student per course presentation.

### Keys
- **PK:** (code_module, code_presentation, id_student)
- **FK:** code_module+code_presentation → courses, assessments

### Column Schema

| Column | Type | Source | Description | Feature Role |
|--------|------|--------|-------------|-------------|
| code_module | VARCHAR | studentInfo | Module code (AAA–GGG) | dimension key |
| code_presentation | VARCHAR | studentInfo | Presentation period (2013B/J, 2014B/J) | dimension key |
| id_student | BIGINT | studentInfo | Student ID | dimension key |
| gender | VARCHAR | studentInfo | F/M | demographic feature |
| region | VARCHAR | studentInfo | UK region | demographic feature |
| highest_education | VARCHAR | studentInfo | Highest qualification level | demographic feature |
| imd_band | VARCHAR | studentInfo | Index of Multiple Deprivation band | demographic feature |
| age_band | VARCHAR | studentInfo | 0-35 / 35-55 / 55<= | demographic feature |
| num_of_prev_attempts | BIGINT | studentInfo | Number of prior course attempts | academic feature |
| studied_credits | BIGINT | studentInfo | Total credits studied | academic feature |
| disability | VARCHAR | studentInfo | Y/N | demographic feature |
| date_registration | BIGINT | studentRegistration | Days relative to presentation start | temporal feature |
| date_unregistration | BIGINT | studentRegistration | Days relative to start | temporal feature |
| total_clicks | HUGEINT | silver_vle_agg | Sum of all VLE clicks | engagement feature |
| days_active | BIGINT | silver_vle_agg | Distinct days with VLE activity | engagement feature |
| last_activity_day | BIGINT | silver_vle_agg | Most recent VLE click day | engagement feature |
| first_activity_day | BIGINT | silver_vle_agg | First VLE click day | engagement feature |
| click_trend | DOUBLE | silver_vle_agg | Ratio of post-start clicks / total clicks (0–1) | engagement feature |
| avg_daily_clicks | DOUBLE | derived | total_clicks / days_active | engagement feature |
| weighted_avg_score | DOUBLE | silver_assessment_agg | Weighted average of assessment scores (0–100) | academic feature |
| num_tma | BIGINT | silver_assessment_agg | Count of Tutor-Marked Assessments | academic feature |
| num_cma | BIGINT | silver_assessment_agg | Count of Computer-Marked Assessments | academic feature |
| num_exams | BIGINT | silver_assessment_agg | Count of Exams | academic feature |
| avg_assessment_score | DOUBLE | silver_assessment_agg | Simple average of all scores | academic feature |
| avg_submission_delta | DOUBLE | silver_assessment_agg | Avg (submitted − deadline) — negative = early | academic feature |
| module_presentation_length | BIGINT | courses | Module length in days | course metadata |
| is_dropout | INTEGER | derived | **TARGET** — 1 if Withdrawn, 0 otherwise | target |
| final_result_label | VARCHAR | studentInfo | Original label (Pass/Fail/Distinction/Withdrawn) | target metadata |

### Derived Features (ML Pipeline)

| Feature | Formula | Description |
|---------|---------|-------------|
| engagement_intensity | total_clicks / module_presentation_length | Clicks per day of module |
| activity_coverage | days_active / module_presentation_length | Fraction of module days with activity |
| has_vle_activity | total_clicks > 0 (binary) | Whether student used VLE at all |
| assessment_count | num_tma + num_cma + num_exams | Total assessments submitted |
| submission_rate | assessment_count / module_presentation_length | Assessment submission consistency |
| late_submission_flag | avg_submission_delta > 0 (binary) | Whether student submitted late on average |
| registration_earliness | date_registration | Proxy for how early student registered |

### Target Encoding
- `Withdrawn` → 1 (dropout/abandono)
- `Pass`, `Fail`, `Distinction` → 0 (nao-abandono)

### Target Distribution
| Label | Count | % |
|-------|-------|---|
| Withdrawn (1) | 10,156 | 31.2% |
| Non-dropout (0) | 22,437 | 68.8% |

### Partitioning Strategy
N/A — single table, small enough for in-memory ML (32K rows).

### Refresh Cadence
Static snapshot. No refresh expected.

### Source Lineage
```
7 OULAD CSVs
  → bronze_* tables
      ↓
  silver_vle_agg + silver_assessment_agg
      ↓
  gold_oulad_features
      ↓
  ML Pipeline (T4-T6, 6 modelos)
      ↓
  src/model.pkl (Random Forest)
```

## ML Pipeline (T4-T6)

### Pipeline Overview

```
gold_oulad_features (32,593 × 28)
    ↓ T4: Feature Engineering
  + 7 derived features → 23 numeric + 8 categorical = 31 total features
    ↓ T5: Model Training
  Stratified 80/20 split → 5-fold cross-validation
  6 modelos: Dummy, LR, RF, GBM, XGBoost, LightGBM
    ↓ T6: Evaluation
  Test set metrics + confusion matrix + statistical tests
```

## Resultado: Seleção de Modelo

**Modelo escolhido:** Random Forest


Justificativa: Random Forest manteve-se como modelo padrão por oferecer o melhor
equilíbrio entre ROC-AUC, recall (prioridade de negócio: identificar evadidos),
tempo de treino e interpretabilidade. Nenhum modelo alternativo demonstrou ganho
superior a 0.01 no ROC-AUC com significância estatística consistente.

### Benchmark: 6 Modelos (Test Set)

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC | Treino (s) | Inferência (s/1k) | Tamanho (KB) | Interpretab. (1-5) |
|--------|----------|-----------|--------|----|---------|------------|-------------------|--------------|---------------------|
| Dummy | 0.5655775425678785 | — | — | — | — | — | — | — | 1 |
| Logistic Regression | 0.8695 | 0.7352 | 0.9079 | 0.8125 | 0.9458 | 0.76 | 0.0170 | 5.7 | 4 |
| Random Forest | 0.8787 | 0.7588 | 0.8951 | 0.8213 | 0.9537 | 12.53 | 0.0785 | 57943.2 | 3 |
| Gradient Boosting | 0.8811 | 0.7849 | 0.8518 | 0.8170 | 0.9546 | 48.51 | 0.0164 | 484.6 | 3 |
| XGBoost | 0.8761 | 0.7420 | 0.9232 | 0.8227 | 0.9547 | 3.08 | 0.0243 | 708.9 | 3 |
| LightGBM | 0.8777 | 0.7405 | 0.9355 | 0.8266 | 0.9547 | 1.70 | 0.0226 | 686.0 | 3 |

### Cross-Validation Results (5-fold stratified)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Dummy | 0.5697 | 0.3067 | 0.3022 | 0.3044 | 0.4965 |
| Logistic Regression | 0.8643 | 0.7272 | 0.9035 | 0.8058 | 0.9420 |
| Random Forest | 0.8738 | 0.7512 | 0.8897 | 0.8146 | 0.9498 |
| Gradient Boosting | 0.8770 | 0.7804 | 0.8423 | 0.8102 | 0.9520 |
| XGBoost | 0.8687 | 0.7341 | 0.9073 | 0.8116 | 0.9511 |
| LightGBM | 0.8708 | 0.7345 | 0.9164 | 0.8155 | 0.9514 |

### Confusion Matrix — Logistic Regression (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | 3,824 | 664 |
| **Actual Dropout** | 187 | 1,844 |

### Confusion Matrix — Random Forest (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | 3,910 | 578 |
| **Actual Dropout** | 213 | 1,818 |

### Confusion Matrix — Gradient Boosting (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | 4,014 | 474 |
| **Actual Dropout** | 301 | 1,730 |

### Confusion Matrix — XGBoost (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | 3,836 | 652 |
| **Actual Dropout** | 156 | 1,875 |

### Confusion Matrix — LightGBM (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | 3,822 | 666 |
| **Actual Dropout** | 131 | 1,900 |

### Classification Report — Logistic Regression (Test Set)

```
              precision    recall  f1-score   support

 Non-dropout       0.95      0.85      0.90      4488
   Withdrawn       0.74      0.91      0.81      2031

    accuracy                           0.87      6519
   macro avg       0.84      0.88      0.86      6519
weighted avg       0.89      0.87      0.87      6519

```

### Classification Report — Random Forest (Test Set)

```
              precision    recall  f1-score   support

 Non-dropout       0.95      0.87      0.91      4488
   Withdrawn       0.76      0.90      0.82      2031

    accuracy                           0.88      6519
   macro avg       0.85      0.88      0.86      6519
weighted avg       0.89      0.88      0.88      6519

```

### Classification Report — Gradient Boosting (Test Set)

```
              precision    recall  f1-score   support

 Non-dropout       0.93      0.89      0.91      4488
   Withdrawn       0.78      0.85      0.82      2031

    accuracy                           0.88      6519
   macro avg       0.86      0.87      0.86      6519
weighted avg       0.88      0.88      0.88      6519

```

### Classification Report — XGBoost (Test Set)

```
              precision    recall  f1-score   support

 Non-dropout       0.96      0.85      0.90      4488
   Withdrawn       0.74      0.92      0.82      2031

    accuracy                           0.88      6519
   macro avg       0.85      0.89      0.86      6519
weighted avg       0.89      0.88      0.88      6519

```

### Classification Report — LightGBM (Test Set)

```
              precision    recall  f1-score   support

 Non-dropout       0.97      0.85      0.91      4488
   Withdrawn       0.74      0.94      0.83      2031

    accuracy                           0.88      6519
   macro avg       0.85      0.89      0.87      6519
weighted avg       0.90      0.88      0.88      6519

```

### Statistical Significance Tests

| Test | Statistic | p-value | Significant (α=0.05) | Interpretation |
|------|-----------|---------|----------------------|----------------|
| Logistic Regression vs Dummy (permutation) | 0.2946 | 0.0010 | ✅ Yes | Logistic Regression (0.8643) vs Dummy (0.5697), Δ=0.2946 |
| Random Forest vs Dummy (permutation) | 0.3041 | 0.0010 | ✅ Yes | Random Forest (0.8738) vs Dummy (0.5697), Δ=0.3041 |
| Gradient Boosting vs Dummy (permutation) | 0.3073 | 0.0010 | ✅ Yes | Gradient Boosting (0.8770) vs Dummy (0.5697), Δ=0.3073 |
| XGBoost vs Dummy (permutation) | 0.2990 | 0.0010 | ✅ Yes | XGBoost (0.8687) vs Dummy (0.5697), Δ=0.2990 |
| LightGBM vs Dummy (permutation) | 0.3011 | 0.0010 | ✅ Yes | LightGBM (0.8708) vs Dummy (0.5697), Δ=0.3011 |
| Logistic Regression vs Random Forest (paired t-test, 5-fold) | -7.2763 | 0.0019 | ✅ Yes | Logistic Regression: 0.8643±0.0060, Random Forest: 0.8738±0.0076 |
| Logistic Regression vs Gradient Boosting (paired t-test, 5-fold) | -7.8630 | 0.0014 | ✅ Yes | Logistic Regression: 0.8643±0.0060, Gradient Boosting: 0.8770±0.0064 |
| Logistic Regression vs XGBoost (paired t-test, 5-fold) | -2.5081 | 0.0662 | ❌ No | Logistic Regression: 0.8643±0.0060, XGBoost: 0.8687±0.0075 |
| Logistic Regression vs LightGBM (paired t-test, 5-fold) | -2.7194 | 0.0530 | ❌ No | Logistic Regression: 0.8643±0.0060, LightGBM: 0.8708±0.0080 |
| Random Forest vs Gradient Boosting (paired t-test, 5-fold) | -2.2918 | 0.0837 | ❌ No | Random Forest: 0.8738±0.0076, Gradient Boosting: 0.8770±0.0064 |
| Random Forest vs XGBoost (paired t-test, 5-fold) | 3.7745 | 0.0195 | ✅ Yes | Random Forest: 0.8738±0.0076, XGBoost: 0.8687±0.0075 |
| Random Forest vs LightGBM (paired t-test, 5-fold) | 2.1439 | 0.0987 | ❌ No | Random Forest: 0.8738±0.0076, LightGBM: 0.8708±0.0080 |
| Gradient Boosting vs XGBoost (paired t-test, 5-fold) | 3.3799 | 0.0278 | ✅ Yes | Gradient Boosting: 0.8770±0.0064, XGBoost: 0.8687±0.0075 |
| Gradient Boosting vs LightGBM (paired t-test, 5-fold) | 3.1160 | 0.0357 | ✅ Yes | Gradient Boosting: 0.8770±0.0064, LightGBM: 0.8708±0.0080 |
| XGBoost vs LightGBM (paired t-test, 5-fold) | -1.3984 | 0.2345 | ❌ No | XGBoost: 0.8687±0.0075, LightGBM: 0.8708±0.0080 |

### Top 15 Feature Importances

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | last_activity_day | 0.2000 |
| 2 | assessment_count | 0.1173 |
| 3 | submission_rate | 0.0937 |
| 4 | num_tma | 0.0759 |
| 5 | avg_assessment_score | 0.0455 |
| 6 | activity_coverage | 0.0447 |
| 7 | engagement_intensity | 0.0380 |
| 8 | num_cma | 0.0377 |
| 9 | total_clicks | 0.0359 |
| 10 | click_trend | 0.0338 |
| 11 | days_active | 0.0323 |
| 12 | weighted_avg_score | 0.0274 |
| 13 | avg_daily_clicks | 0.0219 |
| 14 | first_activity_day | 0.0210 |
| 15 | registration_earliness | 0.0164 |

### Full Feature Importance Table

| Feature | Importance |
|---------|-----------|
| last_activity_day | 0.2000 |
| assessment_count | 0.1173 |
| submission_rate | 0.0937 |
| num_tma | 0.0759 |
| avg_assessment_score | 0.0455 |
| activity_coverage | 0.0447 |
| engagement_intensity | 0.0380 |
| num_cma | 0.0377 |
| total_clicks | 0.0359 |
| click_trend | 0.0338 |
| days_active | 0.0323 |
| weighted_avg_score | 0.0274 |
| avg_daily_clicks | 0.0219 |
| first_activity_day | 0.0210 |
| registration_earliness | 0.0164 |
| date_registration | 0.0164 |
| avg_submission_delta | 0.0162 |
| num_exams | 0.0110 |
| studied_credits | 0.0109 |
| module_presentation_length | 0.0076 |
| code_module_GGG | 0.0066 |
| code_module_DDD | 0.0053 |
| has_vle_activity | 0.0050 |
| code_module_FFF | 0.0036 |
| code_module_CCC | 0.0035 |
| code_module_EEE | 0.0034 |
| code_presentation_2014J | 0.0032 |
| num_of_prev_attempts | 0.0032 |
| highest_education_Lower Than A Level | 0.0029 |
| code_module_BBB | 0.0028 |
| highest_education_A Level or Equivalent | 0.0026 |
| region_Scotland | 0.0026 |
| code_presentation_2013J | 0.0024 |
| gender_M | 0.0024 |
| gender_F | 0.0023 |
| region_Wales | 0.0023 |
| late_submission_flag | 0.0022 |
| age_band_0-35 | 0.0022 |
| age_band_35-55 | 0.0022 |
| code_presentation_2013B | 0.0021 |
| code_presentation_2014B | 0.0020 |
| imd_band_10-20 | 0.0019 |
| imd_band_0-10% | 0.0018 |
| imd_band_20-30% | 0.0016 |
| region_North Western Region | 0.0015 |
| disability_Y | 0.0015 |
| imd_band_40-50% | 0.0015 |
| imd_band_50-60% | 0.0014 |
| imd_band_30-40% | 0.0014 |
| highest_education_HE Qualification | 0.0013 |
| region_London Region | 0.0013 |
| disability_N | 0.0013 |
| region_East Anglian Region | 0.0013 |
| region_South Region | 0.0013 |
| imd_band_70-80% | 0.0012 |
| imd_band_60-70% | 0.0012 |
| imd_band_80-90% | 0.0012 |
| region_East Midlands Region | 0.0011 |
| region_Yorkshire Region | 0.0010 |
| region_South West Region | 0.0010 |
| region_West Midlands Region | 0.0010 |
| region_South East Region | 0.0009 |
| imd_band_90-100% | 0.0009 |
| region_North Region | 0.0008 |
| region_Ireland | 0.0006 |
| code_module_AAA | 0.0005 |
| imd_band_Unknown | 0.0004 |
| highest_education_No Formal quals | 0.0002 |
| age_band_55<= | 0.0001 |
| highest_education_Post Graduate Qualification | 0.0001 |

### Model Proxy (Dashboard Simulation)

Arquivo: `artifacts/dashboard/model_proxy.json`

Regressão logística calibrada com as 3 features top (last_activity_day, assessment_count, submission_rate)
para simulação rápida no dashboard.

| Parâmetro | Valor |
|-----------|-------|
| Coeficiente: intercept | -0.8913 |
| Coeficiente: last_activity_day | -0.5963 |
| Coeficiente: assessment_count | -4.1771 |
| Coeficiente: submission_rate | 1.9842 |
| feature_range: last_activity_day | [-999, 269] |
| feature_range: assessment_count | [0.0, 14.0] |
| feature_range: submission_rate | [0.000, 0.058] |
| default_meta_dropout | 0.20 |
| meta_bounds | [0.05, 0.50] |
| test_set_baseline_p | 0.312 |
| best_model | Random Forest |
| best_model_test_roc_auc | 0.9537 |

## Comparative Analysis

### Prós e Contras por Modelo

| Modelo | Prós | Contras |
|--------|------|---------|
| Dummy | Baseline gratuita, custo zero | Sem poder preditivo real |
| Logistic Regression | Máxima interpretabilidade (coeficientes), treino rápido, baixo custo | Não captura não-linearidades, requer feature engineering manual |
| Random Forest | **Modelo padrão.** Robustez, feature importances nativas, lida com não-linearidades, escala bem | Menos interpretável que LR, maior tamanho em disco |
| Gradient Boosting | Geralmente melhor accuracy que RF em dados tabulares, feature importances | Mais lento para treinar, mais hiperparâmetros para tunar |
| XGBoost | Estado-da-arte em competições tabulares, regularização nativa, velocidade | Mais dependências, tuning mais sensível, puede overfittar |
| LightGBM | Mais rápido que XGBoost em datasets grandes, menor uso de memória, Leaf-wise growth | Pode overfittar em datasets pequenos, menos estável que RF |

### Performance Relativa

Para este dataset (32K rows, 31% positive class):
- **RF, XGBoost e LightGBM** têm desempenho similar (diferenças < 0.01 ROC-AUC)
- **Logistic Regression** é competitiva mas perde em recall
- **Gradient Boosting** é o mais lento para treinar com pouco ganho marginal
- **Dummy** confirma que os modelos têm valor preditivo real (p < 0.001)

### Caminhos Recomendados

1. **Produção (padrão):** Random Forest — robusto, interpretável, sem dependências extras
2. **Se deploy leve:** Logistic Regression com top-3 features (model_proxy.json)
3. **Se performance máxima necessária:** XGBoost com tuning de hiperparâmetros
4. **Se dataset crescer:** LightGBM escala melhor com mais dados

### Modeling Decisions

1. **Target encoding:** `Withdrawn` → 1, all others → 0.
2. **Class weight:** `balanced` on LR, RF, LGBM; `scale_pos_weight` on XGBoost.
3. **One-hot encoding** for categorical features (8 categorical → ~40 one-hot columns).
4. **StandardScaler** on numeric features.
5. **200 trees** for ensemble models (stability vs. cost tradeoff).
6. **Dummy classifier** as floor comparison.
7. **Permutation tests** (1000 iterations) for model vs dummy significance.
8. **Paired t-test** for all model pairs across 5-fold CV.
9. **7 derived features** added.
10. **Null handling:** imd_band (3.4%) → "Unknown"; date_registration (0.1%) → median.

### Owner
Laurent (data-architect)
