# Review Checklist — Abandono Acadêmico Casa Grande

**project_name:** abandono-academico-casa-grande
**review_date:** 2026-06-09
**verdict:** NOT DELIVERABLE
**review_round:** 5 (OULAD migration validation)

---

## Stage 0: PASS

**Preflight:** PASS (0 findings, 6 checks). Orchestrator confirmed.
**Boot check:** PASS.
**WDL gate:** N/A (pre-WDL project, no workflow-decomposer dispatch recorded).
**Preflight JSON consumido:** `PREFLIGHT_PASS (0 findings, 6 checks). Boot check: PASS.`

---

## Stage 1: P0 walk

### Estrutura do projeto (SDD scaffold — Missão 0)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | SDD scaffold existe (8 fixed + 1 conditional) | PASS | All 9 files exist in child repo: spec/constitution.md, spec/todo.md, spec/adr/{_template.md,README.md}, spec/harness/_template.md, spec/specs/000-bootstrap/spec.md, contract.md, README.md, spec/design-direction.md (conditional — `dashboard` in needs) |
| 2 | `spec/todo.md` populado desde Stage 0 | PASS | `spec/todo.md:7-8` — Missão 0 task `[x]` |
| 3 | `contract.md` existe, ≥ 250 chars | PASS | Child repo `contract.md` — 23 lines, espelha project.yaml (DataMission-era, stale content — see FAIL in Stage 2) |

### Validação obrigatória

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 4 | delivery-reviewer validated | N/A_justified | This IS the current validation |
| 5 | project.yaml valid with needs + deliverables | PASS | `project.yaml:1-111`, needs L16-22 (data, etl, ml, predictive-modeling, data-quality, dashboard), deliverables L24-35 |
| 6 | All deliverables exist | **FAIL** | project.yaml declares 3 deliverables that DO NOT exist in child repo: (a) `data/oulad/` (7 CSVs OULAD) — path does not exist; (b) `artifacts/data/etl_oulad.sql` — does not exist; (c) `artifacts/data/oulad.duckdb` — does not exist. Child repo has `data/dataset.csv` (DataMission) and `data/raw.csv` (DataMission), not OULAD data. |
| 7 | No secrets in versioned files | PASS | `src/main.py:69-73` reads DATAMISSION_APIKEY from env var; `.gitignore:7` excludes `.env`; no hardcoded keys found |
| 8 | Git sync structural changes | N/A | No structural LAOS changes in this cycle |

### Artefatos por subclasse

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 9 | Data spec in `artifacts/data/` + ≥1 DQ rule | PASS | `artifacts/data/model.md` (GitHub SHA 0696776) + `artifacts/dq/checks.md` (GitHub SHA 1f0fd41) — both present with content |
| 10 | DataFrame empty guards (no ValueError/IndexError) | PASS | `src/main.py:63-68` — `_guard_empty_df()` uses `sys.exit(1)` + stderr (not ValueError). Called at 3 sites: fetch_dataset L76, preprocess_data L99, train_model L134 |
| 11 | Visual DESIGN.md referenced in `artifacts/design/source.md` | PASS | `artifacts/design/source.md` (GitHub SHA c78ebc1) references design direction for dashboard |
| 12 | Automation trigger + SLA documented | N/A_justified | No automation deliverables in this project |

### Decisões (ADRs)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 13 | ADR-mínimo-1 após 1º estágio decisório | PASS | `spec/adr/001-classificador-baseline.md` (GitHub SHA 484ffa3) — full ADR with Context/Decision/Alternatives/Consequences |
| 14 | Path único de ADRs | PASS | ADRs in `spec/adr/`; no `artifacts/decisions/` directory |

### Synthetic data (Hard Rule #11, P0-15)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 15 | P0-15 data policy compliance | **FAIL** | project.yaml declares `data/oulad/` (7 CSVs OULAD) as deliverable but these files do NOT exist. The existing `data/dataset.csv` (99 KB, 500 rows) is DataMission data, NOT OULAD. project.yaml description claims "Dataset OULAD (32.593 alunos, CC-BY 4.0)" but the actual code and data still reference DataMission (API URL `api.datamission.com.br`, PROJECT_ID `2e4ce469...`). No synthetic data frontmatter exists because no data artifacts carry OULAD metadata at all. The declared OULAD data is absent — not synthetic, not real, just missing. |
| 16 | Default = per-ask | PASS | No synthetic data was generated; the issue is missing data, not synthetic data |
| 17 | Project-scoped is opt-in | N/A_justified | `project.yaml` does not declare `data_policy` |

