# Review Checklist — abandono-academico-casa-grande

**project_name:** abandono-academico-casa-grande
**review_date:** 2026-06-07
**verdict:** NOT DELIVERABLE

---

## Stage 0: PASS

Preflight mecânico executado pelo orchestrator: exit_code=0, 0 findings. Boot check PASS. Pipeline rodou e2e com sucesso.

**Preflight JSON consumido:** `PREFLIGHT_PASS: 0 findings, 5 checks completed.` (5 checks: YAML arithmetic, path existence, secret scan, cross-reference integrity, no implementation code in LAOS).

---

## Stage 1: P0 Walk

### Estrutura do projeto (SDD scaffold — Missão 0)

- [PASS] **SDD scaffold existe (8 fixos + 1 condicional).**
  - `spec/constitution.md` — EXISTE, ≥400 chars, seções "Princípios" (5), "Scope", "Non-goals" (2). ✓
  - `spec/todo.md` — EXISTE, ≥100 chars, 1ª task = Missão 0 (Stage 0: SDD Scaffold). ✓
  - `spec/adr/_template.md` — EXISTE, stub-por-design. ✓
  - `spec/adr/README.md` — EXISTE, ≥80 chars. ✓
  - `spec/harness/_template.md` — EXISTE, stub-por-design. ✓
  - `spec/specs/000-bootstrap/spec.md` — EXISTE, ≥400 chars, seções "Contexto", "Decisão inicial", "Critérios de pronto". ✓
  - `contract.md` — EXISTE, ≥250 chars, espelha project.yaml (brief, needs, deliverables, capabilities_used, repo). ✓
  - `README.md` — EXISTE, ≥400 chars, seções "O que é", "Como rodar", "Onde está o quê". ✓
  - `spec/design-direction.md` — N/A (needs não contém `dashboard` nem `design` declarados). ✓

- [PASS] **`spec/todo.md` populado desde Stage 0.** `spec/todo.md:5-9` — 1ª seção = "Stage 0: SDD Scaffold (Missão 0)". ✓

- [PASS] **`contract.md` existe e espelha project.yaml.** `contract.md:1-28` — brief, needs, capabilities_used, deliverables, repo, Notas Fase 2. ≥250 chars. ✓

### Validação obrigatória

- [PASS] **project.yaml existe, válido, declara needs + deliverables.** `project.yaml:1-106`. ✓

- [PASS] **Todos os deliverables listados existem.** Declared: `src/main.py`, `requirements.txt`, `.gitignore`, `data/.gitkeep`, `models/.gitkeep`, `reports/.gitkeep`, `README.md` — all exist in child repo. Runtime outputs (parquet, pkl, metrics.md) correctly commented out. ✓

- [PASS] **Nenhum segredo em arquivos versionados.** `src/main.py:47-48` usa `os.environ.get("DATAMISSION_APIKEY")` — lê de env var, não hardcoded. `.env` está em `.gitignore:7`. ✓

- [N/A] **Git sync pós-mudança estrutural (LACOUNCIL 391a8179).** Não é mudança estrutural; é entrega de projeto (Regime B). N/A.

### Artefatos por subclasse

