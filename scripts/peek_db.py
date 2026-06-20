import sqlite3
import pandas as pd

con = sqlite3.connect("outputs/meyar.db")

tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("TABLES:", tables)

for t in tables:
    print(f"\n--- {t} ---")
    print(pd.read_sql(f"PRAGMA table_info({t})", con))
    print(f"\nfirst 3 rows of {t}:")
    print(pd.read_sql(f"SELECT * FROM {t} LIMIT 3", con))