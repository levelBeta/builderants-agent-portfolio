"""Agent 1 wiring: rules -> explanations -> audit log, inside the sovereignty monitor.
ALL DATA IS SYNTHETIC. The UI calls analyse() only. No detection logic lives here.
"""
from audit import append, verify
from db import load_scenario
from explain import _template, explain
from rules import run_rules
from sovereignty import SovereigntyMonitor

LOG_PATH = "audit_log.jsonl"


def analyse(scenario, use_llm=True, model="qwen2.5:3b", log_path=LOG_PATH):
    """Run one scenario end to end and return everything the UI needs."""
    con = load_scenario(f"data/{scenario}.csv")
    findings = run_rules(con)
    total = round(sum(f["est_monthly_saving_usd"] for f in findings), 2)
    append(log_path, "run_start", {"scenario": scenario, "findings": len(findings), "use_llm": use_llm})
    rows = []
    with SovereigntyMonitor() as mon:
        for f in findings:
            if use_llm:
                ex = explain(f, model=model)
            else:
                ex = {"text": _template(f), "source": "template", "model": model, "note": "llm skipped"}
            rows.append({**f, "explanation": ex["text"], "source": ex["source"], "note": ex["note"]})
            append(log_path, "finding", {
                "rule_id": f["rule_id"], "resource_id": f["resource_id"],
                "severity": f["severity"], "saving": f["est_monthly_saving_usd"],
                "source": ex["source"], "model": ex["model"],
            })
    sov = mon.report()
    append(log_path, "run_end", {"total_saving": total, "sovereignty_passed": sov["passed"], "samples": sov["samples"]})
    return {"scenario": scenario, "findings": rows, "total_saving": total,
            "sovereignty": sov, "audit": verify(log_path)}
