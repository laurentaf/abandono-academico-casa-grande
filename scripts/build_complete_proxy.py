"""Construir proxy completo com dados populacionais, thresholds e cenarios."""
import duckdb, json, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.special import expit
from sklearn.metrics import roc_auc_score

con = duckdb.connect('E:/projects/abandono-academico-casa-grande/artifacts/data/oulad.duckdb', read_only=True)
df = con.execute("""
    SELECT 
        module_presentation_length, last_activity_day, avg_submission_delta,
        avg_assessment_score, is_dropout
    FROM gold_oulad_features
    WHERE last_activity_day >= 0 AND last_activity_day <= 300
""").fetchdf()
con.close()
N = len(df)

# --- Features ---
df['dias_sem_atividade'] = (df['module_presentation_length'] - df['last_activity_day']).clip(0, 270)
df['avg_submission_delta'] = df['avg_submission_delta'].fillna(0)
df['avg_assessment_score'] = df['avg_assessment_score'].fillna(df.avg_assessment_score.median())

features = ['dias_sem_atividade', 'avg_submission_delta', 'avg_assessment_score']
labels = {
    'dias_sem_atividade': 'Dias sem atividade no VLE',
    'avg_submission_delta': 'Atraso medio na entrega',
    'avg_assessment_score': 'Nota media nas provas'
}
units = {
    'dias_sem_atividade': 'dias',
    'avg_submission_delta': 'dias',
    'avg_assessment_score': 'pontos'
}
descriptions = {
    'dias_sem_atividade': 'Tempo que o aluno fica sem acessar a plataforma. Quanto mais dias, maior a chance de desistir.',
    'avg_submission_delta': 'Media de quanto o aluno atrasa as entregas (positivo = atraso, negativo = adiantamento). Quanto maior, pior.',
    'avg_assessment_score': 'Nota media em todas as provas. Quanto menor, maior o risco.'
}
defaults = {
    'dias_sem_atividade': float(df.dias_sem_atividade.median()),
    'avg_submission_delta': 0.0,
    'avg_assessment_score': float(df.avg_assessment_score.median())
}
ranges = {
    'dias_sem_atividade': [0, 270],
    'avg_submission_delta': [-30, 30],
    'avg_assessment_score': [0, 100]
}

# --- Modelo hibrido ---
X2 = df[['dias_sem_atividade', 'avg_submission_delta']].values
y = df['is_dropout'].values
scaler2 = StandardScaler()
X2s = scaler2.fit_transform(X2)
lr2 = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
lr2.fit(X2s, y)

scaler_aas = StandardScaler()
aas_s = scaler_aas.fit_transform(df[['avg_assessment_score']].values)
lr_aas = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
lr_aas.fit(aas_s, y)
coef_aas = float(lr_aas.coef_[0][0])

# Probabilidade de cada aluno
log_odds = float(lr2.intercept_[0]) + X2s @ lr2.coef_[0] + coef_aas * aas_s.flatten()
probs = expit(log_odds)
roc_hib = roc_auc_score(y, probs)

baseline_rate = float(y.mean())  # ~0.229

print(f'N={N}, ROC-AUC={roc_hib:.4f}, baseline_rate={baseline_rate:.4f}')
print(f'Coefs: dias_sem={lr2.coef_[0][0]:.4f}, delta={lr2.coef_[0][1]:.4f}, aas={coef_aas:.4f}')

# --- Funcao de probabilidade (para JS) ---
def calc_p(dias, delta, nota):
    d_n = (dias - scaler2.mean_[0]) / scaler2.scale_[0]
    dl_n = (delta - scaler2.mean_[1]) / scaler2.scale_[1]
    n_n = (nota - scaler_aas.mean_[0]) / scaler_aas.scale_[0]
    logit = float(lr2.intercept_[0]) + float(lr2.coef_[0][0])*d_n + float(lr2.coef_[0][1])*dl_n + coef_aas*n_n
    return float(expit(logit))

