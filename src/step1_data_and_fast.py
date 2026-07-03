"""Step 1: Load data, prep, train fast models (Dummy, LR)"""
import sys, io, json, pickle, time, warnings
from pathlib import Path
import numpy as np, duckdb
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

BASE = Path(r'E:\projects\abandono-academico-casa-grande')
DATA_DIR = BASE / 'artifacts' / 'data'
DUCKDB_PATH = DATA_DIR / 'oulad.duckdb'

con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
df = con.execute('SELECT * FROM gold_oulad_features').fetchdf()
con.close()

df['imd_band'] = df['imd_band'].fillna('Unknown')
nr = df['date_registration'].isnull().sum()
if nr > 0: df['date_registration'] = df['date_registration'].fillna(df['date_registration'].median())
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

X = df[CAT+NUM].copy()
y = df['is_dropout'].values
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

# Dummy
t0 = time.time()
dummy = Pipeline([('prep', prep), ('clf', DummyClassifier(strategy='stratified', random_state=42))])
dummy.fit(X_train, y_train)
dt = time.time() - t0
y_pred = dummy.predict(X_test)
results = {'Dummy': {'accuracy': float(accuracy_score(y_test, y_pred)), 'train_time': dt}}
dummy_acc = results['Dummy']['accuracy']
print(f'Dummy: acc={dummy_acc:.4f} t={dt:.3f}s')

# Logistic Regression
t0 = time.time()
lr = Pipeline([('prep', prep), ('clf', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42, C=1.0))])
lr.fit(X_train, y_train)
dt = time.time() - t0
y_pred = lr.predict(X_test)
y_proba = lr.predict_proba(X_test)[:, 1]
results['LR'] = {
    'accuracy': float(accuracy_score(y_test, y_pred)),
    'precision': float(precision_score(y_test, y_pred, zero_division=0)),
    'recall': float(recall_score(y_test, y_pred, zero_division=0)),
    'f1': float(f1_score(y_test, y_pred, zero_division=0)),
    'roc_auc': float(roc_auc_score(y_test, y_proba)),
    'train_time': dt,
}
lr_acc, lr_rec, lr_auc = results['LR']['accuracy'], results['LR']['recall'], results['LR']['roc_auc']
print(f'LR: acc={lr_acc:.4f} rec={lr_rec:.4f} auc={lr_auc:.4f} t={dt:.2f}s')

pickle.dump(lr, open(str(BASE / 'src' / 'model_lr.pkl'), 'wb'))
pickle.dump({'X_train': X_train, 'X_test': X_test, 'y_train': y_train, 'y_test': y_test, 'prep': prep,
             'CAT': CAT, 'NUM': NUM, 'results': results}, open(str(DATA_DIR / 'step1.pkl'), 'wb'))
print('Step 1 complete')
