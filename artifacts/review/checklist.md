# Review: abandono-academico-casa-grande

**project_name:** abandono-academico-casa-grande
**review_date:** 2026-06-10
**reviewer:** delivery-reviewer (Round 7)
**verdict:** NOT DELIVERABLE

---

## Stage 0: PASS (wdl_gate exit_code=N/A)

Preflight consumed from orchestrator: **PASS (0 findings)**. Boot check: **PASS**.

> **Note on WDL gate:** This project was created before WDL v1 (LACOUNCIL `a4fe9faa` + `7fd94c1a`, 2026-06-06). No `artifacts/wdl/` directory exists in the child repo, and the project predates the mandatory WDL gate. Per DR-E8, this is not a retroactive violation — WDL applies to new dispatches after 2026-06-06. The findings below are content-level P0 violations, not WDL gate violations.

---

## Stage 1: P0 Walk

### SDD Scaffold (Mission 0)

- [PASS] **SDD scaffold exists.** `spec/constitution.md`, `spec/todo.md`, `spec/adr/{_template.md,README.md}`, `spec/harness/_template.md`, `spec/specs/000-bootstrap/spec.md`, `spec/design-direction.md`, `contract.md`, `README.md` — all present in child repo. Per-file minimum sizes met.
- [PASS] **`spec/todo.md` populated since Stage 0.** First task is Mission 0; all stages checked off.

### Validation

- [PASS] **delivery-reviewer validated.** This is the sign-off document.
- [PASS] **project.yaml exists, valid, declares needs + deliverables.** 6 needs, 11+ deliverables.
- [PASS] **All deliverables exist in `artifacts/`.** Confirmed: `src/main.py`, `requirements.txt`, `.gitignore`, `artifacts/data/model.md`, `artifacts/data/etl_oulad.sql`, `artifacts/dashboard/index.html`, `artifacts/dq/checks.md`, `artifacts/design/source.md`, `README.md`, `contract.md` — all on GitHub. Gitignored items (`src/model.pkl`, `data/oulad/*.csv`, `artifacts/data/oulad.duckdb`) are expected to be absent from GitHub per `.gitignore`.
- [PASS] **No secrets in versioned files.** No API keys, tokens, or connection strings found. `.env` in `.gitignore`.
- [PASS] **Git sync.** Round 6 corrections committed and pushed (SHA `7cd74ad`).

### Artifacts by subclass

- [PASS] **Data artifact: spec exists.** `artifacts/data/model.md` — comprehensive (35+ KB), includes schema, ML results, feature importance, statistical tests.
- [PASS] **Data artifact: DQ rule documented.** `artifacts/dq/checks.md` — 6 DQ baseline checks documented (DQ-01 through DQ-06), all PASS.
- [PASS] **Empty DataFrame guard complete.** `_guard_empty()` called in all 6 pipeline stages: `load_gold_table` (line after fetchdf), `engineer_features`, `prepare_ml_data`, `train_models` (via X_train guard), `evaluate_on_test` (via X_test guard), `save_model` (via X_train guard). **Fixed since Round 6.**
- [FAIL] **Visual artifact: dashboard content is stale DataMission.** `artifacts/dashboard/index.html` is entirely DataMission-era content. Evidence:
  - Header: `Abandono Acadêmico <span>DataMission</span>` (should be OULAD)
  - Badge: `n = 1.000` (should be n = 32.593)
  - Metrics: Accuracy 66.5%, F1=0.152, Precision=0.28, Recall=0.10 (should be Accuracy 87.5%, Recall 93.7%, ROC-AUC 0.954)
  - Feature importance: CRA (0.352), Presença (0.298), Bolsa (0.178), Curso (0.172) (should be last_activity_day 20.2%, assessment_count 12.4%, submission_rate 8.8%, etc.)
  - Simulation sliders: CRA 0–4, Presença 0–100%, Bolsa 0–100% (should be last_activity_day, assessment_count, avg_assessment_score, total_clicks, days_active per design-direction.md)
  - Distribution charts: CRA histogram, Presença histogram, Bolsa histogram (should be OULAD feature distributions)
  - Target donut: 75%/25% Non-Abandono/Abandono (should be 68.8%/31.2% per OULAD)
  - Decision table: 7 DataMission columns (student_id, timestamp, course_name, etc.) (should reflect OULAD features/decisions)
  - Conclusions: all reference CRA, Presença, Bolsa (should reference OULAD engagement features)
  - Footer: "Dados: DataMission API · 1.000 registros · 4 cursos · 7 colunas" (should be OULAD)
  - This contradicts: `spec/design-direction.md` (OULAD top-5 features), `artifacts/design/source.md` (OULAD feature table), `contract.md` (OULAD metrics), `README.md` (OULAD metrics), `artifacts/data/model.md` (OULAD schema+results).
  - **Fix:** Rewrite `artifacts/dashboard/index.html` entirely with OULAD content: correct metrics (87.5%, 93.7%, 0.954), OULAD top-5 features as sliders, OULAD feature importance bars, OULAD distribution charts, OULAD conclusions. **Owner:** dashboard-designer.

