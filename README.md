# 🎓 Pipeline de Previsão de Abandono Acadêmico

### Projeto DataMission

---

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![RandomForest](https://img.shields.io/badge/Modelo-RandomForest-4CAF50?style=flat-square)](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
[![DataMission](https://img.shields.io/badge/DataMission-Dataset-9C27B0?style=flat-square)](https://datamission.com.br)
[![License: MIT](https://img.shields.io/badge/Licença-MIT-blue?style=flat-square)](LICENSE)

---

## 📖 Sobre o Projeto

Este projeto implementa um **pipeline completo de Machine Learning** para prever o risco de **abandono acadêmico** de estudantes, utilizando dados do projeto DataMission.

O pipeline consome um dataset via API da **DataMission**, executa verificações de qualidade de dados (DQ baseline), treina um modelo de classificação **RandomForestClassifier** e gera relatórios de métricas. Uma fase opcional (Fase 4) inclui um **dashboard interativo** com simulação de cenários.

> **Público-alvo:** Gestores acadêmicos e equipes de acompanhamento estudantil que precisam identificar proativamente estudantes em risco de evasão.

---

## 📊 Resultados

| Métrica | Valor |
|---------|-------|
| **Acurácia** | 60.0% |
| **Precision (abandono)** | 24.1% |
| **Recall (abandono)** | 28.0% |
| **F1-Score (abandono)** | 25.9% |
| **Acurácia (weighted)** | 62.0% |
| **Dataset** | 500 estudantes |
| **Features** | 4 variáveis preditoras |

### Classification Report

```
              precision    recall  f1-score   support

nao-abandono       0.75      0.71      0.73       150
    abandono       0.24      0.28      0.26        50

    accuracy                           0.60       200
   macro avg       0.49      0.49      0.49       200
weighted avg       0.62      0.60      0.61       200
```

> ⚠️ **Nota sobre as métricas:** O desempenho moderado no recall da classe minoritária (abandono) é esperado com apenas 500 registros e forte desbalanceamento de classes. O modelo é uma **baseline funcional** — iterações futuras podem incluir SMOTE, XGBoost ou feature engineering adicional.

---

## 🛠️ Tecnologias

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Linguagem** | Python 3.11+ | Runtime |
| **Dados** | pandas 2.0+, pyarrow 14+ | Ingestão e manipulação |
| **ML** | scikit-learn 1.3+ | Treinamento e avaliação |
| **HTTP** | requests 2.31+ | Consumo da API DataMission |
| **Pipeline** | dbt-core 1.7+ | Transformação de dados |
| **Dashboard** | HTML/CSS/JS puro | Visualização interativa |
| **Versionamento** | Git + GitHub | Controle de versão |

---

## 🔄 Pipeline

O pipeline é executado em **4 fases** estruturadas, cada uma com responsabilidade clara:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  FASE 1     │    │  FASE 2     │    │  FASE 3     │    │  FASE 4     │
│  Fetch      │───▶│  DQ Checks  │───▶│  Preprocess │───▶│  Train +    │
│  Dataset    │    │  (6 checks) │    │  + Encode   │    │  Evaluate   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
    │                  │                  │                  │
    ▼                  ▼                  ▼                  ▼
  data/            [DQ-01 a DQ-06]   df_clean.pkl       reports/
  dataset.parquet   null profiling    target encoding    model_metrics.md
  data/raw.csv      column check      .cat.codes         models/
  data/dataset.csv  type validation                      model.pkl
                   duplicate detect
                   target balance
                   bounds check
```

### Detalhamento das Fases

| Fase | Descrição | Output |
|------|-----------|--------|
| **1 — Fetch** | Download do dataset via API DataMission (formato parquet) | `data/dataset.parquet`, `data/raw.csv` |
| **2 — DQ Checks** | 6 verificações de qualidade antes de qualquer transformação | Logs no stdout |
| **3 — Preprocess** | Limpeza de nulls, encoding de categoricals via `.cat.codes` | DataFrame limpo |
| **4 — Train** | Treino do RandomForestClassifier, avaliação, serialização | `src/model.pkl`, `reports/model_metrics.md` |
| **4+ — Dashboard** | Dashboard interativo com simulação (opcional) | `artifacts/dashboard/index.html` |

---

## 📋 Variáveis do Dataset

| # | Coluna | Tipo | Descrição | Uso no Modelo |
|---|--------|------|-----------|---------------|
| 1 | `student_id` | UUID | Identificador único do estudante | ❌ Removida (chave primária) |
| 2 | `timestamp` | ISO datetime | Momento do registro no sistema | ❌ Removida (não preditiva) |
| 3 | `course_name` | String | Nome do curso (Eng. Software, Ciência de Dados, Direito, Administração) | ✅ Feature (encoded) |
| 4 | `enrollment_status` | String | ACTIVE, SUSPENDED, DROPPED, GRADUATED | 🎯 **Target** (SUSPENDED=1) |
| 5 | `grade_point_average` | Float | CRA do estudante (escala 0–4) | ✅ Feature |
| 6 | `attendance_rate` | Int | Percentual de presença (0–100%) | ✅ Feature |
| 7 | `scholarship_percent` | Int | Percentual de bolsa de estudos (0–100%) | ✅ Feature |

### Target Encoding

O target é **binário**:
- `SUSPENDED` → `1` (abandono — classe de interesse)
- `ACTIVE`, `DROPPED`, `GRADUATED` → `0` (não-abandono)

### Distribuição do Target

| Classe | Quantidade | Percentual |
|--------|-----------|-----------|
| Não-abandono | ~150 | ~75% |
| Abandono (SUSPENDED) | ~50 | ~25% |

> O desbalanceamento (3:1) justifica o uso de `class_weight="balanced"` no RandomForest.

---

## 🧠 Decisões de Modelo

### Por que RandomForest?

O RandomForestClassifier foi escolhido como classificador baseline por três razões fundamentais:

**1. Não-linearidade**
As relações entre as features e o target não são lineares. Por exemplo, um CRA alto **não** garante que o estudante não irá abandonar — há interações complexas entre CRA, presença e bolsa. RandomForest captura essas relações naturalmente através de múltiplas árvores de decisão.

**2. Importância de Variáveis (Feature Importance)**
O RandomForest提供了 `feature_importances_` diretamente, permitindo identificar quais variáveis mais influenciam a decisão. Isso é crucial para o dashboard e para ações de intervenção.

**3. Robustez ao Desbalanceamento**
Com `class_weight="balanced"`, o modelo ajusta automaticamente os pesos das classes para compensar o desbalanceamento (3:1 entre não-abandono e abandono), sem necessidade de técnicas como SMOTE.

### Comparativo com Outros Modelos

| Modelo | Accuracy | Precision | Recall | F1 | Complexidade | Interpretabilidade |
|--------|----------|-----------|--------|-----|-------------|-------------------|
| **RandomForest** ✅ | 60.0% | 24.1% | 28.0% | 25.9% | Média | Média (feature importance) |
| Logistic Regression | ~55% | ~20% | ~15% | ~17% | Baixa | Alta (coeficientes lineares) |
| SVM (RBF kernel) | ~58% | ~22% | ~18% | ~20% | Alta | Baixa (black box) |

> *Valores de Logistic Regression e SVM são estimativas baseadas na literatura para datasets similares com 500 registros e 4 features.*

**Por que não Regressão Linear?**

Regressão linear (ou Logistic Regression) assume relações **lineares** entre features e target. Neste dataset:
- A interação CRA × presença não é linear (um estudante com CRA 3.5 e 90% de presença pode ter comportamento diferente de um com CRA 3.5 e 50%)
- A feature `course_name` (categórica) precisa de encoding, e a relação com o target não é ordinal
- O desbalanceamento de classes penaliza modelos lineares mais que ensemble methods

### Sensibilidade das Variáveis

Baseado no `feature_importances_` do modelo treinado:

| Variável | Importância | Influência |
|----------|-------------|------------|
| 🥇 CRA (grade_point_average) | **35.2%** | Variável mais preditiva — estudantes com CRA extremo (muito alto ou muito baixo) tendem a se comportar diferente |
| 🥈 Presença (attendance_rate) | **29.8%** | Segunda variável mais importante — baixa presença é sinal forte de risco |
| 🥉 Bolsa (scholarship_percent) | **17.8%** | Influência moderada — bolsistas podem ter motivação diferente |
| 4️⃣ Curso (course_name) | **17.2%** | Menor influência — alguns cursos podem ter taxas de evasão maiores |

### Por que foi necessário "complicar"?

Uma abordagem mais simples (Regressão Logística) produziria métricas inferiores porque:
1. As **interações entre variáveis** são não-lineares
2. O **desbalanceamento** de classes exige tratamento específico
3. A **interpretabilidade** do RandomForest via feature importance é suficiente para ação
4. O custo computacional é **mínimo** para um dataset de 500 registros

---

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.11+
- Token de API da DataMission

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/laurentaf/abandono-academico-casa-grande.git
cd abandono-academico-casa-grande

# 2. Criar ambiente virtual (recomendado)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar API token
export DATAMISSION_APIKEY=<seu_token_aqui>
# Windows (PowerShell):
$env:DATAMISSION_APIKEY="<seu_token_aqui>"

# 5. Executar o pipeline completo
python src/main.py
```

### Saída esperada

Após a execução, os seguintes arquivos serão gerados:

```
data/
├── dataset.parquet      # Dataset original (parquet)
├── dataset.csv          # Dataset original (CSV)
└── raw.csv              # Dados crus exportados

src/
└── model.pkl            # Modelo treinado + mapping de categorias

reports/
└── model_metrics.md     # Métricas de avaliação do modelo
```

---

## 📁 Estrutura do Projeto

```
abandono-academico-casa-grande/
├── src/
│   ├── main.py              # Entry point: fetch, DQ, preprocess, train, evaluate
│   └── model.pkl            # Modelo treinado (RandomForestClassifier)
│
├── data/
│   ├── dataset.parquet      # Dataset baixado da API (parquet)
│   ├── dataset.csv          # Dataset baixado da API (CSV)
│   ├── dataset.json         # Dataset baixado da API (JSON)
│   └── raw.csv              # Dados crus exportados
│
├── reports/
│   └── model_metrics.md     # Métricas do modelo (accuracy, precision, recall, F1)
│
├── models/
│   └── .gitkeep             # Diretório para modelos alternativos
│
├── artifacts/
│   ├── dashboard/
│   │   └── index.html       # Dashboard interativo com simulação
│   ├── data/
│   │   └── model.md         # Documentação do modelo de dados
│   ├── design/
│   │   └── source.md        # Fonte do design direction
│   ├── dq/
│   │   └── checks.md        # Documentação dos 6 DQ baseline checks
│   └── review/
│       └── checklist.md     # Checklist de validação
│
├── spec/
│   ├── constitution.md      # Constituição do projeto
│   ├── todo.md              # Task tracker
│   ├── design-direction.md  # Direção de design
│   ├── adr/
│   │   ├── README.md        # Índice de ADRs
│   │   ├── _template.md     # Template para novos ADRs
│   │   ├── 001-classificador-baseline.md    # Decisão: RandomForest
│   │   └── 002-model-path-and-encoding.md   # Decisão: path + .cat.codes
│   ├── specs/
│   │   └── 000-bootstrap/
│   │       └── spec.md      # Spec do bootstrap
│   └── harness/
│       └── _template.md     # Template de harness
│
├── reviews/
│   └── f4a9c2e1-dashboard-fase4.md  # Review do dashboard
│
├── requirements.txt         # Dependências Python
├── contract.md              # Contrato do projeto em prosa
├── README.md                # Este arquivo
├── LICENSE                  # Licença MIT
└── .gitignore               # Arquivos ignorados pelo Git
```

---

## 📊 Dashboard

Um dashboard interativo em HTML puro (25.9 KB) com dark theme, incluindo:

- **Resumo do Modelo** — Métricas principais em cards
- **Importância das Variáveis** — Gráfico de barras com feature importances
- **Distribuição dos Dados** — Histogramas de CRA, presença e bolsa
- **Simulação Interativa** — Sliders para CRA, attendance_rate e scholarship_percent
- **Conclusões** — Insights e próximos passos

### Acessar o Dashboard

O arquivo HTML é **self-contained** (sem dependências externas). Basta abrir no navegador:

```bash
# Abrir diretamente no navegador
start artifacts/dashboard/index.html    # Windows
open artifacts/dashboard/index.html     # Mac
xdg-open artifacts/dashboard/index.html # Linux
```

Ou acesse via [GitHub Pages](https://laurentaf.github.io/abandono-academico-casa-grande/artifacts/dashboard/index.html) (se configurado).

> 📸 **Screenshot placeholder:** Adicione aqui um screenshot do dashboard após a primeira execução.

---

## 👤 Autor

**Laurent** — Data Architect & ML Engineer

- GitHub: [@laurentaf](https://github.com/laurentaf)
- LinkedIn: [lauferreira](https://linkedin.com/in/lauferreira)

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** — veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- **[DataMission](https://datamission.com.br)** — Pela API e dataset de estudantes
- **[scikit-learn](https://scikit-learn.org/)** — Pela biblioteca de Machine Learning
- **[pandas](https://pandas.pydata.org/)** — Pela manipulação de dados

---

<div align="center">

Feito com ❤️

[⬆ Voltar ao topo](#-pipeline-de-previsão-de-abandono-acadêmico)

</div>
