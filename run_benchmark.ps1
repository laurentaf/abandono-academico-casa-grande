# PowerShell script to run benchmark in stages
$Base = "E:\projects\abandono-academico-casa-grande"

Write-Host "Step 1: Loading data + light models (Dummy, LR)"
uv run python -u -c @"
import sys, io, json, pickle, time, warnings
from pathlib import Path
import numpy as np, pandas as pd, duckdb
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')
BASE = Path(r'E:\projects\abandono-academico-casa-grande')
DATA_DIR = BASE / 'artifacts' / 'data'
DUCKDB_PATH = DATA_DIR / 'oulad.duckdb'
MODEL_PATH = BASE / 'src' / 'model.pkl'

con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
df = con.execute('SELECT * FROM gold_oulad_features').fetchdf()
con.close()
print(f'Loaded: {len(df)} rows')

for c in ['imd_band']: df[c] = df[c].fillna('Unknown')
nr = df['date_registration'].isnull().sum()
if nr > 0: df['date_registration'] = df['date_registration'].fillna(df['date_registration'].median())
df['engagement_intensity'] = df['total_clicks'] / df['module_presentation_length'].replace(0, 1)
df['assessment_count'] = df['num_tma'] + df['num_cma'] + df['num_exams']
df['submission_rate'] = df['assessment_count'] / df['module_presentation_length'].replace(0, 1)

CAT = ['code_module','code_presentation','gender','region','highest_education','imd_band','age_band','disability']
NUM = ['num_of_prev_attempts','studied_credits','date_registration','total_clicks','days_active',
       'last_activity_day','first_activity_day','click_trend','avg_daily_clicks','weighted_avg_score',
       'num_tma','num_cma','num_exams','avg_assessment_score','avg_submission_delta',
       'module_presentation_length','engagement_intensity','assessment_count','submission_rate']
X = df[CAT+NUM].copy(); y = df['is_dropout'].values
for c in NUM: X[c] = X[c].fillna(0)
for c in CAT: X[c] = X[c].fillna('Unknown')

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
prep = ColumnTransformer([('num', StandardScaler(), NUM), ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CAT)])

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score

# Save preprocessed data
import joblib
joblib.dump({'X_train': X_train, 'X_test': X_test, 'y_train': y_train, 'y_test': y_test, 'prep': prep}, str(DATA_DIR / 'prepared_data.pkl'))
print('Preprocessed data saved')
"@ 2>&1
Write-Host "Step 1 complete" -ForegroundColor Green

Write-Host "Step 2: Tree-based models (RF, GBM, XGBoost, LightGBM)"
uv run python -u -c @"
import sys, io, json, pickle, time, warnings
from pathlib import Path
import numpy as np, joblib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')
BASE = Path(r'E:\projects\abandono-academico-casa-grande')
DATA_DIR = BASE / 'artifacts' / 'data'

data = joblib.load(str(DATA_DIR / 'prepared_data.pkl'))
X_train, X_test, y_train, y_test = data['X_train'], data['X_test'], data['y_train'], data['y_test']
prep = data['prep']

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
import xgboost as xgb, lightgbm as lgb
import warnings; warnings.filterwarnings('ignore')

models = {
    'RF': RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
    'GBM': GradientBoostingClassifier(n_estimators=200, random_state=42, max_depth=4, min_samples_split=5, min_samples_leaf=2),
}
neg, pos = np.bincount(y_train)
models['XGBoost'] = xgb.XGBClassifier(n_estimators=200, random_state=42, scale_pos_weight=neg/pos, max_depth=6, learning_rate=0.1, verbosity=0)
models['LGBM'] = lgb.LGBMClassifier(n_estimators=200, random_state=42, class_weight='balanced', max_depth=-1, learning_rate=0.1, verbose=-1)

results = {}
for name, clf in models.items():
    t0 = time.time()
    pipe = Pipeline([('prep', prep), ('clf', clf)])
    pipe.fit(X_train, y_train)
    dt = time.time() - t0
    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]
    results[name] = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'roc_auc': float(roc_auc_score(y_test, y_proba)),
        'train_time': dt,
    }
    print(f'{name}: acc={results[name][\"accuracy\"]:.4f} rec={results[name][\"recall\"]:.4f} auc={results[name][\"roc_auc\"]:.4f} t={dt:.1f}s')
    # Save model
    pickle.dump(pipe, open(str(BASE / 'src' / f'model_{name.lower()}.pkl'), 'wb'))

json.dump(results, open(str(DATA_DIR / 'tree_results.json'), 'w'), indent=2)
print('Tree models complete')
"@ 2>&1
Write-Host "Step 2 complete" -ForegroundColor Green

Write-Host "Step 3: Consolidate results"
uv run python -u -c @"
import sys, io, json, pickle
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = Path(r'E:\projects\abandono-academico-casa-grande')
DATA_DIR = BASE / 'artifacts' / 'data'

# Load individual results
lr_data = json.load(open(str(DATA_DIR / 'light_results.json')))
tree_data = json.load(open(str(DATA_DIR / 'tree_results.json')))
all_results = {**lr_data, **tree_data}

# Pick best (by ROC-AUC for non-Dummy)
non_dummy = {k:v for k,v in all_results.items() if k != 'Dummy'}
best_name = max(non_dummy, key=lambda k: non_dummy[k]['roc_auc'])
rf_auc = all_results.get('RF', {}).get('roc_auc', 0)

final_name = best_name if abs(non_dummy[best_name]['roc_auc'] - rf_auc) > 0.01 else 'RF'
all_results['_best_model'] = final_name

json.dump(all_results, open(str(DATA_DIR / 'full_results.json'), 'w'), indent=2)
print(f'Best: {final_name}')
for k,v in all_results.items():
    if k.startswith('_'): continue
    print(f'{k:12s}: acc={v.get(\"accuracy\",0):.4f} rec={v.get(\"recall\",0):.4f} auc={v.get(\"roc_auc\",0):.4f} t={v.get(\"train_time\",0):.1f}s')
"@ 2>&1
Write-Host "=== BENCHMARK COMPLETE ===" -ForegroundColor Green
