# TODO — Abandono Acadêmico Casa Grande

---

## Stage 0: SDD Scaffold (Missão 0)

- [x] Criar estrutura de pastas (src, data, reports)
- [x] Criar constitution, contract, README, ADR template, harness template, bootstrap spec

## Fase 1: Preparar ambiente e dependências

- [x] Criar requirements.txt com pandas, scikit-learn, requests, dbt
- [x] Implementar fetch_dataset() em src/main.py
- [x] Implementar train_model() em src/main.py
- [x] Implementar main() em src/main.py
- [x] ADR-001: RandomForestClassifier como baseline
- [x] Validar pipeline end-to-end (rodar `python src/main.py`) — Acc=0.665, F1=0.152 (baseline, melhorar em F2)

## Fase 2: Capturar dados via API — formato parametrizado + HTTP handling

- [x] fetch_dataset aceita parametro format (parquet/json/csv)
- [x] Tratamento de status HTTP (4xx/5xx) com mensagem amigável
- [x] Salvar dados crus em data/raw.csv
- [x] Print registra tamanho do arquivo baixado
- [x] Validar pipeline end-to-end com novas mudanças — 62.0 KB baixados, raw.csv 98.8 KB, F1=0.220

## Fase 3: Preprocessamento + DQ baseline checks + pipeline reestruturada

- [x] Extrair `preprocess_data(df)` de `train_model()` — separação de concerns
- [x] Implementar limpeza de nulls em `preprocess_data` (drop/fill + logging)
- [x] Substituir sklearn LabelEncoder por pandas encoding (get_dummies ou .cat.codes)
- [x] Implementar 6 DQ baseline checks em `src/main.py` (check_nulls, check_columns, check_types, check_duplicates, check_target_balance, check_bounds)
- [x] Encadear pipeline: `fetch_dataset -> DQ checks -> preprocess_data -> train_model`
- [x] Atualizar `artifacts/dq/checks.md` com implementação dos 6 checks (DQ-01 a DQ-06)
- [x] Decidir path de modelo: `src/model.pkl` (ADR-002 documenta decisao)
- [x] Validar pipeline end-to-end com `python src/main.py` — metrics no console

## Fase 4 (opcional): Dashboard + Simulação

- [ ] Dashboard com conclusões e simulação interativa
