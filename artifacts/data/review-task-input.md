# Data-Architect Delivery Report
## Plan ID: df49b883-f9c6-43a4-bdb2-2a8be0fe7828

## PONTO 1 — Benchmark Completo

### 6 Modelos Treinados e Avaliados

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC | Treino(s) | Tamanho |
|--------|----------|-----------|--------|----|---------|-----------|---------|
| Dummy | 0.5659 | — | — | — | — | 0.13 | — |
| Logistic Regression | 0.8695 | 0.7352 | 0.9079 | 0.8125 | 0.9458 | 0.76 | 6KB |
| Random Forest ✅ | 0.8774 | 0.7857 | 0.8341 | 0.8092 | 0.9525 | 2.25 | 87MB |
| Gradient Boosting | 0.8811 | 0.7849 | 0.8518 | 0.8170 | 0.9546 | 47.71 | — |
| XGBoost | 0.8728 | 0.7355 | 0.9242 | 0.8191 | 0.9533 | 2.98 | 680KB |
| LightGBM | 0.8757 | 0.7384 | 0.9311 | 0.8236 | 0.9547 | 1.73 | — |

### Modelo Selecionado: Random Forest
- ROC-AUC 0.9525 (gap de 0.0022 para LightGBM, abaixo do threshold 0.01)
- Justificativa: RF mantém melhor equilíbrio qualidade/tempo/interpretabilidade
- Observação: LightGBM tem recall 0.9311 (10pp acima do RF 0.8341) — alternativa se recall for prioridade

### Entregáveis
- ✅ `src/main.py` — código estendido com 6 modelos e benchmark
- ✅ `src/model.pkl` — Random Forest retreinado (87MB)
- ✅ `artifacts/data/model.md` — atualizado com tabela benchmark, feature importances, proxy info
- ✅ `artifacts/dashboard/model_proxy.json` — LR calibrado com top-3 features (lad, ac, sr)
- ✅ `spec/adr/003-model-selection-comparative.md` — decisão documentada
- ✅ `requirements.txt` — xgboost, lightgbm adicionados
- ✅ Dados OULAD baixados e DuckDB criado (32.593 rows, 63.8MB)

## PONTO 3 — Conclusões e Ações

- ✅ `artifacts/data/conclusions-and-actions.md` criado com:
  - Correlação vs causalidade: features são PREDITIVAS, não CAUSAIS
  - Limites de generalização: OULAD é EaD UK 2013-2014
  - Features acionáveis vs não-acionáveis (tabela classificatória)
  - 3 ações concretas (gatilho, público, métrica, esforço)
  - O que NÃO se pode extrair dos dados (4 limitações)
