"""Construir proxy com indicadores humanizados + percentis."""
import duckdb, json, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.special import expit
from sklearn.metrics import roc_auc_score

con = duckdb.connect('E:/projects/abandono-academico-casa-grande/artifacts/data/oulad.duckdb', read_only=True)
df = con.execute("""
    SELECT 
        module_presentation_length,
        last_activity_day,
        avg_submission_delta,
        avg_assessment_score,
        is_dropout
    FROM gold_oulad_features
    WHERE last_activity_day >= 0 AND last_activity_day <= 300
""").fetchdf()
con.close()

# --- Feature engineering ---
df['dias_sem_atividade'] = df['module_presentation_length'] - df['last_activity_day']
df['dias_sem_atividade'] = df['dias_sem_atividade'].clip(0, 270)

# avg_submission_delta: trata NaN
df['avg_submission_delta'] = df['avg_submission_delta'].fillna(0)

# avg_assessment_score: trata NaN
df['avg_assessment_score'] = df['avg_assessment_score'].fillna(df['avg_assessment_score'].median())

# Modelo 1: dias_sem_atividade + avg_submission_delta
feats_2 = ['dias_sem_atividade', 'avg_submission_delta']
X2 = df[feats_2].values
y = df['is_dropout'].values
scaler2 = StandardScaler()
X2s = scaler2.fit_transform(X2)
lr2 = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
lr2.fit(X2s, y)
roc2 = roc_auc_score(y, lr2.predict_proba(X2s)[:, 1])
print(f'Model dias_sem+delta: ROC-AUC={roc2:.4f}')
for i, f in enumerate(feats_2):
    print(f'  {f}: {lr2.coef_[0][i]:.4f} (neg={lr2.coef_[0][i] < 0})')

# Modelo 2: avg_assessment_score univariado
scaler_aas = StandardScaler()
aas_scaled = scaler_aas.fit_transform(df[['avg_assessment_score']].values)
lr_aas = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
lr_aas.fit(aas_scaled, y)
print(f'\nModel aas alone: coeff={lr_aas.coef_[0][0]:.4f}, intercept={lr_aas.intercept_[0]:.4f}')
print(f'  ROC-AUC={roc_auc_score(y, lr_aas.predict_proba(aas_scaled)[:,1]):.4f}')
print(f'  Negative? {lr_aas.coef_[0][0] < 0}')

# Hibrido: usa lr2 + lr_aas
from scipy.special import expit
log_odds = float(lr2.intercept_[0]) + X2s @ lr2.coef_[0] + float(lr_aas.coef_[0][0]) * aas_scaled.flatten()
p_hibrido = expit(log_odds)
roc_hib = roc_auc_score(y, p_hibrido)
print(f'ROC-AUC hibrido: {roc_hib:.4f}')

# --- Percentile lookup tables ---
def pct_le(col, values):
    return {str(v): round(float((df[col] <= v).mean()), 4) for v in values}

def pct_ge(col, values):
    return {str(v): round(float((df[col] >= v).mean()), 4) for v in values}

pct_dias_sem_atividade = pct_le('dias_sem_atividade', [0, 7, 15, 30, 60, 90, 120, 180, 270])
pct_submission_delta = pct_le('avg_submission_delta', [-30, -15, -7, 0, 7, 15, 30, 60])
pct_nota = pct_ge('avg_assessment_score', [10, 20, 30, 40, 50, 60, 70, 80, 90])

# --- Summary stats ---
def describe(col):
    vals = df[col]
    return {
        'min': round(float(vals.min()), 1),
        'max': round(float(vals.max()), 1),
        'mean': round(float(vals.mean()), 1),
        'median': round(float(vals.median()), 1),
        'std': round(float(vals.std()), 1),
        'p10': round(float(vals.quantile(0.10)), 1),
        'p25': round(float(vals.quantile(0.25)), 1),
        'p75': round(float(vals.quantile(0.75)), 1),
        'p90': round(float(vals.quantile(0.90)), 1),
        'dropout_mean': round(float(df[df.is_dropout==1][col].mean()), 1),
        'retention_mean': round(float(df[df.is_dropout==0][col].mean()), 1),
    }

coef_aas = float(lr_aas.coef_[0][0])
features = ['dias_sem_atividade', 'avg_submission_delta', 'avg_assessment_score']

