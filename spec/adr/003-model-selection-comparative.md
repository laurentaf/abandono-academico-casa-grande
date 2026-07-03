# ADR-003: Model Selection — Comparative Benchmark de 6 Modelos

## Status

Accepted

## Context

O pipeline de previsão de abandono acadêmico precisava de uma avaliação
sistemática de múltiplos algoritmos para selecionar o modelo mais adequado
para o dataset OULAD (32.593 alunos, 31,2% de taxa de evasão).

Os modelos existentes até então eram Dummy, Logistic Regression e Random
Forest. Este ADR documenta a extensão para 6 modelos com benchmark
completo em qualidade, tempo, custo computacional e interpretabilidade.

## Decision

Realizar benchmark completo com 6 modelos no dataset OULAD, manter
**Random Forest** como modelo padrão de produção.

### Critério de seleção

- **Métrica primária:** ROC-AUC no test set (hold-out 20%)
- **Regra de decisão:** manter Random Forest como default a menos que
  outro modelo supere em > 0.01 ROC-AUC. Este limiar reflete que, para
  este dataset, diferenças menores que 1% são ruído entre folds.
- **Consideração secundária:** recall da classe positiva (Withdrawn) —
  prioridade de negócio é identificar evadidos.

### Hiperparâmetros

| Modelo | Hiperparâmetros |
|--------|----------------|
| Dummy | strategy="stratified" |
| Logistic Regression | max_iter=1000, C=1.0, class_weight="balanced" |
| Random Forest | n_estimators=200, max_depth=None, min_samples_split=5, min_samples_leaf=2, class_weight="balanced" |
| Gradient Boosting | n_estimators=200, max_depth=4, min_samples_split=5, min_samples_leaf=2 |
| XGBoost | n_estimators=200, max_depth=6, learning_rate=0.1, scale_pos_weight=2.21, subsample=0.8, colsample_bytree=0.8 |
| LightGBM | n_estimators=200, max_depth=-1, num_leaves=31, learning_rate=0.1, class_weight="balanced" |

### Estratégia de validação

- 80/20 stratified split (26.074 treino, 6.519 teste)
- 5-fold cross-validation estratificada
- Teste de permutação (1000 iterações) vs Dummy
- Teste t pareado (5-fold) entre todos os pares de modelos

## Alternatives

### A) Apenas Logistic Regression (manter baseline simples)
Rejeitado: LR tem ROC-AUC 0,9458 vs RF 0,9525 — diferença pequena mas
consistente. LR é mantido como proxy para dashboard.

### B) Apenas modelos gradient-based (XGBoost + LightGBM)
Rejeitado: adiciona dependências (xgboost, lightgbm) sem ganho
significativo sobre RF (gap < 0.01 ROC-AUC).

### C) Ensemble stacking (meta-modelo sobre os 6)
Rejeitado: complexidade injustificada — modelos individuais já têm
desempenho similar. Stacking adicionaria risco de overfit sem ganho
garantido.

## Consequences

### Positivas
+ Benchmark sistemático documenta o trade-off entre todos os modelos
+ Random Forest continua sendo o default, sem dependências extras
+ LightGBM documentado como alternativa viável se recall máximo for
  necessário (0,9311 vs 0,8341 do RF)
+ XGBoost disponível como fallback (0,9242 recall)
+ Model proxy (LR com 3 features) gerado para simulação no dashboard
+ Dependências xgboost e lightgbm adicionadas ao requirements.txt

### Negativas
- Dependências extras (xgboost==2.1.4, lightgbm==4.6.0) aumentam
  o tempo de `pip install`
- Tempo de pipeline aumentou de ~3s (LR+RF) para ~55s (6 modelos)
- Modelo final (RF com 200 trees) ocupa ~85 MB em disco
- Gradient Boosting é 20x mais lento que RF para treinar sem
  ganho significativo (0,9546 vs 0,9525 ROC-AUC)

### Observação sobre Recall vs ROC-AUC

LightGBM tem recall 0,9311 vs RF 0,8341 — uma diferença de ~10pp na
identificação de evadidos. Se o custo de falso negativo for alto
(estudante em risco não identificado), LightGBM pode ser preferível.
A decisão de manter RF reflete o critério ROC-AUC adotado, mas a
equipe de negócio pode reverter para LightGBM se recall for prioridade.

## Datas

- Benchmark executado: 2026-07-03
- Modelo selecionado: Random Forest
- Pipeline completo: ~55 segundos (6 modelos com 5-fold CV)
