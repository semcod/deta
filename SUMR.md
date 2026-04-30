# deta

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `deta`
- **version**: `0.2.1`
- **python_requires**: `>=3.8`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(1), app.doql.less, goal.yaml, .env.example, src(3 mod), project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: deta;
  version: 0.2.1;
}

dependencies {
  runtime: "ruamel.yaml>=0.17.0, pyyaml>=6.0, pydantic>=2.0, httpx>=0.24.0, watchfiles>=0.20.0, networkx>=3.0, rich>=13.0, typer>=0.9.0";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="deta"] {

}

deploy {
  target: pip;
}

environment[name="local"] {
  runtime: python;
  env_file: .env;
  python_version: >=3.8;
}
```

### Source Modules

- `deta.cli`
- `deta.config`
- `deta.core`

## Dependencies

### Runtime

```text markpact:deps python
ruamel.yaml>=0.17.0
pyyaml>=6.0
pydantic>=2.0
httpx>=0.24.0
watchfiles>=0.20.0
networkx>=3.0
rich>=13.0
typer>=0.9.0
```

## Source Map

*Top 3 modules by symbol density — signatures for LLM orientation.*

### `deta.cli` (`deta/cli.py`)

```python
def _get_topology(root, depth, config)  # CC=1, fan=1
def _filter_anomalies(anomalies, config)  # CC=15, fan=2 ⚠
def _print_summary(topology, output, config)  # CC=4, fan=6
def _resolve_formats(formats, config)  # CC=4, fan=4
def _probe_once(topology)  # CC=5, fan=6
def _write_outputs(topology, config, output, formats, probe_results)  # CC=8, fan=9
def scan(root, depth, output, config, formats, online)  # CC=5, fan=9
def monitor(root, interval, depth, config, output, formats, online)  # CC=1, fan=3
def _monitor_loop(root, interval, depth, config, output, formats, online)  # CC=8, fan=16
def diff(baseline, root, config)  # CC=9, fan=13
def main()  # CC=2, fan=14
```

### `deta.config` (`deta/config.py`)

```python
def load_config(config_path)  # CC=4, fan=6
def _load_yaml(file_path)  # CC=7, fan=4
def _parse_config(data)  # CC=8, fan=8
class WatchConfig:  # Watch configuration for file monitoring.
class ScanConfig:  # Scan configuration.
class AnomalyConfig:  # Anomaly detection configuration.
class MonitorConfig:  # Real-time monitoring configuration.
class OutputConfig:  # Output configuration.
class AlertConfig:  # Alert configuration.
class DetaConfig:  # Main deta configuration.
```

### `deta.core` (`deta/core.py`)

```python
class Wup:  # Base class for wup operations.
    def __init__(name, dosage)  # CC=1
    def __repr__()  # CC=1
    def get_info()  # CC=2