# --- Thresholds de alerta ---
# Para cada feature, a que valor o risco atinge 20%, 30%, 40%, 50%?
# Mantendo as outras fixas na mediana
thresholds = {}
med_dias, med_delta, med_nota = defaults['dias_sem_atividade'], defaults['avg_submission_delta'], defaults['avg_assessment_score']
target_risks = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

for feat, fix_val, fix_val2 in [
    ('dias_sem_atividade', med_delta, med_nota),
    ('avg_submission_delta', 26.0, med_nota),
    ('avg_assessment_score', 26.0, med_delta)
]:
    th = {}
    for tr in target_risks:
        lo, hi = ranges[feat]
        for _ in range(100):
            mid = (lo + hi) / 2
            if feat == 'dias_sem_atividade': p = calc_p(mid, fix_val, fix_val2)
            elif feat == 'avg_submission_delta': p = calc_p(fix_val, mid, fix_val2)
            else: p = calc_p(fix_val, fix_val2, mid)
            if abs(p - tr) < 0.001: break
            if p > tr: hi = mid
            else: lo = mid
        th[str(tr)] = round(mid, 1)
    thresholds[feat] = th

print(f'\nThresholds de risco:')
for f in features:
    print(f'  {f}: {thresholds[f]}')

# --- Percentis (ja temos) ---
def pct_le(col, values):
    return {str(v): round(float((df[col] <= v).mean()), 4) for v in values}
def pct_ge(col, values):
    return {str(v): round(float((df[col] >= v).mean()), 4) for v in values}

# --- Impacto populacional: se todos os alunos com feature > X melhorassem para X ---
# Para cada feature e cada threshold X, calcula:
# - % alunos afetados (% com valor > X)
# - risco medio desses alunos (antes)
# - risco medio desses alunos DEPOIS (com feature = X, outras fixas)
# - reducao total no risco medio da populacao
impacto_pop = {}
for feat, idx in [('dias_sem_atividade', 0), ('avg_submission_delta', 1), ('avg_assessment_score', 2)]:
    vals = df[feat].values
    pops = {}
    for threshold in [7, 15, 30, 60, 90, 120, 180]:
        mask = vals > threshold
        pct_afetados = float(mask.mean())
        if pct_afetados == 0: continue
        
        # Risco atual desses alunos
        risco_atual = float(probs[mask].mean())
        
        # Se melhorarmos todos para o threshold (mantendo outras features)
        novas_probs = probs.copy()
        if feat == 'dias_sem_atividade':
            novos_vals = np.clip(vals, 0, threshold)
            d_n = (novos_vals - scaler2.mean_[0]) / scaler2.scale_[0]
            dl_n = (df['avg_submission_delta'].values - scaler2.mean_[1]) / scaler2.scale_[1]
            n_n = aas_s.flatten()
        elif feat == 'avg_submission_delta':
            d_n = (df['dias_sem_atividade'].values - scaler2.mean_[0]) / scaler2.scale_[0]
            novos_vals = np.clip(vals, -30, threshold)
            dl_n = (novos_vals - scaler2.mean_[1]) / scaler2.scale_[1]
            n_n = aas_s.flatten()
        else:  # nota
            d_n = (df['dias_sem_atividade'].values - scaler2.mean_[0]) / scaler2.scale_[0]
            dl_n = (df['avg_submission_delta'].values - scaler2.mean_[1]) / scaler2.scale_[1]
            novos_vals = np.clip(vals, threshold, 100)
            n_n = (novos_vals - scaler_aas.mean_[0]) / scaler_aas.scale_[0]
        
        novos_logits = float(lr2.intercept_[0]) + float(lr2.coef_[0][0])*d_n + float(lr2.coef_[0][1])*dl_n + coef_aas*n_n
        risco_depois = float(expit(novos_logits)[mask].mean())
        
        reducao_pop = (float(probs.mean()) - float(expit(novos_logits).mean())) * 100  # pp
        
        pops[str(threshold)] = {
            'pct_afetados': round(pct_afetados * 100, 1),
            'risco_atual_afetados': round(risco_atual * 100, 1),
            'risco_depois_afetados': round(risco_depois * 100, 1),
            'reducao_media_pop': round(reducao_pop, 2)
        }
    impacto_pop[feat] = pops

