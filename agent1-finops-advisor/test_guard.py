import duckdb
from db import run_select, SQLGuardError

con = duckdb.connect(":memory:")
con.execute("CREATE TABLE t (x INTEGER)")
con.execute("INSERT INTO t VALUES (1),(2)")

tests = [
    "SELECT x FROM t",
    "DROP TABLE t",
    "SELECT 1; DROP TABLE t",
    "select x from t /* ok */ ; delete from t",
    "SELECT x FROM t -- harmless comment",
]
for q in tests:
    try:
        print(repr(q), "-> ALLOWED", run_select(con, q))
    except SQLGuardError as e:
        print(repr(q), "-> BLOCKED:", e)
