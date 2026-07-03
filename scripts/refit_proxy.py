"""Refit LR proxy — modelo hibrido:
- last_activity_day + submission_rate (LR, ambos negativos)
- avg_assessment_score: coeficiente de LR univariado (negativo)
"""
import duckdb, json, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.special import expit
from sklearn.metrics import roc_auc_score

con = duckdb.connect('E:/projects/abandono-academico-casa-grande/artifacts/data/oulad.duckdb', read_only=True)
df = con.execute("""
    SELECT
        last_activity_day,
        CAST(num_tma + num_cma + num_exams AS DOUBLE) / NULLIF(module_presentation_length, 0) AS submission_rate,
        avg_assessment_score,
        is_dropout
    FROM gold_oulad_features
    WHERE last_activity_day >= 0 AND last_activity_day <= 300
""").fetchdf()
con.close()

# Modelo 1: lad + sr
feats_2 = ['last_activity_day', 'submission_rate']
X2 = df[feats_2].values
y = df['is_dropout'].values
scaler2 = StandardScaler()
X2s = scaler2.fit_transform(X2)
lr2 = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
lr2.fit(X2s, y)

roc2 = roc_auc_score(y, lr2.predict_proba(X2s)[:, 1])
print(f'Model lad+sr: ROC-AUC={roc2:.4f}')
for i, f in enumerate(feats_2):
    print(f'  {f}: {lr2.coef_[0][i]:.4f} (neg={lr2.coef_[0][i] < 0})')

# Modelo 2: aas sozinho (univariado)
scaler_aas = StandardScaler()
aas_scaled = scaler_aas.fit_transform(df[['avg_assessment_score']].values)
lr_aas = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
lr_aas.fit(aas_scaled, y)
print(f'\nModel aas alone: coeff={lr_aas.coef_[0][0]:.4f}, intercept={lr_aas.intercept_[0]:.4f}')
print(f'  ROC-AUC={roc_auc_score(y, lr_aas.predict_proba(aas_scaled)[:,1]):.4f}')
print(f'  Negative? {lr_aas.coef_[0][0] < 0}')

# Proxy hibrido: intercept do lad+sr, coefs do lad+sr, coef aas do univariado
# Logica: P = sigmoid(intercept_lr2 + lad_norm*c_lad + sr_norm*c_sr + aas_norm*c_aas)
# Onde aas_norm usa scaler do univariado
coef_aas = float(lr_aas.coef_[0][0])
intercept_aas = float(lr_aas.intercept_[0])

print(f'\nCoef aas (univariado): {coef_aas:.4f}')
print(f'Intercept aas (univariado): {intercept_aas:.4f}')

# Validacao: ROC-AUC do modelo hibrido
# P = sigmoid(lr2.intercept_ + lr2.coef_ @ X2_scaled + lr_aas.coef_ * aas_scaled)
from sklearn.metrics import roc_auc_score
log_odds = float(lr2.intercept_[0]) + X2s @ lr2.coef_[0] + float(lr_aas.coef_[0][0]) * aas_scaled.flatten()
p_hibrido = expit(log_odds)
roc_hib = roc_auc_score(y, p_hibrido)
print(f'ROC-AUC modelo hibrido: {roc_hib:.4f}')

# Salvar proxy
mean_lad, std_lad = float(df.last_activity_day.mean()), float(df.last_activity_day.std())
mean_sr, std_sr = float(df.submission_rate.mean()), float(df.submission_rate.std())
mean_aas, std_aas = float(df.avg_assessment_score.mean()), float(df.avg_assessment_score.std())

proxy = {
    'model': 'LogisticRegression (hibrido)',
    'features': ['last_activity_day', 'submission_rate', 'avg_assessment_score'],
    'feature_labels': {
        'last_activity_day': 'Ultimo dia de atividade VLE (0-270 dias do modulo)',
        'submission_rate': 'Taxa de envio de avaliacoes (0 = nenhuma, ~0.058 = max)',
        'avg_assessment_score': 'Nota media nas provas (0-100)'
    },
    'coefficients': {
        'intercept': float(lr2.intercept_[0]),
        'last_activity_day': float(lr2.coef_[0][0]),
        'submission_rate': float(lr2.coef_[0][1]),
        'avg_assessment_score': coef_aas
    },
    'intercept_aas': intercept_aas,
    'feature_ranges': {
        'last_activity_day': {'min': 0, 'max': 270, 'mean': mean_lad, 'std': std_lad},
        'submission_rate': {'min': 0.0, 'max': 0.058, 'mean': mean_sr, 'std': std_sr},
        'avg_assessment_score': {'min': 0, 'max': 100, 'mean': mean_aas, 'std': std_aas}
    },
    'scaler_mean': [float(m) for m in scaler2.mean_],
    'scaler_std': [float(s) for s in scaler2.scale_],
    'scaler_aas_mean': float(scaler_aas.mean_[0]),
    'scaler_aas_std': float(scaler_aas.scale_[0]),
    'default_meta_dropout': 0.20,
    'meta_bounds': [0.05, 0.50],
    'test_set_baseline_p': float(y.mean()),
    'best_model': 'Random Forest',
    'best_model_test_roc_auc': 0.9525,
    'proxy_roc_auc': round(roc_hib, 4),
    'note': 'Proxy hibrido: lad+sr de LR completo, aas de LR univariado (coeficiente negativo verdadeiro). last_activity_day >= 0.'
}

