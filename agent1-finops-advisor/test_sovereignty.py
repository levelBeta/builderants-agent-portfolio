import socket
import threading
import time

from db import load_scenario
from explain import explain
from rules import run_rules
from sovereignty import LOOPBACK, SovereigntyMonitor

# 1. Positive control: a live loopback connection must be seen and labelled loopback.
srv = socket.socket()
srv.bind(("127.0.0.1", 0))
srv.listen(1)
port = srv.getsockname()[1]
threading.Thread(target=lambda: srv.accept(), daemon=True).start()

with SovereigntyMonitor() as m1:
    c = socket.create_connection(("127.0.0.1", port))
    time.sleep(0.6)
    c.close()
r1 = m1.report()
print("CONTROL passed:", r1["passed"], "| loopback seen:", len(r1["loopback_connections"]) > 0, "| samples:", r1["samples"])

# 2. Real run: one explanation call through Ollama.
finding = run_rules(load_scenario("data/flawed.csv"))[0]
with SovereigntyMonitor() as m2:
    result = explain(finding)
r2 = m2.report()
print("REAL RUN source:", result["source"])
print("REAL RUN passed:", r2["passed"], "| samples:", r2["samples"])
print("REAL RUN external:", r2["external_connections"])
print("REAL RUN loopback:", r2["loopback_connections"])
print("OLLAMA SERVER external:", r2["ollama_server_external"])
print("CLAIM:", r2["claim"])

# 3. Classification check on plain values.
print("LOOPBACK check:", "127.0.0.1" in LOOPBACK, "::1" in LOOPBACK, "8.8.8.8" in LOOPBACK)
