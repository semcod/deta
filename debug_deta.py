import sys
from pathlib import Path

sys.path.insert(0, "/home/tom/github/semcod/deta")
from deta.builder.topology import build_topology

root_path = Path("/home/tom/github/maskservice/c2004")
topology = build_topology(root_path, max_depth=3)

for anomaly in topology.detect_anomalies():
    if anomaly["type"] == "missing_healthcheck":
        svc_name = anomaly["service"]
        svc = topology.services[svc_name]
        print(f"Missing healthcheck for {svc_name} defined in {svc.source_file}")