- [N/A] **Automation trigger + SLA.** No automation deliverable. Project is batch ML pipeline, not n8n workflow.

### Decisions (ADRs)

- [PASS] **ADR-mínimo-1 with temporal gate.** 3 ADRs exist (001 Superseded, 002 Accepted, 003 Accepted), all after first decision stage. Path `spec/adr/NNN-*.md` correct. `_template.md` + `README.md` present.

### Synthetic Data

- [PASS] **P0-15 data policy compliance.** No synthetic data artifacts detected. All data is from OULAD (real, published, CC-BY 4.0). No frontmatter marking needed.

### Reproduction and legibility

- [PASS] **README ≥ 400 chars.** Comprehensive (OULAD, 32,593 students, 87.5% accuracy, "Como Rodar", "Onde está o quê").
- [PASS] **No implementation code in LAOS.** No *.sql, *.dax, *.pbix found under `projects/`.

### Calibration and pre-flight

- [PASS] **PR-1 calibration.** Level-A rigor applied (permutation test for significance, 5-fold CV, stratified split — appropriate for 32K row dataset, not PhD-overkill).
- [PASS] **Preflight passed.** Consumed from orchestrator.
- [N/A] **Boot check 6th dimension.** Not re-run for this round; consumed from orchestrator PASS.

### Stale DataMission references — Round 6 corrections verified

- [PASS] **`spec/constitution.md` Scope updated to OULAD.** Reads: "Pipeline de previsao de abandono academico, utilizando o Open University Learning Analytics Dataset (OULAD) — 32.593 estudantes..." **Fixed since Round 6.**
- [PASS] **`spec/specs/000-bootstrap/spec.md` rewritten for OULAD.** Version 2.0 (OULAD migration), describes 7 CSVs, 32,593 students, DuckDB pipeline. **Fixed since Round 6.**
- [PASS] **`spec/design-direction.md` updated with OULAD features.** Section 4 lists: last_activity_day, assessment_count, submission_rate, num_tma, avg_assessment_score. **Fixed since Round 6.**
- [PASS] **`artifacts/design/source.md` updated with OULAD features.** Contains OULAD feature table with importance/scale, OULAD metrics. **Fixed since Round 6.**
- [PASS] **`requirements.txt` updated.** Contains: pandas>=2.0.0, scikit-learn>=1.3.0, duckdb>=0.9.0, scipy>=1.11.0, pyarrow>=14.0.0. No stale dbt-core/requests. **Fixed since Round 6.**

### project.yaml stale references (P0 — acceptance criteria describe DataMission pipeline)

