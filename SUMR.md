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
- **version**: `0.2.42`
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
  version: 0.2.42;
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
def _pid_on_port(host, port)  # CC=10, fan=7 ⚠
def _terminate_pid(pid)  # CC=2, fan=1
def _get_topology(root, depth, config)  # CC=1, fan=1
def _is_anomaly_enabled(anomaly_type, anomaly_config)  # CC=2, fan=2
def _meets_severity_threshold(severity, min_severity)  # CC=1, fan=1
def _filter_anomalies(anomalies, config)  # CC=8, fan=4
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

*109 nodes · 125 edges · 16 modules · CC̄=2.0*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `create_app` *(in deta.web.app)* | 5 | 1 | 121 | **122** |
| `_monitor_loop` *(in deta.cli)* | 7 | 1 | 48 | **49** |
| `_parse_config` *(in deta.config)* | 9 | 1 | 46 | **47** |
| `diff` *(in deta.cli)* | 9 | 1 | 27 | **28** |
| `generate_mermaid` *(in deta.formatter.graph)* | 10 ⚠ | 3 | 21 | **24** |
| `_build_service_def` *(in deta.scanner.compose)* | 5 | 1 | 23 | **24** |
| `generate_toon` *(in deta.formatter.toon)* | 2 | 1 | 21 | **22** |
| `probe_port` *(in deta.monitor.prober)* | 13 ⚠ | 1 | 21 | **22** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/deta
# nodes: 109 | edges: 125 | modules: 16
# CC̄=2.0

HUBS[20]:
  deta.web.app.create_app
    CC=5  in:1  out:121  total:122
  deta.cli._monitor_loop
    CC=7  in:1  out:48  total:49
  deta.config._parse_config
    CC=9  in:1  out:46  total:47
  deta.cli.diff
    CC=9  in:1  out:27  total:28
  deta.formatter.graph.generate_mermaid
    CC=10  in:3  out:21  total:24
  deta.scanner.compose._build_service_def
    CC=5  in:1  out:23  total:24
  deta.formatter.toon.generate_toon
    CC=2  in:1  out:21  total:22
  deta.monitor.prober.probe_port
    CC=13  in:1  out:21  total:22
  deta.scanner.python.scan_python
    CC=11  in:1  out:20  total:21
  deta.monitor.prober.probe_service
    CC=9  in:1  out:19  total:20
  deta.monitor.alerter.print_topology_table
    CC=8  in:1  out:19  total:20
  deta.formatter.graph.save_png
    CC=11  in:1  out:19  total:20
  deta.monitor.prober.probe_all
    CC=11  in:4  out:14  total:18
  deta.formatter.graph._graph_yaml_node
    CC=8  in:1  out:16  total:17
  deta.scanner.env.load_env_file
    CC=12  in:2  out:14  total:16
  deta.web.app._topology_json_with_status
    CC=6  in:1  out:15  total:16
  deta.cli._write_outputs
    CC=8  in:3  out:12  total:15
  deta.config.load_config
    CC=4  in:8  out:7  total:15
  deta.scanner.openapi.scan_openapi
    CC=12  in:0  out:14  total:14
  deta.scanner.ports.parse_port
    CC=10  in:2  out:12  total:14

