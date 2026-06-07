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
- [ ] Validar pipeline end-to-end com novas mudanças

## Fase 3: (aguardar briefing DataMission)

- [ ] TBD

## Fase 4 (opcional): Dashboard + Simulação

- [ ] Dashboard com conclusões e simulação interativa
