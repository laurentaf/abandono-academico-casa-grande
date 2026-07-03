"""Fix names and generate final results."""
import sys, io, json, pickle, time, warnings
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

BASE = Path(r'E:\projects\abandono-academico-casa-grande')
DATA_DIR = BASE / 'artifacts' / 'data'
DASHBOARD_DIR = BASE / 'artifacts' / 'dashboard'
MODEL_PATH = BASE / 'src' / 'model.pkl'

step1 = pickle.load(open(str(DATA_DIR / 'step1.pkl'), 'rb'))

# Load step2 tree results
tree_raw = pickle.load(open(str(DATA_DIR / 'step2_results.pkl'), 'rb'))
tree_results = {}
for k, v in tree_raw.items():
    if k.startswith('_'): continue
    # Map abbreviated names to canonical names
    name_map = {
        'RandomForest': 'Random Forest',
        'GradientBoosting': 'Gradient Boosting',
        'XGBoost': 'XGBoost',
        'LightGBM': 'LightGBM',
    }
    canonical = name_map.get(k, k)
    tree_results[canonical] = v

# Merge all results
all_results = {
    'Dummy': step1['results']['Dummy'],
    'Logistic Regression': step1['results']['LR'],
}
all_results.update(tree_results)

print("=== BENCHMARK RESULTS (Test Set) ===")
print(f"{'Model':25s} {'Accuracy':>9s} {'Precision':>10s} {'Recall':>7s} {'F1':>7s} {'ROC-AUC':>8s} {'Time(s)':>7s}")
print("-" * 75)
for name in ['Dummy', 'Logistic Regression', 'Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM']:
    r = all_results.get(name, {})
    acc = r.get('accuracy', 0)
    prec = r.get('precision', 0)
    rec = r.get('recall', 0)
    f1 = r.get('f1', 0)
    auc = r.get('roc_auc', 0)
    t = r.get('train_time', 0)
    print(f"{name:25s} {acc:9.4f} {prec:10.4f} {rec:7.4f} {f1:7.4f} {auc:8.4f} {t:7.2f}")

# Model selection: RF default unless gap > 0.01 ROC-AUC
non_dummy_aucs = {n: all_results[n].get('roc_auc', 0) for n in all_results
                  if n != 'Dummy' and 'roc_auc' in all_results.get(n, {})}
best_auc_name = max(non_dummy_aucs, key=non_dummy_aucs.get)
rf_auc = non_dummy_aucs.get('Random Forest', 0)
best_diff = non_dummy_aucs[best_auc_name] - rf_auc

if best_auc_name != 'Random Forest' and best_diff > 0.01:
    final_name = best_auc_name
else:
    final_name = 'Random Forest'

print(f"\nBest ROC-AUC: {best_auc_name} ({non_dummy_aucs[best_auc_name]:.4f})")
print(f"RF gap: {best_diff:.4f} (threshold: 0.01)")
print(f"Selected: {final_name}")

# Save best model
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

X_train, X_test = step1['X_train'], step1['X_test']
y_train, y_test = step1['y_train'], step1['y_test']

if final_name == 'Random Forest':
    final_pipe = pickle.load(open(str(BASE / 'src' / 'model_rf.pkl'), 'rb'))
elif final_name == 'LightGBM':
    final_pipe = pickle.load(open(str(BASE / 'src' / 'model_lgbm.pkl'), 'rb'))
elif final_name == 'XGBoost':
    final_pipe = pickle.load(open(str(BASE / 'src' / 'model_xgboost.pkl'), 'rb'))
elif final_name == 'Gradient Boosting':
    final_pipe = pickle.load(open(str(BASE / 'src' / 'model_gbm.pkl'), 'rb'))
else:
    final_pipe = pickle.load(open(str(BASE / 'src' / 'model_rf.pkl'), 'rb'))

pickle.dump({
    'model': final_pipe,
    'model_type': final_name,
    'random_state': 42,
}, open(str(MODEL_PATH), 'wb'))
print(f"Model saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")

# Model proxy (already generated, just verify)
import json
proxy = json.load(open(str(DASHBOARD_DIR / 'model_proxy.json')))
print(f"\nProxy coefs: intercept={proxy['coefficients']['intercept']:.4f}, "
      f"lad={proxy['coefficients']['last_activity_day']:.4f}, "
      f"ac={proxy['coefficients']['assessment_count']:.4f}, "
      f"sr={proxy['coefficients']['submission_rate']:.4f}")

# Save final consolidated results
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

final_results = convert({
    'all_results': all_results,
    'best_model': final_name,
    'best_model_roc_auc': all_results.get(final_name, {}).get('roc_auc', 0),
    'best_model_recall': all_results.get(final_name, {}).get('recall', 0),
})
json.dump(final_results, open(str(DATA_DIR / 'final_results.json'), 'w'), indent=2)
print(f"Final results saved: {DATA_DIR / 'final_results.json'}")
print("\nDone!")
