"""Step 2: Train tree-based models (RF, GBM, XGBoost, LightGBM)"""
import sys, io, json, pickle, time, warnings
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

BASE = Path(r'E:\projects\abandono-academico-casa-grande')
DATA_DIR = BASE / 'artifacts' / 'data'

step1 = pickle.load(open(str(DATA_DIR / 'step1.pkl'), 'rb'))
X_train, X_test = step1['X_train'], step1['X_test']
y_train, y_test = step1['y_train'], step1['y_test']
prep = step1['prep']

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

neg, pos = np.bincount(y_train)

import xgboost as xgb
import lightgbm as lgb

models = {
    'RF': ('RandomForest', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1)),
    'GBM': ('GradientBoosting', GradientBoostingClassifier(n_estimators=200, random_state=42, max_depth=4, min_samples_split=5, min_samples_leaf=2)),
    'XGBoost': ('XGBoost', xgb.XGBClassifier(n_estimators=200, random_state=42, scale_pos_weight=neg/pos, max_depth=6, learning_rate=0.1, verbosity=0)),
    'LGBM': ('LightGBM', lgb.LGBMClassifier(n_estimators=200, random_state=42, class_weight='balanced', max_depth=-1, learning_rate=0.1, verbose=-1)),
}

results = {}
for short, (full_name, clf) in models.items():
    t0 = time.time()
    pipe = Pipeline([('prep', prep), ('clf', clf)])
    pipe.fit(X_train, y_train)
    dt = time.time() - t0

    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    results[full_name] = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'roc_auc': float(roc_auc_score(y_test, y_proba)),
        'train_time': dt,
    }
    r_acc, r_rec, r_auc = results[full_name]['accuracy'], results[full_name]['recall'], results[full_name]['roc_auc']
    print(f'{full_name}: acc={r_acc:.4f} rec={r_rec:.4f} auc={r_auc:.4f} t={dt:.1f}s')

    # Save individually
    pickle.dump(pipe, open(str(BASE / 'src' / f'model_{short.lower()}.pkl'), 'wb'))

# Save results
results['_tree_names'] = list(results.keys())
pickle.dump(results, open(str(DATA_DIR / 'step2_results.pkl'), 'wb'))
print(f'Step 2 complete. Models: {list(results.keys())}')
