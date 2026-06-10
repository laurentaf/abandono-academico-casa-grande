# Pipeline de Previsao de Abandono Academico — OULAD

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![RandomForest](https://img.shields.io/badge/Modelo-RandomForest-4CAF50?style=flat-square)](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
[![OULAD](https://img.shields.io/badge/Dataset-OULAD-9C27B0?style=flat-square)](https://analyse.kmi.open.ac.uk/open_dataset)
[![License: MIT](https://img.shields.io/badge/Licenca-MIT-blue?style=flat-square)](LICENSE)

---

## O que e

Pipeline completo de Machine Learning para prever o risco de **abandono academico** de estudantes universitarios, utilizando o **Open University Learning Analytics Dataset (OULAD)** — dataset real publicado em *Nature Scientific Data* (Kuzilek et al., 2017, CC-BY 4.0).

O pipeline cobre: ingestao de 7 tabelas OULAD (bronze), agregacoes (silver), feature engineering (gold), treinamento de modelo preditivo com validacao estatistica, e dashboard interativo com simulacao.

> **Publico-alvo:** Gestores academicos e equipes de acompanhamento estudantil que precisam identificar proativamente estudantes em risco de evasao.

---

## Resultados

| Metrica | Random Forest | Logistic Regression | Dummy (stratified) |
|---------|:----------:|:-----------------:|:------------------:|
| **Accuracy** | **87.5%** | 87.0% | 56.6% |
| **Precision (dropout)** | 73.5% | 73.5% | — |
| **Recall (dropout)** | **93.7%** | 90.8% | — |
| **F1 (dropout)** | **82.4%** | 81.3% | — |
| **ROC-AUC** | **0.954** | 0.946 | 0.497 |

> **Destaque:** 93.7% de recall na classe dropout significa que o modelo identifica **19 em cada 20** estudantes que realmente abandonam. O Random Forest supera o Dummy por +30.9pp de acuracia (p=0.001, permutation test). Diferenca RF vs LR nao e estatisticamente significativa (p=0.084, paired t-test), mas RF tem recall 2.9pp superior.

### Top 5 Features (Random Forest)

| Rank | Feature | Importancia | Interpretacao |
|------|---------|------------|---------------|
| 1 | `last_activity_day` | 20.2% | Quanto mais cedo o estudante para de interagir com o VLE, maior o risco |
| 2 | `assessment_count` | 12.4% | Menos avaliacoes submetidas = maior risco |
| 3 | `submission_rate` | 8.8% | Taxa de submissao ao longo do modulo |
| 4 | `num_tma` | 7.8% | Tutor-Marked Assessments completados |
| 5 | `avg_assessment_score` | 4.6% | Nota media nas avaliacoes |

---

## Como Rodar

### Pre-requisitos

- Python 3.11+
- OULAD dataset (7 CSVs) em `data/oulad/`

### Passo a passo

```bash
# 1. Clonar o repositorio
git clone https://github.com/laurentaf/abandono-academico-casa-grande.git
cd abandono-academico-casa-grande

# 2. Criar ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Baixar OULAD dataset
# Obtenha os 7 CSVs de https://analyse.kmi.open.ac.uk/open_dataset
# Coloque em data/oulad/ (studentInfo.csv, studentVle.csv, etc.)

# 5. Executar o pipeline
python src/main.py
```

### Saida esperada

```
=== DQ Baseline Checks ===
DQ-01 Null profiling: PASS
DQ-02 Column existence: PASS
DQ-03 Type validation: PASS
DQ-04 Duplicate detection: PASS
DQ-05 Target balance: PASS (31.2% dropout)
DQ-06 Range/bounds: PASS

=== Model Evaluation (Test Set) ===
Accuracy:  0.875
Precision: 0.735
Recall:    0.937
F1:        0.824
ROC-AUC:   0.954
```

---

## Onde esta o que

| Diretorio | Conteudo |
|-----------|----------|
| `src/` | `main.py` (pipeline E2E) + `model.pkl` (modelo treinado) |
| `data/oulad/` | 7 CSVs do OULAD (studentInfo, studentVle, etc.) |
| `artifacts/data/` | `model.md` (schema + ML results) + `oulad.duckdb` (DuckDB com 12 tabelas) + `etl_oulad.sql` (SQL reprodutivel) |
| `artifacts/dq/` | `checks.md` (6 DQ baseline checks documentados) |
| `artifacts/dashboard/` | `index.html` (dashboard interativo, self-contained) |
| `artifacts/design/` | `source.md` (design direction reference) |
| `artifacts/review/` | `checklist.md` (validacao de entrega) |
| `spec/adr/` | ADR-001 (RandomForest baseline) + ADR-002 (model path + .cat.codes) |
| `spec/` | `constitution.md`, `todo.md`, `specs/`, `harness/` |

---

## Dataset: OULAD

O **Open University Learning Analytics Dataset** contem dados de 32.593 estudantes em 7 modulos e 22 apresentacoes (2013-2014) da Open University (UK).

| Tabela | Registros | Descricao |
|--------|-----------|-----------|
| `studentInfo` | 32.593 | Demografia + resultado final |
| `studentVle` | 10.655.280 | Interacoes diarias com o VLE (clicks) |
| `studentAssessment` | 173.912 | Notas e datas de submissao |
| `studentRegistration` | 32.593 | Datas de registro/desistencia |
| `assessments` | 206 | Metadados das avaliacoes |
| `courses` | 22 | Modulos e apresentacoes |
| `vle` | 6.364 | Recursos do Virtual Learning Environment |

### Target Encoding

- `Withdrawn` → **1** (abandono)
- `Pass`, `Fail`, `Distinction` → **0** (nao-abandono)

Distribuicao: **31.2% abandono** vs 68.8% nao-abandono.

### Feature Engineering (7 features derivadas)

| Feature | Formula | Papel |
|---------|---------|-------|
| `engagement_intensity` | total_clicks / module_length | Engajamento por dia de modulo |
| `activity_coverage` | days_active / module_length | Fracao do modulo com atividade |
| `has_vle_activity` | total_clicks > 0 | Uso do VLE (binario) |
| `assessment_count` | num_tma + num_cma + num_exams | Total de avaliacoes submetidas |
| `submission_rate` | assessment_count / module_length | Consistencia de submissao |
| `late_submission_flag` | avg_submission_delta > 0 | Submissoes atrasadas em media |
| `registration_earliness` | date_registration | Proxy de planejamento |

---

## Tecnologias

| Camada | Tecnologia | Funcao |
|--------|-----------|--------|
| **Linguagem** | Python 3.11+ | Runtime |
| **Dados** | pandas, DuckDB | Ingestao, agregacao, SQL analitico |
| **ML** | scikit-learn 1.3+ | Treinamento e avaliacao |
| **Dashboard** | HTML/CSS/JS puro | Visualizacao interativa (self-contained) |
| **Versionamento** | Git + GitHub | Controle de versao |

---

## Dashboard

Dashboard interativo (HTML self-contained, dark theme) com:

- **Resumo do Modelo** — Metricas principais em cards (accuracy, recall, ROC-AUC)
- **Importancia das Variaveis** — Grafico de barras com top 15 feature importances
- **Distribuicao do Target** — Proporcao dropout vs nao-dropout
- **Simulacao Interativa** — Sliders para ajustar variaveis e ver impacto na probabilidade de abandono
- **Conclusoes** — Insights acionaveis e proximos passos

### Acessar

```bash
start artifacts/dashboard/index.html   # Windows
open artifacts/dashboard/index.html    # Mac
xdg-open artifacts/dashboard/index.html # Linux
```

---

## Decisoes Tecnicas (ADRs)

- **ADR-001:** RandomForest como classificador baseline — captura nao-linearidades, fornece feature importance, robusto ao desbalanceamento com `class_weight="balanced"`.
- **ADR-002:** Modelo salvo em `src/model.pkl` (nao `models/`) + encoding de categoricas via pandas `.cat.codes` (nao sklearn LabelEncoder).

---

## Autor

**Laurent** — Data Architect & ML Engineer

- GitHub: [@laurentaf](https://github.com/laurentaf)
- LinkedIn: [lauferreira](https://linkedin.com/in/lauferreira)

---

## Licenca

Este projeto esta licenciado sob a **Licenca MIT** — veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Agradecimentos

- **Kuzilek et al.** — Pelo OULAD dataset (Nature Sci. Data 4:170171, 2017, CC-BY 4.0)
- **[scikit-learn](https://scikit-learn.org/)** — Pela biblioteca de Machine Learning
- **[pandas](https://pandas.pydata.org/)** — Pela manipulacao de dados
