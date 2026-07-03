"""
Comprehensive 6-Model Benchmark Pipeline
Writes results to artifacts/data/ for later doc generation.
"""
import sys, io, json, pickle, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / 'artifacts' / 'data'
DQ_DIR = BASE / 'artifacts' / 'dq'
DASHBOARD_DIR = BASE / 'artifacts' / 'dashboard'
DUCKDB_PATH = DATA_DIR / 'oulad.duckdb'
MODEL_PATH = BASE / 'src' / 'model.pkl'
RESULTS_PATH = DATA_DIR / 'full_results.json'
PROXY_PATH = DASHBOARD_DIR / 'model_proxy.json'

for p in [DATA_DIR, DQ_DIR, DASHBOARD_DIR]:
    p.mkdir(parents=True, exist_ok=True)

import duckdb
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, roc_auc_score, precision_score,
                             recall_score, f1_score, confusion_matrix, classification_report)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from scipy import stats as scipy_stats
import xgboost as xgb
import lightgbm as lgb

RANDOM_STATE = 42
N_ESTIMATORS = 200
CV_FOLDS = 5

# ── Load ──
print("=" * 60)
print("[T4] Loading OULAD data...")
con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
df = con.execute("SELECT * FROM gold_oulad_features").fetchdf()
con.close()
print(f"  Gold table: {len(df):,} rows")
print(f"  Dropout rate: {df['is_dropout'].mean():.1%}")

# ── Feature Engineering ──
print("\n[T4] Feature engineering...")
df['imd_band'] = df['imd_band'].fillna('Unknown')
null_reg = df['date_registration'].isnull().sum()
if null_reg > 0:
    df['date_registration'] = df['date_registration'].fillna(df['date_registration'].median())

df['engagement_intensity'] = df['total_clicks'] / df['module_presentation_length'].replace(0, 1)
df['activity_coverage'] = df['days_active'] / df['module_presentation_length'].replace(0, 1)
df['has_vle_activity'] = (df['total_clicks'] > 0).astype(int)
df['assessment_count'] = df['num_tma'] + df['num_cma'] + df['num_exams']
df['submission_rate'] = df['assessment_count'] / df['module_presentation_length'].replace(0, 1)
df['late_submission_flag'] = (df['avg_submission_delta'] > 0).astype(int)
df['registration_earliness'] = df['date_registration']

CAT = ['code_module','code_presentation','gender','region','highest_education','imd_band','age_band','disability']
NUM = ['num_of_prev_attempts','studied_credits','date_registration','total_clicks','days_active',
       'last_activity_day','first_activity_day','click_trend','avg_daily_clicks','weighted_avg_score',
       'num_tma','num_cma','num_exams','avg_assessment_score','avg_submission_delta',
       'module_presentation_length','engagement_intensity','activity_coverage','has_vle_activity',
       'assessment_count','submission_rate','late_submission_flag','registration_earliness']

all_features = CAT + NUM
X = df[all_features].copy()
y = df['is_dropout'].values

for c in NUM: X[c] = X[c].fillna(0)
for c in CAT: X[c] = X[c].fillna('Unknown')

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)
print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

prep = ColumnTransformer([
    ('num', StandardScaler(), NUM),
    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CAT),
])

# ── Model Definitions ──
neg, pos = np.bincount(y_train)
scale_pos_weight = neg / pos

model_defs = [
    ('Dummy', DummyClassifier(strategy='stratified', random_state=RANDOM_STATE), False),
    ('Logistic Regression', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=RANDOM_STATE), True),
    ('Random Forest', RandomForestClassifier(n_estimators=N_ESTIMATORS, class_weight='balanced',
     random_state=RANDOM_STATE, max_depth=None, min_samples_split=5, min_samples_leaf=2), True),
    ('Gradient Boosting', GradientBoostingClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE,
     max_depth=4, min_samples_split=5, min_samples_leaf=2), True),
    ('XGBoost', xgb.XGBClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE,
     scale_pos_weight=scale_pos_weight, max_depth=6, learning_rate=0.1, subsample=0.8,
     colsample_bytree=0.8, verbosity=0), True),
    ('LightGBM', lgb.LGBMClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE,
     class_weight='balanced', max_depth=-1, learning_rate=0.1, num_leaves=31,
     subsample=0.8, colsample_bytree=0.8, verbose=-1), True),
]

# ── T5: Training & CV ──
print("\n[T5] Training & 5-fold Cross-Validation:")
cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

cv_results = {}
models = {}

