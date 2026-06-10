# Review: abandono-academico-casa-grande

**project_name:** abandono-academico-casa-grande
**review_date:** 2026-06-09
**reviewer:** delivery-reviewer (Round 6)
**verdict:** NOT DELIVERABLE

---

## Stage 0: PASS (wdl_gate exit_code=N/A)

Preflight consumed from orchestrator: **PASS (0 findings)**.
Boot check: **PASS**.

> **Note on WDL gate:** This project was created before WDL v1 (LACOUNCIL `a4fe9faa` + `7fd94c1a`, 2026-06-06). No `artifacts/wdl/` directory exists in the child repo, and the project predates the mandatory WDL gate. Per DR-E8, this is not a retroactive violation — WDL applies to new dispatches after 2026-06-06. The 6 findings below are all stale-reference P0 violations, not WDL gate violations.

---

## Stage 1: P0 Walk

### SDD Scaffold (Mission 0)

- [PASS] **SDD scaffold exists.** `spec/constitution.md`, `spec/todo.md`, `spec/adr/{_template.md,README.md}`, `spec/harness/_template.md`, `spec/specs/000-bootstrap/spec.md`, `spec/design-direction.md`, `contract.md`, `README.md` — all present in child repo. Per-file minimum sizes met.
- [PASS] **`spec/todo.md` populated since Stage 0.** First task is Mission 0; all stages checked off.

### Validation

- [PASS] **delivery-reviewer validated.** This is the sign-off document.
- [PASS] **project.yaml exists, valid, declares needs + deliverables.** 6 needs, 11 deliverables.
- [PASS] **All deliverables exist in `artifacts/`.** Confirmed: `src/main.py`, `requirements.txt`, `.gitignore`, `artifacts/data/model.md`, `artifacts/data/etl_oulad.sql`, `artifacts/dashboard/index.html`, `artifacts/dq/checks.md`, `artifacts/design/source.md`, `README.md`, `contract.md` — all on GitHub. Gitignored items (`src/model.pkl`, `data/oulad/*.csv`, `artifacts/data/oulad.duckdb`) are expected to be absent from GitHub per `.gitignore`.
- [PASS] **No secrets in versioned files.** No API keys, tokens, or connection strings found. `.env` in `.gitignore`.
- [PASS] **Git sync.** Round 5 corrections committed and pushed (SHA `1f522e4`).

### Artifacts by subclass

- [PASS] **Data artifact: spec exists.** `artifacts/data/model.md` — comprehensive (35+ KB), includes schema, ML results, feature importance, statistical tests.
- [PASS] **Data artifact: DQ rule documented.** `artifacts/dq/checks.md` — 6 DQ baseline checks documented (DQ-01 through DQ-06), all PASS.
- [FAIL] **Empty DataFrame guard incomplete.** Constitution principle 4: "Nenhuma etapa do pipeline crasha com dados vazios — produz mensagem amigável." `_guard_empty()` exists and is called in `engineer_features()`, but is NOT called in `load_gold_table()`, `prepare_ml_data()`, `train_models()`, `evaluate_on_test()`, or `save_model()`. These stages would crash (KeyError, ValueError, or pickle empty) on empty input.
  - **Fix:** Add `_guard_empty(df, ...)` calls at the entry of every pipeline function that receives a DataFrame or derived data. Specifically: `load_gold_table` after `fetchdf()`, `prepare_ml_data` after receiving `df`, `evaluate_on_test` after receiving `X_test`/`y_test`. For `train_models` and `save_model`, add `if len(y_train) == 0` / `if model is None` guards. **Owner:** data-architect.
- [FAIL] **Visual artifact: DESIGN.md reference is stale.** `artifacts/design/source.md` references "CRA scale is 0–4" and "7-column table" — these are DataMission-era descriptions. The OULAD dashboard uses OULAD features (engagement_intensity, days_active, weighted_avg_score), not CRA or 7 columns. The "Decisões do Modelo" section's "Variáveis do Dataset (7-column table with keep/remove decisions)" describes the old dataset.
  - **Fix:** Rewrite `artifacts/design/source.md` to describe the actual OULAD dashboard changes (feature importance bars, OULAD simulation variables, PT-BR translations of OULAD-specific terms). Remove all CRA / 7-column references. **Owner:** dashboard-designer.
- [N/A] **Automation trigger + SLA.** No automation deliverable. Project is batch ML pipeline, not n8n workflow.

### Decisions (ADRs)

