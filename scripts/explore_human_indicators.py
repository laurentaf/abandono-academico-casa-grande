"""Explorar dados OULAD para criar indicadores humanizados.
1. dias_sem_atividade = module_presentation_length - last_activity_day
2. dias_para_entregar = avg_submission_delta (dias de atraso medio)
3. nota_media = avg_assessment_score
"""
import duckdb
import numpy as np
from scipy import stats

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

print(f'Total students: {len(df):,}')

# Indicador 1: dias sem atividade no VLE
df['dias_sem_atividade'] = df['module_presentation_length'] - df['last_activity_day']
print(f'\n--- Indicador 1: Dias sem atividade VLE ---')
print(f'Range: {df.dias_sem_atividade.min():.0f} a {df.dias_sem_atividade.max():.0f}')
print(f'Mean: {df.dias_sem_atividade.mean():.1f}, Median: {df.dias_sem_atividade.median():.1f}')
print(f'Std: {df.dias_sem_atividade.std():.1f}')

# Percentis para sub-indices
for p in [10, 25, 50, 75, 90, 95, 99]:
    val = df.dias_sem_atividade.quantile(p/100)
    print(f'  {p}% dos alunos tem <= {val:.0f} dias sem atividade')

# "90% com <= 15 dias?" - qual o percentil de 15 dias?
pct_le_15 = (df.dias_sem_atividade <= 15).mean() * 100
print(f'  % com <= 15 dias sem atividade: {pct_le_15:.1f}%')

# Relacao com dropout
print(f'\n  Media dias sem atividade - dropout=0: {df[df.is_dropout==0].dias_sem_atividade.mean():.1f}')
print(f'  Media dias sem atividade - dropout=1: {df[df.is_dropout==1].dias_sem_atividade.mean():.1f}')

# Indicador 2: dias para entregar (avg_submission_delta)
print(f'\n--- Indicador 2: Dias para entrega de avaliacoes (avg_submission_delta) ---')
print(f'Range: {df.avg_submission_delta.min():.2f} a {df.avg_submission_delta.max():.2f}')
print(f'Mean: {df.avg_submission_delta.mean():.2f}, Median: {df.avg_submission_delta.median():.2f}')
print(f'Std: {df.avg_submission_delta.std():.2f}')

# Note: avg_submission_delta can be negative (early submissions)
# Let's check nulls
null_delta = df.avg_submission_delta.isnull().sum()
print(f'Nulls: {null_delta} ({null_delta/len(df)*100:.1f}%)')

# Fill nulls with median
df['avg_submission_delta'] = df['avg_submission_delta'].fillna(df.avg_submission_delta.median())

for p in [10, 25, 50, 75, 90, 95, 99]:
    val = df.avg_submission_delta.quantile(p/100)
    print(f'  {p}% dos alunos tem delta <= {val:.2f} dias')

# Positive = late, negative = early. For humanization, use absolute days late
# But the sign matters: more positive = more late = higher risk
# Let's use a proxy: "dias de atraso medio" (0 = no atraso, positivo = atrasado)
# For those who submit on average early (negative), treat as 0 delay
df['dias_atraso'] = df['avg_submission_delta'].clip(lower=0)
print(f'\n  Dias de atraso medio (>=0): mean={df.dias_atraso.mean():.2f}, median={df.dias_atraso.median():.2f}')
for p in [10, 25, 50, 75, 90, 95, 99]:
    val = df.dias_atraso.quantile(p/100)
    print(f'  {p}% dos alunos tem <= {val:.2f} dias de atraso')

# Relacao com dropout
print(f'\n  Media atraso - dropout=0: {df[df.is_dropout==0].dias_atraso.mean():.2f}')
print(f'  Media atraso - dropout=1: {df[df.is_dropout==1].dias_atraso.mean():.2f}')

# Indicador 3: nota media
print(f'\n--- Indicador 3: Nota media nas avaliacoes ---')
print(f'Range: {df.avg_assessment_score.min():.0f} a {df.avg_assessment_score.max():.0f}')
print(f'Mean: {df.avg_assessment_score.mean():.1f}, Median: {df.avg_assessment_score.median():.1f}')
null_score = df.avg_assessment_score.isnull().sum()
print(f'Nulls: {null_score} ({null_score/len(df)*100:.1f}%)')

# Fill nulls
df['avg_assessment_score'] = df['avg_assessment_score'].fillna(df.avg_assessment_score.median())

for p in [10, 25, 50, 75, 90, 95, 99]:
    val = df.avg_assessment_score.quantile(p/100)
    print(f'  {p}% dos alunos tem nota <= {val:.0f}')

print(f'\n  Media nota - dropout=0: {df[df.is_dropout==0].avg_assessment_score.mean():.1f}')
print(f'  Media nota - dropout=1: {df[df.is_dropout==1].avg_assessment_score.mean():.1f}')

# Percentile lookup functions
print('\n\n--- Percentile lookup tables (para dashboard) ---')

# For a GIVEN value, what % of students are BELOW or AT that value?
def percentile_lookup(col, values):
    """Return % of students with col <= each value"""
    return [(v, (df[col] <= v).mean() * 100) for v in values]

print('\ndias_sem_atividade:')
for v, pct in percentile_lookup('dias_sem_atividade', [0, 7, 15, 30, 60, 90, 120, 180, 270]):
    print(f'  <= {v:3.0f} dias: {pct:5.1f}% dos alunos')

print('\navg_submission_delta (dias atraso real, pode ser negativo):')
for v, pct in percentile_lookup('avg_submission_delta', [-30, -15, -7, 0, 7, 15, 30, 60]):
    print(f'  <= {v:+.0f} dias: {pct:5.1f}% dos alunos')

print('\navg_assessment_score:')
# For assessment score, we want % with score >= X (higher is better)
for v in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
    pct_ge = (df.avg_assessment_score >= v).mean() * 100
    print(f'  >= {v:2.0f} pts: {pct_ge:5.1f}% dos alunos')