MODULES:
  deta.cli  [12 funcs]
    _filter_anomalies  CC=8  out:5
    _get_topology  CC=1  out:1
    _is_anomaly_enabled  CC=2  out:2
    _meets_severity_threshold  CC=1  out:2
    _monitor_loop  CC=7  out:48
    _print_summary  CC=4  out:11
    _probe_once  CC=5  out:6
    _resolve_formats  CC=4  out:4
    _write_outputs  CC=8  out:12
    diff  CC=9  out:27
  deta.config  [3 funcs]
    _load_yaml  CC=7  out:11
    _parse_config  CC=9  out:46
    load_config  CC=4  out:7
  deta.dsl.commands  [14 funcs]
    _diff_service_ports  CC=9  out:6
    _escape_value  CC=4  out:2
    _port_key  CC=1  out:0
    _ports_added  CC=4  out:2
    _ports_removed  CC=4  out:2
    format_port_changes  CC=2  out:6
    format_probe_change  CC=12  out:12
    format_service_changes  CC=4  out:8
    port_added  CC=2  out:3
    port_removed  CC=2  out:3
  deta.formatter.graph  [10 funcs]
    _graph_yaml_node  CC=8  out:16
    _port_probe_status  CC=2  out:1
    _safe_mermaid_id  CC=3  out:2
    _save_output  CC=1  out:1
    _service_bindings  CC=2  out:1
    generate_graph_yaml  CC=4  out:10
    generate_mermaid  CC=10  out:21
    save_graph_yaml  CC=1  out:2
    save_mermaid  CC=1  out:2
    save_png  CC=11  out:19
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
  deta.monitor.prober  [12 funcs]
    _extract_health_url  CC=11  out:9
    _extract_host_port_from_url  CC=4  out:2
    _first_resolved_binding  CC=6  out:1
    _get_client  CC=4  out:2
    _has_explicit_healthcheck_url  CC=10  out:6
    _is_database_port  CC=1  out:0
    _service_probe_targets  CC=8  out:10
    group_probes_by_service  CC=3  out:2
    probe_all  CC=11  out:14
    probe_port  CC=13  out:21
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
  deta.web.app  [8 funcs]
    _compute_events  CC=7  out:10
    _probe_status  CC=2  out:1
    _probe_status_events  CC=11  out:11
    _service_payload  CC=3  out:2
    _service_status_map  CC=2  out:3
    _topology_json_with_status  CC=6  out:15
    create_app  CC=5  out:121
    run_dashboard  CC=5  out:6
  project.map.toon  [1 funcs]
    build_topology  CC=0  out:0

EDGES:
  deta.config.load_config → deta.config._load_yaml
  deta.config.load_config → deta.config._parse_config
  deta.cli._get_topology → project.map.toon.build_topology
  deta.cli._filter_anomalies → deta.cli._meets_severity_threshold
  deta.cli._filter_anomalies → deta.cli._is_anomaly_enabled
  deta.cli._print_summary → deta.monitor.alerter.print_topology_table
  deta.cli._print_summary → deta.monitor.alerter.alert_anomaly
  deta.cli._probe_once → deta.monitor.prober.probe_all
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
  deta.cli.scan → deta.config.load_config
  deta.cli.scan → deta.cli._filter_anomalies
  deta.cli.scan → deta.cli._probe_once
  deta.cli.monitor → deta.cli._monitor_loop
  deta.cli._monitor_loop → deta.cli._resolve_formats
  deta.cli._monitor_loop → deta.cli._get_topology
  deta.cli._monitor_loop → deta.cli._filter_anomalies
  deta.cli._monitor_loop → deta.cli._write_outputs
  deta.cli._monitor_loop → deta.cli._print_summary
  deta.cli.diff → deta.config.load_config
  deta.cli.diff → deta.cli._get_topology
  deta.web.app._probe_status → deta.monitor.prober.resolve_service_status
  deta.web.app._service_payload → deta.monitor.prober.resolve_service_status
  deta.web.app._topology_json_with_status → deta.monitor.prober.group_probes_by_service
  deta.web.app._topology_json_with_status → deta.web.app._service_payload
  deta.web.app._service_status_map → deta.monitor.prober.group_probes_by_service
  deta.web.app._service_status_map → deta.monitor.prober.resolve_service_status
  deta.web.app._probe_status_events → deta.monitor.prober.group_probes_by_service
  deta.web.app._probe_status_events → deta.monitor.prober.resolve_service_status
  deta.web.app._compute_events → deta.web.app._probe_status_events
  deta.web.app.run_dashboard → deta.config.load_config
  deta.web.app.run_dashboard → deta.web.app.create_app
  deta.monitor.alerter.alert_anomaly → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_failure → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_success → deta.monitor.alerter._get_console
  deta.monitor.alerter.print_topology_table → deta.monitor.alerter._get_console
  deta.monitor.prober._first_resolved_binding → deta.scanner.ports.parse_port
  deta.monitor.prober._extract_health_url → deta.monitor.prober._first_resolved_binding
  deta.monitor.prober._extract_health_url → deta.scanner.ports.published_url
  deta.monitor.prober._service_probe_targets → deta.monitor.prober._first_resolved_binding
  deta.monitor.prober._service_probe_targets → deta.monitor.prober._extract_host_port_from_url
  deta.monitor.prober._service_probe_targets → deta.scanner.ports.published_url
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
# nodes: 109 | edges: 125 | modules: 16
# CC̄=2.0

