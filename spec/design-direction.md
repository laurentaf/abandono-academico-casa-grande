# Design Direction — Dashboard + Simulacao (OULAD)

## Visao Geral

Dashboard interativo em HTML que apresenta as conclusoes do modelo preditivo de abandono academico (OULAD), com simulacao interativa que permite ao usuario ajustar variaveis e observar impacto em tempo real na probabilidade de abandono.

## Principios de Design

1. **Dados primeiro, ornamento segundo.** A hierarquia visual prioriza metricas, feature importance e a simulacao. Animacoes e cores existem apenas para guiar a atencao, nao para decorar.

2. **Interatividade como ferramenta de entendimento.** Sliders e controles nao sao brinquedos — cada variavel ajustavel revela uma relacao causal com o target. O usuario deve sair sabendo mais sobre abandono academico do que quando entrou.

3. **Responsividade sem perda de informacao.** O dashboard funciona em desktop e mobile, mas a experiencia mobile e uma adaptacao inteligente, nao uma remocao de conteudo.

## Paleta e Tipografia

- Fundo neutro (#1a1a2e ou similar escuro) para contraste com dados coloridos
- Cores de destaque: verde (#6bcb77) para metricas positivas, vermelho (#ff6b6b) para alertas de abandono, azul (#00d2ff) para acentos
- Tipografia sans-serif legivel (Segoe UI, Inter, ou sistema)
- Grid responsivo com cards para metricas e charts

## Elementos-Chave do Dashboard

1. **Resumo do Modelo** — Accuracy (87.5%), Recall dropout (93.7%), ROC-AUC (0.954) em cards
2. **Importancia das Variaveis** — Barras horizontais com top 15 features (last_activity_day, assessment_count, submission_rate, etc.)
3. **Distribuicao do Target** — Proporcao dropout vs nao-dropout (31.2% vs 68.8%)
4. **Simulacao Interativa** — Sliders para variaveis-chave (last_activity_day, assessment_count, avg_assessment_score, total_clicks, days_active) com output de probabilidade de abandono
5. **Conclusao** — Texto explicativo com insights acionaveis (intervencao precoce em estudantes com queda de atividade VLE)

## Variaveis do Modelo OULAD

Top 5 features por importancia:
- last_activity_day (20.2%) — dia da ultima interacao com VLE
- assessment_count (12.4%) — total de avaliacoes submetidas
- submission_rate (8.8%) — taxa de submissao ao longo do modulo
- num_tma (7.8%) — Tutor-Marked Assessments completados
- avg_assessment_score (4.6%) — nota media nas avaliacoes
