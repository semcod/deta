# deta


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.2.32-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$5.10-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-5.9h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $5.1000 (34 commits)
- 👤 **Human dev:** ~$588 (5.9h @ $100/h, 30min dedup)

Generated on 2026-04-30 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Infrastructure anomaly detection and monitoring tool for development environments.

![PyPI](https://img.shields.io/badge/pypi-deta-blue) ![Version](https://img.shields.io/badge/version-0.2.32-blue) ![Python](https://img.shields.io/badge/python-3.8+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)

## Features

- **Manifest Scanning**: Scans docker-compose, OpenAPI, package.json, and pyproject.toml files up to 3 layers deep
- **Topology Building**: Builds service dependency graphs and detects anomalies
- **Real-time Monitoring**: Watches for config changes and probes HTTP health checks
- **Anomaly Detection**: Detects missing healthchecks, port conflicts, dependency cycles, and hardcoded secrets
- **Toon Format**: Generates Semcod-compatible toon output for ecosystem integration
- **CLI Interface**: Simple command-line interface with scan, monitor, and diff commands

## Installation

```bash
pip install deta
```

Or with optional dependencies:

```bash
pip install deta[docker,toml]
```

Jak uruchomić

Instalacja zależności web:
pip install 'deta[web]'
Start dashboardu:
deta web /home/tom/github/maskservice/c2004 --depth 3 --host 127.0.0.1 --port 8765
Otwórz:
http://127.0.0.1:8765


## Usage

### Scan infrastructure

```bash
deta scan /path/to/project --depth 3 --output infra-map.json
```

### Generate graph outputs (YAML / Mermaid / PNG)

```bash
# text graph + mermaid + json
deta scan /path/to/project --formats json,yaml,mermaid

# include online checks (localhost probes)
deta scan /path/to/project --formats json,yaml,mermaid --online

# try PNG (requires graphviz python package + graphviz binary)
deta scan /path/to/project --formats png
```

Generated files (configurable in `deta.yaml`):
- `infra-map.json`
- `infra-graph.yaml`
- `infra-graph.mmd`
- `infra-graph.png`
- `infra.toon.yaml`

### Monitor in real-time

```bash
deta monitor /path/to/project --interval 30 --depth 3
deta monitor . --interval 30 --depth 3

# realtime watch from scan command (regenerates outputs on each change)
deta scan /path/to/project --watch --formats json,yaml,mermaid --online
```

### Compare with baseline

```bash
deta diff --baseline infra-map.json /path/to/project
```

### Python API

```python
from pathlib import Path
from deta import build_topology

# Build topology from manifests
topology = build_topology(Path("/path/to/project"), max_depth=3)

# Detect anomalies
anomalies = topology.detect_anomalies()
for anomaly in anomalies:
    print(f"{anomaly['severity']}: {anomaly['type']}")

# Export to JSON
import json
output = json.loads(topology.to_json())
```

## Architecture

```
deta/
├── scanner/          # Manifest parsing
│   ├── compose.py    # docker-compose.yml
│   ├── openapi.py    # OpenAPI specs
│   ├── npm.py        # package.json
│   └── python.py     # pyproject.toml
├── builder/          # Topology construction
│   └── topology.py   # Graph & anomaly detection
├── monitor/          # Real-time monitoring
│   ├── watcher.py    # File watching
│   ├── prober.py     # HTTP health checks
│   └── alerter.py    # Colored output
├── formatter/        # Output formats
│   └── toon.py       # Semcod toon format
├── integration/      # Ecosystem hooks
│   └── semcod.py     # sumd, pyqual, vallm
└── cli.py            # Command-line interface
```

## Semcod Integration

deta integrates with the Semcod ecosystem:

```python
from deta.integration import generate_for_sumd, pre_deploy_check

# Generate toon for sumd
generate_for_sumd(Path("."), output=Path("infra.toon.yaml"))

# Pre-deployment validation
passed, issues = pre_deploy_check(Path("."))
if not passed:
    print("Deployment blocked:", issues)
```

## License

Licensed under Apache-2.0.