proxy = {
    'model': 'LogisticRegression (hibrido humanizado)',
    'features': features,
    'feature_labels': {
        'dias_sem_atividade': 'Dias sem acessar o ambiente virtual',
        'avg_submission_delta': 'Dias de atraso medio na entrega de avaliacoes',
        'avg_assessment_score': 'Nota media nas avaliacoes'
    },
    'feature_descriptions': {
        'dias_sem_atividade': 'Quantos dias o aluno ficou sem acessar o VLE ate o final do modulo. Quanto MAIOR, maior o risco.',
        'avg_submission_delta': 'Media de dias de atraso (positivo) ou adiantamento (negativo) na entrega de avaliacoes. Quanto MAIOR, maior o risco.',
        'avg_assessment_score': 'Nota media em todas as avaliacoes (0-100). Quanto MENOR, maior o risco.'
    },
    'feature_units': {
        'dias_sem_atividade': 'dias',
        'avg_submission_delta': 'dias',
        'avg_assessment_score': 'pontos (0-100)'
    },
    'feature_defaults': {
        'dias_sem_atividade': float(df['dias_sem_atividade'].median()),
        'avg_submission_delta': 0.0,
        'avg_assessment_score': float(df['avg_assessment_score'].median())
    },
    'feature_insights': {
        'dias_sem_atividade': 'Alunos que evadem ficam em media 136 dias sem acessar o VLE. Alunos que concluem ficam 43 dias.',
        'avg_submission_delta': '63,8% dos alunos entregam no prazo (delta <= 0). Atraso medio de quem evade: 2 dias vs 1 dia de quem conclui.',
        'avg_assessment_score': 'Nota media de quem evade: 46 pts vs 72 pts de quem conclui — diferenca de 26 pontos.'
    },
    'coefficients': {
        'intercept': float(lr2.intercept_[0]),
        'dias_sem_atividade': float(lr2.coef_[0][0]),
        'avg_submission_delta': float(lr2.coef_[0][1]),
        'avg_assessment_score': coef_aas
    },
    'feature_ranges': {
        'dias_sem_atividade': {'min': 0, 'max': 270, 'mean': round(float(df.dias_sem_atividade.mean()), 2), 'std': round(float(df.dias_sem_atividade.std()), 2)},
        'avg_submission_delta': {'min': -30, 'max': 30, 'mean': round(float(df.avg_submission_delta.mean()), 2), 'std': round(float(df.avg_submission_delta.std()), 2)},
        'avg_assessment_score': {'min': 0, 'max': 100, 'mean': round(float(df.avg_assessment_score.mean()), 2), 'std': round(float(df.avg_assessment_score.std()), 2)}
    },
    'scaler_mean': [round(float(m), 4) for m in scaler2.mean_],
    'scaler_std': [round(float(s), 4) for s in scaler2.scale_],
    'scaler_aas_mean': round(float(scaler_aas.mean_[0]), 4),
    'scaler_aas_std': round(float(scaler_aas.scale_[0]), 4),
    'percentiles': {
        'dias_sem_atividade': pct_dias_sem_atividade,
        'avg_submission_delta': pct_submission_delta,
        'avg_assessment_score': pct_nota
    },
    'descriptive_stats': {
        'dias_sem_atividade': describe('dias_sem_atividade'),
        'avg_submission_delta': describe('avg_submission_delta'),
        'avg_assessment_score': describe('avg_assessment_score')
    },
    'baseline_dropout_rate': round(float(y.mean()), 4),
    'default_meta_dropout': 0.20,
    'meta_bounds': [0.05, 0.50],
    'best_model': 'Random Forest',
    'best_model_test_roc_auc': 0.9525,
    'proxy_roc_auc': round(roc_hib, 4),
    'note': 'Proxy hibrido humanizado: dias_sem_atividade+delta (LR) + nota (LR univariado). Sub-indices com percentis reais do OULAD.'
}

with open('E:/projects/abandono-academico-casa-grande/artifacts/dashboard/model_proxy.json', 'w', encoding='utf-8') as f:
    json.dump(proxy, f, indent=2, ensure_ascii=False)
print('\nmodel_proxy.json atualizado!')

# Test
dias, delta, nota = 26.0, 0.0, 74.0
sc_2 = scaler2.transform([[dias, delta]])[0]
aas_n = (nota - scaler_aas.mean_[0]) / scaler_aas.scale_[0]
logit = float(lr2.intercept_[0]) + float(lr2.coef_[0][0])*float(sc_2[0]) + float(lr2.coef_[0][1])*float(sc_2[1]) + coef_aas * float(aas_n)
p = float(expit(logit))
print(f'P(dias_sem=26, delta=0, nota=74): {p:.1%}')

# Compare extremes
print('Extremos:')
for dias, delta, nota in [(0, -30, 90), (270, 30, 0)]:
    sc_2 = scaler2.transform([[dias, delta]])[0]
    aas_n = (nota - scaler_aas.mean_[0]) / scaler_aas.scale_[0]
    logit = float(lr2.intercept_[0]) + float(lr2.coef_[0][0])*float(sc_2[0]) + float(lr2.coef_[0][1])*float(sc_2[1]) + coef_aas * float(aas_n)
    p = float(expit(logit))
    print(f'  {dias}d sem, {delta:+.0f}d atraso, {nota}pts -> P={p:.1%}')

# Check all coefficients negative
print(f'\nCoef dias_sem ({lr2.coef_[0][0]:.4f}) < 0? {lr2.coef_[0][0] < 0}')
print(f'Coef delta ({lr2.coef_[0][1]:.4f}) < 0? {lr2.coef_[0][1] < 0}')
print(f'Coef aas ({coef_aas:.4f}) < 0? {coef_aas < 0}')