HUBS[20]:
  deta.web.app.create_app
    CC=5  in:1  out:121  total:122
  deta.cli._monitor_loop
    CC=7  in:1  out:48  total:49
  deta.config._parse_config
    CC=9  in:1  out:46  total:47
  deta.cli.diff
    CC=9  in:1  out:27  total:28
  deta.formatter.graph.generate_mermaid
    CC=10  in:3  out:21  total:24
  deta.scanner.compose._build_service_def
    CC=5  in:1  out:23  total:24
  deta.formatter.toon.generate_toon
    CC=2  in:1  out:21  total:22
  deta.monitor.prober.probe_port
    CC=13  in:1  out:21  total:22
  deta.scanner.python.scan_python
    CC=11  in:1  out:20  total:21
  deta.monitor.prober.probe_service
    CC=9  in:1  out:19  total:20
  deta.monitor.alerter.print_topology_table
    CC=8  in:1  out:19  total:20
  deta.formatter.graph.save_png
    CC=11  in:1  out:19  total:20
  deta.monitor.prober.probe_all
    CC=11  in:4  out:14  total:18
  deta.formatter.graph._graph_yaml_node
    CC=8  in:1  out:16  total:17
  deta.scanner.env.load_env_file
    CC=12  in:2  out:14  total:16
  deta.web.app._topology_json_with_status
    CC=6  in:1  out:15  total:16
  deta.cli._write_outputs
    CC=8  in:3  out:12  total:15
  deta.config.load_config
    CC=4  in:8  out:7  total:15
  deta.scanner.openapi.scan_openapi
    CC=12  in:0  out:14  total:14
  deta.scanner.ports.parse_port
    CC=10  in:2  out:12  total:14

MODULES:
  deta.cli  [12 funcs]
    _filter_anomalies  CC=8  out:5
    _get_topology  CC=1  out:1
    _is_anomaly_enabled  CC=2  out:2
    _meets_severity_threshold  CC=1  out:2
    _monitor_loop  CC=7  out:48
    _print_summary  CC=4  out:11
    _probe_once  CC=5  out:6
    _resolve_formats  CC=4  out:4
    _write_outputs  CC=8  out:12
    diff  CC=9  out:27
  deta.config  [3 funcs]
    _load_yaml  CC=7  out:11
    _parse_config  CC=9  out:46
    load_config  CC=4  out:7
  deta.dsl.commands  [14 funcs]
    _diff_service_ports  CC=9  out:6
    _escape_value  CC=4  out:2
    _port_key  CC=1  out:0
    _ports_added  CC=4  out:2
    _ports_removed  CC=4  out:2
    format_port_changes  CC=2  out:6
    format_probe_change  CC=12  out:12
    format_service_changes  CC=4  out:8
    port_added  CC=2  out:3
    port_removed  CC=2  out:3
  deta.formatter.graph  [10 funcs]
    _graph_yaml_node  CC=8  out:16
    _port_probe_status  CC=2  out:1
    _safe_mermaid_id  CC=3  out:2
    _save_output  CC=1  out:1
    _service_bindings  CC=2  out:1
    generate_graph_yaml  CC=4  out:10
    generate_mermaid  CC=10  out:21
    save_graph_yaml  CC=1  out:2
    save_mermaid  CC=1  out:2
    save_png  CC=11  out:19
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
  deta.monitor.prober  [12 funcs]
    _extract_health_url  CC=11  out:9
    _extract_host_port_from_url  CC=4  out:2
    _first_resolved_binding  CC=6  out:1
    _get_client  CC=4  out:2
    _has_explicit_healthcheck_url  CC=10  out:6
    _is_database_port  CC=1  out:0
    _service_probe_targets  CC=8  out:10
    group_probes_by_service  CC=3  out:2
    probe_all  CC=11  out:14
    probe_port  CC=13  out:21
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
  deta.web.app  [8 funcs]
    _compute_events  CC=7  out:10
    _probe_status  CC=2  out:1
    _probe_status_events  CC=11  out:11
    _service_payload  CC=3  out:2
    _service_status_map  CC=2  out:3
    _topology_json_with_status  CC=6  out:15
    create_app  CC=5  out:121
    run_dashboard  CC=5  out:6
  project.map.toon  [1 funcs]
    build_topology  CC=0  out:0

