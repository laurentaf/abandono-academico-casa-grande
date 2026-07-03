"""Quick check that data is accessible."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import duckdb
import pandas as pd

con = duckdb.connect('artifacts/data/oulad.duckdb', read_only=True)
df = con.execute('SELECT COUNT(*) as cnt, AVG(is_dropout) as dropout_rate FROM gold_oulad_features').fetchdf()
msg = f"Rows: {df.iloc[0,0]}, Dropout rate: {df.iloc[0,1]:.3f}"
print(msg)
print("VERIFIED: oulad.duckdb OK")
con.close()
