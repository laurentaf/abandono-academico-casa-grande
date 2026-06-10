# Design Source

**Artifact:** `artifacts/dashboard/index.html`
**Project:** Abandono Academico Casa Grande (OULAD)
**Task:** Dashboard interativo com simulacao de risco de abandono

## Dataset

OULAD — Open University Learning Analytics Dataset (Kuzilek et al., 2017, Nature Scientific Data, CC-BY 4.0).
32.593 estudantes, 7 modulos, 22 apresentacoes (semestres 2013B-2014J).
Target binarizado: Withdrawn=1 (dropout), Pass/Fail/Distinction=0 (31.2% classe positiva).

## Features do Modelo (top 5)

| Feature | Importancia | Escala |
|---------|------------|--------|
| last_activity_day | 20.2% | 0–270 (dias) |
| assessment_count | 12.4% | 0–15 (contagem) |
| submission_rate | 8.8% | 0.0–1.0 (proporcao) |
| num_tma | 7.8% | 0–6 (contagem TMA) |
| avg_assessment_score | 4.6% | 0–100 (pontos) |

## Metricas do Modelo

- Accuracy: 87.5%
- Recall (dropout): 93.7%
- ROC-AUC: 0.954

## Decisoes de Design

1. **Dark theme (#1a1a2e)** — fundo neutro para contraste com dados coloridos
2. **Cards de metricas** — 3 KPIs principais (accuracy, recall, AUC) em destaque
3. **Barras horizontais** — feature importance top 15, ordenadas por importancia
4. **Simulacao com sliders** — 5 variaveis-chave ajustadas pelo usuario, output = probabilidade de abandono
5. **Gauge de risco** — visual semicircular (verde/amarelo/vermelho) para probabilidade

## Design direction

N/A — dashboard uses existing DESIGN.md from child repo.
