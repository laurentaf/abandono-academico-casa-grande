# Design Direction — Fase 4: Dashboard + Simulação

## Visão Geral

Dashboard interativo em HTML que apresenta as conclusões do modelo preditivo de abandono acadêmico da Universidade Casa Grande, com simulação interativa que permite ao usuário ajustar variáveis e observar impacto em tempo real na probabilidade de abandono.

## Princípios de Design

1. **Dados primeiro, ornamento segundo.** A hierarquia visual prioriza métricas, feature importance e a simulação. Animações e cores existem apenas para guiar a atenção, não para decorar.

2. **Interatividade como ferramenta de entendimento.** Sliders e controles não são brinquedos — cada variável ajustável revela uma relação causal com o target. O usuário deve sair sabendo mais sobre abandono acadêmico do que quando entrou.

3. **Responsividade sem perda de informação.** O dashboard funciona em desktop e mobile, mas a experiência mobile é uma adaptação inteligente, não uma remoção de conteúdo. Dados complexos merecem espaço; telas pequenas merecem foco.

## Paleta e Tipografia

- Fundo neutro (#1a1a2e ou similar escuro) para contraste com dados coloridos
- Cores de destaque: verde (#00d2ff) para métricas positivas, vermelho (#ff6b6b) para alertas de abandono
- Tipografia sans-serif legível (Inter, Segoe UI, ou sistema)
- Grid responsivo com cards para métricas e charts

## Elementos-Chave do Dashboard

1. **Resumo do Modelo** — Accuracy, F1-score, feature importance (barras horizontais)
2. **Distribuição dos Dados** — histogramas ou densidade das variáveis numéricas
3. **Simulação Interativa** — sliders para grade_point_average, attendance_rate, scholarship_percent com output visual (gauge ou indicador de risco)
4. **Conclusão** — texto explicativo com insights acionáveis
