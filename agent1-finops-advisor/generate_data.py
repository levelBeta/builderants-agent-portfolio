"""Synthetic FinOps cost data generator for Agent 1.
ALL DATA IS SYNTHETIC. Written for this project. No real client or production data.
Resource IDs are prefixed "syn-" so that is obvious in every row.
"""
import csv
import os

COLUMNS = [
    "resource_id", "service", "resource_type", "region", "instance_size",
    "avg_cpu_pct", "monthly_cost_usd", "pricing_model", "attached", "egress_gb",
]


def row(rid, service, rtype, region, size, cpu, cost, pricing, attached, egress):
    return [rid, service, rtype, region, size, cpu, f"{cost:.2f}",
            pricing, "true" if attached else "false", egress]


AP2 = "ap-southeast-2"
AP1 = "ap-southeast-1"

# Healthy rows: present in every scenario. None of these should be flagged.
HEALTHY = [
    row("syn-i-001", "EC2", "instance", AP2, "large", 62.0, 140.00, "reserved", True, 20),
    row("syn-i-002", "EC2", "instance", AP2, "xlarge", 71.0, 280.00, "savings-plan", True, 35),
    row("syn-i-003", "EC2", "instance", AP2, "medium", 48.0, 70.00, "reserved", True, 12),
    row("syn-i-004", "EC2", "instance", AP2, "2xlarge", 66.0, 560.00, "reserved", True, 50),
    row("syn-i-005", "EC2", "instance", AP1, "large", 28.0, 140.00, "on-demand", True, 8),
    row("syn-i-006", "EC2", "instance", AP2, "small", 33.0, 35.00, "on-demand", True, 5),
    row("syn-v-001", "EBS", "volume", AP2, "n/a", 0.0, 40.00, "n/a", True, 0),
    row("syn-v-002", "EBS", "volume", AP2, "n/a", 0.0, 60.00, "n/a", True, 0),
    row("syn-v-003", "EBS", "volume", AP1, "n/a", 0.0, 25.00, "n/a", True, 0),
    row("syn-dt-001", "DataTransfer", "data_transfer", AP2, "n/a", 0.0, 90.00, "on-demand", True, 300),
    row("syn-dt-002", "DataTransfer", "data_transfer", AP2, "n/a", 0.0, 45.00, "on-demand", True, 150),
]

# Boundary rows just outside each threshold: must NOT fire.
HEALTHY += [
    row("syn-i-204", "EC2", "instance", AP2, "2xlarge", 20.0, 560.00, "reserved", True, 10),
    row("syn-i-206", "EC2", "instance", AP2, "large", 39.9, 140.00, "on-demand", True, 10),
    row("syn-dt-202", "DataTransfer", "data_transfer", AP2, "n/a", 0.0, 90.00, "on-demand", True, 1000),
]

# Problem rows: each one should trigger exactly one rule.
PROBLEMS = {
    # Rule 1: idle compute (CPU under 5)
    "syn-i-101": row("syn-i-101", "EC2", "instance", AP2, "xlarge", 1.2, 280.00, "on-demand", True, 4),
    "syn-i-102": row("syn-i-102", "EC2", "instance", AP2, "large", 2.5, 140.00, "on-demand", True, 3),
    "syn-i-103": row("syn-i-103", "EC2", "instance", AP1, "medium", 0.8, 70.00, "on-demand", True, 2),
    # Rule 2: oversized (2xlarge or bigger, CPU 5 to under 20)
    "syn-i-111": row("syn-i-111", "EC2", "instance", AP2, "4xlarge", 9.0, 1120.00, "on-demand", True, 25),
    "syn-i-112": row("syn-i-112", "EC2", "instance", AP2, "2xlarge", 14.0, 560.00, "on-demand", True, 18),
    "syn-i-113": row("syn-i-113", "EC2", "instance", AP2, "8xlarge", 17.5, 2240.00, "on-demand", True, 40),
    # Rule 3: orphaned storage (volume not attached)
    "syn-v-101": row("syn-v-101", "EBS", "volume", AP2, "n/a", 0.0, 80.00, "n/a", False, 0),
    "syn-v-102": row("syn-v-102", "EBS", "volume", AP2, "n/a", 0.0, 120.00, "n/a", False, 0),
    "syn-v-103": row("syn-v-103", "EBS", "volume", AP1, "n/a", 0.0, 45.00, "n/a", False, 0),
    "syn-v-104": row("syn-v-104", "EBS", "volume", AP2, "n/a", 0.0, 200.00, "n/a", False, 0),
    # Rule 4: no reserved capacity (steady CPU of 40+ still on-demand)
    "syn-i-121": row("syn-i-121", "EC2", "instance", AP2, "xlarge", 72.0, 280.00, "on-demand", True, 30),
    "syn-i-122": row("syn-i-122", "EC2", "instance", AP2, "large", 65.0, 140.00, "on-demand", True, 22),
    "syn-i-123": row("syn-i-123", "EC2", "instance", AP2, "2xlarge", 58.0, 560.00, "on-demand", True, 45),
    # Rule 5: abnormal egress (over 1000 GB)
    "syn-dt-101": row("syn-dt-101", "DataTransfer", "data_transfer", AP2, "n/a", 0.0, 216.00, "on-demand", True, 2400),
    "syn-dt-102": row("syn-dt-102", "DataTransfer", "data_transfer", AP2, "n/a", 0.0, 135.00, "on-demand", True, 1500),
}

# Boundary rows just inside each threshold: each fires exactly one rule.
PROBLEMS.update({
    "syn-i-201": row("syn-i-201", "EC2", "instance", AP2, "large", 4.9, 140.00, "on-demand", True, 5),
    "syn-i-202": row("syn-i-202", "EC2", "instance", AP2, "2xlarge", 5.0, 560.00, "on-demand", True, 5),
    "syn-i-203": row("syn-i-203", "EC2", "instance", AP2, "2xlarge", 19.9, 560.00, "on-demand", True, 5),
    "syn-i-205": row("syn-i-205", "EC2", "instance", AP2, "large", 40.0, 140.00, "on-demand", True, 5),
    "syn-dt-201": row("syn-dt-201", "DataTransfer", "data_transfer", AP2, "n/a", 0.0, 90.00, "on-demand", True, 1001),
})

# Partial: about half the waste has been fixed (those rows are gone from the bill).
PARTIAL_IDS = [
    "syn-i-101",
    "syn-i-111",
    "syn-v-101", "syn-v-102",
    "syn-i-121", "syn-i-122",
    "syn-dt-101",
]

PARTIAL_IDS += ["syn-i-201", "syn-dt-201"]

SCENARIOS = {
    "flawed": list(PROBLEMS.keys()),
    "partial": PARTIAL_IDS,
    "clean": [],
}


def write_scenario(name, problem_ids):
    rows = HEALTHY + [PROBLEMS[pid] for pid in problem_ids]
    path = os.path.join("data", f"{name}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"{path}: {len(rows)} rows")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    for scenario_name, ids in SCENARIOS.items():
        write_scenario(scenario_name, ids)
