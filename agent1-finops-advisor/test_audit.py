import json
import os

from audit import append, verify

PATH = "tamper_test.jsonl"
if os.path.exists(PATH):
    os.remove(PATH)

for i in range(1, 6):
    append(PATH, "test_event", {"n": i})

print("BEFORE TAMPER:", verify(PATH))

with open(PATH, encoding="utf-8") as f:
    lines = f.read().splitlines()
entry = json.loads(lines[2])
entry["data"]["n"] = 999
lines[2] = json.dumps(entry, sort_keys=True)
with open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

print("AFTER TAMPER: ", verify(PATH))

os.remove(PATH)
print("scratch log removed:", not os.path.exists(PATH))