EDGES:
  deta.config.load_config → deta.config._load_yaml
  deta.config.load_config → deta.config._parse_config
  deta.cli._get_topology → project.map.toon.build_topology
  deta.cli._filter_anomalies → deta.cli._meets_severity_threshold
  deta.cli._filter_anomalies → deta.cli._is_anomaly_enabled
  deta.cli._print_summary → deta.monitor.alerter.print_topology_table
  deta.cli._print_summary → deta.monitor.alerter.alert_anomaly
  deta.cli._probe_once → deta.monitor.prober.probe_all
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
  deta.cli.scan → deta.config.load_config
  deta.cli.scan → deta.cli._filter_anomalies
  deta.cli.scan → deta.cli._probe_once
  deta.cli.monitor → deta.cli._monitor_loop
  deta.cli._monitor_loop → deta.cli._resolve_formats
  deta.cli._monitor_loop → deta.cli._get_topology
  deta.cli._monitor_loop → deta.cli._filter_anomalies
  deta.cli._monitor_loop → deta.cli._write_outputs
  deta.cli._monitor_loop → deta.cli._print_summary
  deta.cli.diff → deta.config.load_config
  deta.cli.diff → deta.cli._get_topology
  deta.web.app._probe_status → deta.monitor.prober.resolve_service_status
  deta.web.app._service_payload → deta.monitor.prober.resolve_service_status
  deta.web.app._topology_json_with_status → deta.monitor.prober.group_probes_by_service
  deta.web.app._topology_json_with_status → deta.web.app._service_payload
  deta.web.app._service_status_map → deta.monitor.prober.group_probes_by_service
  deta.web.app._service_status_map → deta.monitor.prober.resolve_service_status
  deta.web.app._probe_status_events → deta.monitor.prober.group_probes_by_service
  deta.web.app._probe_status_events → deta.monitor.prober.resolve_service_status
  deta.web.app._compute_events → deta.web.app._probe_status_events
  deta.web.app.run_dashboard → deta.config.load_config
  deta.web.app.run_dashboard → deta.web.app.create_app
  deta.monitor.alerter.alert_anomaly → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_failure → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_success → deta.monitor.alerter._get_console
  deta.monitor.alerter.print_topology_table → deta.monitor.alerter._get_console
  deta.monitor.prober._first_resolved_binding → deta.scanner.ports.parse_port
  deta.monitor.prober._extract_health_url → deta.monitor.prober._first_resolved_binding
  deta.monitor.prober._extract_health_url → deta.scanner.ports.published_url
  deta.monitor.prober._service_probe_targets → deta.monitor.prober._first_resolved_binding
  deta.monitor.prober._service_probe_targets → deta.monitor.prober._extract_host_port_from_url
  deta.monitor.prober._service_probe_targets → deta.scanner.ports.published_url
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 43f 8747L | python:24,yaml:11,yml:3,shell:2,json:1,txt:1,toml:1 | 2026-05-04
# CC̄=2.0 | critical:0/309 | dups:0 | cycles:2

HEALTH[0]: ok

REFACTOR[1]:
  1. break 2 circular dependencies

PIPELINES[15]:
  [1] Src [main]: main → load_config → _load_yaml
      PURITY: 100% pure
  [2] Src [__init__]: __init__
      PURITY: 100% pure
  [3] Src [connect]: connect
      PURITY: 100% pure
  [4] Src [has_connections]: has_connections
      PURITY: 100% pure
  [5] Src [disconnect]: disconnect
      PURITY: 100% pure