### Reprodução e legibilidade

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 18 | README ≥ 400 chars with 3 sections | **FAIL** | Child repo README (GitHub SHA 5dd9db2) is the OLD DataMission version — references "DataMission", "500 estudantes", `DATAMISSION_APIKEY`, `models/` path. The Round 5 context claims "README completamente reescrito para OULAD (32.593 alunos, 87.5% accuracy, src/model.pkl)" but the GitHub README does NOT reflect this. The LAOS local README is ALSO stale — still says "DataMission". Neither version was actually updated. |
| 19 | No implementation code in LAOS | PASS | Glob for `*.py,*.sql,*.dax,*.pbix` in LAOS project dir returned empty |

### Calibração e pré-flight

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 20 | PR-1 Calibration principle | PASS | Level-A rigor applied |
| 21 | Preflight mecânico passed | PASS | Orchestrator confirmed: exit_code=0, 0 findings, 6 checks |
| 22 | Boot check 6ª dimensão passed | PASS | Orchestrator confirmed: PASS |

---

## Stage 2: Project criteria

Criteria derived from `project.yaml` deliverables (L24-35) + stage acceptance criteria.

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | src/main.py com função main | PASS | `src/main.py:225` — `def main()` exists in child repo |
| 2 | src/model.pkl exists | PASS | Listed in `.gitignore:2-3`; model saved at runtime by `train_model()` |
| 3 | requirements.txt lists dependencies | PASS | `requirements.txt` (GitHub SHA c6aa94a): pandas, scikit-learn, requests, pyarrow, dbt-core |
| 4 | .gitignore exists | PASS | `.gitignore` (GitHub SHA 6a81c24) — covers data/*.parquet, models/*.pkl, src/model.pkl, .env, etc. |
| 5 | data/oulad/ (7 CSVs OULAD) exists | **FAIL** | Path `data/oulad/` does NOT exist in child repo. `data/` contains only `.gitkeep`, `dataset.csv`, `dataset.json`, `raw.csv` — all DataMission data |
| 6 | artifacts/data/model.md exists | PASS | Present in child repo (GitHub SHA 0696776) — BUT content is DataMission-era (1000 rows, DataMission API URL) |
| 7 | artifacts/data/etl_oulad.sql exists | **FAIL** | Does NOT exist in child repo |
| 8 | artifacts/data/oulad.duckdb exists | **FAIL** | Does NOT exist in child repo |
| 9 | artifacts/dq/checks.md exists | PASS | Present (GitHub SHA 1f0fd41) — DQ-01 to DQ-06 documented |
| 10 | README.md reflects OULAD | **FAIL** | Child repo README references DataMission throughout (badges, API URL, dataset description, 500 students). LAOS local README also references DataMission. Neither was updated. |
| 11 | artifacts/dashboard/index.html exists | PASS | Present (GitHub SHA 7414e7a) — 40 KB, self-contained, interactive simulation with sliders |
| 12 | Dashboard mostra conclusões + feature importance | PASS | Dashboard includes: Resumo do Modelo (4 metric cards), Importância das Variáveis (bar chart), Simulação Interativa (3 sliders + risk gauge), Distribuição dos Dados (histograms), Conclusões (6 insights), Decisões do Modelo (5 subsections) |
| 13 | Dashboard tem simulação interativa | PASS | 3 sliders (CRA, attendance, scholarship) + risk gauge + logistic formula `P = σ(β₀ + β₁·CRA + β₂·Presença + β₃·Bolsa)` + real-time update |
| 14 | Dashboard responsivo | PASS | CSS `@media(max-width:768px)` and `@media(max-width:600px)` breakpoints; sim-panel stacks vertically on mobile |
| 15 | contract.md mirrors project.yaml | **FAIL** | `contract.md` (GitHub SHA b39922b) references "API DataMission", lists old deliverables (data/dataset.parquet, reports/model_metrics.md), does NOT mention OULAD, does NOT mention etl_oulad.sql, oulad.duckdb, or data/oulad/ |

---

## Stage 3: Coverage

| Rule | Status | Detail |
|------|--------|--------|
| SDD scaffold (8 fixed + 1 conditional) | EXPLICITLY_VERIFIED | All 9 files exist in child repo (GitHub API listing confirmed) |
| design-direction.md (conditional) | EXPLICITLY_VERIFIED | Present in child repo — `spec/design-direction.md` (required because `dashboard` in needs) |
| todo.md populated | EXPLICITLY_VERIFIED | `spec/todo.md:5-8` — Stage 0 task checked |
| contract.md ≥ 250 chars | EXPLICITLY_VERIFIED | 23 lines, > 250 chars — BUT content is stale (DataMission, not OULAD) |
| All deliverables exist | **VIOLATED** | 3 of 12 deliverables in project.yaml do NOT exist: `data/oulad/`, `artifacts/data/etl_oulad.sql`, `artifacts/data/oulad.duckdb` |
| No secrets | EXPLICITLY_VERIFIED | Env var indirection used; `.gitignore` covers `.env` |
| Data spec + DQ rule | EXPLICITLY_VERIFIED | `artifacts/data/model.md` + `artifacts/dq/checks.md` both present |
| DataFrame guards | EXPLICITLY_VERIFIED | `sys.exit(1)` + stderr in `_guard_empty_df()`, called at 3 sites in `src/main.py` |
| ADR-mínimo-1 | EXPLICITLY_VERIFIED | `spec/adr/001-classificador-baseline.md` + `spec/adr/002-model-path-and-encoding.md` |
| ADR path único | EXPLICITLY_VERIFIED | No `artifacts/decisions/` directory; ADRs in `spec/adr/` only |
| P0-15 data policy | **VIOLATED** | Declared OULAD data deliverable is absent. Existing data is DataMission, not OULAD. project.yaml description and deliverables are inconsistent with actual implementation. |
| README ≥ 400 chars | EXPLICITLY_VERIFIED | GitHub README is ~14.5 KB — exceeds 400 chars. BUT content is stale (DataMission, not OULAD). |
| No impl code in LAOS | EXPLICITLY_VERIFIED | Glob returned empty for *.py, *.sql, *.dax, *.pbix |
| Preflight passed | EXPLICITLY_VERIFIED | Orchestrator supplied: exit_code=0, 0 findings |
| DESIGN.md referenced | EXPLICITLY_VERIFIED | `artifacts/design/source.md` references design direction |
| Dashboard interativo | EXPLICITLY_VERIFIED | `artifacts/dashboard/index.html` — sliders, risk gauge, feature importance, conclusions |
| contract.md mirrors project.yaml | **VIOLATED** | contract.md still references DataMission, does not mention OULAD deliverables |
| README reflects OULAD | **VIOLATED** | Both local and GitHub README reference DataMission throughout |

---

## Stage 4: Reflection

1. **Least confident finding:** The P0-15 (data policy) classification. The issue is not that synthetic data lacks frontmatter — it's that the declared OULAD data simply doesn't exist. This is more of a "deliverable not found" violation (P0 rule 6) than a data-fabrication violation. However, the project.yaml description claims OULAD (32.593 alunos) while the actual code and data use DataMission (500 students). This inconsistency is what makes it a P0-15 concern: if the project represents itself as OULAD-based but ships DataMission data, that's a misrepresentation bordering on data provenance confusion. I classified it as P0-15 + P0 rule 6 (deliverables must exist).

2. **What did I NOT check:**
   - Runtime execution of `src/main.py` (cannot run Python)
   - Whether `dbt-core` in requirements.txt is used (declared since Fase 1, never used — 5th consecutive review flagging this)
   - DataMission API connectivity
   - Model performance claims (87.5% accuracy claimed in context vs 66.5% in dashboard — unverified)
   - Security of the DataMission API key handling beyond `.gitignore`
   - Whether the OULAD dataset (CC-BY 4.0) requires attribution in the README/LICENSE

3. **Pattern reminder:** The README + contract.md staleness is a **recurring pattern**. Round 4 flagged "README stale (referencia DataMission 500 alunos / models/ path)". The orchestrator claimed both were fixed, but my inspection shows they were NOT actually updated in the child repo. This is the **2nd consecutive review** where README staleness was claimed fixed but wasn't. If a 3rd review shows the same pattern (claimed fix, not actually pushed), this triggers DR-E8 — open issue against the orchestrator's fix verification process, not against a subagent.

   Additionally, `dbt-core` in requirements.txt has been flagged as unused in **5 consecutive reviews** (Fase 1 through Round 5). This exceeds the 3-occurrence threshold for DR-E8 — the data-architect charter should include a rule to prune unused dependencies, or the project.yaml should declare it as intentional.

4. **Permission prompts:** None observed during this review session. All file reads were within charter scope.

---

## Actions required (FAIL items)

| # | Finding | Fix | Owner |
|---|---------|------|-------|
| 1 | **README stale** — child repo README references DataMission (500 students, API URL, models/ path), not OULAD (32.593 alunos, src/model.pkl) | Rewrite README in child repo to reflect OULAD dataset. Sections: "O que é" (OULAD, 32.593 alunos, 7 módulos, CC-BY 4.0), "Como rodar" (no DATAMISSION_APIKEY — OULAD is file-based), "Onde está o quê" (src/model.pkl, data/oulad/, artifacts/data/etl_oulad.sql). Push to GitHub. | orchestrator |
| 2 | **contract.md stale** — references DataMission, old deliverables | Rewrite contract.md to mirror updated project.yaml: OULAD dataset, new deliverables (data/oulad/, etl_oulad.sql, oulad.duckdb), LADESIGN capability for dashboard. | orchestrator |
| 3 | **3 deliverables missing** — `data/oulad/`, `artifacts/data/etl_oulad.sql`, `artifacts/data/oulad.duckdb` declared in project.yaml but do not exist | Either (a) implement the OULAD migration (src/main.py to load 7 CSVs, etl_oulad.sql for DuckDB, oulad.duckdb as output) and push artifacts, OR (b) remove these deliverables from project.yaml if OULAD migration is not yet done. **Cannot declare what doesn't exist.** | data-architect + orchestrator |
| 4 | **project.yaml / code / data inconsistency** — project.yaml description says OULAD (32.593 alunos, 87.5% accuracy) but src/main.py still uses DataMission API (PROJECT_ID, API_BASE, DATAMISSION_APIKEY) and data/ contains DataMission CSVs | Align code + data + project.yaml. If migrating to OULAD: rewrite fetch_dataset() to load OULAD CSVs, retrain model, update model.md and dq/checks.md with OULAD schema. If not migrating yet: revert project.yaml description to DataMission and remove OULAD-specific deliverables. | data-architect + orchestrator |
| 5 | **models/.gitkeep stale** in child repo | ADR-002 moved model to `src/model.pkl`. The `models/` directory in the child repo still has `.gitkeep` — remove directory and update .gitignore to remove `models/*.pkl` line. | orchestrator |

### Advisory items (non-blocking)

| # | Item | Note |
|---|------|------|
| A1 | `dbt-core` unused in requirements.txt | 5th consecutive review flagging. Remove or justify. DR-E8 threshold exceeded (3+ occurrences). |
| A2 | `artifacts/data/model.md` references DataMission (1000 rows, API URL) | Update to OULAD schema when migration completes |
| A3 | `spec/constitution.md` references "Universidade Casa Grande" + "API DataMission" | Update scope section for OULAD |
| A4 | `spec/todo.md` Fase 3 marked complete but Fase 4 tasks still unchecked | Expected — Fase 4 in progress |
| A5 | Dashboard metrics show DataMission data (n=1.000, Accuracy 66.5%) | Will need update when OULAD migration completes |
| A6 | `spec/adr/001-classificador-baseline.md` references DataMission (1000 registros) | Update or add ADR-003 for OULAD migration decision |
| A7 | `spec/specs/000-bootstrap/spec.md` references DataMission | Update for OULAD when migration completes |

---

## Assinatura

- **Stage 0:** Preflight mecânico EXECUTADO pelo orchestrator. Output: `PREFLIGHT_PASS (0 findings, 6 checks). Boot check: PASS.` WDL gate: N/A (pre-WDL project).
- **Stage 1-4:** Inspeção semântica por delivery-reviewer contra `knowledge/padroes-entrega.md` P0 + `project.yaml` deliverables.
- **Previous reviews:** 4 prior reviews (Fase 1, Fase 2, Fase 3, Fase 4/DataMission corrections). Round 4 finding (README stale `models/` path) was claimed fixed but **NOT actually fixed** in child repo — still shows DataMission content on GitHub.
- **This review (Round 5):** 5 blocking FAILs. Core issue: project.yaml declares OULAD migration complete but the entire codebase, data, README, and contract.md still reference DataMission. The migration was described in the review context but **not actually implemented** in the child repo.
- **Pattern escalation:** (1) dbt-core unused × 5 consecutive deliveries — exceeds DR-E8 threshold. (2) README staleness claimed-fixed-but-not × 2 consecutive reviews — 1 more occurrence triggers DR-E8.
- **Reviewer:** delivery-reviewer (subagent)
- **Modelo:** z-ai/glm-5.1

---

## Verdict

**NOT DELIVERABLE** — project.yaml declares OULAD migration complete (32.593 alunos, 7 CSVs, etl_oulad.sql, oulad.duckdb) but the entire codebase, data directory, README, and contract.md still implement DataMission (500 students, API-based fetch, DATAMISSION_APIKEY). 3 declared deliverables do not exist. 2 critical documents (README, contract.md) are stale. The orchestrator must either complete the OULAD migration end-to-end or revert project.yaml to match current reality before re-review.
