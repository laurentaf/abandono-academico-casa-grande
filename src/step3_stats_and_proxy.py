"""Step 3: Statistical tests, model proxy, and consolidate results"""
import sys, io, json, pickle, time, warnings
from pathlib import Path
import numpy as np
from scipy import stats as scipy_stats
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

BASE = Path(r'E:\projects\abandono-academico-casa-grande')
DATA_DIR = BASE / 'artifacts' / 'data'
DASHBOARD_DIR = BASE / 'artifacts' / 'dashboard'
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = BASE / 'src' / 'model.pkl'

step1 = pickle.load(open(str(DATA_DIR / 'step1.pkl'), 'rb'))
X_train, X_test = step1['X_train'], step1['X_test']
y_train, y_test = step1['y_train'], step1['y_test']
prep = step1['prep']
CAT, NUM = step1['CAT'], step1['NUM']

fast_results = step1['results']
tree_results = pickle.load(open(str(DATA_DIR / 'step2_results.pkl'), 'rb'))

# Merge results
all_results = {**fast_results}
for k, v in tree_results.items():
    if k.startswith('_'): continue
    all_results[k] = v

print("Results overview:")
for k, v in all_results.items():
    print(f"  {k:22s}: acc={v.get('accuracy',0):.4f} rec={v.get('recall',0):.4f} auc={v.get('roc_auc',0):.4f} t={v.get('train_time',0):.1f}s")

# Statistical tests
print("\nPermutation tests (1000 iterações) vs Dummy:")
rng = np.random.RandomState(42)
dummy_acc = all_results['Dummy']['accuracy']
non_dummy_names = [n for n in all_results if n != 'Dummy' and isinstance(all_results[n], dict) and 'recall' in all_results[n]]

stat_tests = []
models_for_cv = {}

for name in non_dummy_names:
    sk = name.replace(' ', '').lower()
    model_path = BASE / 'src'
    model_files = {
        'LR': model_path / 'model_lr.pkl',
        'RandomForest': model_path / 'model_rf.pkl',
        'GradientBoosting': model_path / 'model_gbm.pkl',
        'XGBoost': model_path / 'model_xgboost.pkl',
        'LightGBM': model_path / 'model_lgbm.pkl',
    }
    
    key_map = {
        'LR': 'LR',
        'Random Forest': 'RandomForest',
        'Gradient Boosting': 'GradientBoosting',
        'XGBoost': 'XGBoost',
        'LightGBM': 'LightGBM',
    }
    
    if name in key_map and (model_path / f'model_{key_map[name].lower()}.pkl').exists():
        models_for_cv[name] = pickle.load(open(str(model_path / f'model_{key_map[name].lower()}.pkl'), 'rb'))

# Permutation test
for name in non_dummy_names:
    model_acc = all_results[name]['accuracy']
    # Use y_pred from model
    if name in models_for_cv:
        pipe = models_for_cv[name]
        y_pred_cv = pipe.predict(X_train)
        count = 0
        for _ in range(1000):
            perm = rng.permutation(y_train)
            perm_acc = accuracy_score(perm, y_pred_cv)
            if perm_acc >= model_acc:
                count += 1
        p = (count + 1) / 1001
        sig = p < 0.05
        stat_tests.append({
            'test': f'{name} vs Dummy (permutation)',
            'statistic': model_acc - dummy_acc,
            'p_value': float(p),
            'significant_005': sig,
            'interpretation': f'{name} ({model_acc:.4f}) vs Dummy ({dummy_acc:.4f}), Δ={model_acc - dummy_acc:.4f}',
        })
        print(f"  {name:22s}: Δ={model_acc - dummy_acc:.4f} p={p:.4f} {'***' if sig else 'ns'}")

