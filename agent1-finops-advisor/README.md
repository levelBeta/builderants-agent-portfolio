# FinOps Waste & Savings Advisor (Agent 1)

A local, offline reference agent from the builderAnts agent portfolio. All data is synthetic, written for this project.

## Why it exists

Maps to builderAnts' Measurable ROI Outcomes pillar and its cost-savings work. It shows governed, read-only SQL analysis of a cloud bill, with a local LLM that only explains what the code has already decided.

## What it checks

Five deterministic rules, each a plain SQL SELECT:

- R1 Idle compute: running instances with average CPU under 5%.
- R2 Oversized instance: 2xlarge, 4xlarge or 8xlarge with CPU from 5% to under 20%.
- R3 Orphaned storage: volumes not attached to anything.
- R4 No reserved capacity: on-demand instances with CPU of 40% or more.
- R5 Abnormal egress: data transfer over 1,000 GB.

Savings are rough illustrative estimates: 100% of cost for R1 and R3, 50% for R2, a flat 30% for R4, and none estimated for R5.

## Architecture

- Synthetic cost CSV (flawed, partial or clean scenario)
- loaded into an in-memory DuckDB table
- every query passes the SELECT-only SQL guard
- deterministic rules engine produces findings
- explanation layer: code builds the facts and action, the local LLM rewords them
- reply checks, with a fixed template fallback
- hash-chained audit log entry per run and per finding
- all inside a process-scoped sovereignty monitor
- Streamlit UI

## Governance features

- **Detection is code, not the model.** The LLM never decides what counts as a finding. It only rewords a finding the rules engine has already produced.
- **SELECT-only SQL guard.** Every query must be a single SELECT. Write and admin keywords, file and network readers (such as read_csv), and INTO are blocked. Tested with three guard test scripts.
- **No severity words from the model.** Only the deterministic severity tag (HIGH, MEDIUM, LOW) carries that label. Replies containing severity words are rejected.
- **Reply checks.** A reply is rejected if it contains a number not in the facts, an instance size not in the facts, or no mention of the recommended action. Code, not the model, chooses the target size for a resize. A rejected reply gets one retry, then a fixed template sentence, labelled source=template.
- **Tamper-evident audit log.** JSONL, each entry hashed over its own content and the previous entry's hash. Verification resets to the recomputed hash and reports every entry from the first failure onward. Tested by editing entry 3 of 5: the check flagged lines 3, 4 and 5.
- **Process-scoped sovereignty check.** Samples TCP connections of this process and its children every 0.2 seconds while work runs. In the real run it observed no external connection in 36 samples, and only loopback connections to Ollama on port 11434. Ollama's own server process showed no external connections either, reported as supporting evidence only.
- **Compliance language.** Nothing here claims compliance with any named standard.

## Eval results

Run with `python eval.py`. Expected counts are hard-coded and were checked by hand against the CSV values.

| Scenario | Findings | By rule (R1 to R5) | Est. monthly saving |
|---|---|---|---|
| flawed | 20 | 4, 5, 4, 4, 3 | $3,931.00 |
| partial | 9 | 2, 1, 2, 2, 2 | $1,306.00 |
| clean | 0 | none | $0.00 |

The data includes boundary rows just inside and just outside each threshold. Before they were added, shifting the R1 threshold from 5 to 6 passed the eval unnoticed. After, the same shift fails the flawed scenario (21 findings, $4,491.00).

Model speed, 5 findings per model, warm-up excluded, measured on a CPU-only mini PC (approximate, small sample):

| Model | Avg per reply | LLM replies passing checks |
|---|---|---|
| llama3.2:3b | 3.1s | 4/5 |
| qwen2.5:3b (default) | 2.9s | 5/5 |
| qwen2.5:7b | 4.7s | 5/5 |

## How to run it

From the `agent1-finops-advisor` folder, with Python 3.12 and Ollama installed and the models `qwen2.5:3b`, `llama3.2:3b` and `qwen2.5:7b` pulled:

1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `python -m pip install -r requirements.txt`
4. `python generate_data.py` (regenerates the synthetic CSVs)
5. `python eval.py` (regression check and model speed comparison)
6. `streamlit run app.py` (the UI)

Before any real demo, delete `audit_log.jsonl` so the log starts empty. In a UI run with 20 findings, the sovereignty monitor took 312 samples and observed no external TCP connection.

## Limitations

- **Synthetic data only.** Nothing here has been run against a real cloud bill. Real billing exports have far more columns, services and edge cases.
- **Savings are rough.** The percentages are flat illustrative figures, not quotes, and R5 has no estimate at all.
- **Explanation checks are narrow.** They catch severity words, numbers or sizes not in the facts, and a missing action. They cannot catch an invented cause or a logical slip. In one UI run, an egress explanation confused a threshold with a cost. A reply can pass every check and still be subtly wrong.
- **Template fallbacks happen.** Some replies fall back to a fixed sentence, and the UI does not currently show why.
- **Small samples.** Speed figures use five findings per model on one machine. Two totals repeated to the decimal across runs, which I cannot explain, so treat the timings as approximate.
- **Sovereignty check is a sample, not proof.** It covers TCP only, takes snapshots every 0.2 seconds, and could miss a very short connection. Detection of an external connection was not tested live. Only the loopback classification and a loopback control were.
- **The claim is about one process.** It says this process tree made no external TCP connection. It says nothing about the rest of the machine.
- **Audit log scope.** It detects edits to the file after the fact. It does not stop someone deleting the whole log or rewriting every entry consistently.
- **Rules are simple.** Fixed thresholds, no seasonality or trend analysis, and boundary behaviour is only tested at the points listed in the data.
