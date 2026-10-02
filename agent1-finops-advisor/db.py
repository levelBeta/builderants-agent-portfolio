"""Governed, read-only SQL layer for Agent 1.
ALL DATA IS SYNTHETIC. Every query goes through run_select(), a SELECT-only allowlist.
"""
import csv
import re

import duckdb

FORBIDDEN = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "ATTACH",
    "DETACH", "COPY", "PRAGMA", "INSTALL", "LOAD", "EXPORT", "IMPORT",
    "TRUNCATE", "REPLACE", "CALL", "SET", "INTO",
]


class SQLGuardError(Exception):
    """Raised when a query is not a safe, single, read-only SELECT."""


def _strip_comments(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def validate_select(sql):
    """Return the cleaned query if it is a single read-only SELECT, else raise."""
    cleaned = _strip_comments(sql).strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()
    if ";" in cleaned:
        raise SQLGuardError("Multiple statements are not allowed.")
    if not re.match(r"(?i)^SELECT\b", cleaned):
        raise SQLGuardError("Only SELECT statements are allowed.")
    for word in FORBIDDEN:
        if re.search(rf"(?i)\b{word}\b", cleaned):
            raise SQLGuardError(f"Forbidden keyword in query: {word}")
    if re.search(r'(?i)\b(read_[a-z_]+|glob|parquet_scan|csv_scan|json_scan|http[a-z_]*)\s*\(', cleaned):
        raise SQLGuardError('File and network readers are not allowed.')
    return cleaned


def load_scenario(csv_path):
    """Load a scenario CSV into a fresh in-memory DuckDB connection."""
    con = duckdb.connect(":memory:")
    con.execute(
        """CREATE TABLE costs (
            resource_id VARCHAR, service VARCHAR, resource_type VARCHAR,
            region VARCHAR, instance_size VARCHAR, avg_cpu_pct DOUBLE,
            monthly_cost_usd DOUBLE, pricing_model VARCHAR,
            attached BOOLEAN, egress_gb DOUBLE)"""
    )
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            con.execute(
                "INSERT INTO costs VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    r["resource_id"], r["service"], r["resource_type"],
                    r["region"], r["instance_size"], float(r["avg_cpu_pct"]),
                    float(r["monthly_cost_usd"]), r["pricing_model"],
                    r["attached"].strip().lower() == "true",
                    float(r["egress_gb"]),
                ],
            )
    return con


def run_select(con, sql):
    """The only query path rules may use. Returns a list of dicts."""
    cleaned = validate_select(sql)
    cur = con.execute(cleaned)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


