"""Deterministic rules engine for Agent 1.
ALL DATA IS SYNTHETIC. Detection is plain SQL via the SELECT-only guard.
The LLM never decides what counts as a finding. Savings are rough estimates.
"""
from db import run_select

# (rule_id, rule_name, severity, saving_fraction, SQL)
RULES = [
    (
        "R1", "Idle compute", "HIGH", 1.0,
        "SELECT resource_id, service, resource_type, region, instance_size, "
        "avg_cpu_pct, monthly_cost_usd, pricing_model, attached, egress_gb "
        "FROM costs WHERE resource_type = 'instance' AND avg_cpu_pct < 5 "
        "ORDER BY resource_id",
    ),
    (
        "R2", "Oversized instance", "MEDIUM", 0.5,
        "SELECT resource_id, service, resource_type, region, instance_size, "
        "avg_cpu_pct, monthly_cost_usd, pricing_model, attached, egress_gb "
        "FROM costs WHERE resource_type = 'instance' "
        "AND instance_size IN ('2xlarge', '4xlarge', '8xlarge') "
        "AND avg_cpu_pct >= 5 AND avg_cpu_pct < 20 "
        "ORDER BY resource_id",
    ),
    (
        "R3", "Orphaned storage", "HIGH", 1.0,
        "SELECT resource_id, service, resource_type, region, instance_size, "
        "avg_cpu_pct, monthly_cost_usd, pricing_model, attached, egress_gb "
        "FROM costs WHERE resource_type = 'volume' AND attached = false "
        "ORDER BY resource_id",
    ),
    (
        "R4", "No reserved capacity", "MEDIUM", 0.3,
        "SELECT resource_id, service, resource_type, region, instance_size, "
        "avg_cpu_pct, monthly_cost_usd, pricing_model, attached, egress_gb "
        "FROM costs WHERE resource_type = 'instance' "
        "AND pricing_model = 'on-demand' AND avg_cpu_pct >= 40 "
        "ORDER BY resource_id",
    ),
    (
        "R5", "Abnormal egress", "LOW", 0.0,
        "SELECT resource_id, service, resource_type, region, instance_size, "
        "avg_cpu_pct, monthly_cost_usd, pricing_model, attached, egress_gb "
        "FROM costs WHERE resource_type = 'data_transfer' AND egress_gb > 1000 "
        "ORDER BY resource_id",
    ),
]


def run_rules(con):
    """Run every rule and return a list of finding dicts."""
    findings = []
    for rule_id, rule_name, severity, fraction, sql in RULES:
        for r in run_select(con, sql):
            findings.append(
                {
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "severity": severity,
                    "resource_id": r["resource_id"],
                    "service": r["service"],
                    "region": r["region"],
                    "instance_size": r["instance_size"],
                    "avg_cpu_pct": r["avg_cpu_pct"],
                    "monthly_cost_usd": r["monthly_cost_usd"],
                    "pricing_model": r["pricing_model"],
                    "egress_gb": r["egress_gb"],
                    "est_monthly_saving_usd": round(r["monthly_cost_usd"] * fraction, 2),
                }
            )
    return findings