- [FAIL] **`project.yaml` stages 1–2 acceptance_criteria describe DataMission pipeline.** Stage 1: "requirements.txt lista pandas, scikit-learn, requests e dbt", "Existe funcao fetch_dataset que usa requests.get com URL da API". Stage 2: same stale criteria + "fetch_dataset aceita parametro format", "fetch_dataset salva dados crus em data/raw.csv". These describe the old DataMission API pipeline, not the current OULAD DuckDB pipeline. The actual pipeline has no `fetch_dataset()`, no `requests.get`, no `dbt-core`. Stages 3–4 are OULAD-neutral and pass.
  - **Fix:** Update stages 1–2 acceptance_criteria to match the actual OULAD pipeline. Stage 1: "requirements.txt lista pandas, scikit-learn, duckdb, scipy", "src/main.py com load_gold_table() via DuckDB". Stage 2: remove fetch_dataset criteria; replace with OULAD ingestion criteria (CSV load, DuckDB bronze/silver/gold). **Owner:** orchestrator (project.yaml is LAOS-side).

### todo.md stale references (P0 — tracker describes old pipeline)

- [FAIL] **`spec/todo.md` stages 1–2 still describe DataMission pipeline.** Stage 1: "Criar requirements.txt com pandas, scikit-learn, requests, dbt", "Implementar fetch_dataset() em src/main.py". Stage 2: "fetch_dataset aceita parametro format", "Tratamento de status HTTP". These tasks are obsolete per ADR-003. Stage 4 says "Dashboard com conclusões e simulação" but the dashboard content is still DataMission (see dashboard FAIL above).
  - **Fix:** Update stages 1–2 task descriptions to match OULAD pipeline. Stage 4 checkbox should note that dashboard content needs OULAD update. **Owner:** data-architect (or orchestrator).

### ADR stale references (advisory, not blocking)

- [N/A] **ADR-001 DataMission content.** ADR-001 describes the DataMission dataset (1000 records, 7 columns). Status: **Superseded** by ADR-003. The Superseded status + post-mortem section makes this acceptable — it documents the historical decision and why it was reversed. No fix needed.
- [PASS] **ADR-002 references "DataMission briefing".** ADR-002 Context says "a DataMission briefing e a reestruturação do pipeline exigem...". This is historically accurate — ADR-002 was written during the DataMission phase and the decision (model path + encoding) remains valid for OULAD. The actual encoding used is OneHotEncoder (improvement over .cat.codes), which is documented in model.md. Acceptable as-is.

---

## Stage 2: Project Criteria

Derived from `project.yaml` stages 1–4 acceptance criteria:

- [PASS] **Stage 1: `src/main.py` with `main()` defined.** Confirmed: `def main()` at entry point, 847 lines.
- [FAIL] **Stage 1: `requirements.txt` lists pandas, scikit-learn, requests, dbt.** The criteria say "requests e dbt" but these were removed. Actual requirements.txt is correct (duckdb, scipy), but the acceptance criterion text in project.yaml is stale. See project.yaml FAIL above.
- [N/A] **Stage 1: `fetch_dataset()` uses `requests.get` with API URL.** This criterion is obsolete per ADR-003 (DataMission→OULAD). The OULAD pipeline loads CSVs via DuckDB — no API fetch. The old `fetch_dataset` was replaced by `load_gold_table()`. Criterion needs updating in project.yaml.
- [PASS] **Stage 3: `preprocess_data` equivalent.** `engineer_features()` + `prepare_ml_data()` separate from `train_models()`. Pipeline chains: load → engineer → prepare → train → evaluate.
- [PASS] **Stage 3: Categorical encoding.** `OneHotEncoder` used in `ColumnTransformer` (improvement over `.cat.codes`). Documented in ADR-002 + model.md.
- [PASS] **Stage 3: 6 DQ baseline checks implemented.** `artifacts/dq/checks.md` documents all 6 checks (DQ-01 to DQ-06), all PASS.
- [PASS] **Stage 3: Model saved at `src/model.pkl`.** `.gitignore` confirms it's produced (gitignored as binary).
- [PASS] **Stage 4: Dashboard exists at `artifacts/dashboard/index.html`.** File exists (40KB self-contained HTML).
- [PASS] **Stage 4: Dashboard shows conclusions.** Has feature importance bars, metrics cards, distribution charts, conclusions section. (Content is DataMission-era — see P0 FAIL in Stage 1.)
- [FAIL] **Stage 4: Dashboard has interactive simulation with correct variables.** Dashboard has sliders, but they are for DataMission variables (CRA, Presença, Bolsa), not OULAD features (last_activity_day, assessment_count, etc.) as specified in design-direction.md. The simulation math uses DataMission coefficients, not OULAD model coefficients. This makes the simulation misleading for anyone using the dashboard.
- [PASS] **Stage 4: Dashboard is visually professional and responsive.** Dark theme, responsive grid, PT-BR labels, animations. (Visual quality is good; content is wrong.)