```

## Call Graph

*48 nodes · 54 edges · 11 modules · CC̄=3.5*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `generate_toon` *(in deta.formatter.toon)* | 30 ⚠ | 1 | 58 | **59** |
| `_parse_config` *(in deta.config)* | 8 | 1 | 36 | **37** |
| `_monitor_loop` *(in deta.cli)* | 8 | 1 | 28 | **29** |
| `diff` *(in deta.cli)* | 9 | 1 | 27 | **28** |
| `_poll_configs` *(in deta.monitor.watcher)* | 16 ⚠ | 1 | 22 | **23** |
| `scan_python` *(in deta.scanner.python)* | 11 ⚠ | 1 | 20 | **21** |
| `print_topology_table` *(in deta.monitor.alerter)* | 8 | 1 | 19 | **20** |
| `generate_graph_yaml` *(in deta.formatter.graph)* | 11 ⚠ | 1 | 18 | **19** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/deta
# nodes: 48 | edges: 54 | modules: 11
# CC̄=3.5

HUBS[20]:
  deta.formatter.toon.generate_toon
    CC=30  in:1  out:58  total:59
  deta.config._parse_config
    CC=8  in:1  out:36  total:37
  deta.cli._monitor_loop
    CC=8  in:1  out:28  total:29
  deta.cli.diff
    CC=9  in:1  out:27  total:28
  deta.monitor.watcher._poll_configs
    CC=16  in:1  out:22  total:23
  deta.scanner.python.scan_python
    CC=11  in:1  out:20  total:21
  deta.monitor.alerter.print_topology_table
    CC=8  in:1  out:19  total:20
  deta.formatter.graph.generate_graph_yaml
    CC=11  in:1  out:18  total:19
  deta.formatter.graph.generate_mermaid
    CC=10  in:1  out:16  total:17
  deta.monitor.prober.probe_service
    CC=4  in:1  out:16  total:17
  deta.formatter.graph.save_png
    CC=12  in:1  out:15  total:16
  deta.monitor.prober._extract_health_url
    CC=16  in:1  out:14  total:15
  deta.cli._write_outputs
    CC=8  in:3  out:12  total:15
  deta.scanner.openapi.scan_openapi
    CC=12  in:0  out:14  total:14
  deta.cli._print_summary
    CC=4  in:2  out:11  total:13
  deta.monitor.alerter.alert_anomaly
    CC=2  in:2  out:10  total:12
  deta.config._load_yaml
    CC=7  in:1  out:11  total:12
  deta.scanner.python._parse_requirements
    CC=6  in:1  out:11  total:12
  deta.cli.scan
    CC=5  in:1  out:10  total:11
  deta.integration.semcod.pre_deploy_check
    CC=7  in:0  out:10  total:10

MODULES:
  deta.cli  [10 funcs]
    _filter_anomalies  CC=15  out:5
    _get_topology  CC=1  out:1
    _monitor_loop  CC=8  out:28
    _print_summary  CC=4  out:11
    _probe_once  CC=5  out:6
    _resolve_formats  CC=4  out:4
    _write_outputs  CC=8  out:12
    diff  CC=9  out:27
    monitor  CC=1  out:4
    scan  CC=5  out:10
  deta.config  [3 funcs]
    _load_yaml  CC=7  out:11
    _parse_config  CC=8  out:36
    load_config  CC=4  out:7
  deta.formatter.graph  [9 funcs]
    _parse_host_ports  CC=3  out:4
    _resolve_host_port  CC=8  out:7
    _safe_mermaid_id  CC=3  out:2
    _split_port_mapping  CC=7  out:5
    generate_graph_yaml  CC=11  out:18
    generate_mermaid  CC=10  out:16
    save_graph_yaml  CC=1  out:2
    save_mermaid  CC=1  out:2
    save_png  CC=12  out:15
  deta.formatter.toon  [2 funcs]
    generate_toon  CC=30  out:58
    save_toon  CC=1  out:2
  deta.integration.semcod  [4 funcs]
    generate_for_pyqual  CC=2  out:6
    generate_for_sumd  CC=1  out:4
    generate_for_vallm  CC=3  out:4
    pre_deploy_check  CC=7  out:10
  deta.monitor.alerter  [5 funcs]
    _get_console  CC=3  out:1
    alert_anomaly  CC=2  out:10
    alert_probe_failure  CC=4  out:3
    alert_probe_success  CC=2  out:3
    print_topology_table  CC=8  out:19
  deta.monitor.prober  [4 funcs]
    _extract_health_url  CC=16  out:14
    _split_port_mapping  CC=7  out:5
    probe_all  CC=2  out:2
    probe_service  CC=4  out:16
  deta.monitor.watcher  [3 funcs]
    _is_config_file  CC=2  out:4
    _poll_configs  CC=16  out:22
    watch_configs  CC=6  out:10
  deta.scanner.openapi  [2 funcs]
    _load  CC=6  out:8
    scan_openapi  CC=12  out:14
  deta.scanner.python  [3 funcs]
    _load_toml  CC=4  out:6
    _parse_requirements  CC=6  out:11
    scan_python  CC=11  out:20
  project.map.toon  [3 funcs]
    build_topology  CC=0  out:0
    load_config  CC=0  out:0
    probe_all  CC=0  out:0

EDGES:
  deta.monitor.alerter.alert_anomaly → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_failure → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_success → deta.monitor.alerter._get_console
  deta.monitor.alerter.print_topology_table → deta.monitor.alerter._get_console
  deta.scanner.python.scan_python → deta.scanner.python._load_toml
  deta.scanner.python.scan_python → deta.scanner.python._parse_requirements
  deta.scanner.openapi.scan_openapi → deta.scanner.openapi._load
  deta.integration.semcod.generate_for_sumd → project.map.toon.build_topology
  deta.integration.semcod.generate_for_sumd → deta.formatter.toon.save_toon
  deta.integration.semcod.generate_for_pyqual → deta.scanner.python.scan_python
  deta.integration.semcod.generate_for_vallm → project.map.toon.build_topology
  deta.integration.semcod.pre_deploy_check → project.map.toon.build_topology
  deta.formatter.toon.save_toon → deta.formatter.toon.generate_toon
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._is_config_file
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._poll_configs
  deta.formatter.graph._parse_host_ports → deta.formatter.graph._split_port_mapping
  deta.formatter.graph._parse_host_ports → deta.formatter.graph._resolve_host_port
  deta.formatter.graph.generate_graph_yaml → deta.formatter.graph._parse_host_ports
  deta.formatter.graph.save_graph_yaml → deta.formatter.graph.generate_graph_yaml
  deta.formatter.graph.generate_mermaid → deta.formatter.graph._safe_mermaid_id
  deta.formatter.graph.generate_mermaid → deta.formatter.graph._parse_host_ports
  deta.formatter.graph.save_mermaid → deta.formatter.graph.generate_mermaid
  deta.formatter.graph.save_png → deta.formatter.graph._parse_host_ports
  deta.cli._get_topology → project.map.toon.build_topology
  deta.cli._print_summary → deta.monitor.alerter.print_topology_table
  deta.cli._print_summary → deta.monitor.alerter.alert_anomaly
  deta.cli._probe_once → project.map.toon.probe_all
  deta.cli._probe_once → deta.monitor.alerter.alert_probe_success
  deta.cli._probe_once → deta.monitor.alerter.alert_probe_failure
  deta.cli._write_outputs → deta.formatter.toon.save_toon
  deta.cli._write_outputs → deta.formatter.graph.save_graph_yaml
  deta.cli._write_outputs → deta.formatter.graph.save_mermaid
  deta.cli._write_outputs → deta.formatter.graph.save_png
  deta.cli.scan → deta.cli._resolve_formats
  deta.cli.scan → deta.cli._get_topology
  deta.cli.scan → deta.cli._write_outputs
  deta.cli.scan → deta.cli._print_summary
  deta.cli.scan → project.map.toon.load_config
  deta.cli.scan → deta.cli._filter_anomalies
  deta.cli.scan → deta.cli._probe_once
  deta.cli.monitor → deta.cli._monitor_loop
  deta.cli._monitor_loop → deta.cli._resolve_formats
  deta.cli._monitor_loop → deta.cli._get_topology
  deta.cli._monitor_loop → deta.cli._filter_anomalies
  deta.cli._monitor_loop → deta.cli._write_outputs
  deta.cli._monitor_loop → deta.cli._print_summary
  deta.cli._monitor_loop → project.map.toon.load_config
  deta.cli.diff → project.map.toon.load_config
  deta.cli.diff → deta.cli._get_topology
  deta.config.load_config → deta.config._load_yaml
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/deta
# nodes: 48 | edges: 54 | modules: 11
# CC̄=3.5

HUBS[20]:
  deta.formatter.toon.generate_toon
    CC=30  in:1  out:58  total:59
  deta.config._parse_config
    CC=8  in:1  out:36  total:37
  deta.cli._monitor_loop
    CC=8  in:1  out:28  total:29
  deta.cli.diff
    CC=9  in:1  out:27  total:28
  deta.monitor.watcher._poll_configs
    CC=16  in:1  out:22  total:23
  deta.scanner.python.scan_python
    CC=11  in:1  out:20  total:21
  deta.monitor.alerter.print_topology_table
    CC=8  in:1  out:19  total:20
  deta.formatter.graph.generate_graph_yaml
    CC=11  in:1  out:18  total:19
  deta.formatter.graph.generate_mermaid
    CC=10  in:1  out:16  total:17
  deta.monitor.prober.probe_service
    CC=4  in:1  out:16  total:17
  deta.formatter.graph.save_png
    CC=12  in:1  out:15  total:16
  deta.monitor.prober._extract_health_url
    CC=16  in:1  out:14  total:15
  deta.cli._write_outputs
    CC=8  in:3  out:12  total:15
  deta.scanner.openapi.scan_openapi
    CC=12  in:0  out:14  total:14
  deta.cli._print_summary
    CC=4  in:2  out:11  total:13
  deta.monitor.alerter.alert_anomaly
    CC=2  in:2  out:10  total:12
  deta.config._load_yaml
    CC=7  in:1  out:11  total:12
  deta.scanner.python._parse_requirements
    CC=6  in:1  out:11  total:12
  deta.cli.scan
    CC=5  in:1  out:10  total:11
  deta.integration.semcod.pre_deploy_check
    CC=7  in:0  out:10  total:10

MODULES:
  deta.cli  [10 funcs]
    _filter_anomalies  CC=15  out:5
    _get_topology  CC=1  out:1
    _monitor_loop  CC=8  out:28
    _print_summary  CC=4  out:11
    _probe_once  CC=5  out:6
    _resolve_formats  CC=4  out:4
    _write_outputs  CC=8  out:12
    diff  CC=9  out:27
    monitor  CC=1  out:4
    scan  CC=5  out:10
  deta.config  [3 funcs]
    _load_yaml  CC=7  out:11
    _parse_config  CC=8  out:36
    load_config  CC=4  out:7
  deta.formatter.graph  [9 funcs]
    _parse_host_ports  CC=3  out:4
    _resolve_host_port  CC=8  out:7
    _safe_mermaid_id  CC=3  out:2
    _split_port_mapping  CC=7  out:5
    generate_graph_yaml  CC=11  out:18
    generate_mermaid  CC=10  out:16
    save_graph_yaml  CC=1  out:2
    save_mermaid  CC=1  out:2
    save_png  CC=12  out:15
  deta.formatter.toon  [2 funcs]
    generate_toon  CC=30  out:58
    save_toon  CC=1  out:2
  deta.integration.semcod  [4 funcs]
    generate_for_pyqual  CC=2  out:6
    generate_for_sumd  CC=1  out:4
    generate_for_vallm  CC=3  out:4
    pre_deploy_check  CC=7  out:10
  deta.monitor.alerter  [5 funcs]
    _get_console  CC=3  out:1
    alert_anomaly  CC=2  out:10
    alert_probe_failure  CC=4  out:3
    alert_probe_success  CC=2  out:3
    print_topology_table  CC=8  out:19
  deta.monitor.prober  [4 funcs]
    _extract_health_url  CC=16  out:14
    _split_port_mapping  CC=7  out:5
    probe_all  CC=2  out:2
    probe_service  CC=4  out:16
  deta.monitor.watcher  [3 funcs]
    _is_config_file  CC=2  out:4
    _poll_configs  CC=16  out:22
    watch_configs  CC=6  out:10
  deta.scanner.openapi  [2 funcs]
    _load  CC=6  out:8
    scan_openapi  CC=12  out:14
  deta.scanner.python  [3 funcs]
    _load_toml  CC=4  out:6
    _parse_requirements  CC=6  out:11
    scan_python  CC=11  out:20
  project.map.toon  [3 funcs]
    build_topology  CC=0  out:0
    load_config  CC=0  out:0
    probe_all  CC=0  out:0

EDGES:
  deta.monitor.alerter.alert_anomaly → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_failure → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_success → deta.monitor.alerter._get_console
  deta.monitor.alerter.print_topology_table → deta.monitor.alerter._get_console
  deta.scanner.python.scan_python → deta.scanner.python._load_toml
  deta.scanner.python.scan_python → deta.scanner.python._parse_requirements
  deta.scanner.openapi.scan_openapi → deta.scanner.openapi._load
  deta.integration.semcod.generate_for_sumd → project.map.toon.build_topology
  deta.integration.semcod.generate_for_sumd → deta.formatter.toon.save_toon
  deta.integration.semcod.generate_for_pyqual → deta.scanner.python.scan_python
  deta.integration.semcod.generate_for_vallm → project.map.toon.build_topology
  deta.integration.semcod.pre_deploy_check → project.map.toon.build_topology
  deta.formatter.toon.save_toon → deta.formatter.toon.generate_toon
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._is_config_file
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._poll_configs
  deta.formatter.graph._parse_host_ports → deta.formatter.graph._split_port_mapping
  deta.formatter.graph._parse_host_ports → deta.formatter.graph._resolve_host_port
  deta.formatter.graph.generate_graph_yaml → deta.formatter.graph._parse_host_ports
  deta.formatter.graph.save_graph_yaml → deta.formatter.graph.generate_graph_yaml
  deta.formatter.graph.generate_mermaid → deta.formatter.graph._safe_mermaid_id
  deta.formatter.graph.generate_mermaid → deta.formatter.graph._parse_host_ports
  deta.formatter.graph.save_mermaid → deta.formatter.graph.generate_mermaid
  deta.formatter.graph.save_png → deta.formatter.graph._parse_host_ports
  deta.cli._get_topology → project.map.toon.build_topology
  deta.cli._print_summary → deta.monitor.alerter.print_topology_table
  deta.cli._print_summary → deta.monitor.alerter.alert_anomaly
  deta.cli._probe_once → project.map.toon.probe_all
  deta.cli._probe_once → deta.monitor.alerter.alert_probe_success
  deta.cli._probe_once → deta.monitor.alerter.alert_probe_failure
  deta.cli._write_outputs → deta.formatter.toon.save_toon
  deta.cli._write_outputs → deta.formatter.graph.save_graph_yaml
  deta.cli._write_outputs → deta.formatter.graph.save_mermaid
  deta.cli._write_outputs → deta.formatter.graph.save_png
  deta.cli.scan → deta.cli._resolve_formats
  deta.cli.scan → deta.cli._get_topology
  deta.cli.scan → deta.cli._write_outputs
  deta.cli.scan → deta.cli._print_summary
  deta.cli.scan → project.map.toon.load_config
  deta.cli.scan → deta.cli._filter_anomalies
  deta.cli.scan → deta.cli._probe_once
  deta.cli.monitor → deta.cli._monitor_loop
  deta.cli._monitor_loop → deta.cli._resolve_formats
  deta.cli._monitor_loop → deta.cli._get_topology
  deta.cli._monitor_loop → deta.cli._filter_anomalies
  deta.cli._monitor_loop → deta.cli._write_outputs
  deta.cli._monitor_loop → deta.cli._print_summary
  deta.cli._monitor_loop → project.map.toon.load_config
  deta.cli.diff → project.map.toon.load_config
  deta.cli.diff → deta.cli._get_topology
  deta.config.load_config → deta.config._load_yaml
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 34f 4499L | python:18,yaml:11,shell:2,json:1,toml:1,txt:1 | 2026-04-30
# CC̄=3.5 | critical:4/97 | dups:0 | cycles:0

HEALTH[4]:
  🟡 CC    generate_toon CC=30 (limit:15)
  🟡 CC    _poll_configs CC=16 (limit:15)
  🟡 CC    _filter_anomalies CC=15 (limit:15)
  🟡 CC    _extract_health_url CC=16 (limit:15)

REFACTOR[1]:
  1. split 4 high-CC methods  (CC>15)

PIPELINES[11]:
  [1] Src [scan_npm]: scan_npm
      PURITY: 100% pure
  [2] Src [scan_openapi]: scan_openapi → _load
      PURITY: 100% pure
  [3] Src [scan_compose]: scan_compose → _parse_ports
      PURITY: 100% pure
  [4] Src [generate_for_sumd]: generate_for_sumd → build_topology
      PURITY: 100% pure
  [5] Src [generate_for_pyqual]: generate_for_pyqual → scan_python → _load_toml
      PURITY: 100% pure

LAYERS:
  deta/                           CC̄=6.1    ←in:0  →out:24  !! split
  │ !! cli                        344L  0C   11m  CC=15     ←0
  │ config                     235L  7C    3m  CC=8      ←0
  │ graph                      193L  0C    9m  CC=12     ←1
  │ !! prober                     161L  1C    4m  CC=16     ←0
  │ !! toon                       131L  0C    2m  CC=30     ←2
  │ compose                    130L  1C    5m  CC=11     ←0
  │ semcod                     129L  0C    4m  CC=7      ←0
  │ !! watcher                    110L  0C    3m  CC=16     ←0
  │ python                     102L  0C    3m  CC=11     ←1
  │ alerter                     99L  0C    5m  CC=8      ←1
  │ openapi                     89L  1C    2m  CC=12     ←0
  │ npm                         45L  0C    1m  CC=5      ←0
  │ core                        26L  1C    3m  CC=2      ←0
  │ __init__                    23L  0C    0m  CC=0.0    ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ __init__                    18L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ calls.yaml                 371L  0C    0m  CC=0.0    ←0
  │ calls.toon.yaml            120L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              119L  0C   42m  CC=0.0    ←2
  │ analysis.toon.yaml          66L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           57L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         51L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  49L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml        9L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! infra-map.json             757L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ infra-graph.yaml           241L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              81L  0C    0m  CC=0.0    ←0
  │ infra.toon.yaml             68L  0C    0m  CC=0.0    ←0
  │ project.sh                  50L  0C    0m  CC=0.0    ←0
  │ scan-infra.sh               37L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                deta       project.map      deta.monitor    deta.formatter  deta.integration      deta.scanner
              deta                ──                11                 9                 4                                      !! fan-out
       project.map               ←11                ──                                                    ←3                    hub
      deta.monitor                ←9                                  ──                                                        hub
    deta.formatter                ←4                                                    ──                ←1                    hub
  deta.integration                                   3                                   1                ──                 1
      deta.scanner                                                                                        ←1                ──
  CYCLES: none
  HUB: deta.formatter/ (fan-in=5)
  HUB: deta.monitor/ (fan-in=9)
  HUB: project.map/ (fan-in=14)
  SMELL: deta/ fan-out=24 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 2 groups | 19f 1932L | 2026-04-30

SUMMARY:
  files_scanned: 19
  total_lines:   1932
  dup_groups:    2
  dup_fragments: 4
  saved_lines:   23
  scan_ms:       4552

HOTSPOTS[2] (files with most duplication):
  deta/formatter/graph.py  dup=29L  groups=2  frags=3  (1.5%)
  deta/monitor/prober.py  dup=17L  groups=1  frags=1  (0.9%)

DUPLICATES[2] (ranked by impact):
  [1f55f99cef41a53e]   EXAC  _split_port_mapping  L=17 N=2 saved=17 sim=1.00
      deta/formatter/graph.py:11-27  (_split_port_mapping)
      deta/monitor/prober.py:24-40  (_split_port_mapping)
  [b78b4f28f5959a4a]   STRU  save_graph_yaml  L=6 N=2 saved=6 sim=1.00
      deta/formatter/graph.py:106-111  (save_graph_yaml)
      deta/formatter/graph.py:149-154  (save_mermaid)

REFACTOR[2] (ranked by priority):
  [1] ○ extract_function   → deta/utils/_split_port_mapping.py
      WHY: 2 occurrences of 17-line block across 2 files — saves 17 lines
      FILES: deta/formatter/graph.py, deta/monitor/prober.py
  [2] ○ extract_function   → deta/formatter/utils/save_graph_yaml.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: deta/formatter/graph.py

QUICK_WINS[2] (low risk, high savings — do first):
  [1] extract_function   saved=17L  → deta/utils/_split_port_mapping.py
      FILES: graph.py, prober.py
  [2] extract_function   saved=6L  → deta/formatter/utils/save_graph_yaml.py
      FILES: graph.py

EFFORT_ESTIMATE (total ≈ 0.8h):
  medium _split_port_mapping                 saved=17L  ~34min
  easy   save_graph_yaml                     saved=6L  ~12min

METRICS-TARGET:
  dup_groups:  2 → 0
  saved_lines: 23 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 97 func | 14f | 2026-04-30

NEXT[4] (ranked by impact):
  [1] !! SPLIT-FUNC      generate_toon  CC=30  fan=16
      WHY: CC=30 exceeds 15
      EFFORT: ~1h  IMPACT: 480

  [2] !  SPLIT-FUNC      _poll_configs  CC=16  fan=12
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 192

  [3] !  SPLIT-FUNC      _extract_health_url  CC=16  fan=12
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 192

  [4] !  SPLIT-FUNC      _filter_anomalies  CC=15  fan=3
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 45


RISKS[0]: none

METRICS-TARGET:
  CC̄:          3.5 → ≤2.4
  max-CC:      30 → ≤15
  god-modules: 0 → 0
  high-CC(≥15): 4 → ≤2
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=5.9 → now CC̄=3.5
```

## Intent

Infrastructure anomaly detection and monitoring tool