- [FAIL] **Para cada artefato de dados: existe spec do modelo em `artifacts/data/` e ao menos uma regra de qualidade documentada.**
  - `artifacts/data/model.md` existe APENAS no lado LAOS (`projects/abandono-academico-casa-grande/artifacts/data/model.md`), **NÃO existe no child repo** (`E:\projects\abandono-academico-casa-grande\artifacts\` só contém `review/checklist.md`).
  - `artifacts/dq/checks.md` existe APENAS no lado LAOS (`projects/abandono-academico-casa-grande/artifacts/dq/checks.md`), **NÃO existe no child repo**.
  - **Hard Rule #2:** "LAOS never stores domain artifacts. If you find yourself writing SQL, dashboard markup, n8n JSON, or any other implementation inside `LAOS/projects/<name>/`, it belongs in the child repo."
  - A P0 rule em `padroes-entrega.md` diz "Para cada artefato de dados: existe spec do modelo em `artifacts/data/`" — o path `artifacts/data/` refere-se ao **child repo**, não ao LAOS side.
  - **Evidence:** `E:\projects\abandono-academico-casa-grande\artifacts\` directory listing contains only `review/`. No `data/` or `dq/` subdirectory.
  - Fix: Copiar `artifacts/data/model.md` e `artifacts/dq/checks.md` do LAOS side para o child repo, depois remover do LAOS side (Hard Rule #2). Owner: **data-architect**.

- [PASS] **Para cada artefato de dados: o pipeline tem guards para DataFrame vazio.**
  - `src/main.py:36-39` — `_guard_empty_df()` definida com `sys.exit(1)` + `print(..., file=sys.stderr)`. ✓
  - `src/main.py:74` — guard após `pd.read_parquet` em `fetch_dataset`. ✓
  - `src/main.py:85` — guard após `pd.read_parquet` em `train_model`. ✓
  - `src/main.py:98` — guard em features após preprocessamento. ✓

- [N/A] **Para cada artefato visual: DESIGN.md referenciado em artifacts/design/source.md.** Projeto não tem needs `dashboard` ou `design` nesta fase.

- [N/A] **Para cada automação: trigger e SLA documentados.** Projeto não tem needs `automation` ou `alerts`.

### Decisões (ADRs)

- [PASS] **ADR-mínimo-1.** `spec/adr/001-classificador-baseline.md` EXISTE, numerado a partir de 001, com seções Status, Context, Decision, Alternatives (3), Consequences (+4/-3). ✓

- [PASS] **Path único de ADRs: `spec/adr/NNN-<slug>.md`.** ADR-001 segue o formato correto. Nenhum ADR em `artifacts/decisions/`. ✓

### Synthetic data (Hard Rule #11, P0-15)

- [PASS] **Nenhum artefato de produção com dados não-marcados.** `data/raw.csv` e `data/dataset.parquet` contêm dados da API DataMission (reais), não sintéticos. Nenhum `synthetic: true` necessário. ✓

- [N/A] **Default = per-ask.** Dados reais disponíveis via API; não houve necessidade de dados sintéticos.

### Reprodução e legibilidade

- [PASS] **README do child repo (≥400 chars).** `README.md:1-32` — seções "O que é", "Como rodar", "Onde está o quê". ✓

- [PASS] **Não há código de implementação dentro de LAOS.** Glob `projects/abandono-academico-casa-grande/**/*.{sql,dax,pbix}` retornou vazio. **NOTA:** `artifacts/data/model.md` e `artifacts/dq/checks.md` no lado LAOS são documentação de dados (violação de Hard Rule #2, já flagged acima). ✓ para .sql/.dax/.pbix; FAIL para domain artifacts em LAOS (ver finding acima).

### Calibração e pré-flight

- [PASS] **PR-1 (Calibração 20/10 vs 50/1).** Nível de rigor Level-A. RandomForest baseline é parcimonioso. `class_weight="balanced"` é default responsável. ✓

- [PASS] **Preflight mecânico (Stage 0) passou.** Exit code 0, 0 findings. ✓

- [PASS] **Boot check 6ª dimensão passou.** Orchestrator confirmou: "Boot check PASS." ✓

---

## Stage 2: Project-Specific Criteria (DataMission Fase 2 — 8 acceptance criteria)

- [PASS] **1. Existe src/main.py com função main definida.** `src/main.py:159` — `def main() -> None:` definida, chama `fetch_dataset`, `train_model`, `_save_metrics` em sequência. ✓

- [PASS] **2. requirements.txt lista pandas, scikit-learn, requests e dbt.** `requirements.txt:1-5` — pandas>=2.0.0, scikit-learn>=1.3.0, requests>=2.31.0, pyarrow>=14.0.0, dbt-core>=1.7.0. ✓

- [PASS] **3. Existe função fetch_dataset que usa requests.get com URL da API.** `src/main.py:42` — `def fetch_dataset(project_id, fmt, token)` definida. `src/main.py:56` — `response = requests.get(url, headers=headers, timeout=60)`. URL construída dinamicamente: `src/main.py:53` — `url = f"{API_BASE}/projects/{project_id}/dataset?format={fmt}"`. ✓

- [PASS] **4. Existe função train_model que treina e salva modelo via scikit-learn.** `src/main.py:83` — `def train_model(data_path)`. `src/main.py:104-105` — `RandomForestClassifier(...)`, `clf.fit(X_train, y_train)`. `src/main.py:108-109` — `pickle.dump({"model": clf, "label_encoder": le_course}, f)`. ✓

- [PASS] **5. fetch_dataset aceita parametro format (parquet/json/csv).** `src/main.py:42` — `def fetch_dataset(project_id: str = PROJECT_ID, fmt: str = "parquet", ...)`. `src/main.py:33` — `SUPPORTED_FORMATS = ("parquet", "json", "csv")`. `src/main.py:43-45` — validação `if fmt not in SUPPORTED_FORMATS`. ✓

- [PASS] **6. fetch_dataset trata erros HTTP (4xx/5xx) com mensagem amigável.** `src/main.py:58-65` — `if response.status_code >= 400:` → `print(f"Erro: API retornou HTTP {response.status_code} ao buscar dataset. Resposta: {reason}", file=sys.stderr)` + `sys.exit(1)`. Mensagem inclui código HTTP e excerto do corpo da resposta. ✓

- [PASS] **7. fetch_dataset salva dados crus em data/raw.csv.** `src/main.py:76` — `RAW_CSV_PATH.write_text(df.to_csv(index=False), encoding="utf-8")`. `src/main.py:29` — `RAW_CSV_PATH = DATA_DIR / "raw.csv"`. Arquivo `data/raw.csv` existe no child repo (2002 linhas, 7 colunas confirmadas). ✓

- [PASS] **8. Print registra tamanho do arquivo baixado.** `src/main.py:70-71` — `file_size_kb = len(response.content) / 1024` → `print(f"Dataset baixado: {file_size_kb:.1f} KB (formato={fmt}, HTTP {response.status_code})")`. ✓

---

## Stage 3: Coverage Verification

| P0 Rule / Criterion | Verdict | Evidence |
|---|---|---|
| SDD scaffold (8 fixos + 1 condicional) | EXPLICITLY_VERIFIED | Todos 8 arquivos lidos e validados contra matriz sdd-principles.md §2 |
| spec/todo.md populado desde Stage 0 | EXPLICITLY_VERIFIED | `spec/todo.md:5-9` — 1ª seção = "Stage 0: SDD Scaffold" |
| contract.md existe e espelha project.yaml | EXPLICITLY_VERIFIED | `contract.md:1-28` — brief, needs, deliverables, capabilities_used, repo |
| project.yaml existe e declara needs + deliverables | EXPLICITLY_VERIFIED | `project.yaml:1-106` |
| Todos deliverables listados existem | EXPLICITLY_VERIFIED | All 7 uncommented deliverables exist in child repo |
| Nenhum segredo em arquivos versionados | EXPLICITLY_VERIFIED | Token via env var (`src/main.py:47-48`); .env in .gitignore |
| **Artefato de dados: spec em artifacts/data/** | **VIOLATED** | `artifacts/data/model.md` existe APENAS no lado LAOS; ausente no child repo. Hard Rule #2 violado. |
| **Artefato de dados: regra de qualidade documentada** | **VIOLATED** | `artifacts/dq/checks.md` existe APENAS no lado LAOS; ausente no child repo. Hard Rule #2 violado. |
| Artefato de dados: guards para DataFrame vazio | EXPLICITLY_VERIFIED | `src/main.py:36-39` — `_guard_empty_df()` com sys.exit(1) + stderr; called at lines 74, 85, 98 |
| ADR-mínimo-1 | EXPLICITLY_VERIFIED | `spec/adr/001-classificador-baseline.md` — 37 lines, 4 seções obrigatórias |
| Path único de ADRs | EXPLICITLY_VERIFIED | No ADRs in `artifacts/decisions/` |
| README child repo (≥400 chars) | EXPLICITLY_VERIFIED | `README.md:1-32` — required sections present |
| Não há código de implementação em LAOS | EXPLICITLY_VERIFIED | No .sql/.dax/.pbix; domain artifacts em LAOS flagged separadamente |
| P0-15 Synthetic data policy | EXPLICITLY_VERIFIED | Nenhum dado sintético; dados são da API DataMission (real) |
| PR-1 Calibração | EXPLICITLY_VERIFIED | RandomForest baseline, class_weight balanced, no over-engineering |
| Preflight mecânico passou | EXPLICITLY_VERIFIED | Exit code 0, 0 findings |
| Boot check 6ª dimensão passou | EXPLICITLY_VERIFIED | "Boot check PASS" |
| Criterion 1: src/main.py com main() | EXPLICITLY_VERIFIED | `src/main.py:159` |
| Criterion 2: requirements.txt com 4 deps | EXPLICITLY_VERIFIED | `requirements.txt:1-5` |
| Criterion 3: fetch_dataset com requests.get | EXPLICITLY_VERIFIED | `src/main.py:56` |
| Criterion 4: train_model via scikit-learn | EXPLICITLY_VERIFIED | `src/main.py:104-109` |
| Criterion 5: fetch_dataset aceita parametro format | EXPLICITLY_VERIFIED | `src/main.py:42,33,43-45` |
| Criterion 6: fetch_dataset trata erros HTTP | EXPLICITLY_VERIFIED | `src/main.py:58-65` |
| Criterion 7: fetch_dataset salva dados em raw.csv | EXPLICITLY_VERIFIED | `src/main.py:76,29`; `data/raw.csv` exists (2002 lines) |
| Criterion 8: Print registra tamanho do arquivo | EXPLICITLY_VERIFIED | `src/main.py:70-71` |

---

## Stage 4: Reflection

1. **Least confident finding:** The VIOLATED finding for `artifacts/data/model.md` and `artifacts/dq/checks.md` not being in the child repo. These files EXIST in the LAOS side (`projects/abandono-academico-casa-grande/artifacts/data/model.md` and `artifacts/dq/checks.md`) and the Phase 1 review marked them as PASS — but the Phase 1 reviewer checked the LAOS side path instead of the child repo path. Hard Rule #2 is unambiguous: domain artifacts belong in the child repo, not in LAOS. The P0 rule "existe spec do modelo em artifacts/data/" in `padroes-entrega.md` refers to the child repo's `artifacts/` directory. I'm confident this is a real violation, but I acknowledge the Phase 1 reviewer may have interpreted the path differently.

2. **Did NOT check:**
   - (a) Execução real do pipeline (`python src/main.py`) — não tenho bash.
   - (b) Se o modelo treinado produz métricas aceitáveis (qualidade preditiva).
   - (c) Segurança da API DataMission (HTTPS, token scope).
   - (d) Performance do pipeline com dados maiores.
   - (e) Se `dbt-core` em requirements.txt é realmente usado — advisory from Phase 1 remains unresolved; dbt não é referenciado em nenhum código.

3. **Pattern reminder:**
   - **Domain-artifacts-in-LAOS pattern:** This is the 1st tracked occurrence where domain artifacts (data spec, DQ checks) were written to the LAOS side instead of the child repo. The Phase 1 reviewer accepted this as PASS, which means the reviewer itself misread the path. If this appears in 3+ consecutive deliveries, escalate via `lacouncil.detect_patterns` as a charter gap — the data-architect may not have clear instructions about WHERE to write artifacts (LAOS vs child repo).
   - **dbt declared but unused** — advisory from Phase 1 review (A2) was NOT addressed. Carries forward as advisory.

4. **Permission prompts observados:** Nenhum prompt de permissão observado durante esta execução. N/A.

---

## Ações requeridas se FAIL

| # | Finding | Severidade | Correção sugerida | Owner |
|---|---------|------------|-------------------|-------|
| 1 | `artifacts/data/model.md` ausente no child repo; existe APENAS no lado LAOS | P0 BLOCKING | Copiar para `E:\projects\abandono-academico-casa-grande\artifacts\data\model.md` e remover de `LAOS/projects/abandono-academico-casa-grande/artifacts/data/model.md` | data-architect |
| 2 | `artifacts/dq/checks.md` ausente no child repo; existe APENAS no lado LAOS | P0 BLOCKING | Copiar para `E:\projects\abandono-academico-casa-grande\artifacts\dq\checks.md` e remover de `LAOS/projects/abandono-academico-casa-grande/artifacts/dq/checks.md` | data-architect |

### Advisory actions (recommended, non-blocking)

| # | Finding | Correção sugerida | Owner |
|---|---------|-------------------|-------|
| A1 | `dbt-core` in requirements.txt unused in Fase 1 e Fase 2 | Document in a TODO ou remover se não planejado para Fase 3+ | data-architect |
| A2 | `artifacts/dq/checks.md:14,19,23` tem TODOs da Fase 2 (validação explícita de colunas, tipos, target balance) | Implementar ou promover para Fase 3 backlog | data-architect |

---

## Assinatura

- **Stage 0:** Preflight mecânico EXECUTADO pelo orchestrator. Output: `"PREFLIGHT_PASS: 0 findings, 5 checks completed."` Exit code 0.
- **Stage 1-4:** Inspeção semântica completa por delivery-reviewer contra `knowledge/padroes-entrega.md` P0 + `project.yaml` acceptance_criteria (Fase 2 — 8 criteria).
- **Phase 1 review findings:** 2 P0 findings from Phase 1 (commit 6303377) were RESOLVED in commit db860e0. New findings in Phase 2: 2 P0 BLOCKING (domain artifacts in wrong location).
- **Reviewer:** delivery-reviewer (subagent)
- **Modelo:** z-ai/glm-5.1
