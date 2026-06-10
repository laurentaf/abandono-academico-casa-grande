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
| imd_band | VARCHAR | studentInfo | Index of Multiple Deprivation band (1,111 nulls → "Unknown") | demographic feature |
| age_band | VARCHAR | studentInfo | 0-35 / 35-55 / 55<= | demographic feature |
| num_of_prev_attempts | BIGINT | studentInfo | Number of prior course attempts | academic feature |
| studied_credits | BIGINT | studentInfo | Total credits studied | academic feature |
| disability | VARCHAR | studentInfo | Y/N | demographic feature |
| date_registration | BIGINT | studentRegistration | Days relative to presentation start (45 nulls → median) | temporal feature |
| date_unregistration | BIGINT | studentRegistration | Days relative to start (69% null — expected) | temporal feature |
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

### Null Profile (post-imputation)
| Column | Nulls | Treatment |
|--------|-------|-----------|
| imd_band | 1,111 (3.4%) | Filled with "Unknown" |
| date_registration | 45 (0.1%) | Filled with median |
| All other columns | 0 | Clean |

### Partitioning Strategy
N/A — single table, small enough for in-memory ML (32K rows).

### Refresh Cadence
Static snapshot. No refresh expected.

### Source Lineage
```
7 OULAD CSVs
  → bronze_student_info (32,593)
  → bronze_student_registration (32,593)
  → bronze_student_assessment (173,912)
  → bronze_student_vle (10,655,280)
  → bronze_assessments (206)
  → bronze_courses (22)
  → bronze_vle (6,364)
      ↓
  silver_vle_agg (29,228)
  silver_assessment_agg (25,843)
      ↓
  gold_oulad_features (32,593)
      ↓
  ML Pipeline (T4-T6)
      ↓
  src/model.pkl (RandomForestClassifier)
```

## ML Pipeline (T4-T6)

### Pipeline Overview

```
gold_oulad_features (32,593 × 28)
    ↓ T4: Feature Engineering
  + 7 derived features → 23 numeric + 8 categorical = 31 total features
    ↓ T5: Model Training
  Stratified 80/20 split → 5-fold cross-validation
  Logistic Regression (baseline) + Random Forest + Dummy (stratified)
    ↓ T6: Evaluation
  Test set metrics + confusion matrix + statistical significance tests
```

### Model Configurations

| Model | Hyperparameters | Class Weight |
|-------|----------------|--------------|
| Logistic Regression | max_iter=1000, C=1.0 | balanced |
| Random Forest | n_estimators=200, max_depth=None, min_samples_split=5, min_samples_leaf=2 | balanced |
| Dummy Classifier | strategy="stratified" | N/A |

### Cross-Validation Results (5-fold stratified)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | 0.8643 | 0.7272 | 0.9035 | 0.8058 | 0.9420 |
| Random Forest | 0.8671 | 0.7235 | 0.9280 | 0.8131 | 0.9495 |
| Dummy (stratified) | 0.5697 | 0.3067 | 0.3022 | 0.3044 | 0.4965 |

### Test Set Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | 0.8695 | 0.7352 | 0.9079 | 0.8125 | 0.9458 |
| Random Forest | 0.8750 | 0.7347 | 0.9370 | 0.8236 | 0.9536 |
| Dummy (stratified) | 0.5656 | — | — | — | — |

### Confusion Matrix — Random Forest (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | 3,801 | 687 |
| **Actual Dropout** | 128 | 1,903 |

### Classification Report — Random Forest (Test Set)

```
                       precision    recall  f1-score   support

Pass/Fail/Distinction       0.97      0.85      0.90      4488
            Withdrawn       0.73      0.94      0.82      2031

             accuracy                           0.87      6519
            macro avg       0.85      0.89      0.86      6519
         weighted avg       0.89      0.87      0.88      6519

```

### Confusion Matrix — Logistic Regression (Test Set)

|  | Predicted Non-Dropout | Predicted Dropout |
|--|----------------------|-------------------|
| **Actual Non-Dropout** | 3,824 | 664 |
| **Actual Dropout** | 187 | 1,844 |

### Classification Report — Logistic Regression (Test Set)

```
                       precision    recall  f1-score   support

Pass/Fail/Distinction       0.95      0.85      0.90      4488
            Withdrawn       0.74      0.91      0.81      2031

             accuracy                           0.87      6519
            macro avg       0.84      0.88      0.86      6519
         weighted avg       0.89      0.87      0.87      6519

```

### Statistical Significance Tests

| Test | Statistic | p-value | Significant (α=0.05) | Interpretation |
|------|-----------|---------|----------------------|----------------|
| LR vs Dummy (permutation) | 0.2946 | 0.0010 | ✅ Yes | LR accuracy (0.8643) vs Dummy (0.5697), Δ=0.2946 |
| RF vs Dummy (permutation) | 0.2974 | 0.0010 | ✅ Yes | RF accuracy (0.8671) vs Dummy (0.5697), Δ=0.2974 |
| LR vs RF (paired t-test, 5-fold) | -2.2924 | 0.0836 | ❌ No | LR mean=0.8643±0.0060, RF mean=0.8671±0.0071 |