### ML/DS: Constitution Art. 10 — Detalhamento Metodológico Extremo

Per `padroes-entrega.md` §Stage 2: ML/DS projects must verify Constitution Art. 10 diagnostic report. This project does not use the `laecon` MCP (laecon is BASIC status; pipeline uses scikit-learn directly per contract.md note). Art. 10 requires answering 7 mandatory questions for every model trained. Checking against `artifacts/data/model.md`:

| # | Question | Answered? | Evidence |
|---|----------|-----------|----------|
| 1 | Which model family and why? | YES | model.md §"Modeling Decisions" item 1–2: RF chosen for non-linearity + feature importance; LR as linear baseline |
| 2 | What is the target encoding? | YES | model.md §"Target Encoding": Withdrawn→1, others→0 |
| 3 | How is class imbalance handled? | YES | model.md §"Modeling Decisions" item 2: class_weight="balanced" |
| 4 | What is the train/test split? | YES | model.md §"Pipeline Overview": Stratified 80/20 |
| 5 | What are the evaluation metrics and why? | YES | model.md §"Modeling Decisions" items 6–8: Dummy floor, permutation tests, paired t-test |
| 6 | What are the assumptions/limitations? | YES | Constitution Non-goals + model.md §"Non-goals" equivalent in modeling decisions |
| 7 | Is the model statistically significant vs baseline? | YES | model.md §"Statistical Significance Tests": RF vs Dummy p=0.001; RF vs LR p=0.084 (ns) |

**Art. 10 verdict: PASS** — all 7 questions explicitly answered in `artifacts/data/model.md`.

---

## Stage 3: Coverage