print(f'\nImpacto populacional:')
for f in features:
    for k, v in impacto_pop[f].items():
        print(f'  {f} <= {k}: {v}')

# --- Dados descritivos ---
def desc(col):
    v = df[col]
    return {
        'min': round(float(v.min()), 1), 'max': round(float(v.max()), 1),
        'mean': round(float(v.mean()), 1), 'median': round(float(v.median()), 1),
        'std': round(float(v.std()), 1),
        'pct_dropout': round(float(df[df.is_dropout==1][col].mean()), 1),
        'pct_retention': round(float(df[df.is_dropout==0][col].mean()), 1)
    }

# --- Salvar JSON ---
proxy = {
    'model': 'LR hibrido humanizado',
    'features': features,
    'feature_labels': labels,
    'feature_units': units,
    'feature_descriptions': descriptions,
    'feature_defaults': defaults,
    'feature_ranges': {f: {'min': r[0], 'max': r[1], 'mean': round(float(df[f].mean()), 2), 'std': round(float(df[f].std()), 2)} for f, r in zip(features, [ranges[f] for f in features])},
    'coefficients': {
        'intercept': float(lr2.intercept_[0]),
        'dias_sem_atividade': float(lr2.coef_[0][0]),
        'avg_submission_delta': float(lr2.coef_[0][1]),
        'avg_assessment_score': coef_aas
    },
    'scaler_mean': [round(float(m), 4) for m in scaler2.mean_],
    'scaler_std': [round(float(s), 4) for s in scaler2.scale_],
    'scaler_aas_mean': round(float(scaler_aas.mean_[0]), 4),
    'scaler_aas_std': round(float(scaler_aas.scale_[0]), 4),
    'percentiles': {
        'dias_sem_atividade': pct_le('dias_sem_atividade', [0, 7, 15, 30, 60, 90, 120, 180, 270]),
        'avg_submission_delta': pct_le('avg_submission_delta', [-30, -15, -7, 0, 7, 15, 30]),
        'avg_assessment_score': pct_ge('avg_assessment_score', [10, 20, 30, 40, 50, 60, 70, 80, 90])
    },
    'descriptive_stats': {f: desc(f) for f in features},
    'baseline_stats': {
        'total_students': N,
        'baseline_rate': round(baseline_rate, 4),
        'baseline_at_risk': round(N * baseline_rate),
        'median_risk': round(float(np.median(probs)), 4),
        'q25_risk': round(float(np.percentile(probs, 25)), 4),
        'q75_risk': round(float(np.percentile(probs, 75)), 4)
    },
    'thresholds': thresholds,
    'impacto_populacional': impacto_pop,
    'default_meta_dropout': 0.20,
    'meta_bounds': [0.05, 0.50],
    'proxy_roc_auc': round(roc_hib, 4)
}

with open('E:/projects/abandono-academico-casa-grande/artifacts/dashboard/model_proxy.json', 'w', encoding='utf-8') as f:
    json.dump(proxy, f, indent=2, ensure_ascii=False)
print('\nmodel_proxy.json salvo!')

# Verificacao
p_default = calc_p(26, 0, 74)
p_bom = calc_p(7, -7, 85)
p_ruim = calc_p(180, 15, 30)
print(f'P(26, 0, 74) = {p_default:.1%}')
print(f'P(7, -7, 85) = {p_bom:.1%}')
print(f'P(180, 15, 30) = {p_ruim:.1%}')
