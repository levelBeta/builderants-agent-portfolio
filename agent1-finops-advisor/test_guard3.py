import duckdb
from db import run_select, SQLGuardError

con = duckdb.connect(":memory:")
con.execute("CREATE TABLE t (x INTEGER)")
con.execute("INSERT INTO t VALUES (1),(2)")

tests = [
    "SELECT * FROM read_csv('x.csv')",
    "SELECT * FROM read_parquet('x.parquet')",
    "SELECT * FROM glob('*')",
    "SELECT x FROM t",
]
for q in tests:
    try:
        print(repr(q), "-> ALLOWED", run_select(con, q))
    except SQLGuardError as e:
        print(repr(q), "-> BLOCKED:", e)
    except Exception as e:
        print(repr(q), "-> DB ERROR (past the guard):", type(e).__name__)