| Rule / Criterion | Verdict | Evidence |
|---|---|---|
| SDD scaffold exists | EXPLICITLY_VERIFIED | All 9 files present in child repo (GitHub SHA `9c454c`, `8dbfd9`, etc.) |
| spec/todo.md populated since Stage 0 | EXPLICITLY_VERIFIED | `spec/todo.md` — all phases checked off |
| project.yaml valid | EXPLICITLY_VERIFIED | 6 needs, 11+ deliverables, `repo:` field set |
| All deliverables exist | EXPLICITLY_VERIFIED | 8+ on GitHub; 3 gitignored — expected |
| No secrets | EXPLICITLY_VERIFIED | No API keys/tokens; `.env` in `.gitignore` |
| Data artifact spec + DQ rule | EXPLICITLY_VERIFIED | `artifacts/data/model.md` (35KB), `artifacts/dq/checks.md` (6 checks) |
| Empty DataFrame guard | EXPLICITLY_VERIFIED | `_guard_empty()` called in 6 locations: `load_gold_table`, `engineer_features`, `prepare_ml_data`, `train_models`, `evaluate_on_test`, `save_model` (`src/main.py`) |
| DESIGN.md reference | EXPLICITLY_VERIFIED | `artifacts/design/source.md` — rewritten for OULAD (top-5 features, metrics, design decisions) |
| Dashboard content matches project | VIOLATED | `artifacts/dashboard/index.html` — entirely DataMission: header "DataMission", n=1000, accuracy 66.5%, sliders for CRA/Presença/Bolsa. Conflicts with all OULAD docs. |
| ADR minimum 1 | EXPLICITLY_VERIFIED | 3 ADRs: 001 (Superseded), 002 (Accepted), 003 (Accepted) |
| ADR path spec/adr/ | EXPLICITLY_VERIFIED | All ADRs in `spec/adr/NNN-*.md` |
| README ≥ 400 chars | EXPLICITLY_VERIFIED | Comprehensive OULAD README with results, how-to-run, directory map |
| No implementation code in LAOS | EXPLICITLY_VERIFIED | No *.sql, *.dax, *.pbix under `projects/` |
| Constitution matches project | EXPLICITLY_VERIFIED | `spec/constitution.md` Scope: "utilizando o Open University Learning Analytics Dataset (OULAD) — 32.593 estudantes" |
| Bootstrap spec matches project | EXPLICITLY_VERIFIED | `spec/specs/000-bootstrap/spec.md` Version 2.0 (OULAD migration), 7 CSVs, 32,593 students |
| Design direction matches dashboard | VIOLATED | `spec/design-direction.md` correctly lists OULAD features, but dashboard `index.html` does NOT implement them — uses CRA/Presença/Bolsa instead |
| requirements.txt matches pipeline | EXPLICITLY_VERIFIED | pandas, scikit-learn, duckdb, scipy, pyarrow — matches `src/main.py` imports |
| project.yaml acceptance_criteria match pipeline | VIOLATED | Stages 1–2 still reference `requests`, `dbt`, `fetch_dataset()` — DataMission-era criteria |
| todo.md task descriptions match pipeline | VIOLATED | Stages 1–2 still describe DataMission tasks (fetch_dataset, requests, HTTP handling) |
| No synthetic data without frontmatter | N/A_justified | No synthetic data — all from OULAD (real, CC-BY 4.0) |
| Automation trigger + SLA | N/A_justified | No automation deliverable in this project |
| contract.md ≥ 250 chars | EXPLICITLY_VERIFIED | Contract rewritten for OULAD (GitHub SHA `1dd445`), mirrors project.yaml |
| PR-1 calibration | EXPLICITLY_VERIFIED | Level-A rigor: permutation tests, 5-fold CV, stratified splits |
| Art. 10 diagnostic report | EXPLICITLY_VERIFIED | All 7 mandatory questions answered in `artifacts/data/model.md` |

---

## Stage 4: Reflection

### 1. Least confident finding

The **project.yaml acceptance_criteria** and **todo.md** stale references are borderline P0/P1. The argument for P0: acceptance criteria are the contract by which this project is judged; stale criteria mean the contract doesn't reflect reality. The argument for P1: the actual *deliverables* are correct (requirements.txt has the right deps, main.py has the right pipeline), only the *descriptive text* in the contract is stale. I'm calling it P0 because project.yaml is the authoritative contract — if someone reads it and tries to verify "requirements.txt lists requests and dbt", they'll find a FAIL, causing confusion. However, this is a lower-priority P0 than the dashboard — the dashboard shows *wrong data to end users*.

### 2. Did NOT check

1. **Dashboard accessibility (WCAG 2.1 AA)** — P1 item, not checked in detail (color contrast, screen reader order).
2. **Dashboard JS simulation math correctness** — did not verify that the OULAD version (if it existed) would correctly compute predict_proba. The current DataMission simulation math is irrelevant since the entire dashboard needs rewriting.
3. **OULAD CSV data integrity** — gitignored files can't be verified via GitHub; would need local access to run the pipeline.
4. **`src/model.pkl` quality** — binary file can't be reviewed; trusting the pipeline output documentation.
5. **Performance / runtime** — no check on pipeline execution time or memory usage.

### 3. Pattern reminder

