import time

from db import load_scenario
from explain import explain, SEVERITY_RE
from rules import run_rules

con = load_scenario("data/flawed.csv")
findings = run_rules(con)

seen = set()
samples = []
for f in findings:
    if f["rule_id"] not in seen:
        seen.add(f["rule_id"])
        samples.append(f)

for f in samples:
    start = time.time()
    result = explain(f)
    secs = time.time() - start
    sev = "SEVERITY WORD FOUND" if SEVERITY_RE.search(result["text"]) else "no severity words"
    print(f"[{f['rule_id']}] {f['resource_id']} | source={result['source']} | {secs:.1f}s | {sev} | note={result['note'] or '-'}")
    print(f"    {result['text']}")
