import duckdb
con = duckdb.connect('E:/projects/abandono-academico-casa-grande/artifacts/data/oulad.duckdb', read_only=True)
cols = con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='gold_oulad_features'").fetchall()
for c, t in cols:
    print(f'{c} ({t})')
con.close()