- [PASS] **ADR-mínimo-1 with temporal gate.** 3 ADRs exist (001 Superseded, 002 Accepted, 003 Accepted), all after first decision stage. Path `spec/adr/NNN-*.md` correct. `_template.md` + `README.md` present.

### Synthetic Data

- [PASS] **P0-15 data policy compliance.** No synthetic data artifacts detected. All data is from OULAD (real, published, CC-BY 4.0). No frontmatter marking needed.

### Reproduction and legibility

- [PASS] **README ≥ 400 chars.** Comprehensive (32,593 students, 87.5% accuracy, "Como Rodar", "Onde está o quê").
- [PASS] **No implementation code in LAOS.** `Get-ChildItem projects -Recurse -Include *.sql,*.dax,*.pbix` returns empty.

### Calibration and pre-flight

- [PASS] **PR-1 calibration.** Level-A rigor applied (permutation test for significance, 5-fold CV, stratified split — appropriate for 32K row dataset, not PhD-overkill).
- [PASS] **Preflight passed.** Consumed from orchestrator.
- [N/A] **Boot check 6th dimension.** Not re-run for this round; consumed from orchestrator PASS.

### Stale DataMission references (P0 — Constitution + specs don't match actual project)

- [FAIL] **`spec/constitution.md` Scope section says "consumindo dataset via API DataMission".** This is the foundational governance document and it references the wrong dataset. After ADR-003 reversed to OULAD, the constitution was not updated.
  - **Fix:** Change Scope line from "consumindo dataset via API DataMission" to "consumindo dataset OULAD (Open University Learning Analytics Dataset, 32.593 alunos, 7 módulos, 2013–2014)". **Owner:** data-architect (constitution changes are typically the project lead's responsibility).
- [FAIL] **`spec/specs/000-bootstrap/spec.md` references DataMission API, 1000 records, 7 columns.** The bootstrap spec describes the old dataset entirely (project ID, enrollment_status, grade_point_average, etc.). None of this matches OULAD.
  - **Fix:** Rewrite `spec/specs/000-bootstrap/spec.md` to describe the actual OULAD project: 7 CSVs, 32,593 students, DuckDB, feature engineering, ML pipeline. **Owner:** data-architect.
- [FAIL] **`spec/design-direction.md` Section 4 references `grade_point_average, attendance_rate, scholarship_percent`** as dashboard simulation sliders. These are DataMission variables that don't exist in OULAD. The actual dashboard uses OULAD features.
  - **Fix:** Update Element 3 (Simulação Interativa) to list OULAD features: `days_active`, `total_clicks`, `weighted_avg_score`, `assessment_count`, `engagement_intensity`, etc. **Owner:** dashboard-designer.
- [FAIL] **`requirements.txt` lists `dbt-core>=1.7.0` and `requests>=2.31.0`.** These are DataMission-era dependencies. The OULAD pipeline uses DuckDB (not dbt) and reads CSVs locally (not API requests). Missing: `duckdb` and `scipy` (which `src/main.py` imports). Stale deps mislead reproducibility.
  - **Fix:** Remove `dbt-core` and `requests`. Add `duckdb>=0.9.0` and `scipy>=1.11.0`. **Owner:** data-architect.

---

## Stage 2: Project Criteria

Derived from `project.yaml` stages 1–4 acceptance criteria:

- [PASS] **Stage 1: `src/main.py` with `main()` defined.** Confirmed: `def main()` at entry point.
- [FAIL] **Stage 1: `requirements.txt` lists pandas, scikit-learn, requests, dbt.** `requests` and `dbt-core` are stale (DataMission-era). Missing `duckdb` and `scipy` which the pipeline actually uses.
  - **Fix:** Same as P0 stale deps fix above. **Owner:** data-architect.
- [N/A] **Stage 1: `fetch_dataset()` uses `requests.get` with API URL.** This was the DataMission ingestion method. The OULAD pipeline loads CSVs via DuckDB — no API fetch. The old `fetch_dataset` function was replaced by `load_gold_table()`. Acceptance criterion is obsolete per ADR-003.
- [PASS] **Stage 3: `preprocess_data` equivalent.** `engineer_features()` + `prepare_ml_data()` separate from `train_models()`. Pipeline chains: load → engineer → prepare → train → evaluate.
- [PASS] **Stage 3: Categorical encoding via pandas (not sklearn LabelEncoder).** ADR-002 documents switch from LabelEncoder to pandas. In actual code, `OneHotEncoder` is used in `ColumnTransformer` (not pandas `.cat.codes`), but this is an improvement over `.cat.codes` (avoids ordinality). Acceptable deviation documented in ADR-002.
- [PASS] **Stage 3: 6 DQ baseline checks implemented.** `artifacts/dq/checks.md` documents all 6 checks.
- [PASS] **Stage 3: Model saved at `src/model.pkl`.** `.gitignore` confirms it's produced (gitignored as binary).
- [PASS] **Stage 4: Dashboard exists at `artifacts/dashboard/index.html`.** Confirmed: 40KB self-contained HTML.
- [PASS] **Stage 4: Dashboard shows conclusions.** Feature importance bars, metrics cards, distribution chart.
- [PASS] **Stage 4: Dashboard has interactive simulation.** Sliders for OULAD features with probability output.
- [PASS] **Stage 4: Dashboard is visually professional and responsive.** Dark theme, responsive grid, PT-BR labels.

---

## Stage 3: Coverage

| Rule / Criterion | Verdict | Evidence |
|---|---|---|
| SDD scaffold exists | EXPLICITLY_VERIFIED | `spec/constitution.md` (GitHub SHA `0c0693`), `spec/todo.md`, `spec/adr/{_template.md,README.md}`, `spec/harness/_template.md`, `spec/specs/000-bootstrap/spec.md`, `spec/design-direction.md`, `contract.md`, `README.md` — all present |
| spec/todo.md populated since Stage 0 | EXPLICITLY_VERIFIED | `spec/todo.md` — all phases checked off |
| project.yaml valid | EXPLICITLY_VERIFIED | 6 needs, 11 deliverables, `repo:` field set |
| All deliverables exist | EXPLICITLY_VERIFIED | 8/11 on GitHub; 3 gitignored (`model.pkl`, `*.csv`, `oulad.duckdb`) — expected |
| No secrets | EXPLICITLY_VERIFIED | No API keys/tokens in any file; `.env` in `.gitignore` |
| Data artifact spec + DQ rule | EXPLICITLY_VERIFIED | `artifacts/data/model.md` (35KB), `artifacts/dq/checks.md` (6 checks) |
| Empty DataFrame guard | VIOLATED | `_guard_empty()` only called in `engineer_features()` (`src/main.py:72`). Missing in: `load_gold_table`, `prepare_ml_data`, `train_models`, `evaluate_on_test`, `save_model` |
| DESIGN.md reference | VIOLATED | `artifacts/design/source.md` references "CRA scale 0–4" and "7-column table" — DataMission-era |
| ADR minimum 1 | EXPLICITLY_VERIFIED | 3 ADRs: 001 (Superseded), 002 (Accepted), 003 (Accepted) |
| ADR path spec/adr/ | EXPLICITLY_VERIFIED | All ADRs in `spec/adr/NNN-*.md` |
| README ≥ 400 chars | EXPLICITLY_VERIFIED | Comprehensive, includes results, how-to-run, directory map |
| No implementation code in LAOS | EXPLICITLY_VERIFIED | Glob `projects/**/*.sql`, `*.dax`, `*.pbix` returns empty |
| Constitution matches project | VIOLATED | `spec/constitution.md` Scope: "consumindo dataset via API DataMission" — stale |
| Bootstrap spec matches project | VIOLATED | `spec/specs/000-bootstrap/spec.md` describes DataMission API, 1000 records, 7 columns |
| Design direction matches dashboard | VIOLATED | `spec/design-direction.md` Section 4 lists `grade_point_average, attendance_rate, scholarship_percent` — DataMission variables |
| requirements.txt matches pipeline | VIOLATED | Lists `dbt-core>=1.7.0`, `requests>=2.31.0` (stale); missing `duckdb`, `scipy` (used by `src/main.py`) |
| No synthetic data without frontmatter | N/A_justified | No synthetic data — all from OULAD (real, CC-BY 4.0) |
| Automation trigger + SLA | N/A_justified | No automation deliverable in this project |
| contract.md ≥ 250 chars | EXPLICITLY_VERIFIED | Contract rewritten for OULAD (GitHub SHA `1dd445`), mirrors project.yaml |
| PR-1 calibration | EXPLICITLY_VERIFIED | Level-A rigor: permutation tests, 5-fold CV, stratified splits |

---

## Stage 4: Reflection

### 1. Least confident finding

The **`requirements.txt`** finding: `dbt-core` and `requests` are clearly stale, but I'm less confident about whether their presence is a P0 violation (blocks delivery) vs. P1 (should fix). The argument for P0: reproducibility is a Constitution principle (principle 2), and `pip install -r requirements.txt` would install two unused packages while missing two required ones (`duckdb`, `scipy`) — the pipeline would **fail to run** after a clean install. This makes it P0.

### 2. Did NOT check

1. **Dashboard accessibility (WCAG 2.1 AA)** — P1 item, not checked in detail (color contrast, screen reader order).
2. **Dashboard JS logic correctness** — did not verify the simulation math matches the model's predict_proba.
3. **OULAD CSV data integrity** — gitignored files can't be verified via GitHub; would need local access.
4. **`src/model.pkl` quality** — binary file can't be reviewed; trusting the pipeline output documentation.
5. **Performance / runtime** — no check on pipeline execution time or memory usage.

### 3. Pattern reminder

**Stale spec after dataset reversal (3rd occurrence).** This is the 3rd time across projects that a fundamental scope change (dataset reversal, API change, target redefinition) left stale references in constitution, bootstrap spec, and design-direction. Previous occurrences:
- Round 4 of this same project (DataMission → OULAD reversal left stale `models/` directory, fixed in Round 5).
- Round 3 of this project (old dataset references in contract.md, fixed in Round 5).

**Pattern signal:** When a project undergoes a fundamental reversal (ADR-003 type), the subagent making the change should update ALL upstream spec documents (constitution, bootstrap spec, design-direction, requirements.txt) as part of the same commit — not just the implementation artifacts. This is a **charter gap** in `data-architect.md` and `dashboard-designer.md` — neither charter explicitly requires updating spec/ documents after a dataset reversal.

**Recommended action (DR-E8):** Open issue against `.opencode/agent/data-architect.md` §"Artefatos obrigatórios" to add: "After any ADR that changes the project's fundamental scope (dataset, target, API), update `spec/constitution.md`, `spec/specs/000-bootstrap/spec.md`, and `requirements.txt` in the same commit." Same for `dashboard-designer.md` for `spec/design-direction.md` and `artifacts/design/source.md`.

### 4. Permission prompts observed during execution

None. All file reads were via GitHub MCP (no local path access required for this review).

---

## Actions Required (FAIL items)

| # | Finding | Severity | Fix | Owner |
|---|---------|----------|-----|-------|
| 1 | `spec/constitution.md` Scope: stale "DataMission" reference | P0 | Change to "consumindo dataset OULAD (Open University Learning Analytics Dataset, 32.593 alunos, 7 módulos, 2013–2014)" | data-architect |
| 2 | `spec/specs/000-bootstrap/spec.md`: describes DataMission (1000 records, 7 columns, API) | P0 | Rewrite to describe OULAD (7 CSVs, 32,593 students, DuckDB, feature engineering, ML pipeline) | data-architect |
| 3 | `spec/design-direction.md` Section 4: lists DataMission variables (grade_point_average, attendance_rate, scholarship_percent) | P0 | Update simulation sliders to OULAD features (days_active, total_clicks, weighted_avg_score, assessment_count, engagement_intensity) | dashboard-designer |
| 4 | `artifacts/design/source.md`: references "CRA scale 0–4" and "7-column table" | P0 | Rewrite to describe OULAD dashboard changes (OULAD feature importance, simulation variables, PT-BR translations of OULAD terms) | dashboard-designer |
| 5 | `requirements.txt`: lists `dbt-core`, `requests` (stale); missing `duckdb`, `scipy` | P0 | Remove `dbt-core>=1.7.0` and `requests>=2.31.0`; add `duckdb>=0.9.0` and `scipy>=1.11.0` | data-architect |
| 6 | Empty DataFrame guard incomplete: only in `engineer_features()`, missing in 5 other pipeline stages | P0 | Add `_guard_empty()` / empty-data guards at entry of `load_gold_table`, `prepare_ml_data`, `train_models`, `evaluate_on_test`, `save_model` | data-architect |

---

## Signature

**Preflight Stage 0:** PASS (0 findings), consumed from orchestrator.
**WDL gate:** N/A — project predates WDL v1 mandate (pre-2026-06-06).
**Stages 1–4:** 6 P0 violations found (4 stale DataMission references + 1 stale requirements.txt + 1 incomplete empty-DF guard).

**Reviewer:** delivery-reviewer (automated subagent)
**Date:** 2026-06-09
**Round:** 6

---

## Verdict

**NOT DELIVERABLE** — 6 P0 violations: constitution, bootstrap spec, design-direction, design source, and requirements.txt contain stale DataMission-era references that conflict with the actual OULAD project; empty DataFrame guard coverage is incomplete per Constitution principle 4. Fix the 6 items above and re-submit for Round 7 review.
