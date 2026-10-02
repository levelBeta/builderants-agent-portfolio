import duckdb
from db import run_select, SQLGuardError

con = duckdb.connect(":memory:")
con.execute("CREATE TABLE t (x INTEGER)")
con.execute("INSERT INTO t VALUES (1),(2)")

tests = [
    "SELECT x FROM t WHERE x = 1",
    "SELECT * FROM t UNION SELECT * FROM t",
    "SELECT x FROM t WHERE x IN (SELECT x FROM t)",
    "SELECT x FROM t /* DROP */",
    "SELECT x FROM t WHERE 'a' = 'a' OR COPY",
    "SELECT * FROM read_csv('x.csv') ATTACH",
    "SELECT x INTO newtbl FROM t",
]
for q in tests:
    try:
        print(repr(q), "-> ALLOWED", run_select(con, q))
    except SQLGuardError as e:
        print(repr(q), "-> BLOCKED:", e)
    except Exception as e:
        print(repr(q), "-> DB ERROR (past the guard):", type(e).__name__)
