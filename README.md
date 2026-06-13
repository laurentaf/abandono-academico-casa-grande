# Academic Dropout Prediction Pipeline — OULAD

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![RandomForest](https://img.shields.io/badge/Model-RandomForest-4CAF50?style=flat-square)](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
[![OULAD](https://img.shields.io/badge/Dataset-OULAD-9C27B0?style=flat-square)](https://analyse.kmi.open.ac.uk/open_dataset)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

---

## EN Quick Summary

**Stack:** Python 3.11+ · pandas · DuckDB · scikit-learn · HTML/CSS/JS (dashboard)

**What it does:** End-to-end ML pipeline predicting university student dropout using the
OULAD dataset (32,593 students, 7 modules, 22 presentations).

**Model performance:** Random Forest achieves **87.5% accuracy** and **93.7% recall**
on the dropout class — identifies 19 in 20 students who will abandon.

**Proves:** Full ML lifecycle (Bronze→Silver→Gold data pipeline), feature engineering
(7 derived features), model evaluation (accuracy, precision, recall, ROC-AUC, statistical
significance testing), DQ baseline validation, self-contained HTML dashboard.

**Run:** `python src/main.py`

---

## What It Is

End-to-end ML pipeline predicting university student **dropout risk**, using the
**Open University Learning Analytics Dataset (OULAD)** — a real dataset published in
*Nature Scientific Data* (Kuzilek et al., 2017, CC-BY 4.0).

The pipeline covers: ingestion of 7 OULAD tables (bronze), aggregations (silver),
feature engineering (gold), predictive model training with statistical validation,
and an interactive HTML dashboard with simulation.

> **Target audience:** Academic administrators and student support teams that need
> to proactively identify students at risk of dropping out.

---

## Results

| Metric | Random Forest | Logistic Regression | Dummy (stratified) |
|--------|:-------------:|:-------------------:|:------------------:|
| **Accuracy** | **87.5%** | 87.0% | 56.6% |
| **Precision (dropout)** | 73.5% | 73.5% | — |
| **Recall (dropout)** | **93.7%** | 90.8% | — |
| **F1 (dropout)** | **82.4%** | 81.3% | — |
| **ROC-AUC** | **0.954** | 0.946 | 0.497 |

> **Key insight:** 93.7% recall on the dropout class means the model identifies
> **19 out of 20** students who will actually abandon. Random Forest outperforms
> the Dummy baseline by +30.9pp accuracy (p=0.001, permutation test). The RF vs.
> LR difference is not statistically significant (p=0.084, paired t-test), but RF
> has 2.9pp higher recall.

### Top 5 Features (Random Forest)

| Rank | Feature | Importance | Interpretation |
|------|---------|-----------|----------------|
| 1 | `last_activity_day` | 20.2% | Earlier last VLE interaction → higher dropout risk |
| 2 | `assessment_count` | 12.4% | Fewer assessments submitted → higher risk |
| 3 | `submission_rate` | 8.8% | Submission consistency across modules |
| 4 | `num_tma` | 7.8% | Tutor-Marked Assessments completed |
| 5 | `avg_assessment_score` | 4.6% | Average score on assessments |

---

## 💼 What This Proves

| Skill | Evidence |
|-------|----------|
| Data pipeline (Bronze→Silver→Gold) | 3-stage ETL: OULAD ingestion → aggregation → feature engineering |
| DuckDB for analytics | `artifacts/data/oulad.duckdb` (12 tables, SQL queries) |
| Feature engineering | 7 derived features (engagement_intensity, submission_rate, etc.) |
| Model evaluation | RF vs LR statistical comparison with p-values |
| DQ validation | 6 baseline checks (null, type, duplicates, target balance, range) |
| Production thinking | ADR-001 (model choice), ADR-002 (serialization path) |
| Dashboard | Self-contained HTML with interactive sliders |

---

## How to Run

### Prerequisites

- Python 3.11+
- OULAD dataset (7 CSVs) in `data/oulad/`

### Step by step

```bash
# 1. Clone the repository
git clone https://github.com/laurentaf/abandono-academico-casa-grande.git
cd abandono-academico-casa-grande

# 2. Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download OULAD dataset
# Get the 7 CSVs from https://analyse.kmi.open.ac.uk/open_dataset
# Place in data/oulad/ (studentInfo.csv, studentVle.csv, etc.)

# 5. Run the pipeline
python src/main.py
```

### Expected output

```
=== DQ Baseline Checks ===
DQ-01 Null profiling: PASS
DQ-02 Column existence: PASS
DQ-03 Type validation: PASS
DQ-04 Duplicate detection: PASS
DQ-05 Target balance: PASS (31.2% dropout)
DQ-06 Range/bounds: PASS

=== Model Evaluation (Test Set) ===
Accuracy:  0.875
Precision: 0.735
Recall:    0.937
F1:        0.824
ROC-AUC:   0.954
```

---

## Where Is What

| Directory | Contents |
|----------|----------|
| `src/` | `main.py` (E2E pipeline) + `model.pkl` (trained model) |
| `data/oulad/` | 7 OULAD CSVs (studentInfo, studentVle, etc.) |
| `artifacts/data/` | `model.md` (schema + ML results) + `oulad.duckdb` (DuckDB, 12 tables) + `etl_oulad.sql` (reproducible SQL) |
| `artifacts/dq/` | `checks.md` (6 DQ baseline checks documented) |
| `artifacts/dashboard/` | `index.html` (interactive dashboard, self-contained) |
| `artifacts/design/` | `source.md` (design direction reference) |
| `spec/adr/` | ADR-001 (RandomForest baseline) + ADR-002 (model path + .cat.codes) |
| `spec/` | `constitution.md`, `todo.md`, `specs/`, `harness/` |

---

## Dataset: OULAD

The **Open University Learning Analytics Dataset** contains data on 32,593 students
across 7 modules and 22 presentations (2013-2014) from the Open University (UK).

| Table | Records | Description |
|-------|---------|-------------|
| `studentInfo` | 32,593 | Demographics + final result |
| `studentVle` | 10,655,280 | Daily VLE interactions (clicks) |
| `studentAssessment` | 173,912 | Grades and submission dates |
| `studentRegistration` | 32,593 | Registration/withdrawal dates |
| `assessments` | 206 | Assessment metadata |
| `courses` | 22 | Modules and presentations |
| `vle` | 6,364 | Virtual Learning Environment resources |

### Target Encoding

- `Withdrawn` → **1** (dropout)
- `Pass`, `Fail`, `Distinction` → **0** (no dropout)

Distribution: **31.2% dropout** vs 68.8% no dropout.

### Feature Engineering (7 derived features)

| Feature | Formula | Role |
|---------|---------|------|
| `engagement_intensity` | total_clicks / module_length | Engagement per module day |
| `activity_coverage` | days_active / module_length | Fraction of module with activity |
| `has_vle_activity` | total_clicks > 0 | Binary VLE usage flag |
| `assessment_count` | num_tma + num_cma + num_exams | Total assessments submitted |
| `submission_rate` | assessment_count / module_length | Submission consistency |
| `late_submission_flag` | avg_submission_delta > 0 | Average late submissions |
| `registration_earliness` | date_registration | Planning proxy |

---

## Technologies

| Layer | Technology | Role |
|-------|-----------|------|
| Language | Python 3.11+ | Runtime |
| Data | pandas, DuckDB | Ingestion, aggregation, analytic SQL |
| ML | scikit-learn 1.3+ | Training and evaluation |
| Dashboard | Pure HTML/CSS/JS | Interactive visualization (self-contained) |
| Versioning | Git + GitHub | Version control |

---

## Dashboard

Interactive dashboard (self-contained HTML, dark theme) with:

- **Model Summary** — Key metrics in cards (accuracy, recall, ROC-AUC)
- **Feature Importance** — Bar chart with top 15 feature importances
- **Target Distribution** — Dropout vs. no-dropout proportions
- **Interactive Simulation** — Sliders to adjust variables and see impact on dropout probability
- **Conclusions** — Actionable insights and next steps

### Access

```bash
start artifacts/dashboard/index.html   # Windows
open artifacts/dashboard/index.html    # Mac
xdg-open artifacts/dashboard/index.html # Linux
```

---

## Technical Decisions (ADRs)

- **ADR-001:** RandomForest as baseline classifier — captures non-linearities,
  provides feature importance, robust to class imbalance with `class_weight="balanced"`.
- **ADR-002:** Model saved to `src/model.pkl` (not `models/`) + categorical encoding
  via pandas `.cat.codes` (not sklearn LabelEncoder).

---

## Author

**Laurent** — Data Architect & ML Engineer

- GitHub: [@laurentaf](https://github.com/laurentaf)
- LinkedIn: [lauferreira](https://linkedin.com/in/lauferreira)

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- **Kuzilek et al.** — For the OULAD dataset (Nature Sci. Data 4:170171, 2017, CC-BY 4.0)
- **[scikit-learn](https://scikit-learn.org/)** — Machine Learning library
- **[pandas](https://pandas.pydata.org/)** — Data manipulation