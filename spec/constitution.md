# Constitution — Abandono Acadêmico Casa Grande

**Version:** 1.0 | **Status:** Vigente

---

## Princípios

1. **Dados primeiro, modelo depois.** Sem profiling e DQ, não há modelo.
2. **Reprodutibilidade obrigatória.** Toda etapa do pipeline pode ser re-executada do zero e produz o mesmo resultado.
3. **Sem vazamento temporal.** Split treino/teste respeita ordem cronológica quando aplicável; nunca treinar no futuro.
4. **Guard para DataFrame vazio.** Nenhuma etapa do pipeline crasha com dados vazios — produz mensagem amigável.
5. **Parcimônia (PR-1).** Nível de rigor Level-A: se +10% qualidade por +20% tempo, adotar; se +1% por +50% tempo, rejeitar.

## Scope

Pipeline de previsao de abandono academico, utilizando o Open University Learning Analytics Dataset (OULAD) — 32.593 estudantes, 7 modulos, 22 apresentacoes (2013-2014). Dataset real publicado em Nature Scientific Data (Kuzilek et al., 2017, CC-BY 4.0). Pipeline cobre ingestao de 7 tabelas CSV, feature engineering (bronze/silver/gold), treinamento de modelo preditivo (Random Forest 87.5% accuracy, 93.7% recall), e dashboard interativo com simulacao.

## Non-goals

1. Nao e um sistema de producao com API REST — e um pipeline batch para analise e modelagem.
2. Nao substitui sistemas academicos existentes da universidade.
3. Nao cobre predicao em tempo real ou integracao com LMS ativos.
