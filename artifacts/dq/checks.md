# Data Quality Checks — OULAD Dropout Prediction

## Overview

This document describes the 6 DQ baseline checks implemented in the ML pipeline for the OULAD dropout prediction task.

**Dataset:** Open University Learning Analytics Dataset (OULAD)
**Rows:** 32,593 students
**Features:** 28 gold features + 7 derived features = 35 total
**Target:** is_dropout (31.2% positive class)

---

## DQ Baseline Checks

### DQ-01: Null Profiling

| Check | Status | Details |
|-------|--------|---------|
| **Column null counts** | ✅ PASS | Total 1,156 nulls (3.4% of data) |
| **Null locations** | ✅ Documented | imd_band: 1,111 (3.4%), date_registration: 45 (0.1%) |
| **Treatment applied** | ✅ Yes | imd_band → "Unknown", date_registration → median |

### DQ-02: Column Existence

| Check | Status | Details |
|-------|--------|---------|
| **Expected columns** | ✅ PASS | All 28 gold columns + 7 derived columns present |
| **Target column** | ✅ PASS | is_dropout column exists and is binary (0/1) |
| **Categorical columns** | ✅ PASS | 8 categorical features present |
| **Numeric columns** | ✅ PASS | 23 numeric features present |

### DQ-03: Type Validation

| Check | Status | Details |
|-------|--------|---------|
| **Numeric types** | ✅ PASS | int64, float64 for numeric features |
| **Categorical types** | ✅ PASS | object/VARCHAR for categorical features |
| **Target type** | ✅ PASS | INTEGER (0/1) |
| **No unexpected types** | ✅ PASS | All columns have expected types |

### DQ-04: Duplicate Detection

| Check | Status | Details |
|-------|--------|---------|
| **Duplicate rows** | ✅ PASS | 0 exact duplicates found |
| **Duplicate student IDs** | ✅ PASS | Each student appears once per course presentation |
| **Primary key uniqueness** | ✅ PASS | (code_module, code_presentation, id_student) is unique |

### DQ-05: Target Balance

| Check | Status | Details |
|-------|--------|---------|
| **Class distribution** | ✅ PASS | 31.2% dropout (10,156 / 32,593) |
| **Stratified split** | ✅ PASS | Train/test maintain same distribution |
| **Class weight** | ✅ Applied | balanced weight used in models |

### DQ-06: Range/Bounds Validation

| Check | Status | Details |
|-------|--------|---------|
| **Click counts** | ✅ PASS | total_clicks ≥ 0, all values valid |
| **Assessment scores** | ✅ PASS | 0 ≤ avg_assessment_score ≤ 100 |
| **Date fields** | ✅ PASS | date_registration: 0-365, valid ranges |
| **Binary flags** | ✅ PASS | has_vle_activity, late_submission_flag ∈ {0,1} |
| **Click trend** | ✅ PASS | 0 ≤ click_trend ≤ 1 |

---

## Summary

| Check | Status |
|-------|--------|
| DQ-01: Null Profiling | ✅ PASS |
| DQ-02: Column Existence | ✅ PASS |
| DQ-03: Type Validation | ✅ PASS |
| DQ-04: Duplicate Detection | ✅ PASS |
| DQ-05: Target Balance | ✅ PASS |
| DQ-06: Range/Bounds | ✅ PASS |

**Overall DQ Status:** ✅ ALL CHECKS PASSED

---

## Owner

Laurent (data-architect)  
Date: 2026-06-09