for name, clf, use_prep in model_defs:
    t0 = time.perf_counter()
    model = Pipeline([('prep', prep), ('clf', clf)]) if use_prep else Pipeline([('prep', prep), ('clf', clf)])
    # For Dummy we need a pipeline too (Dummy doesn't care about features but we need the interface)
    if name == 'Dummy':
        model = Pipeline([('prep', prep), ('clf', clf)])
    
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - t0

    # CV
    cv_t0 = time.perf_counter()
    y_pred_cv = cross_val_predict(model, X_train, y_train, cv=cv, method='predict')
    y_proba_cv = cross_val_predict(model, X_train, y_train, cv=cv, method='predict_proba')[:, 1]
    cv_time = time.perf_counter() - cv_t0

    acc = accuracy_score(y_train, y_pred_cv)
    prec = precision_score(y_train, y_pred_cv, zero_division=0)
    rec = recall_score(y_train, y_pred_cv, zero_division=0)
    f1 = f1_score(y_train, y_pred_cv, zero_division=0)
    auc = roc_auc_score(y_train, y_proba_cv)

    # Model size
    buf = io.BytesIO()
    pickle.dump(model, buf)
    size_kb = len(buf.getvalue()) / 1024

    # Inference time
    inf_t0 = time.perf_counter()
    _ = model.predict(X_test.head(1000))
    inf_time = time.perf_counter() - inf_t0

    cv_results[name] = {
        'accuracy': float(acc), 'precision': float(prec), 'recall': float(rec),
        'f1': float(f1), 'roc_auc': float(auc), 'train_time': train_time,
        'cv_time': cv_time, 'model_size_kb': size_kb, 'inference_time_1000': inf_time,
        'y_pred_cv': y_pred_cv.tolist(), 'y_proba_cv': y_proba_cv.tolist(),
    }
    models[name] = model

    print(f"  {name:22s} | acc={acc:.4f} prec={prec:.4f} rec={rec:.4f} f1={f1:.4f} auc={auc:.4f} | "
          f"train={train_time:.1f}s size={size_kb:.0f}KB inf={inf_time:.4f}s")

# ── T6: Test Set Evaluation ──
print("\n[T6] Test Set Evaluation:")
test_results = {}
for name, _, use_prep in model_defs:
    model = models[name]
    if name == 'Dummy':
        d = DummyClassifier(strategy='stratified', random_state=RANDOM_STATE)
        d.fit(X_test, y_test)
        y_pred = d.predict(X_test)
        test_results[name] = {'accuracy': float(accuracy_score(y_test, y_pred))}
        print(f"  {name:22s} | acc={test_results[name]['accuracy']:.4f}")
        continue

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['Non-dropout', 'Withdrawn'], zero_division=0, output_dict=True)

    tr = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'roc_auc': float(roc_auc_score(y_test, y_proba)),
        'confusion_matrix': cm.tolist(),
        'classification_report': str(classification_report(y_test, y_pred, target_names=['Non-dropout', 'Withdrawn'], zero_division=0)),
    }
    test_results[name] = tr
    print(f"  {name:22s} | acc={tr['accuracy']:.4f} prec={tr['precision']:.4f} rec={tr['recall']:.4f} "
          f"f1={tr['f1']:.4f} auc={tr['roc_auc']:.4f}")

# ── Statistical Tests ──
print("\n[T6] Statistical Tests:")
stat_tests = []
non_dummy_names = [n for n, _, _ in model_defs if n != 'Dummy']
rng = np.random.RandomState(RANDOM_STATE)

# Permutation tests (1000)
dummy_acc = cv_results['Dummy']['accuracy']
for name in non_dummy_names:
    acc = cv_results[name]['accuracy']
    y_pred = np.array(cv_results[name]['y_pred_cv'])
    count = sum(1 for _ in range(1000) if accuracy_score(rng.permutation(y_train), y_pred) >= acc)
    p = (count + 1) / 1001
    sig = p < 0.05
    stat_tests.append({
        'test': f'{name} vs Dummy (permutation)',
        'statistic': acc - dummy_acc, 'p_value': p,
        'significant_005': sig,
        'interpretation': f'{name} ({acc:.4f}) vs Dummy ({dummy_acc:.4f}), Δ={acc - dummy_acc:.4f}',
    })
    print(f"  {name:22s} vs Dummy | Δ={acc - dummy_acc:.4f} p={p:.4f} {'***' if sig else 'ns'}")

# Paired t-tests
for i in range(len(non_dummy_names)):
    for j in range(i+1, len(non_dummy_names)):
        na, nb = non_dummy_names[i], non_dummy_names[j]
        sa = cross_val_score(models[na], X_train, y_train, cv=cv, scoring='accuracy')
        sb = cross_val_score(models[nb], X_train, y_train, cv=cv, scoring='accuracy')
        t_stat, p_val = scipy_stats.ttest_rel(sa, sb)
        sig = p_val < 0.05
        stat_tests.append({
            'test': f'{na} vs {nb} (paired t-test, 5-fold)',
            'statistic': float(t_stat), 'p_value': float(p_val),
            'significant_005': sig,
            'interpretation': f'{na}: {sa.mean():.4f}±{sa.std():.4f}, {nb}: {sb.mean():.4f}±{sb.std():.4f}',
        })
        print(f"  {na:22s} vs {nb:22s} | t={t_stat:.3f} p={p_val:.4f} {'***' if sig else 'ns'}")

