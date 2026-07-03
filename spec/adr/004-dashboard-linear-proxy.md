# ADR-004: Dashboard com Proxy Linear (3 features) no lugar do RF completo

## Contexto

O dashboard interativo de abandono acadêmico (OULAD) precisa permitir
que o usuário ajuste sliders dos 3 principais indicadores preditivos
(last_activity_day, assessment_count, submission_rate) e veja em
tempo real:

1. A probabilidade estimada de evasão
2. O **esforço individual** de cada indicador para atingir uma meta
   configurável (inversão analítica: "quanto este indicador precisa
   mudar sozinho para que P(evasão) = meta?")

O modelo completo é um Random Forest com ~31 features (numéricas +
one-hot encoded categóricas), treinado em 32.593 registros com 500
árvores. O arquivo do modelo serializado (`model.pkl`) tem ~87 MB.

## Decisão

Substituir o RF completo por uma **Regressão Logística (proxy linear)
com apenas 3 features** no dashboard interativo, mantendo o RF como
modelo de referência de produção.

O proxy está calibrado e documentado em
`artifacts/dashboard/model_proxy.json`. A fórmula de cálculo:

```
normalized_val = (raw_val - mean) / std
log_odds = intercept + Σ(coeff_i × normalized_val_i)
probability = 1 / (1 + exp(-log_odds))
```

Os coeficientes foram extraídos de uma LogisticRegression treinada
com as mesmas 3 features do pipeline completo.

## Alternativas Consideradas

### Alternativa 1 — Rodar RF a cada slider

Carregar o modelo `model.pkl` (~87 MB) em JavaScript no navegador
via ONNX.js ou TensorFlow.js e recalcular a predição a cada
movimento de slider.

- **Prós:** fidelidade total ao modelo de produção
- **Contras:**
  - Impossível em `file://` (sem servidor) — modelo precisa ser
    baixado de um endpoint
  - 87 MB de download para o cliente
  - Inversão analítica (esforço por indicador) requer otimização
    numérica iterativa, não há fórmula fechada para RF
  - Complexidade técnica elevada para um dashboard estático
- **Custo-benefício:** rejeitado — ganho marginal de ~0,02 ROC-AUC
  versus custo operacional alto

### Alternativa 2 — Regressão Polinomial

Usar uma regressão logística com termos polinomiais e de interação
(quadráticos, produto entre features) para capturar não-linearidades
do RF de forma aproximada.

- **Prós:** maior fidelidade que a LR linear pura
- **Contras:**
  - Overfitting fácil com 3 features e 32K pontos
  - Interpretabilidade prejudicada (coeficientes não mais lineares)
  - Inversão analítica ainda possível mas mais complexa (solução
    de equação quadrática, raiz única pode não existir)
  - Ganho marginal sobre LR linear não justifica complexidade
- **Custo-benefício:** rejeitado — complexidade adicional sem
  ganho claro de usabilidade

### Alternativa 3 — Lookup Table

Pré-calcular uma tabela 3D com grades da probabilidade para todas
as combinações de valores dos 3 indicadores, e interpolar para
valores intermediários.

- **Prós:** execução instantânea, sem modelo no navegador
- **Contras:**
  - Grade de resolução útil exigiria milhões de combinações
    (ex: 270×15×60 ≈ 243.000 pontos, sem interpolação)
  - Inversão analítica impossível — lookup table não é invertível
  - Consulta individual por indicador requer scanning ou busca binária
- **Custo-benefício:** rejeitado — sem inversão analítica, o
  requisito central "esforço por indicador" não é atendido

### Alternativa 4 — API server com RF

Manter o RF completo e expor via API (FastAPI/Flask), com o
dashboard fazendo fetch para o servidor.

- **Prós:** fidelidade total ao modelo de produção
- **Contras:**
  - Impossível em `file://` (requer servidor rodando)
  - Complexidade operacional (deploy, keep-alive)
  - O dashboard deixa de ser auto-contido
- **Custo-benefício:** rejeitado — o requisito explícito é
  "sem servidor, abre via start index.html"

## Consequências

### Positivas

- **Interatividade total:** todos os cálculos ocorrem em tempo real
  no navegador, sem necessidade de servidor, modelo serializado, ou
  dependências externas
- **Inversão analítica fechada:** a fórmula da LR permite resolver
  algebraicamente para cada feature qual valor é necessário para
  atingir uma probabilidade-alvo — essencial para a seção "esforço
  por indicador"
- **Dashboard auto-contido:** HTML + CSS + JS inline, sem CDN,
  sem fetch, sem servidor
- **Tamanho mínimo:** nenhum download de modelo, página < 100 KB

### Negativas

- **Perda de ~0,02 ROC-AUC:** o proxy linear (LR 3-features) tem
  ROC-AUC ~0,946 vs ~0,953 do RF completo. Diferença pequena mas
  mensurável.
- **Apenas 3 features:** o proxy ignora as outras ~28 features
  (módulo do curso, demographics, etc.), que coletivamente somam
  ~60% da importância no RF. A simulação é aproximada, focada nos
  fatores acionáveis.
- **Relação linear no log-odds:** a LR assume que o log-odds da
  evasão é linear nas features normalizadas. A relação real pode
  ser não-linear (efeitos limiar, saturação).

### Mitigações

1. O dashboard exibe **disclaimer explícito** sobre a natureza
   aproximada do proxy linear
2. A tabela comparativa de modelos (seção 7) mostra a diferença
   de desempenho entre LR e RF, contextualizando a perda
3. O `model_proxy.json` referencia o `best_model: "Random Forest"`
   e `best_model_test_roc_auc: 0.9525` para manter a transparência
4. As métricas do header (acurácia 87,7%, recall 83,4%, ROC-AUC
   0,953) referem-se ao **RF completo**, não ao proxy — o usuário
   vê o modelo real nas métricas e o proxy nos sliders

## Status

Aceito.

## Data

2026-07-03

## Autor

dashboard-designer (LADESIGN)