with open('E:/projects/abandono-academico-casa-grande/artifacts/dashboard/model_proxy.json', 'w') as f:
    json.dump(proxy, f, indent=2)
print('\nmodel_proxy.json salvo!')

# Teste
lad, sr, aas = 128.0, 0.024, 65.0
scaled = scaler2.transform([[lad, sr]])[0]
aas_norm = (aas - scaler_aas.mean_[0]) / scaler_aas.scale_[0]
logit = float(lr2.intercept_[0]) + float(lr2.coef_[0][0])*float(scaled[0]) + float(lr2.coef_[0][1])*float(scaled[1]) + coef_aas * float(aas_norm)
p = float(expit(logit))
print(f'P(lad=128, sr=0.024, aas=65): {p:.1%}')

# Per unit impact
for name, rng, coef_on_scaled in [
    ('last_activity_day', std_lad, float(lr2.coef_[0][0])),
    ('submission_rate', std_sr, float(lr2.coef_[0][1])),
    ('avg_assessment_score', std_aas, coef_aas)
]:
    impact = (coef_on_scaled / rng) * p * (1.0 - p) * 100.0
    direction = 'menor' if impact < 0 else 'maior'
    print(f'  +1 {name}: {impact:+.4f}pp -> {direction} risco')

# Effort for meta 20%
target_p = 0.20
logit_target = float(np.log(target_p / (1.0 - target_p)))
scaled_vals = {'last_activity_day': lad, 'submission_rate': sr, 'avg_assessment_score': aas}
coeffs_2 = {'last_activity_day': float(lr2.coef_[0][0]), 'submission_rate': float(lr2.coef_[0][1])}
stds_2 = {'last_activity_day': std_lad, 'submission_rate': std_sr}
means_2 = {'last_activity_day': mean_lad, 'submission_rate': mean_sr}

print(f'\nEffort to reach {target_p:.0%} (baseline {p:.1%}):')
for name in ['last_activity_day', 'submission_rate', 'avg_assessment_score']:
    raw_val = scaled_vals[name]
    lo = proxy['feature_ranges'][name]['min']
    hi = proxy['feature_ranges'][name]['max']

    if name == 'avg_assessment_score':
        # Effort for aas: use univariado
        other_logit = float(lr2.intercept_[0])
        for f2 in feats_2:
            f_scaled = (scaled_vals[f2] - proxy['scaler_mean'][0 if f2 == 'last_activity_day' else 1]) / proxy['scaler_std'][0 if f2 == 'last_activity_day' else 1]
            other_logit += coeffs_2[f2] * float(f_scaled)
        target_aas_scaled = (logit_target - other_logit) / coef_aas
        target_raw = target_aas_scaled * std_aas + mean_aas
    else:
        f_idx = 0 if name == 'last_activity_day' else 1
        c = coeffs_2[name]
        other_sum = float(lr2.intercept_[0])
        for f2 in feats_2:
            if f2 == name: continue
            f_scaled = (scaled_vals[f2] - proxy['scaler_mean'][0 if f2 == 'last_activity_day' else 1]) / proxy['scaler_std'][0 if f2 == 'last_activity_day' else 1]
            other_sum += coeffs_2[f2] * float(f_scaled)
        # Add aas
        aas_n = (scaled_vals['avg_assessment_score'] - proxy['scaler_aas_mean']) / proxy['scaler_aas_std']
        other_sum += coef_aas * float(aas_n)
        target_scaled = float(logit_target - other_sum) / c
        target_raw = float(target_scaled * proxy['scaler_std'][f_idx] + proxy['scaler_mean'][f_idx])

    feasible = 'yes' if lo <= target_raw <= hi else 'no'
    delta = target_raw - raw_val
    print(f'  {name}: {raw_val:.1f} -> {target_raw:.1f} (delta={delta:+.1f}, limit [{lo:.0f},{hi:.0f}]) feasible={feasible}')