# ── Model Selection ──
print("\n[T6] Model Selection:")
candidates = {n: test_results[n]['roc_auc'] for n in non_dummy_names if n in test_results and 'roc_auc' in test_results[n]}
best_name = max(candidates, key=candidates.get)
rf_auc = candidates.get('Random Forest', 0)
final_name = best_name if (best_name != 'Random Forest' and abs(candidates[best_name] - rf_auc) > 0.01) else 'Random Forest'
print(f"  Best by ROC-AUC: {best_name} ({candidates[best_name]:.4f})")
print(f"  Selected: {final_name}")

# ── Save model ──
best_model = models[final_name]
pickle.dump({'model': best_model, 'model_type': final_name, 'random_state': RANDOM_STATE }, open(str(MODEL_PATH), 'wb'))
print(f"\n  Model saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")

# ── Feature Importance ──
fi_source = None
fi_data = []
for preferred in ['Random Forest', 'XGBoost', 'LightGBM', 'Gradient Boosting']:
    if preferred not in models: continue
    try:
        model = models[preferred]
        preprocessor = model.named_steps['prep']
        cat_encoder = preprocessor.named_transformers_['cat']
        cat_names = cat_encoder.get_feature_names_out(CAT).tolist()
        fnames = NUM + cat_names
        clf = model.named_steps['clf']
        if hasattr(clf, 'feature_importances_'):
            imp = clf.feature_importances_
            fi_data = [{'feature': fn, 'importance': float(imp[i])} for i, fn in enumerate(fnames)]
            fi_data.sort(key=lambda x: x['importance'], reverse=True)
            fi_source = preferred
            print(f"\n  Feature importance from: {preferred}")
            for fd in fi_data[:10]:
                print(f"    {fd['feature']:30s}: {fd['importance']:.4f}")
            break
    except Exception as e:
        print(f"  Could not get importance from {preferred}: {e}")
        continue

# ── Model Proxy ──
print("\n[T6] Generating model_proxy.json...")
top3 = ['last_activity_day', 'assessment_count', 'submission_rate']
X_test_top = X_test[top3].copy()
scaler = StandardScaler()
X_test_scaled = scaler.fit_transform(X_test_top)

lr_proxy = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, class_weight='balanced')
lr_proxy.fit(X_test_scaled, y_test)

proxy = {
    'model': 'LogisticRegression',
    'features': top3,
    'coefficients': {
        'intercept': float(lr_proxy.intercept_[0]),
        'last_activity_day': float(lr_proxy.coef_[0][0]),
        'assessment_count': float(lr_proxy.coef_[0][1]),
        'submission_rate': float(lr_proxy.coef_[0][2]),
    },
    'feature_ranges': {
        f: {'min': float(X_test_top[f].min()), 'max': float(X_test_top[f].max()),
            'mean': float(X_test_top[f].mean()), 'std': float(X_test_top[f].std())}
        for f in top3
    },
    'default_meta_dropout': 0.20,
    'meta_bounds': [0.05, 0.50],
    'test_set_baseline_p': float(y_test.mean()),
    'scaler_mean': scaler.mean_.tolist(),
    'scaler_std': scaler.scale_.tolist(),
    'best_model': final_name,
    'best_model_test_roc_auc': float(test_results.get(final_name, {}).get('roc_auc', 0)),
}

with open(str(PROXY_PATH), 'w') as f:
    json.dump(proxy, f, indent=2)
print(f"  Proxy saved: {PROXY_PATH}")

# ── Save all results for doc generation ──
results_package = {
    'cv_results': {k: {kk: vv for kk, vv in v.items() if kk not in ('y_pred_cv', 'y_proba_cv')} for k, v in cv_results.items()},
    'test_results': test_results,
    'stat_tests': stat_tests,
    'feature_importance': {'source': fi_source, 'data': fi_data},
    'best_model': final_name,
    'model_defs': [(n, type(c).__name__) for n, c, _ in model_defs],
}

with open(str(RESULTS_PATH), 'w') as f:
    json.dump(results_package, f, indent=2)
print(f"\n  Results saved: {RESULTS_PATH}")

# ── Summary ──
print("\n" + "=" * 60)
print("  PIPELINE COMPLETE")
print("=" * 60)
print(f"  Models: {', '.join(n for n,_,_ in model_defs)}")
print(f"  Best: {final_name}")
print(f"  Test ROC-AUC: {test_results.get(final_name, {}).get('roc_auc', 0):.4f}")
print(f"  Test Recall: {test_results.get(final_name, {}).get('recall', 0):.4f}")
print(f"  Test Accuracy: {test_results.get(final_name, {}).get('accuracy', 0):.4f}")
print("=" * 60)
