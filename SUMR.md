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
- **version**: `0.2.23`
- **python_requires**: `>=3.8`
- **license**: {'text': 'Apache-2.0'}
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
  version: 0.2.23;
}

dependencies {
  runtime: "ruamel.yaml>=0.17.0, pyyaml>=6.0, pydantic>=2.0, httpx>=0.24.0, watchfiles>=0.20.0, networkx>=3.0, rich>=13.0, typer>=0.9.0";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
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
def _port_in_use(host, port)  # CC=1, fan=3
def _pid_on_port(host, port)  # CC=11, fan=6 ⚠
def _terminate_pid(pid)  # CC=2, fan=1
def _get_topology(root, depth, config)  # CC=1, fan=1
def _filter_anomalies(anomalies, config)  # CC=15, fan=2 ⚠
def _print_summary(topology, output, config)  # CC=4, fan=6
def _resolve_formats(formats, config)  # CC=4, fan=4
def _probe_once(topology)  # CC=5, fan=6
def _write_outputs(topology, config, output, formats, probe_results)  # CC=8, fan=9
def scan(root, depth, output, config, formats, online)  # CC=5, fan=9
def monitor(root, interval, depth, config, output, formats, online)  # CC=1, fan=3
def _extract_ports_snapshot(topology)  # CC=3, fan=2
def _log_port_changes(old_snapshot, new_snapshot)  # CC=4, fan=6
def _print_status_summary(topology, probe_results)  # CC=11, fan=7 ⚠
def _monitor_loop(root, interval, depth, config, output, formats, online)  # CC=7, fan=27
def diff(baseline, root, config)  # CC=9, fan=13
def main()  # CC=2, fan=20
```

### `deta.config` (`deta/config.py`)

```python
def load_config(config_path)  # CC=4, fan=6
def _load_yaml(file_path)  # CC=7, fan=4
def _parse_config(data)  # CC=9, fan=9
class WatchConfig:  # Watch configuration for file monitoring.
class ScanConfig:  # Scan configuration.
class AnomalyConfig:  # Anomaly detection configuration.
class MonitorConfig:  # Real-time monitoring configuration.
class OutputConfig:  # Output configuration.
class AlertConfig:  # Alert configuration.
class WebConfig:  # Web dashboard configuration.
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

*93 nodes · 96 edges · 16 modules · CC̄=2.4*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `create_app` *(in deta.web.app)* | 5 | 1 | 113 | **114** |
| `_monitor_loop` *(in deta.cli)* | 7 | 1 | 48 | **49** |
| `_parse_config` *(in deta.config)* | 9 | 1 | 44 | **45** |
| `diff` *(in deta.cli)* | 9 | 1 | 27 | **28** |
| `generate_mermaid` *(in deta.formatter.graph)* | 17 ⚠ | 1 | 23 | **24** |
| `_build_service_def` *(in deta.scanner.compose)* | 5 | 1 | 23 | **24** |
| `generate_graph_yaml` *(in deta.formatter.graph)* | 23 ⚠ | 1 | 22 | **23** |
| `generate_toon` *(in deta.formatter.toon)* | 2 | 1 | 21 | **22** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/deta
# nodes: 93 | edges: 96 | modules: 16
# CC̄=2.4

HUBS[20]:
  deta.web.app.create_app
    CC=5  in:1  out:113  total:114
  deta.cli._monitor_loop
    CC=7  in:1  out:48  total:49
  deta.config._parse_config
    CC=9  in:1  out:44  total:45
  deta.cli.diff
    CC=9  in:1  out:27  total:28
  deta.formatter.graph.generate_mermaid
    CC=17  in:1  out:23  total:24
  deta.scanner.compose._build_service_def
    CC=5  in:1  out:23  total:24
  deta.formatter.graph.generate_graph_yaml
    CC=23  in:1  out:22  total:23
  deta.formatter.toon.generate_toon
    CC=2  in:1  out:21  total:22
  deta.scanner.python.scan_python
    CC=11  in:1  out:20  total:21
  deta.monitor.alerter.print_topology_table
    CC=8  in:1  out:19  total:20
  deta.monitor.prober.probe_service
    CC=8  in:1  out:17  total:18
  deta.monitor.prober.probe_port
    CC=7  in:1  out:16  total:17
  deta.formatter.graph.save_png
    CC=15  in:0  out:17  total:17
  deta.scanner.env.load_env_file
    CC=12  in:2  out:14  total:16
  deta.cli._write_outputs
    CC=8  in:3  out:12  total:15
  deta.scanner.ports.parse_port
    CC=10  in:2  out:12  total:14
  deta.scanner.openapi.scan_openapi
    CC=12  in:0  out:14  total:14
  deta.monitor.prober.probe_all
    CC=11  in:0  out:14  total:14
  deta.dsl.commands.format_port_changes
    CC=16  in:1  out:12  total:13
  deta.cli._print_summary
    CC=4  in:2  out:11  total:13

MODULES:
  deta.cli  [10 funcs]
    _filter_anomalies  CC=15  out:5
    _get_topology  CC=1  out:1
    _monitor_loop  CC=7  out:48
    _print_summary  CC=4  out:11
    _probe_once  CC=5  out:6
    _resolve_formats  CC=4  out:4
    _write_outputs  CC=8  out:12
    diff  CC=9  out:27
    monitor  CC=1  out:4
    scan  CC=5  out:10
  deta.config  [3 funcs]
    _load_yaml  CC=7  out:11
    _parse_config  CC=9  out:44
    load_config  CC=4  out:7
  deta.dsl.commands  [8 funcs]
    _escape_value  CC=4  out:2
    format_port_changes  CC=16  out:12
    format_service_changes  CC=4  out:8
    port_added  CC=2  out:3
    port_removed  CC=2  out:3
    service_added  CC=1  out:3
    service_down  CC=3  out:5
    service_removed  CC=1  out:3
  deta.formatter.graph  [8 funcs]
    _safe_mermaid_id  CC=3  out:2
    _save_output  CC=1  out:1
    _service_bindings  CC=2  out:1
    generate_graph_yaml  CC=23  out:22
    generate_mermaid  CC=17  out:23
    save_graph_yaml  CC=1  out:2
    save_mermaid  CC=1  out:2
    save_png  CC=15  out:17
  deta.formatter.toon  [9 funcs]
    _format_alert_line  CC=5  out:6
    _format_alerts  CC=3  out:6
    _format_endpoint_line  CC=1  out:2
    _format_endpoints  CC=5  out:9
    _format_service_line  CC=4  out:2
    _format_services  CC=2  out:4
    _group_endpoints_by_service  CC=3  out:1
    generate_toon  CC=2  out:21
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
  deta.monitor.prober  [7 funcs]
    _extract_health_url  CC=11  out:9
    _extract_host_port_from_url  CC=4  out:2
    _first_resolved_binding  CC=6  out:1
    _get_client  CC=4  out:2
    probe_all  CC=11  out:14
    probe_port  CC=7  out:16
    probe_service  CC=8  out:17
  deta.monitor.watcher  [6 funcs]
    _detect_change_type  CC=8  out:0
    _emit_changes  CC=3  out:10
    _is_config_file  CC=2  out:4
    _poll_configs  CC=2  out:4
    _scan_file_mtimes  CC=4  out:3
    watch_configs  CC=6  out:10
  deta.scanner.compose  [11 funcs]
    _build_service_def  CC=5  out:23
    _collect_compose_files  CC=6  out:10
    _deep_merge  CC=5  out:5
    _find_primary_source  CC=4  out:4
    _get_yaml_loader  CC=2  out:1
    _load_yaml_file  CC=5  out:3
    _merge_services  CC=5  out:6
    _parse_env  CC=6  out:4
    _parse_ports  CC=7  out:7
    _resolve_env_files  CC=7  out:6
  deta.scanner.env  [5 funcs]
    discover_env  CC=4  out:9
    interpolate  CC=3  out:6
    interpolate_recursive  CC=6  out:7
    load_env_file  CC=12  out:14
    merge_env_files  CC=2  out:4
  deta.scanner.openapi  [2 funcs]
    _load  CC=6  out:8
    scan_openapi  CC=12  out:14
  deta.scanner.ports  [4 funcs]
    _split_top_level  CC=6  out:8
    parse_port  CC=10  out:12
    parse_ports  CC=4  out:1
    published_url  CC=4  out:1
  deta.scanner.python  [3 funcs]
    _load_toml  CC=4  out:6
    _parse_requirements  CC=6  out:11
    scan_python  CC=11  out:20
  deta.web.app  [2 funcs]
    create_app  CC=5  out:113
    run_dashboard  CC=5  out:6
  project.map.toon  [6 funcs]
    build_topology  CC=0  out:0
    load_config  CC=0  out:0
    probe_all  CC=0  out:0
    save_graph_yaml  CC=0  out:0
    save_mermaid  CC=0  out:0
    save_png  CC=0  out:0

EDGES:
  deta.monitor.alerter.alert_anomaly → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_failure → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_success → deta.monitor.alerter._get_console
  deta.monitor.alerter.print_topology_table → deta.monitor.alerter._get_console
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._is_config_file
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._poll_configs
  deta.monitor.watcher._emit_changes → deta.monitor.watcher._detect_change_type
  deta.monitor.watcher._poll_configs → deta.monitor.watcher._scan_file_mtimes
  deta.monitor.watcher._poll_configs → deta.monitor.watcher._emit_changes
  deta.scanner.python.scan_python → deta.scanner.python._load_toml
  deta.scanner.python.scan_python → deta.scanner.python._parse_requirements
  deta.scanner.ports.parse_port → deta.scanner.env.interpolate
  deta.scanner.ports.parse_port → deta.scanner.ports._split_top_level
  deta.scanner.ports.parse_ports → deta.scanner.ports.parse_port
  deta.scanner.openapi.scan_openapi → deta.scanner.openapi._load
  deta.scanner.compose._merge_services → deta.scanner.compose._load_yaml_file
  deta.scanner.compose._merge_services → deta.scanner.compose._deep_merge
  deta.scanner.compose._find_primary_source → deta.scanner.compose._load_yaml_file
  deta.scanner.compose._build_service_def → deta.scanner.env.discover_env
  deta.scanner.compose._build_service_def → deta.scanner.compose._resolve_env_files
  deta.scanner.compose._build_service_def → deta.scanner.env.merge_env_files
  deta.scanner.compose._build_service_def → deta.scanner.compose._parse_env
  deta.scanner.compose._build_service_def → deta.scanner.compose._parse_ports
  deta.scanner.compose._build_service_def → deta.scanner.ports.parse_ports
  deta.scanner.compose._build_service_def → deta.scanner.env.interpolate_recursive
  deta.scanner.compose._build_service_def → deta.scanner.compose._find_primary_source
  deta.scanner.compose.scan_compose → deta.scanner.compose._get_yaml_loader
  deta.scanner.compose.scan_compose → deta.scanner.compose._collect_compose_files
  deta.scanner.compose.scan_compose → deta.scanner.compose._merge_services
  deta.scanner.compose.scan_compose → deta.scanner.compose._build_service_def
  deta.scanner.env.discover_env → deta.scanner.env.load_env_file
  deta.scanner.env.merge_env_files → deta.scanner.env.load_env_file
  deta.scanner.env.interpolate_recursive → deta.scanner.env.interpolate
  deta.integration.semcod.generate_for_sumd → project.map.toon.build_topology
  deta.integration.semcod.generate_for_sumd → deta.formatter.toon.save_toon
  deta.integration.semcod.generate_for_pyqual → deta.scanner.python.scan_python
  deta.integration.semcod.generate_for_vallm → project.map.toon.build_topology
  deta.integration.semcod.pre_deploy_check → project.map.toon.build_topology
  deta.dsl.commands.service_down → deta.dsl.commands._escape_value
  deta.dsl.commands.format_port_changes → deta.dsl.commands.port_added
  deta.dsl.commands.format_port_changes → deta.dsl.commands.port_removed
  deta.dsl.commands.format_service_changes → deta.dsl.commands.service_added
  deta.dsl.commands.format_service_changes → deta.dsl.commands.service_removed
  deta.formatter.toon._format_alerts → deta.formatter.toon._format_alert_line
  deta.formatter.toon._format_services → deta.formatter.toon._format_service_line
  deta.formatter.toon._format_endpoints → deta.formatter.toon._group_endpoints_by_service
  deta.formatter.toon._format_endpoints → deta.formatter.toon._format_endpoint_line
  deta.formatter.toon.save_toon → deta.formatter.toon.generate_toon
  deta.formatter.graph._service_bindings → deta.scanner.ports.parse_ports
  deta.formatter.graph.generate_graph_yaml → deta.formatter.graph._service_bindings
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
# nodes: 93 | edges: 96 | modules: 16
# CC̄=2.4

HUBS[20]:
  deta.web.app.create_app
    CC=5  in:1  out:113  total:114
  deta.cli._monitor_loop
    CC=7  in:1  out:48  total:49
  deta.config._parse_config
    CC=9  in:1  out:44  total:45
  deta.cli.diff
    CC=9  in:1  out:27  total:28
  deta.formatter.graph.generate_mermaid
    CC=17  in:1  out:23  total:24
  deta.scanner.compose._build_service_def
    CC=5  in:1  out:23  total:24
  deta.formatter.graph.generate_graph_yaml
    CC=23  in:1  out:22  total:23
  deta.formatter.toon.generate_toon
    CC=2  in:1  out:21  total:22
  deta.scanner.python.scan_python
    CC=11  in:1  out:20  total:21
  deta.monitor.alerter.print_topology_table
    CC=8  in:1  out:19  total:20
  deta.monitor.prober.probe_service
    CC=8  in:1  out:17  total:18
  deta.monitor.prober.probe_port
    CC=7  in:1  out:16  total:17
  deta.formatter.graph.save_png
    CC=15  in:0  out:17  total:17
  deta.scanner.env.load_env_file
    CC=12  in:2  out:14  total:16
  deta.cli._write_outputs
    CC=8  in:3  out:12  total:15
  deta.scanner.ports.parse_port
    CC=10  in:2  out:12  total:14
  deta.scanner.openapi.scan_openapi
    CC=12  in:0  out:14  total:14
  deta.monitor.prober.probe_all
    CC=11  in:0  out:14  total:14
  deta.dsl.commands.format_port_changes
    CC=16  in:1  out:12  total:13
  deta.cli._print_summary
    CC=4  in:2  out:11  total:13

MODULES:
  deta.cli  [10 funcs]
    _filter_anomalies  CC=15  out:5
    _get_topology  CC=1  out:1
    _monitor_loop  CC=7  out:48
    _print_summary  CC=4  out:11
    _probe_once  CC=5  out:6
    _resolve_formats  CC=4  out:4
    _write_outputs  CC=8  out:12
    diff  CC=9  out:27
    monitor  CC=1  out:4
    scan  CC=5  out:10
  deta.config  [3 funcs]
    _load_yaml  CC=7  out:11
    _parse_config  CC=9  out:44
    load_config  CC=4  out:7
  deta.dsl.commands  [8 funcs]
    _escape_value  CC=4  out:2
    format_port_changes  CC=16  out:12
    format_service_changes  CC=4  out:8
    port_added  CC=2  out:3
    port_removed  CC=2  out:3
    service_added  CC=1  out:3
    service_down  CC=3  out:5
    service_removed  CC=1  out:3
  deta.formatter.graph  [8 funcs]
    _safe_mermaid_id  CC=3  out:2
    _save_output  CC=1  out:1
    _service_bindings  CC=2  out:1
    generate_graph_yaml  CC=23  out:22
    generate_mermaid  CC=17  out:23
    save_graph_yaml  CC=1  out:2
    save_mermaid  CC=1  out:2
    save_png  CC=15  out:17
  deta.formatter.toon  [9 funcs]
    _format_alert_line  CC=5  out:6
    _format_alerts  CC=3  out:6
    _format_endpoint_line  CC=1  out:2
    _format_endpoints  CC=5  out:9
    _format_service_line  CC=4  out:2
    _format_services  CC=2  out:4
    _group_endpoints_by_service  CC=3  out:1
    generate_toon  CC=2  out:21
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
  deta.monitor.prober  [7 funcs]
    _extract_health_url  CC=11  out:9
    _extract_host_port_from_url  CC=4  out:2
    _first_resolved_binding  CC=6  out:1
    _get_client  CC=4  out:2
    probe_all  CC=11  out:14
    probe_port  CC=7  out:16
    probe_service  CC=8  out:17
  deta.monitor.watcher  [6 funcs]
    _detect_change_type  CC=8  out:0
    _emit_changes  CC=3  out:10
    _is_config_file  CC=2  out:4
    _poll_configs  CC=2  out:4
    _scan_file_mtimes  CC=4  out:3
    watch_configs  CC=6  out:10
  deta.scanner.compose  [11 funcs]
    _build_service_def  CC=5  out:23
    _collect_compose_files  CC=6  out:10
    _deep_merge  CC=5  out:5
    _find_primary_source  CC=4  out:4
    _get_yaml_loader  CC=2  out:1
    _load_yaml_file  CC=5  out:3
    _merge_services  CC=5  out:6
    _parse_env  CC=6  out:4
    _parse_ports  CC=7  out:7
    _resolve_env_files  CC=7  out:6
  deta.scanner.env  [5 funcs]
    discover_env  CC=4  out:9
    interpolate  CC=3  out:6
    interpolate_recursive  CC=6  out:7
    load_env_file  CC=12  out:14
    merge_env_files  CC=2  out:4
  deta.scanner.openapi  [2 funcs]
    _load  CC=6  out:8
    scan_openapi  CC=12  out:14
  deta.scanner.ports  [4 funcs]
    _split_top_level  CC=6  out:8
    parse_port  CC=10  out:12
    parse_ports  CC=4  out:1
    published_url  CC=4  out:1
  deta.scanner.python  [3 funcs]
    _load_toml  CC=4  out:6
    _parse_requirements  CC=6  out:11
    scan_python  CC=11  out:20
  deta.web.app  [2 funcs]
    create_app  CC=5  out:113
    run_dashboard  CC=5  out:6
  project.map.toon  [6 funcs]
    build_topology  CC=0  out:0
    load_config  CC=0  out:0
    probe_all  CC=0  out:0
    save_graph_yaml  CC=0  out:0
    save_mermaid  CC=0  out:0
    save_png  CC=0  out:0

EDGES:
  deta.monitor.alerter.alert_anomaly → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_failure → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_success → deta.monitor.alerter._get_console
  deta.monitor.alerter.print_topology_table → deta.monitor.alerter._get_console
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._is_config_file
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._poll_configs
  deta.monitor.watcher._emit_changes → deta.monitor.watcher._detect_change_type
  deta.monitor.watcher._poll_configs → deta.monitor.watcher._scan_file_mtimes
  deta.monitor.watcher._poll_configs → deta.monitor.watcher._emit_changes
  deta.scanner.python.scan_python → deta.scanner.python._load_toml
  deta.scanner.python.scan_python → deta.scanner.python._parse_requirements
  deta.scanner.ports.parse_port → deta.scanner.env.interpolate
  deta.scanner.ports.parse_port → deta.scanner.ports._split_top_level
  deta.scanner.ports.parse_ports → deta.scanner.ports.parse_port
  deta.scanner.openapi.scan_openapi → deta.scanner.openapi._load
  deta.scanner.compose._merge_services → deta.scanner.compose._load_yaml_file
  deta.scanner.compose._merge_services → deta.scanner.compose._deep_merge
  deta.scanner.compose._find_primary_source → deta.scanner.compose._load_yaml_file
  deta.scanner.compose._build_service_def → deta.scanner.env.discover_env
  deta.scanner.compose._build_service_def → deta.scanner.compose._resolve_env_files
  deta.scanner.compose._build_service_def → deta.scanner.env.merge_env_files
  deta.scanner.compose._build_service_def → deta.scanner.compose._parse_env
  deta.scanner.compose._build_service_def → deta.scanner.compose._parse_ports
  deta.scanner.compose._build_service_def → deta.scanner.ports.parse_ports
  deta.scanner.compose._build_service_def → deta.scanner.env.interpolate_recursive
  deta.scanner.compose._build_service_def → deta.scanner.compose._find_primary_source
  deta.scanner.compose.scan_compose → deta.scanner.compose._get_yaml_loader
  deta.scanner.compose.scan_compose → deta.scanner.compose._collect_compose_files
  deta.scanner.compose.scan_compose → deta.scanner.compose._merge_services
  deta.scanner.compose.scan_compose → deta.scanner.compose._build_service_def
  deta.scanner.env.discover_env → deta.scanner.env.load_env_file
  deta.scanner.env.merge_env_files → deta.scanner.env.load_env_file
  deta.scanner.env.interpolate_recursive → deta.scanner.env.interpolate
  deta.integration.semcod.generate_for_sumd → project.map.toon.build_topology
  deta.integration.semcod.generate_for_sumd → deta.formatter.toon.save_toon
  deta.integration.semcod.generate_for_pyqual → deta.scanner.python.scan_python
  deta.integration.semcod.generate_for_vallm → project.map.toon.build_topology
  deta.integration.semcod.pre_deploy_check → project.map.toon.build_topology
  deta.dsl.commands.service_down → deta.dsl.commands._escape_value
  deta.dsl.commands.format_port_changes → deta.dsl.commands.port_added
  deta.dsl.commands.format_port_changes → deta.dsl.commands.port_removed
  deta.dsl.commands.format_service_changes → deta.dsl.commands.service_added
  deta.dsl.commands.format_service_changes → deta.dsl.commands.service_removed
  deta.formatter.toon._format_alerts → deta.formatter.toon._format_alert_line
  deta.formatter.toon._format_services → deta.formatter.toon._format_service_line
  deta.formatter.toon._format_endpoints → deta.formatter.toon._group_endpoints_by_service
  deta.formatter.toon._format_endpoints → deta.formatter.toon._format_endpoint_line
  deta.formatter.toon.save_toon → deta.formatter.toon.generate_toon
  deta.formatter.graph._service_bindings → deta.scanner.ports.parse_ports
  deta.formatter.graph.generate_graph_yaml → deta.formatter.graph._service_bindings
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 43f 7831L | python:24,yaml:11,yml:3,shell:2,json:1,txt:1,toml:1 | 2026-04-30
# CC̄=2.4 | critical:8/264 | dups:0 | cycles:2

HEALTH[8]:
  🟡 CC    format_probe_change CC=15 (limit:15)
  🟡 CC    format_port_changes CC=16 (limit:15)
  🟡 CC    generate_graph_yaml CC=23 (limit:15)
  🟡 CC    generate_mermaid CC=17 (limit:15)
  🟡 CC    save_png CC=15 (limit:15)
  🟡 CC    _filter_anomalies CC=15 (limit:15)
  🟡 CC    _topology_json_with_status CC=17 (limit:15)
  🟡 CC    _compute_events CC=22 (limit:15)

REFACTOR[2]:
  1. split 8 high-CC methods  (CC>15)
  2. break 2 circular dependencies

PIPELINES[20]:
  [1] Src [scan_npm]: scan_npm
      PURITY: 100% pure
  [2] Src [scan_openapi]: scan_openapi → _load
      PURITY: 100% pure
  [3] Src [scan_compose]: scan_compose → _get_yaml_loader
      PURITY: 100% pure
  [4] Src [generate_for_sumd]: generate_for_sumd → build_topology
      PURITY: 100% pure
  [5] Src [generate_for_pyqual]: generate_for_pyqual → scan_python → _load_toml
      PURITY: 100% pure

LAYERS:
  deta/                           CC̄=5.2    ←in:0  →out:30  !! split
  │ !! app                       1004L  1C   12m  CC=22     ←0
  │ !! cli                        533L  0C   17m  CC=15     ←0
  │ prober                     299L  1C    9m  CC=11     ←1
  │ compose                    278L  1C   13m  CC=7      ←0
  │ config                     272L  8C    3m  CC=9      ←0
  │ !! commands                   255L  1C   12m  CC=16     ←1
  │ !! graph                      199L  0C    9m  CC=23     ←0
  │ toon                       182L  0C   13m  CC=5      ←2
  │ env                        140L  0C    5m  CC=12     ←2
  │ semcod                     129L  0C    4m  CC=7      ←0
  │ watcher                    116L  0C    6m  CC=8      ←2
  │ ports                      116L  1C    4m  CC=10     ←3
  │ python                     102L  0C    3m  CC=11     ←1
  │ alerter                     99L  0C    5m  CC=8      ←1
  │ openapi                     89L  1C    2m  CC=12     ←0
  │ npm                         45L  0C    1m  CC=5      ←0
  │ __init__                    40L  0C    0m  CC=0.0    ←0
  │ core                        26L  1C    3m  CC=2      ←0
  │ __init__                    23L  0C    0m  CC=0.0    ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ __init__                    18L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                1185L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              255L  0C  143m  CC=0.0    ←3
  │ calls.toon.yaml            202L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         104L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         68L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           51L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml       43L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! infra-map.json             757L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ infra-graph.yaml           241L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              84L  0C    0m  CC=0.0    ←0
  │ infra.toon.yaml             68L  0C    0m  CC=0.0    ←0
  │ project.sh                  48L  0C    0m  CC=0.0    ←0
  │ scan-infra.sh               37L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=0.0    ←in:0  →out:0
  │ docker-compose.yml          38L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          28L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          17L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                deta       project.map      deta.monitor      deta.scanner          deta.web  deta.integration          deta.dsl    deta.formatter
              deta                ──                15                10                                                                       4                 1  !! fan-out
       project.map               ←15                ──                                                    ←6                ←3                                      hub
      deta.monitor               ←10                                  ──                 6                ←2                                                        hub
      deta.scanner                                                    ←6                ──                                  ←1                                  ←1  hub
          deta.web                                   6                 2                                  ──                                                        !! fan-out
  deta.integration                                   3                                   1                                  ──                                   1
          deta.dsl                ←4                                                                                                          ──                  
    deta.formatter                ←1                                                     1                                  ←1                                  ──
  CYCLES: 2
  HUB: deta.scanner/ (fan-in=8)
  HUB: project.map/ (fan-in=24)
  HUB: deta.monitor/ (fan-in=12)
  SMELL: deta.web/ fan-out=8 → split needed
  SMELL: deta/ fan-out=30 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 2 groups | 25f 4036L | 2026-04-30

SUMMARY:
  files_scanned: 25
  total_lines:   4036
  dup_groups:    2
  dup_fragments: 4
  saved_lines:   15
  scan_ms:       2936

HOTSPOTS[2] (files with most duplication):
  deta/dsl/commands.py  dup=18L  groups=1  frags=2  (0.4%)
  deta/formatter/graph.py  dup=12L  groups=1  frags=2  (0.3%)

DUPLICATES[2] (ranked by impact):
  [966af33370a97c1c]   STRU  port_added  L=9 N=2 saved=9 sim=1.00
      deta/dsl/commands.py:73-81  (port_added)
      deta/dsl/commands.py:84-92  (port_removed)
  [f598b8d9e9aef7bb]   STRU  save_graph_yaml  L=6 N=2 saved=6 sim=1.00
      deta/formatter/graph.py:90-95  (save_graph_yaml)
      deta/formatter/graph.py:151-156  (save_mermaid)

REFACTOR[2] (ranked by priority):
  [1] ○ extract_function   → deta/dsl/utils/port_added.py
      WHY: 2 occurrences of 9-line block across 1 files — saves 9 lines
      FILES: deta/dsl/commands.py
  [2] ○ extract_function   → deta/formatter/utils/save_graph_yaml.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: deta/formatter/graph.py

QUICK_WINS[2] (low risk, high savings — do first):
  [1] extract_function   saved=9L  → deta/dsl/utils/port_added.py
      FILES: commands.py
  [2] extract_function   saved=6L  → deta/formatter/utils/save_graph_yaml.py
      FILES: graph.py

EFFORT_ESTIMATE (total ≈ 0.5h):
  easy   port_added                          saved=9L  ~18min
  easy   save_graph_yaml                     saved=6L  ~12min

METRICS-TARGET:
  dup_groups:  2 → 0
  saved_lines: 15 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 264 func | 18f | 2026-04-30

NEXT[9] (ranked by impact):
  [1] !! SPLIT           deta/web/app.py
      WHY: 1004L, 1 classes, max CC=22
      EFFORT: ~4h  IMPACT: 22088

  [2] !! SPLIT           deta/cli.py
      WHY: 533L, 0 classes, max CC=15
      EFFORT: ~4h  IMPACT: 7995

  [3] !  SPLIT-FUNC      _compute_events  CC=22  fan=12
      WHY: CC=22 exceeds 15
      EFFORT: ~1h  IMPACT: 264

  [4] !  SPLIT-FUNC      save_png  CC=15  fan=15
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 225

  [5] !  SPLIT-FUNC      generate_mermaid  CC=17  fan=12
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 204

  [6] !  SPLIT-FUNC      _topology_json_with_status  CC=17  fan=10
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 170

  [7] !  SPLIT-FUNC      generate_graph_yaml  CC=23  fan=7
      WHY: CC=23 exceeds 15
      EFFORT: ~1h  IMPACT: 161

  [8] !  SPLIT-FUNC      format_probe_change  CC=15  fan=10
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 150

  [9] !  SPLIT-FUNC      format_port_changes  CC=16  fan=6
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 96


RISKS[2]:
  ⚠ Splitting deta/web/app.py may break 12 import paths
  ⚠ Splitting deta/cli.py may break 17 import paths

METRICS-TARGET:
  CC̄:          2.4 → ≤1.7
  max-CC:      23 → ≤11
  god-modules: 2 → 0
  high-CC(≥15): 8 → ≤4
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
  prev CC̄=2.3 → now CC̄=2.4
```

## Intent

Infrastructure anomaly detection and monitoring tool