# Paired t-tests
print("\nPaired t-tests (5-fold, all pairs):")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
names_list = list(models_for_cv.keys())
for i in range(len(names_list)):
    for j in range(i+1, len(names_list)):
        na, nb = names_list[i], names_list[j]
        sa = cross_val_score(models_for_cv[na], X_train, y_train, cv=cv, scoring='accuracy')
        sb = cross_val_score(models_for_cv[nb], X_train, y_train, cv=cv, scoring='accuracy')
        t_stat, p_val = scipy_stats.ttest_rel(sa, sb)
        sig = p_val < 0.05
        stat_tests.append({
            'test': f'{na} vs {nb} (paired t-test, 5-fold)',
            'statistic': float(t_stat),
            'p_value': float(p_val),
            'significant_005': sig,
            'interpretation': f'{na}: {sa.mean():.4f}±{sa.std():.4f}, {nb}: {sb.mean():.4f}±{sb.std():.4f}',
        })
        print(f"  {na:22s} vs {nb:22s}: t={t_stat:.3f} p={p_val:.4f} {'***' if sig else 'ns'}")

# Model selection
best_name = max(non_dummy_names, key=lambda n: all_results[n].get('roc_auc', 0))
rf_auc = all_results.get('Random Forest', {}).get('roc_auc', 0)
final_name = best_name if abs(all_results[best_name].get('roc_auc', 0) - rf_auc) > 0.01 else 'Random Forest'
print(f"\nBest by ROC-AUC: {best_name} ({all_results[best_name].get('roc_auc', 0):.4f})")
print(f"Selected: {final_name}")

# Save best model
if final_name in models_for_cv:
    best_pipe = models_for_cv[final_name]
    pickle.dump({'model': best_pipe, 'model_type': final_name, 'random_state': 42}, open(str(MODEL_PATH), 'wb'))
    print(f"Best model saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")

# Feature importance
print("\nFeature importances:")
fi_source = None
fi_data = []
for pref in ['Random Forest', 'XGBoost', 'LightGBM', 'Gradient Boosting']:
    if pref not in models_for_cv: continue
    try:
        pipe = models_for_cv[pref]
        cat_encoder = prep.named_transformers_['cat']
        cat_names = cat_encoder.get_feature_names_out(CAT).tolist()
        fnames = NUM + cat_names
        clf = pipe.named_steps['clf']
        imp = clf.feature_importances_
        fi_data = [{'feature': fn, 'importance': float(imp[i])} for i, fn in enumerate(fnames)]
        fi_data.sort(key=lambda x: x['importance'], reverse=True)
        fi_source = pref
        print(f"  Source: {pref}")
        for fd in fi_data[:10]:
            print(f"    {fd['feature']:30s}: {fd['importance']:.4f}")
        break
    except:
        continue

# Model Proxy
print("\nGenerating model_proxy.json...")
top3 = ['last_activity_day', 'assessment_count', 'submission_rate']
X_test_top = X_test[top3].copy()
scaler = StandardScaler()
X_test_scaled = scaler.fit_transform(X_test_top)

lr_proxy = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
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
    'best_model_test_roc_auc': float(all_results.get(final_name, {}).get('roc_auc', 0)),
}
json.dump(proxy, open(str(DASHBOARD_DIR / 'model_proxy.json'), 'w'), indent=2)
print(f"  Proxy saved: {DASHBOARD_DIR / 'model_proxy.json'}")

# Consolidate all results
results_package = {
    'all_results': all_results,
    'stat_tests': stat_tests,
    'feature_importance': {'source': fi_source, 'data': fi_data},
    'best_model': final_name,
}
# Convert numpy types to native Python for JSON serialization
def convert(obj):
    if isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    return obj

results_package = convert(results_package)
json.dump(results_package, open(str(DATA_DIR / 'full_results.json'), 'w'), indent=2)
print(f"\nResults saved: {DATA_DIR / 'full_results.json'}")

# Model size estimates
for name in non_dummy_names:
    if name in models_for_cv:
        buf = io.BytesIO()
        pickle.dump(models_for_cv[name], buf)
        size = len(buf.getvalue()) / 1024
        print(f"  {name:22s} size: {size:.0f} KB")

print("\nStep 3 complete!")