LAYERS:
  deta/                           CC̄=4.5    ←in:1  →out:23  !! split
  │ !! app                       1466L  1C   14m  CC=11     ←1
  │ !! cli                        545L  0C   19m  CC=11     ←0
  │ prober                     443L  1C   16m  CC=13     ←4
  │ compose                    278L  1C   13m  CC=7      ←0
  │ config                     274L  8C    3m  CC=9      ←2
  │ commands                   257L  1C   16m  CC=12     ←1
  │ toon                       182L  0C   13m  CC=5      ←2
  │ graph                      182L  0C   11m  CC=11     ←2
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
  │ __init__                    20L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                1459L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              294L  0C  171m  CC=0.0    ←2
  │ calls.toon.yaml            215L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml          97L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml       52L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           51L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         49L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
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
                        deta.monitor              deta          deta.web    deta.formatter      deta.scanner          deta.dsl  deta.integration       project.map
      deta.monitor                ──               ←13               ←12                ←7                 7                ←2                                      hub
              deta                13                ──                 1                 4                                   4                                   1  !! fan-out
          deta.web                12                 1                ──                 4                                                                          !! fan-out
    deta.formatter                 7                ←4                ←4                ──                 1                                  ←1                    hub
      deta.scanner                ←7                                                    ←1                ──                                  ←1                    hub
          deta.dsl                 2                ←4                                                                      ──                                    
  deta.integration                                                                       1                 1                                  ──                 3
       project.map                                  ←1                                                                                        ←3                ──
  CYCLES: 2
  HUB: deta.scanner/ (fan-in=9)
  HUB: deta.monitor/ (fan-in=34)
  HUB: deta.formatter/ (fan-in=9)
  SMELL: deta.formatter/ fan-out=8 → split needed
  SMELL: deta/ fan-out=23 → split needed
  SMELL: deta.web/ fan-out=17 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 3 groups | 25f 4643L | 2026-05-04

SUMMARY:
  files_scanned: 25
  total_lines:   4643
  dup_groups:    3
  dup_fragments: 6
  saved_lines:   22
  scan_ms:       2950

HOTSPOTS[2] (files with most duplication):
  deta/dsl/commands.py  dup=32L  groups=2  frags=4  (0.7%)
  deta/formatter/graph.py  dup=12L  groups=1  frags=2  (0.3%)

DUPLICATES[3] (ranked by impact):
  [966af33370a97c1c]   STRU  port_added  L=9 N=2 saved=9 sim=1.00
      deta/dsl/commands.py:73-81  (port_added)
      deta/dsl/commands.py:84-92  (port_removed)
  [db6891706a5fb56d]   STRU  _ports_added  L=7 N=2 saved=7 sim=1.00
      deta/dsl/commands.py:175-181  (_ports_added)
      deta/dsl/commands.py:184-190  (_ports_removed)
  [f598b8d9e9aef7bb]   STRU  save_graph_yaml  L=6 N=2 saved=6 sim=1.00
      deta/formatter/graph.py:88-93  (save_graph_yaml)
      deta/formatter/graph.py:135-140  (save_mermaid)

REFACTOR[3] (ranked by priority):
  [1] ○ extract_function   → deta/dsl/utils/port_added.py
      WHY: 2 occurrences of 9-line block across 1 files — saves 9 lines
      FILES: deta/dsl/commands.py
  [2] ○ extract_function   → deta/dsl/utils/_ports_added.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: deta/dsl/commands.py
  [3] ○ extract_function   → deta/formatter/utils/save_graph_yaml.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: deta/formatter/graph.py

QUICK_WINS[3] (low risk, high savings — do first):
  [1] extract_function   saved=9L  → deta/dsl/utils/port_added.py
      FILES: commands.py
  [2] extract_function   saved=7L  → deta/dsl/utils/_ports_added.py
      FILES: commands.py
  [3] extract_function   saved=6L  → deta/formatter/utils/save_graph_yaml.py
      FILES: graph.py

EFFORT_ESTIMATE (total ≈ 0.7h):
  easy   port_added                          saved=9L  ~18min
  easy   _ports_added                        saved=7L  ~14min
  easy   save_graph_yaml                     saved=6L  ~12min

METRICS-TARGET:
  dup_groups:  3 → 0
  saved_lines: 22 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 309 func | 18f | 2026-05-04

NEXT[2] (ranked by impact):
  [1] !! SPLIT           deta/web/app.py
      WHY: 1466L, 1 classes, max CC=11
      EFFORT: ~4h  IMPACT: 16126

  [2] !! SPLIT           deta/cli.py
      WHY: 545L, 0 classes, max CC=11
      EFFORT: ~4h  IMPACT: 5995


RISKS[2]:
  ⚠ Splitting deta/web/app.py may break 14 import paths
  ⚠ Splitting deta/cli.py may break 19 import paths

METRICS-TARGET:
  CC̄:          2.0 → ≤1.4
  max-CC:      13 → ≤6
  god-modules: 2 → 0
  high-CC(≥15): 0 → ≤0
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
  prev CC̄=2.0 → now CC̄=2.0
```

## Intent

Infrastructure anomaly detection and monitoring tool
