# ADR-003: Reversão — Dataset sem Valor Preditivo

## Status
Accepted

## Context
Após análise estatística completa na Fase 4, descobrimos que o dataset da DataMission (1000 registros, 4 features) não contém sinal suficiente para prever abandono acadêmico. O modelo é estatisticamente pior que chutar a classe majoritária.

### Evidência

1. **Accuracy vs Dummy:** 66.5% < 75.1% (dummy sempre prediz "não-abandono")
2. **Cross-validation:** 62.9% ± 2.2% — instável e baixo
3. **Features não discriminam:** CRA p=0.59, Presença p=0.31, Curso p=0.14 — todas não-significativas
4. **Target SUSPENDED é problemático:** CRA de SUSPENDED (5.06) é MAIOR que ACTIVE (4.73)
5. **CRA bins Chi2 p=0.27:** taxa de abandono por faixa de CRA é aleatória
6. **CRA 3.5 vs 4.0:** Fisher p=0.79 — diferença é ruído

### Interpretação do usuário

O dataset parece representar:
- **ACTIVE** → cursando
- **SUSPENDED** → pausado (pode voltar)
- **DROPPED** → saiu definitivamente
- **GRADUATED** → formado

Mas as features (CRA, presença, bolsa) não conseguem distinguir esses estados.

## Decision

**Não publicar este modelo como solução preditiva.** Em vez disso:

1. Documentar os achados estatísticos (ADR-001 post-mortem)
2. Criar novo projeto com dataset **ShadowTraffic** (3-4 mil registros)
3. Incluir campo **tempo_SUSPENDED_antes_de_cancelar** (feature temporal)
4. Reavaliar com dados longitudinais

## Alternatives

### A) Publicar com ressalvas
Divulgar o dashboard "como baseline" com disclaimers. Risco: gestores confiariam em previsões aleatórias.

### B) Coletar dados reais
Parceria com universidade para dados longitudinais reais. Custo alto, demorado.

### C) Usar ShadowTraffic (escolhido)
Dataset sintético de maior qualidade com campos temporais. Rápido, replicável, sem dependência de parceiro.

## Consequences
+ Evita deploy de modelo inútil em produção
+ Transparência científica (publicar achados negativos é válido)
+ Novo projeto com dados melhores tem chance real de funcionar
- Projeto atual fica marcado como "sem valor preditivo"
- Requer novo ciclo de desenvolvimento (4 fases)
- ShadowTraffic pode ter vieses próprios (validar antes)

## Referências
- ADR-001: Classificador baseline (superseded por este)
- ADR-002: Model path e encoding (ainda válido para novo projeto)
- Análise estatística: Fase 4, 2026-06-09