**Stale dashboard after dataset reversal (4th occurrence across projects/rounds).** This is now the 4th time that a fundamental scope change left stale content in a downstream artifact:

1. Round 4 (this project): DataMission→OULAD reversal left stale `models/` directory
2. Round 5 (this project): stale contract.md, old dataset references
3. Round 6 (this project): stale constitution, bootstrap spec, design-direction, source.md, requirements.txt
4. Round 7 (this project): **stale dashboard** — the most visible artifact, entirely DataMission

The pattern is clear: **when a dataset reversal happens (ADR-003 type), every artifact that references the old dataset must be updated in the SAME commit.** The dashboard was missed in Round 6 because the dashboard-designer's corrections focused on `design-direction.md` and `source.md` (the *specs*) but not on `index.html` (the *implementation*).

**Charter gap (DR-E8 signal — 2nd consecutive delivery):** Neither `.opencode/agent/data-architect.md` nor `.opencode/agent/dashboard-designer.md` explicitly requires updating ALL downstream artifacts (including implementation files like index.html, not just spec files) after a dataset reversal. This should be added to both charters. If it appears in a 3rd consecutive delivery, escalate via `lacouncil.detect_patterns`.

### 4. Permission prompts observed during execution

None. All file reads were via GitHub MCP (no local path access required for this review).

---

## Actions Required (FAIL items)

| # | Finding | Severity | Fix | Owner |
|---|---------|----------|-----|-------|
| 1 | `artifacts/dashboard/index.html` entirely stale — DataMission content (header, metrics, sliders, charts, conclusions, footer all reference old dataset) | **P0 (blocking)** | Rewrite `artifacts/dashboard/index.html` with OULAD content: metrics (87.5% accuracy, 93.7% recall, 0.954 ROC-AUC), OULAD top-5 feature importance bars, OULAD simulation sliders (last_activity_day, assessment_count, avg_assessment_score, total_clicks, days_active), OULAD distributions, OULAD target donut (68.8%/31.2%), OULAD conclusions. Follow `spec/design-direction.md` and `artifacts/design/source.md` as source of truth. | dashboard-designer |
| 2 | `project.yaml` stages 1–2 acceptance_criteria describe DataMission pipeline (requests, dbt, fetch_dataset) | **P0 (blocking)** | Update stages 1–2 acceptance_criteria to match OULAD pipeline: "requirements.txt lista pandas, scikit-learn, duckdb, scipy", "src/main.py com load_gold_table() via DuckDB", remove fetch_dataset/HTTP/format criteria, add OULAD ingestion criteria. | orchestrator |
| 3 | `spec/todo.md` stages 1–2 task descriptions still describe DataMission pipeline | **P0 (blocking)** | Update stage 1–2 tasks to reflect OULAD pipeline steps. Update stage 4 to note dashboard content update. | data-architect or orchestrator |

---

## Signature

**Preflight Stage 0:** PASS (0 findings), consumed from orchestrator.
**WDL gate:** N/A — project predates WDL v1 mandate (pre-2026-06-06).
**Stages 1–4:** 3 P0 violations found (1 stale dashboard + 2 stale project.yaml/todo.md DataMission references). 5 of 6 Round 6 corrections confirmed fixed.
**Reviewer:** delivery-reviewer (automated subagent)
**Date:** 2026-06-10
**Round:** 7

---

## Verdict

**NOT DELIVERABLE** — 3 P0 violations: (1) `artifacts/dashboard/index.html` is entirely DataMission-era content with wrong metrics, features, sliders, and conclusions — the most user-facing artifact contradicts all OULAD documentation; (2) `project.yaml` stages 1–2 acceptance_criteria describe the abandoned DataMission pipeline; (3) `spec/todo.md` stages 1–2 describe DataMission tasks. The dashboard is the critical fix — it must be rewritten for OULAD. The project.yaml and todo.md are lower-impact but still P0 because the acceptance contract doesn't match reality. Fix the 3 items and re-submit for Round 8 review.
