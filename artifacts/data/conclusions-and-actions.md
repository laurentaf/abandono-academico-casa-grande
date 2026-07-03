# Conclusões e Ações Concretas — Abandono Acadêmico (OULAD)

## 1. Conclusões Aprofundadas

### 1.1 Correlação vs Causalidade

**OULAD é um dataset observacional.** As features medidas — em especial
as de engajamento VLE (last_activity_day, total_clicks, assessment_count)
— são **PREDITIVAS, não CAUSAIS**. Isto significa:

- **last_activity_day baixo NÃO CAUSA evasão.** É um SINAL PRECOCE de
  que o estudante já está se desengajando. A causalidade reversa é
  plausível: o estudante que já decidiu evadir (ou está com
  dificuldades) simplesmente para de acessar o VLE.
- **Submissão de avaliações é um marcador comportamental.** Baixa taxa
  de submissão indica desengajamento, mas não diz se o estudante está
  com dificuldade no conteúdo, problemas pessoais, ou perdeu interesse.

**Implicação prática:** intervenções devem focar em REVERTER o
desengajamento, não em "corrigir" a feature. Um alerta baseado em
last_activity_day deve acionar uma ação de reconexão (contato do tutor,
nudge no VLE), não uma "correção" do dia de atividade.

### 1.2 Limites de Generalização

O modelo foi treinado e avaliado no OULAD, que tem as seguintes
características:

- **1 universidade** (Open University, UK)
- **Período:** 2013-2014 (duas coortes anuais)
- **Modalidade:** 100% educação a distância (EaD)
- **7 módulos** (disciplinas), 22 apresentações semestrais
- **32.593 estudantes** com dados demográficos do Reino Unido

**O que NÃO se pode assumir:**

- **Não generalizável para ensino presencial.** Estudantes presenciais
  têm padrões de engajamento fundamentalmente diferentes (frequência
  em aula, interação presencial, etc).
- **Não generalizável para outros países.** O sistema educacional,
  perfil socioeconômico e acesso à tecnologia diferem.
- **Não generalizável para outra década.** O comportamento VLE de 2013
  (pre-pandemia, acesso predominante por desktop) é diferente de 2026.
- **Taxa de evasão de 31,2%** é consistente com a literatura de EaD
  (open university context), mas não reflete universidades presenciais
  ou seletivas.

**Recomendação:** para aplicar este modelo em outra instituição, é
necessário recalibrar (retreinar) com dados locais. O pipeline pode
ser reexecutado com o DuckDB da nova instituição.

### 1.3 Features Acionáveis vs Não-Acionáveis

| Feature | Acionável? | O que fazer |
|---------|-----------|-------------|
| `last_activity_day` | ✅ Sim | Monitorar queda de atividade, acionar tutor |
| `assessment_count` | ✅ Sim | Oferecer suporte se baixo número de entregas |
| `submission_rate` | ✅ Sim | Nudge para manter consistência |
| `total_clicks` | ✅ Sim (parcial) | Indicador geral de engajamento |
| `click_trend` | ✅ Sim | Queda relativa de cliques ao longo do tempo |
| `num_tma`, `num_cma` | ✅ Sim | Identificar tipo de avaliação com baixa entrega |
| `gender` | ❌ Não | Apenas segmentação — não é alvo de intervenção |
| `region` | ❌ Não | Apenas segmentação — não é alvo de intervenção |
| `imd_band` | ❌ Não | Contexto socioeconômico — política institucional |
| `age_band` | ❌ Não | Perfil demográfico — não modificável |
| `disability` | ❌ Não | Acomodações necessárias, não intervenção preditiva |
| `highest_education` | ❌ Não | Histórico acadêmico prévio |

**Regra de ouro:** features de engajamento VLE (atividade recente,
frequência de acesso, entregas de avaliação) são ACIONÁVEIS por
intervenções institucionais. Features demográficas servem apenas para
segmentação e equity analysis.

### 1.4 Interpretação do Modelo

- **Top-3 features** (last_activity_day, submission_rate, assessment_count)
  explicam ~41% da importância total (variação entre modelos).
- **Feature dominante:** `last_activity_day` sozinha responde por ~28%
  da importância preditiva no XGBoost.
- **Módulo específico importa:** `code_module_GGG` e `code_module_CCC`
  aparecem no top-5 — módulos com maior taxa de evasão histórica.
- **O modelo depende fortemente de dados de engajamento VLE.** Sem
  dados de atividade (VLE), o modelo perde a maior parte do poder
  preditivo — as features demográficas isoladamente têm pouco sinal.

---

## 2. Ações Concretas

Cada ação abaixo tem gatilho, público-alvo, métrica de sucesso e
esforço estimado. As métricas de sucesso são baseadas na literatura
de learning analytics (Herodotou et al., 2023; Rienties et al., 2022).

### Ação 1 — Alerta de Queda de Atividade (Semana 3)

| Parâmetro | Valor |
|-----------|-------|
| **Gatilho** | `last_activity_day ≤ 21` dias (3 semanas sem atividade VLE) + `total_clicks < 500` |
| **Público** | Estudantes com essas características no momento da checagem |
| **Métrica de sucesso** | Reduzir evasão no grupo-alvo em 10pp vs baseline histórica do módulo |
| **Esforço** | Notificação automática no VLE (baixo) + contato do tutor (médio) |
| **Frequência** | Semanal, a partir da Semana 3 do módulo |
| **Canal** | E-mail + notificação no VLE + alerta no dashboard do tutor |
| **Threshold do modelo** | Probabilidade predita > 0.50 (regra de decisão padrão) |

