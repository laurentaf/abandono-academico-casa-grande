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

Pipeline de previsão de abandono acadêmico, consumindo dataset via API DataMission. 3 fases estruturadas + fase 4 opcional (dashboard + simulação).

## Non-goals

1. Não é um sistema de produção com API REST — é um pipeline batch para análise e modelagem.
2. Não substitui sistemas acadêmicos existentes da universidade.
