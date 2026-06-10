-- ============================================================================
-- ETL Pipeline: OULAD Bronze → Silver → Gold
-- Project: abandono-academico-casa-grande
-- Author: data-architect (LAOS)
-- Date: 2026-06-09
-- DuckDB: artifacts/data/oulad.duckdb
-- ============================================================================

-- ============================================================================
-- BRONZE LAYER (loaded via latade.load_csv_to_bronze)
-- ============================================================================
-- Tables created by MCP:
--   bronze_student_info        (32,593 rows) — studentInfo.csv
--   bronze_student_registration(32,593 rows) — studentRegistration.csv
--   bronze_student_assessment  (173,912 rows) — studentAssessment.csv
--   bronze_student_vle         (10,655,280 rows) — studentVle.csv
--   bronze_assessments         (206 rows) — assessments.csv
--   bronze_courses             (22 rows) — courses.csv
--   bronze_vle                 (6,364 rows) — vle.csv

-- ============================================================================
-- SILVER LAYER: VLE Clickstream Aggregation
-- ============================================================================
CREATE OR REPLACE TABLE silver_vle_agg AS
SELECT
    code_module,
    code_presentation,
    id_student,
    SUM(sum_click) AS total_clicks,
    COUNT(DISTINCT date) AS days_active,
    MAX(date) AS last_activity_day,
    MIN(date) AS first_activity_day,
    -- Click trend: ratio of post-start clicks (date >= 0) vs total
    SUM(CASE WHEN date >= 0 THEN sum_click ELSE 0 END)::DOUBLE / 
        NULLIF(SUM(sum_click), 0) AS click_trend
FROM bronze_student_vle
GROUP BY code_module, code_presentation, id_student;

-- ============================================================================
-- SILVER LAYER: Assessment Aggregation
-- ============================================================================
CREATE OR REPLACE TABLE silver_assessment_agg AS
SELECT
    sa.id_student,
    a.code_module,
    a.code_presentation,
    -- Weighted average score across all assessments
    SUM(sa.score * a.weight) / NULLIF(SUM(a.weight), 0) AS weighted_avg_score,
    -- Assessment counts by type
    COUNT(CASE WHEN a.assessment_type = 'TMA' THEN 1 END) AS num_tma,
    COUNT(CASE WHEN a.assessment_type = 'CMA' THEN 1 END) AS num_cma,
    COUNT(CASE WHEN a.assessment_type = 'Exam' THEN 1 END) AS num_exams,
    -- Score statistics
    AVG(sa.score) AS avg_score,
    MIN(sa.score) AS min_score,
    MAX(sa.score) AS max_score,
    -- Submission timeliness (negative = early, positive = late)
    AVG(sa.date_submitted - a.date) AS avg_submission_delta
FROM bronze_student_assessment sa
JOIN bronze_assessments a ON sa.id_assessment = a.id_assessment
GROUP BY sa.id_student, a.code_module, a.code_presentation;

-- ============================================================================
-- GOLD LAYER: Full Feature Matrix
-- ============================================================================
CREATE OR REPLACE TABLE gold_oulad_features AS
SELECT
    -- === Composite Key ===
    si.code_module,
    si.code_presentation,
    si.id_student,
    
    -- === Demographics (studentInfo) ===
    si.gender,
    si.region,
    si.highest_education,
    si.imd_band,
    si.age_band,
    si.num_of_prev_attempts,
    si.studied_credits,
    si.disability,
    
    -- === Registration (studentRegistration) ===
    sr.date_registration,
    sr.date_unregistration,
    
    -- === VLE Engagement (silver_vle_agg) ===
    COALESCE(va.total_clicks, 0) AS total_clicks,
    COALESCE(va.days_active, 0) AS days_active,
    COALESCE(va.last_activity_day, -999) AS last_activity_day,
    COALESCE(va.first_activity_day, -999) AS first_activity_day,
    COALESCE(va.click_trend, 0.5) AS click_trend,
    -- Derived: avg daily clicks
    CASE WHEN COALESCE(va.days_active, 0) > 0 
         THEN COALESCE(va.total_clicks, 0)::DOUBLE / va.days_active
         ELSE 0 END AS avg_daily_clicks,
    
    -- === Assessment Performance (silver_assessment_agg) ===
    COALESCE(aa.weighted_avg_score, 0) AS weighted_avg_score,
    COALESCE(aa.num_tma, 0) AS num_tma,
    COALESCE(aa.num_cma, 0) AS num_cma,
    COALESCE(aa.num_exams, 0) AS num_exams,
    COALESCE(aa.avg_score, 0) AS avg_assessment_score,
    COALESCE(aa.avg_submission_delta, 0) AS avg_submission_delta,
    
    -- === Course Metadata (courses) ===
    c.module_presentation_length,
    
    -- === TARGET: Binary dropout ===
    CASE WHEN si.final_result = 'Withdrawn' THEN 1 ELSE 0 END AS is_dropout,
    si.final_result AS final_result_label

FROM bronze_student_info si
LEFT JOIN bronze_student_registration sr 
    ON si.code_module = sr.code_module 
    AND si.code_presentation = sr.code_presentation 
    AND si.id_student = sr.id_student
LEFT JOIN silver_vle_agg va 
    ON si.code_module = va.code_module 
    AND si.code_presentation = va.code_presentation 
    AND si.id_student = va.id_student
LEFT JOIN silver_assessment_agg aa 
    ON si.code_module = aa.code_module 
    AND si.code_presentation = aa.code_presentation 
    AND si.id_student = aa.id_student
LEFT JOIN bronze_courses c 
    ON si.code_module = c.code_module 
    AND si.code_presentation = c.code_presentation;
