"""Regression eval for Agent 1.
ALL DATA IS SYNTHETIC. Expected results are hard-coded and were verified by hand
against the CSV values. Any change in the rules, thresholds or data fails this script.
"""
import sys
import time
from collections import Counter

from db import load_scenario
from explain import explain
from rules import run_rules

EXPECTED = {
    "flawed": {"total": 20, "by_rule": {"R1": 4, "R2": 5, "R3": 4, "R4": 4, "R5": 3}, "saving": 3931.00},
    "partial": {"total": 9, "by_rule": {"R1": 2, "R2": 1, "R3": 2, "R4": 2, "R5": 2}, "saving": 1306.00},
    "clean": {"total": 0, "by_rule": {}, "saving": 0.00},
}


def check_regression():
    """Return True if every scenario matches its hard-coded expectation."""
    all_ok = True
    for name, exp in EXPECTED.items():
        findings = run_rules(load_scenario(f"data/{name}.csv"))
        got = {
            "total": len(findings),
            "by_rule": dict(Counter(f["rule_id"] for f in findings)),
            "saving": round(sum(f["est_monthly_saving_usd"] for f in findings), 2),
        }
        ok = got == exp
        all_ok = all_ok and ok
        print(f"{name}: {'PASS' if ok else 'FAIL'} | got {got['total']} findings, ${got['saving']:,.2f}")
        if not ok:
            print(f"    expected {exp}")
            print(f"    got      {got}")
    return all_ok


MODELS = ["llama3.2:3b", "qwen2.5:3b", "qwen2.5:7b"]


def first_of_each_rule(findings):
    seen, picks = set(), []
    for f in findings:
        if f["rule_id"] not in seen:
            seen.add(f["rule_id"])
            picks.append(f)
    return picks


def speed_comparison():
    """Time explain() per model on one finding from each rule. Warm-up call excluded."""
    picks = first_of_each_rule(run_rules(load_scenario("data/flawed.csv")))
    print()
    print("MODEL SPEED COMPARISON (5 findings per model, warm-up excluded)")
    for model in MODELS:
        explain(picks[0], model=model)
        times, llm_ok = [], 0
        for f in picks:
            start = time.time()
            result = explain(f, model=model)
            times.append(time.time() - start)
            if result["source"] == "llm":
                llm_ok += 1
        avg = sum(times) / len(times)
        print(f"{model}: avg {avg:.1f}s | total {sum(times):.1f}s | llm replies {llm_ok}/5")


if __name__ == "__main__":
    print("REGRESSION CHECK")
    ok = check_regression()
    if ok:
        speed_comparison()
    print()
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