**Por que funciona:** o feature mais importante do modelo é
last_activity_day. Intervenção precoce (Semana 3) permite ação antes
que o desengajamento se consolide. A literatura mostra que contato
proativo do tutor reduz evasão em 5-15pp em cursos EaD.

### Ação 2 — Mentoria para Baixa Submissão de Avaliações (meio do módulo)

| Parâmetro | Valor |
|-----------|-------|
| **Gatilho** | `assessment_count ≤ 2` até a metade do módulo |
| **Público** | Estudantes que entregaram ≤ 2 avaliações até o midpoint |
| **Métrica de sucesso** | Aumentar submission_rate no grupo em 15% vs grupo de controle (sem mentoria) |
| **Esforço** | Alocação de mentor dedicado, 1h/semana por estudante |
| **Frequência** | Única checagem no midpoint (avaliação do meio do módulo) |
| **Canal** | Sessões de mentoria individuais (vídeo ou presencial) |
| **Critério de desligamento** | Após 2 entregas consecutivas, estudante sai do programa |

**Por que funciona:** a literatura de EaD mostra que tutoria direcionada
a estudantes com baixa taxa de entrega tem efeito significativo. A
feature assessment_count é a segunda mais importante após a atividade
VLE.

### Ação 3 — Nudge para Submission Rate Consistente

| Parâmetro | Valor |
|-----------|-------|
| **Gatilho** | `submission_rate < 0.30` (menos de 30% das avaliações entregues até o momento) |
| **Público** | Todos os estudantes com baixa taxa de entrega |
| **Métrica de sucesso** | Aumentar submission_rate no grupo em 20% → estimativa de reduzir evasão em 5pp |
| **Esforço** | E-mail automatizado + lembrete no VLE (baixo) |
| **Frequência** | A cada nova avaliação disponibilizada |
| **Canal** | E-mail trigger + notificação push no VLE |
| **Conteúdo sugerido** | "Você está com X% de entregas. Estudos mostram que manter consistência aumenta suas chances de conclusão em Y%. Precisa de ajuda? Fale com seu tutor." |

**Por que funciona:** nudges comportamentais baseados em norma social
(comparação com pares) e feedback de progresso têm efeito comprovado
em contextos educacionais. O custo é baixo (automatizado) e o impacto
potencial é relevante mesmo que modesto.

---

## 3. O que NÃO se Pode Extrair dos Dados

### 3.1 Causalidade

O modelo preditivo não identifica **por que** um estudante parou de
acessar. As causas possíveis incluem:

- Dificuldade com o conteúdo
- Problemas pessoais/familiares
- Perda de interesse/motivação
- Incompatibilidade de horário
- Problemas técnicos (acesso à internet)
- Inscrição equivocada no curso

O modelo SÓ diz: "este estudante tem perfil similar a outros que
evadiram." A intervenção depende de diagnóstico humano (tutor).

### 3.2 Previsão Individual com Certeza

O melhor modelo (Random Forest) erra ~12,5% das previsões no test set.
Isto significa que, para cada 100 estudantes classificados como "risco
de evasão":

- ~78 são corretamente identificados (recall = 0,78 no threshold 0.50)
- ~22 são falsos positivos (identificados como risco mas não evadem)

E para cada 100 estudantes que efetivamente evadem:
- ~16 não são identificados (falsos negativos)

### 3.3 Diagnóstico de Intervenção

O modelo **não diz qual intervenção funciona** para cada estudante.
Para saber se a Ação 1, 2 ou 3 funciona, é necessário:

1. Implementar as ações
2. Medir o resultado (A/B testing ou quasi-experimental)
3. Comparar com grupo de controle

### 3.4 Transferência Direta para Outra Instituição

O modelo é calibrado para dados da Open University UK (2013-2014).
Para aplicar em outro contexto:

- **Mesma universidade, anos recentes:** precisa recalibrar com dados
  pós-2020 (comportamento mudou com pandemia)
- **Outra universidade EaD:** precisa retreinar com dados locais
- **Ensino presencial:** precisa novo modelo (features diferentes)

---

## 4. Resumo Executivo

1. **O modelo funciona.** Random Forest atinge 87,7% accuracy, 83,4%
   recall (evasão), ROC-AUC 0,9525. Supera dummy com p < 0,001.
2. **A feature mais importante é `last_activity_day`** (28% da
   importância) — estudantes que param de acessar o VLE por mais de
   3 semanas têm alto risco de evasão.
3. **Engajamento VLE é acionável.** Três ações concretas podem reduzir
   evasão: alerta precoce (Semana 3), mentoria no meio do módulo, e
   nudges de consistência.
4. **Limitações:** modelo observacional (não causal), específico para
   EaD UK 2013-2014, erro de ~12,5%.
5. **Próximo passo:** implementar as ações em ambiente controlado,
   medir impacto, recalibrar se necessário.

---

*Documento gerado em 2026-07-03. Baseado no pipeline OULAD com 6 modelos
comparados. Para detalhes técnicos, ver `artifacts/data/model.md` e
`spec/adr/003-model-selection-comparative.md`.*
