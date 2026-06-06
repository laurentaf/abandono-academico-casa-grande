# Pipeline de Previsão de Abandono Acadêmico — Universidade Casa Grande

## O que é
Pipeline de ML para prever abandono acadêmico (enrollment_status) de estudantes
da Universidade Casa Grande, usando dataset da DataMission. 3 fases estruturadas
+ fase 4 opcional (dashboard com simulação interativa).

## Como rodar
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar API token
export DATAMISSION_APIKEY="seu_token_aqui"

# 3. Executar pipeline
python src/main.py
```

## Onde está o quê
| Caminho | Descrição |
|---------|-----------|
| `src/main.py` | Entry point: fetch, train, evaluate |
| `data/` | Dataset baixado da API (parquet) |
| `models/` | Modelo treinado (model.pkl) |
| `reports/` | Métricas do modelo |
| `spec/` | SDD scaffold (constitution, ADRs, specs) |
| `contract.md` | Contrato do projeto em prosa |

## DataMission
- Project ID: `2e4ce469-1a75-45fb-a41e-160196c7b989`
- API: `https://api.datamission.com.br/projects/{project_id}/dataset?format=parquet`
