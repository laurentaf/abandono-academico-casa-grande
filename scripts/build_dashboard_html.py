"""Generate dashboard HTML with proxy data embedded."""
import json

with open('E:/projects/abandono-academico-casa-grande/artifacts/dashboard/model_proxy.json', 'r', encoding='utf-8') as f:
    P = json.load(f)

proxy_json = json.dumps(P, ensure_ascii=False)

# Load template and replace placeholders
with open('scripts/dashboard_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('{{PROXY_JSON}}', proxy_json)
html = html.replace('{{N_STUDENTS}}', str(P['baseline_stats']['total_students']))
html = html.replace('{{BASELINE_RATE}}', str(P['baseline_stats']['baseline_rate']))
html = html.replace('{{BASELINE_AT_RISK}}', str(P['baseline_stats']['baseline_at_risk']))
html = html.replace('{{ROC_AUC}}', str(P['proxy_roc_auc']))
html = html.replace('{{DEF_LAD}}', str(int(P['feature_defaults']['dias_sem_atividade'])))
html = html.replace('{{DEF_DEL}}', str(int(P['feature_defaults']['avg_submission_delta'])))
html = html.replace('{{DEF_NOT}}', str(int(P['feature_defaults']['avg_assessment_score'])))

with open('E:/projects/abandono-academico-casa-grande/artifacts/dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Dashboard HTML gerado com sucesso!')
