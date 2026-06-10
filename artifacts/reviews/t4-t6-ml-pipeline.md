# T4-T6: ML Pipeline Execution — OULAD Dropout Prediction

## Task Summary

Successfully executed the complete ML pipeline for OULAD dropout prediction (T4 → T5 → T6).

**Project:** abandono-academico-casa-grande  
**Date:** 2026-06-09  
**Status:** ✅ COMPLETE

---

## T4: Feature Engineering

| Item | Status | Details |
|------|--------|---------|
| Load gold_oulad_features | ✅ | 32,593 × 28 cols from DuckDB |
| Derived features | ✅ | +7 features (engagement_intensity, activity_coverage, etc.) |
| Train/test split | ✅ | 80/20 stratified (26,074 train / 6,519 test) |

---

## T5: Model Training

| Model | CV Accuracy | ROC-AUC |
|-------|-------------|---------|
| Logistic Regression | 0.8643 | 0.9420 |
| Random Forest | 0.8671 | 0.9495 |
| Dummy (stratified) | 0.5697 | 0.4965 |

---

## T6: Evaluation

### Test Set Metrics

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | 0.8695 | 0.7352 | 0.9079 | 0.8125 | 0.9458 |
| Random Forest | 0.8750 | 0.7347 | 0.9370 | 0.8236 | 0.9536 |

### Key Findings

1. **Both models significantly outperform dummy baseline** (p < 0.001, permutation tests)
2. **Random Forest is the best model** (ROC-AUC: 0.9536)
3. **High recall for dropout class** (93.7%) — critical for early intervention
4. **Top predictors:** last_activity_day, assessment_count, submission_rate

---

## Deliverables

| File | Status | Path |
|------|--------|------|
| src/main.py | ✅ | E:\projects\abandono-academico-casa-grande\src\main.py |
| src/model.pkl | ✅ | E:\projects\abandono-academico-casa-grande\src\model.pkl |
| artifacts/data/model.md | ✅ | E:\projects\abandono-academico-casa-grave\artifacts\data\model.md |
| artifacts/dq/checks.md | ✅ | E:\projects\abandono-academico-casa-grande\artifacts\dq\checks.md |
| requirements.txt | ✅ | E:\projects\abandono-academico-casa-grande\requirements.txt |

---

## Owner

Laurent (data-architect)  
Date: 2026-06-09