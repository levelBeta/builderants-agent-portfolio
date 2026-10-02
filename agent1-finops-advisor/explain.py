"""LLM explanation layer for Agent 1.
ALL DATA IS SYNTHETIC. The LLM only explains a finding; it never decides one.
Code builds the facts, the recommended action and any target size. The model only rewords them.
Replies are rejected if they use severity words, numbers or instance sizes not in the facts,
or if they leave out the recommended action.
"""
import re

import ollama

DEFAULT_MODEL = "qwen2.5:3b"

SEVERITY_WORDS = ["critical", "high", "medium", "low", "severe", "urgent", "major", "minor"]
SEVERITY_RE = re.compile(r"(?i)\b(" + "|".join(SEVERITY_WORDS) + r")\b")
NUM_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?!\w)")
SIZE_RE = re.compile(r"(?i)\b(?:\d+x)?x?large\b|\bnano\b|\bmicro\b|\bsmall\b|\bmedium\b")

# Code, not the model, decides the target size for a resize.
NEXT_SIZE_DOWN = {"2xlarge": "xlarge", "4xlarge": "2xlarge", "8xlarge": "4xlarge"}

# Keyword that must appear in a reply, so the recommended action is never dropped.
REQUIRED_ACTION = {
    "R1": r"(?i)\bterminat",
    "R2": r"(?i)\bresiz",
    "R3": r"(?i)\bsnapshot",
    "R4": r"(?i)\breserved|savings plan",
    "R5": r"(?i)\binvestigat",
}

SYSTEM_PROMPT = (
    "You rewrite a cloud cost finding as one or two plain English sentences. "
    "The finding and the recommended action are already decided and given to you. "
    "State them using ONLY the facts provided, and include every step of the recommended action. "
    "Never contradict the finding. "
    "Do not add numbers, causes, benefits or risks that are not listed. "
    "Do not comment on whether the resource is used or what it costs beyond the figures given. "
    "Do not use any severity or priority words such as critical, high, medium, "
    "low, severe, urgent, major or minor. Do not use bullet points or headings."
)


def _facts(f):
    """Deterministic facts and action for one finding. No LLM involved."""
    rid, region = f["resource_id"], f["region"]
    cost = f"${f['monthly_cost_usd']:,.2f}"
    saving = f"${f['est_monthly_saving_usd']:,.2f}"
    rule = f["rule_id"]
    if rule == "R1":
        return (
            f"Finding: {rid} is a {f['service']} instance (size {f['instance_size']}) in {region} "
            f"with average CPU of {f['avg_cpu_pct']}%, below the 5% idle threshold.\n"
            f"Monthly cost: {cost}. Estimated monthly saving if removed: {saving}.\n"
            "Recommended action: confirm it is unused and terminate it."
        )
    if rule == "R2":
        target = NEXT_SIZE_DOWN.get(f["instance_size"], "a smaller size")
        return (
            f"Finding: {rid} is a {f['instance_size']} instance in {region} "
            f"whose average CPU is {f['avg_cpu_pct']}%, so most of its capacity is unused.\n"
            f"Monthly cost: {cost}. Estimated monthly saving: {saving} (assumes one size down).\n"
            f"Recommended action: resize it from {f['instance_size']} to {target}."
        )
    if rule == "R3":
        return (
            f"Finding: {rid} is a storage volume in {region} that is not attached to any instance.\n"
            f"Monthly cost: {cost}. Estimated monthly saving: {saving} (its full cost).\n"
            "Recommended action: snapshot it if the data matters, then delete it."
        )
    if rule == "R4":
        return (
            f"Finding: {rid} is a {f['instance_size']} instance in {region} running on on-demand "
            f"pricing with steady average CPU of {f['avg_cpu_pct']}%.\n"
            f"Monthly cost: {cost}. Estimated monthly saving: {saving} "
            "(a flat 30% illustrative discount).\n"
            "Recommended action: move it to reserved capacity or a savings plan."
        )
    return (
        f"Finding: {rid} is data transfer in {region} with {f['egress_gb']:,.0f} GB of egress, "
        "above the 1,000 GB threshold.\n"
        f"Monthly cost: {cost}. No saving is estimated.\n"
        "Recommended action: investigate what is driving the data transfer."
    )


def _numbers(text):
    return {float(m.rstrip(",").replace(",", "")) for m in NUM_RE.findall(text)}


def _sizes(text):
    return {m.lower() for m in SIZE_RE.findall(text)}


def _template(f):
    """Fixed fallback sentence built only from the finding's fields."""
    return (
        f"{f['resource_id']} ({f['rule_name'].lower()}) has an estimated saving of "
        f"${f['est_monthly_saving_usd']:,.2f} per month."
    )


def explain(finding, model=DEFAULT_MODEL):
    """Return {'text', 'source': 'llm' or 'template', 'model', 'note'}."""
    facts = _facts(finding)
    allowed_nums = _numbers(facts)
    allowed_sizes = _sizes(facts)
    required = REQUIRED_ACTION[finding["rule_id"]]
    note = ""
    feedback = ""
    try:
        for _ in range(2):
            resp = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": facts + feedback + "\n\nWrite the recommendation."},
                ],
                options={"temperature": 0},
            )
            text = resp.message.content.strip()
            if not text:
                note = "empty reply"
            elif SEVERITY_RE.search(text):
                note = "severity word in reply"
            elif not _numbers(text) <= allowed_nums:
                note = "number not in facts"
            elif not _sizes(text) <= allowed_sizes:
                note = "instance size not in facts"
            elif not re.search(required, text):
                note = "recommended action missing"
            else:
                return {"text": text, "source": "llm", "model": model, "note": ""}
            feedback = f"\n\nYour previous reply was rejected: {note}. Rewrite it and fix that."
    except Exception as e:
        note = f"ollama error: {type(e).__name__}"
    return {"text": _template(finding), "source": "template", "model": model, "note": note}