### Top 15 Feature Importances (Random Forest)

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | last_activity_day | 0.2018 |
| 2 | assessment_count | 0.1236 |
| 3 | submission_rate | 0.0884 |
| 4 | num_tma | 0.0784 |
| 5 | avg_assessment_score | 0.0462 |
| 6 | activity_coverage | 0.0424 |
| 7 | total_clicks | 0.0379 |
| 8 | engagement_intensity | 0.0350 |
| 9 | num_cma | 0.0347 |
| 10 | click_trend | 0.0340 |
| 11 | days_active | 0.0331 |
| 12 | weighted_avg_score | 0.0246 |
| 13 | avg_daily_clicks | 0.0221 |
| 14 | first_activity_day | 0.0206 |
| 15 | avg_submission_delta | 0.0183 |

### Full Feature Importance Table

| Feature | Importance |
|---------|-----------|
| last_activity_day | 0.2018 |
| assessment_count | 0.1236 |
| submission_rate | 0.0884 |
| num_tma | 0.0784 |
| avg_assessment_score | 0.0462 |
| activity_coverage | 0.0424 |
| total_clicks | 0.0379 |
| engagement_intensity | 0.0350 |
| num_cma | 0.0347 |
| click_trend | 0.0340 |
| days_active | 0.0331 |
| weighted_avg_score | 0.0246 |
| avg_daily_clicks | 0.0221 |
| first_activity_day | 0.0206 |
| avg_submission_delta | 0.0183 |
| registration_earliness | 0.0164 |
| date_registration | 0.0164 |
| num_exams | 0.0118 |
| studied_credits | 0.0113 |
| module_presentation_length | 0.0074 |
| code_module_GGG | 0.0069 |
| code_module_DDD | 0.0053 |
| has_vle_activity | 0.0050 |
| code_module_EEE | 0.0037 |
| code_module_FFF | 0.0034 |
| code_module_CCC | 0.0034 |
| code_presentation_2014J | 0.0032 |
| num_of_prev_attempts | 0.0029 |
| highest_education_Lower Than A Level | 0.0029 |
| code_module_BBB | 0.0027 |
| region_Scotland | 0.0027 |
| code_presentation_2013J | 0.0025 |
| gender_M | 0.0025 |
| highest_education_A Level or Equivalent | 0.0025 |
| gender_F | 0.0024 |
| region_Wales | 0.0022 |
| late_submission_flag | 0.0022 |
| age_band_0-35 | 0.0022 |
| age_band_35-55 | 0.0021 |
| code_presentation_2014B | 0.0021 |
| code_presentation_2013B | 0.0019 |
| imd_band_10-20 | 0.0018 |
| imd_band_20-30% | 0.0018 |
| imd_band_0-10% | 0.0017 |
| region_North Western Region | 0.0014 |
| imd_band_50-60% | 0.0014 |
| imd_band_30-40% | 0.0014 |
| disability_Y | 0.0014 |
| region_East Anglian Region | 0.0013 |
| imd_band_40-50% | 0.0013 |
| disability_N | 0.0013 |
| highest_education_HE Qualification | 0.0013 |
| region_London Region | 0.0013 |
| region_South Region | 0.0013 |
| imd_band_70-80% | 0.0012 |
| region_East Midlands Region | 0.0011 |
| imd_band_60-70% | 0.0011 |
| imd_band_80-90% | 0.0011 |
| region_South West Region | 0.0011 |
| region_Yorkshire Region | 0.0011 |
| region_West Midlands Region | 0.0010 |
| region_South East Region | 0.0009 |
| imd_band_90-100% | 0.0009 |
| region_North Region | 0.0008 |
| region_Ireland | 0.0006 |
| code_module_AAA | 0.0004 |
| imd_band_Unknown | 0.0004 |
| highest_education_No Formal quals | 0.0002 |
| highest_education_Post Graduate Qualification | 0.0001 |
| age_band_55<= | 0.0001 |

### Modeling Decisions

1. **Target encoding:** `Withdrawn` → 1, all others → 0. Rationale: binary dropout prediction is the business question.
2. **Class weight:** `balanced` on both models. Rationale: 31.2% positive class requires compensation to avoid majority-class bias.
3. **One-hot encoding** for categorical features (8 categorical → ~40 one-hot columns). Chosen over label encoding to avoid ordinality artifacts (see ADR-002).
4. **StandardScaler** on numeric features for Logistic Regression convergence. Random Forest is scale-invariant but scaler is in the pipeline for consistency.
5. **200 trees** in Random Forest (up from 100 baseline). More trees improve stability without overfitting risk.
6. **Dummy classifier** as floor comparison. Models must beat stratified random predictions to have predictive value.
7. **Permutation tests** (1000 iterations) for model vs dummy significance. More robust than parametric tests for non-normal accuracy distributions.
8. **Paired t-test** for LR vs RF comparison across CV folds. Tests whether the difference is systematic or random.
9. **7 derived features** added: engagement_intensity, activity_coverage, has_vle_activity, assessment_count, submission_rate, late_submission_flag, registration_earliness.
10. **Null handling:** imd_band (3.4%) → "Unknown" category; date_registration (0.1%) → median imputation.

### Owner
Laurent (data-architect)
