# Review: T1-T3 Data Pipeline (OULAD pivot)

**Task ID:** oulad-dropout-pipeline  
**Subagent:** data-architect  
**Date:** 2026-06-09  
**Verdict:** READY (WDL preflight verified by delivery-reviewer)

---

## T1 — Data Ingestion (Bronze) ✅

| Table | CSV Source | Rows | Status |
|-------|-----------|------|--------|
| bronze_student_info | studentInfo.csv | 32,593 | ✅ loaded |
| bronze_student_registration | studentRegistration.csv | 32,593 | ✅ loaded |
| bronze_student_assessment | studentAssessment.csv | 173,912 | ✅ loaded |
| bronze_student_vle | studentVle.csv | 10,655,280 | ✅ loaded |
| bronze_assessments | assessments.csv | 206 | ✅ loaded |
| bronze_courses | courses.csv | 22 | ✅ loaded |
| bronze_vle | vle.csv | 6,364 | ✅ loaded |

**Method:** LATADE MCP `load_csv_to_bronze` × 7  
**DuckDB:** `artifacts/data/oulad.duckdb`

## T2 — ETL Pipeline (Silver/Gold) ✅

### Silver Tables
- `silver_vle_agg`: 29,228 rows — VLE clickstream per student+course
- `silver_assessment_agg`: 25,843 rows — assessment scores per student+course

### Gold Table
- `gold_oulad_features`: 32,593 rows × 26 columns
- Grain: one row per student per course presentation
- Target: `is_dropout` (1=Withdrawn, 0=Pass/Fail/Distinction)
- Target balance: 31.2% positive / 68.8% negative — acceptable

### Feature Summary
- **Demographics:** gender, region, highest_education, imd_band, age_band, disability (6)
- **Academic:** num_of_prev_attempts, studied_credits, weighted_avg_score, avg_assessment_score, num_tma, num_cma, num_exams, avg_submission_delta (8)
- **Engagement:** total_clicks, days_active, last_activity_day, first_activity_day, click_trend, avg_daily_clicks (6)
- **Registration:** date_registration, date_unregistration (2)
- **Course:** module_presentation_length (1)
- **Key:** code_module, code_presentation, id_student (3)

## T3 — DQ Baseline Checks ✅

| ID | Check | Severity | Status | Detail |
|----|-------|----------|--------|--------|
| DQ-01 | Null profiling | HIGH | PASS | imd_band 3.4% null (known), date_registration 0.1% (drop), rest 0% |
| DQ-02 | Column existence | HIGH | PASS | 26/26 columns present |
| DQ-03 | Type validation | MEDIUM | PASS | all types match (total_clicks HUGEINT→BIGINT OK) |
| DQ-04 | Duplicate detection | MEDIUM | PASS | 0 duplicates on PK |
| DQ-05 | Target balance | HIGH | PASS | 31.2% positive — within acceptable range |
| DQ-06 | Range/bounds | HIGH | PASS | all values within declared ranges |

## Artifacts Produced

| File | Description |
|------|-------------|
| `artifacts/data/oulad.duckdb` | DuckDB with 7 bronze + 2 silver + 1 gold tables |
| `artifacts/data/model.md` | Full schema spec (grain, keys, partitioning, lineage, owner) |
| `artifacts/data/etl_oulad.sql` | Reproducible ETL SQL (Silver/Gold layers) |
| `artifacts/dq/checks.md` | 6 DQ baseline checks with full results |

## Constraints Honored

- ✅ No model training (T5 deferred)
- ✅ No dashboard (T7 deferred)
- ✅ Used LATADE MCP for ingestion
- ✅ Outputs in project artifacts directory
- ✅ Real data only (Nature CC-BY 4.0) — zero synthetic data
- ✅ No credentials in files

## Known Limitations

1. **imd_band nulls (3.4%):** Students from non-UK regions lack IMD data. ML preprocessing must impute "Unknown".
2. **zero_clicks (10.3%):** 3,365 students have no VLE interaction — feature will be 0 (valid signal: disengagement).
3. **zero_assessment (28.1%):** 9,157 students have no assessment data — feature will be 0 (valid signal: early withdrawal).
4. **HUGEINT → INT64:** DuckDB sums to HUGEINT; ML pipeline should cast to int64.

## Next Steps (blocked on orchestrator)

- **T4:** Feature preprocessing pipeline (handle nulls, encode categoricals)
- **T5:** ML model training (LogisticRegression, RandomForest, XGBoost baseline)
- **T6:** Model evaluation and metrics
- **T7:** Dashboard (dashboard-designer subagent)
