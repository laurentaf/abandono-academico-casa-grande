# Design Source

**Artifact:** `artifacts/dashboard/index.html`
**Project:** Abandono Acadêmico Casa Grande
**Task:** Full PT-BR translation + "Decisões do Modelo" section + histogram label fix

## Changes applied

1. **PT-BR translation** — All English labels translated to Brazilian Portuguese:
   - Accuracy → Acurácia
   - Feature Importance → Importância das Variáveis
   - Model Summary → Resumo do Modelo
   - Interactive Simulation → Simulação Interativa
   - Data Distribution → Distribuição dos Dados
   - Conclusions → Conclusões
   - Slider labels, chart titles, tooltips, comments, footer text

2. **Histogram CRA labels** — Changed from "0, 2, 4, 6, 8, 10" to "0, 1, 2, 3, 4" (CRA scale is 0–4)

3. **New section: "Decisões do Modelo"** — 5 subsections covering:
   - Variáveis do Dataset (7-column table with keep/remove decisions)
   - Por que RandomForest vs Regressão Linear
   - Comparativo com Outros Modelos (3-model table)
   - Sensibilidade das Variáveis (visual bar indicators)
   - Por que foi necessário complicar (justification)

## Design direction

N/A — dashboard uses existing DESIGN.md from child repo.
