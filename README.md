# deta


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.2.44-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$7.05-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-9.6h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $7.0500 (47 commits)
- 👤 **Human dev:** ~$957 (9.6h @ $100/h, 30min dedup)

Generated on 2026-05-04 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Infrastructure anomaly detection and monitoring tool for development environments.

![PyPI](https://img.shields.io/badge/pypi-deta-blue) ![Version](https://img.shields.io/badge/version-0.2.44-blue) ![Python](https://img.shields.io/badge/python-3.8+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)

## Features

- **Manifest Scanning**: Scans docker-compose, OpenAPI, package.json, and pyproject.toml files up to 3 layers deep
- **Environment Interpolation**: Full `${VAR:-default}` support with `.env` file layering and compose override merging
- **Port Parsing**: Resolves host/container port mappings with protocol and host-bind support
- **Topology Building**: Builds service dependency graphs with cycle detection and hub analysis
- **Anomaly Detection**: Detects missing healthchecks, port conflicts, dependency cycles, and hardcoded secrets
- **Real-time Monitoring**: Watches for config changes, probes HTTP/TCP health checks with concurrent probing
- **Web Dashboard**: Real-time FastAPI/WebSocket dashboard with topology visualization and event stream
- **DSL Change Tracking**: Structured change commands for service/port/probe state transitions
- **Topology Caching**: mtime-based cache with configurable TTL to avoid redundant rescans
- **Multi-format Output**: JSON, YAML graph, Mermaid, PNG (graphviz), and Semcod toon format
- **CLI Interface**: `scan`, `monitor`, `diff`, and `web` commands via argparse

## Installation

```bash
pip install deta
```

With optional dependencies:

```bash
# web dashboard (FastAPI + uvicorn + WebSocket)
pip install 'deta[web]'

# all extras
pip install deta[docker,toml,web]
```

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

### Web Dashboard

```bash
deta web /path/to/project --depth 3 --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765` — real-time topology view with WebSocket event push (service up/down, port changes).

Configuration in `deta.yaml`:

```yaml
web:
  enabled: true
  host: 127.0.0.1
  port: 8765
  refresh_seconds: 5
  cache_ttl_seconds: 30.0
  debounce_seconds: 0.5
  push_events:
    - service_added
    - service_removed
    - service_up
    - service_down
```

### Compare with baseline

```bash
deta diff --baseline infra-map.json /path/to/project
```

### Python API

```python
from pathlib import Path
from deta import build_topology, scan_compose, scan_openapi, probe_all

# Build topology from manifests
topology = build_topology(Path("/path/to/project"), max_depth=3)

# Detect anomalies
anomalies = topology.detect_anomalies()
for anomaly in anomalies:
    print(f"{anomaly['severity']}: {anomaly['type']}")

# Cycle & hub analysis
cycles = topology.detect_cycles()
hubs = topology.find_hubs(min_degree=3)

# Export to JSON
import json
output = json.loads(topology.to_json())

# Probe services
results = probe_all(topology.services, max_concurrency=20)
```

## Architecture

```
deta/
├── scanner/          # Manifest parsing
│   ├── compose.py    # docker-compose.yml (with override merging)
│   ├── openapi.py    # OpenAPI specs
│   ├── npm.py        # package.json
│   ├── python.py     # pyproject.toml & requirements.txt
│   ├── env.py        # .env file loading & interpolation
│   └── ports.py      # Port binding parsing & resolution
├── builder/          # Topology construction
│   ├── topology.py   # Graph, anomaly detection, cycles, hubs
│   └── cache.py      # mtime-based topology cache
├── monitor/          # Real-time monitoring
│   ├── watcher.py    # File change polling
│   ├── prober.py     # HTTP/TCP health checks (concurrent)
│   └── alerter.py    # Rich console output
├── formatter/        # Output formats
│   ├── graph.py      # YAML graph, Mermaid, PNG
│   └── toon.py       # Semcod toon format
├── dsl/              # Change tracking DSL
│   └── commands.py   # service_up/down, port_added/removed
├── web/              # Real-time dashboard
│   └── app.py        # FastAPI + WebSocket (topology, probes, events)
├── integration/      # Ecosystem hooks
│   └── semcod.py     # sumd, pyqual, vallm, pre_deploy_check
├── config.py         # deta.yaml configuration (Pydantic models)
├── core.py           # Base Wup class
└── cli.py            # CLI entry point (scan, monitor, diff, web)
```

## Configuration

Place `deta.yaml` in your project root. See [`deta.yaml.example`](deta.yaml.example) for all options:

- **scan** — depth, include/exclude patterns
- **watch** — file monitoring paths and patterns
- **anomaly** — toggle checks, secret patterns, severity levels
- **monitor** — interval, probe timeout/retries, concurrency
- **output** — formats and file paths
- **alert** — console colors, min severity
- **web** — dashboard host/port, refresh, cache TTL, push events

## Semcod Integration

deta integrates with the Semcod ecosystem:

```python
from pathlib import Path
from deta.integration import generate_for_sumd, generate_for_pyqual, generate_for_vallm, pre_deploy_check

# Generate toon for sumd
generate_for_sumd(Path("."), output=Path("infra.toon.yaml"))

# Quality analysis for pyqual
generate_for_pyqual(Path("."), depth=3)

# Validation for vallm
generate_for_vallm(Path("."), depth=3)

# Pre-deployment validation
passed, issues = pre_deploy_check(Path("."))
if not passed:
    print("Deployment blocked:", issues)
```

## Tests

```bash
pytest tests/ -v
```

Test coverage: cache invalidation, compose env interpolation, DSL commands, `.env` parsing, port parsing, monitor port display.

## License

Licensed under Apache-2.0.
