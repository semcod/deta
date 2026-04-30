# deta

Infrastructure anomaly detection and monitoring tool

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `deta`
- **version**: `0.2.18`
- **python_requires**: `>=3.8`
- **license**: {'text': 'Apache-2.0'}
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(1), app.doql.less, goal.yaml, .env.example, src(3 mod), project/(2 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: deta;
  version: 0.2.18;
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

## Interfaces

### CLI Entry Points

- `deta`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m deta
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m deta --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m deta --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m deta --help" 10000
ASSERT_EXIT_CODE 0
```

## Configuration

```yaml
project:
  name: deta
  version: 0.2.18
  env: local
```

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

## Deployment

```bash markpact:run
pip install deta

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`deta`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `deta/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# deta | 34f 4108L | python:31,shell:2,less:1 | 2026-04-30
# stats: 142 func | 16 cls | 34 mod | CC̄=4.8 | critical:15 | cycles:0
# alerts[5]: CC generate_graph_yaml=23; CC _compute_events=22; CC generate_mermaid=17; CC format_port_changes=16; CC _filter_anomalies=15
# hotspots[5]: create_app fan=35; _monitor_loop fan=27; main fan=15; save_png fan=15; generate_toon fan=15
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[34]:
  app.doql.less,33
  deta/__init__.py,24
  deta/builder/__init__.py,8
  deta/builder/topology.py,163
  deta/cli.py,458
  deta/config.py,269
  deta/core.py,27
  deta/dsl/__init__.py,41
  deta/dsl/commands.py,256
  deta/formatter/__init__.py,23
  deta/formatter/graph.py,200
  deta/formatter/toon.py,183
  deta/integration/__init__.py,18
  deta/integration/semcod.py,130
  deta/monitor/__init__.py,19
  deta/monitor/alerter.py,100
  deta/monitor/prober.py,235
  deta/monitor/watcher.py,117
  deta/scanner/__init__.py,18
  deta/scanner/compose.py,279
  deta/scanner/env.py,141
  deta/scanner/npm.py,46
  deta/scanner/openapi.py,90
  deta/scanner/ports.py,117
  deta/scanner/python.py,103
  deta/web/__init__.py,6
  deta/web/app.py,580
  project.sh,48
  scan-infra.sh,38
  tests/test_compose_env.py,123
  tests/test_dsl.py,90
  tests/test_env.py,60
  tests/test_ports.py,53
  tests/test_wup.py,12
D:
  deta/__init__.py:
  deta/builder/__init__.py:
  deta/builder/topology.py:
    e: build_topology,InfraTopology
    InfraTopology: __init__(0),add_services(1),add_endpoints(1),detect_cycles(0),find_hubs(1),detect_anomalies(0),to_json(0)  # Represents the infrastructure topology with services and dep
    build_topology(root;max_depth)
  deta/cli.py:
    e: _get_topology,_filter_anomalies,_print_summary,_resolve_formats,_probe_once,_write_outputs,scan,monitor,_extract_ports_snapshot,_log_port_changes,_print_status_summary,_monitor_loop,diff,main
    _get_topology(root;depth;config)
    _filter_anomalies(anomalies;config)
    _print_summary(topology;output;config)
    _resolve_formats(formats;config)
    _probe_once(topology)
    _write_outputs(topology;config;output;formats;probe_results)
    scan(root;depth;output;config;formats;online)
    monitor(root;interval;depth;config;output;formats;online)
    _extract_ports_snapshot(topology)
    _log_port_changes(old_snapshot;new_snapshot)
    _print_status_summary(topology;probe_results)
    _monitor_loop(root;interval;depth;config;output;formats;online)
    diff(baseline;root;config)
    main()
  deta/config.py:
    e: load_config,_load_yaml,_parse_config,WatchConfig,ScanConfig,AnomalyConfig,MonitorConfig,OutputConfig,AlertConfig,WebConfig,DetaConfig
    WatchConfig:  # Watch configuration for file monitoring.
    ScanConfig:  # Scan configuration.
    AnomalyConfig:  # Anomaly detection configuration.
    MonitorConfig:  # Real-time monitoring configuration.
    OutputConfig:  # Output configuration.
    AlertConfig:  # Alert configuration.
    WebConfig:  # Web dashboard configuration.
    DetaConfig:  # Main deta configuration.
    load_config(config_path)
    _load_yaml(file_path)
    _parse_config(data)
  deta/core.py:
    e: Wup
    Wup: __init__(2),__repr__(0),get_info(0)  # Base class for wup operations.
  deta/dsl/__init__.py:
  deta/dsl/commands.py:
    e: _escape_value,service_up,service_down,port_added,port_removed,service_added,service_removed,status_summary,format_probe_change,format_port_changes,format_service_changes,ChangeDSL
    ChangeDSL: __str__(0)  # Represents a DSL command.
    _escape_value(value)
    service_up(service;port;latency_ms;url)
    service_down(service;port;error;status;url)
    port_added(service;host_port;container_port;host)
    port_removed(service;host_port;container_port;host)
    service_added(service;image;source)
    service_removed(service)
    status_summary(up;down;unknown;total)
    format_probe_change(prev_probes;current_probes)
    format_port_changes(old_topology;new_topology)
    format_service_changes(old_topology;new_topology)
  deta/formatter/__init__.py:
  deta/formatter/graph.py:
    e: _service_bindings,_binding_host,_safe_mermaid_id,generate_graph_yaml,_save_output,save_graph_yaml,generate_mermaid,save_mermaid,save_png
    _service_bindings(service)
    _binding_host(binding)
    _safe_mermaid_id(name)
    generate_graph_yaml(topology;probe_results)
    _save_output(output_path;content)
    save_graph_yaml(topology;output_path;probe_results)
    generate_mermaid(topology;probe_results)
    save_mermaid(topology;output_path;probe_results)
    save_png(topology;output_path;probe_results)
  deta/formatter/toon.py:
    e: _format_header,_format_health,_format_alert_line,_format_alerts,_format_service_line,_format_services,_group_endpoints_by_service,_format_endpoint_line,_format_endpoints,_format_cycles,_format_hubs,generate_toon,save_toon
    _format_header(project;service_count)
    _format_health(services;anomalies)
    _format_alert_line(alert)
    _format_alerts(anomalies)
    _format_service_line(svc)
    _format_services(services)
    _group_endpoints_by_service(endpoints)
    _format_endpoint_line(ep)
    _format_endpoints(endpoints)
    _format_cycles(cycles)
    _format_hubs(hubs)
    generate_toon(topology;project_name)
    save_toon(topology;output_path;project_name)
  deta/integration/__init__.py:
  deta/integration/semcod.py:
    e: generate_for_sumd,generate_for_pyqual,generate_for_vallm,pre_deploy_check
    generate_for_sumd(root;depth;output)
    generate_for_pyqual(root;depth)
    generate_for_vallm(root;depth)
    pre_deploy_check(root;depth)
  deta/monitor/__init__.py:
  deta/monitor/alerter.py:
    e: _get_console,alert_anomaly,alert_probe_failure,alert_probe_success,print_topology_table
    _get_console()
    alert_anomaly(anomaly)
    alert_probe_failure(result)
    alert_probe_success(result)
    print_topology_table(topology)
  deta/monitor/prober.py:
    e: _first_resolved_binding,_extract_health_url,_extract_host_port_from_url,probe_service,probe_port,_noop_probe,probe_all,ProbeResult
    ProbeResult:  # Result of a health check probe.
    _first_resolved_binding(service)
    _extract_health_url(service)
    _extract_host_port_from_url(url)
    probe_service(service)
    probe_port(service;binding;path)
    _noop_probe(service)
    probe_all(services)
  deta/monitor/watcher.py:
    e: watch_configs,_scan_file_mtimes,_detect_change_type,_emit_changes,_poll_configs,_is_config_file
    watch_configs(root;on_change)
    _scan_file_mtimes(root)
    _detect_change_type(file_path;old_mtime;new_mtime)
    _emit_changes(old_mtimes;new_mtimes;on_change)
    _poll_configs(root;on_change;interval)
    _is_config_file(path)
  deta/scanner/__init__.py:
  deta/scanner/compose.py:
    e: _deep_merge,_get_yaml_loader,_load_yaml_file,_collect_compose_files,_merge_services,_find_primary_source,_build_service_def,scan_compose,_resolve_env_files,_parse_ports,_parse_depends_on,_parse_env,_parse_labels,ServiceDef
    ServiceDef:  # Definition of a Docker Compose service.
    _deep_merge(base;override)
    _get_yaml_loader()
    _load_yaml_file(file_path;yaml_loader)
    _collect_compose_files(root;max_depth)
    _merge_services(compose_files;yaml_loader)
    _find_primary_source(svc_name;compose_files;yaml_loader;project_dir)
    _build_service_def(svc_name;svc;project_dir;compose_files;yaml_loader;root)
    scan_compose(root;max_depth)
    _resolve_env_files(value;base_dir)
    _parse_ports(ports)
    _parse_depends_on(dep)
    _parse_env(env)
    _parse_labels(labels)
  deta/scanner/env.py:
    e: load_env_file,discover_env,merge_env_files,interpolate,interpolate_recursive
    load_env_file(path)
    discover_env(compose_file;root)
    merge_env_files(base;env_files)
    interpolate(value;env)
    interpolate_recursive(obj;env)
  deta/scanner/npm.py:
    e: scan_npm
    scan_npm(root;max_depth)
  deta/scanner/openapi.py:
    e: scan_openapi,_load,EndpointDef
    EndpointDef:  # Definition of an OpenAPI endpoint.
    scan_openapi(root;max_depth)
    _load(file_path)
  deta/scanner/ports.py:
    e: _split_top_level,parse_port,parse_ports,published_url,PortBinding
    PortBinding: is_resolved(0)  # Resolved view of a single port mapping.
    _split_top_level(value;separator)
    parse_port(raw;env)
    parse_ports(ports;env)
    published_url(binding;path)
  deta/scanner/python.py:
    e: scan_python,_load_toml,_parse_requirements
    scan_python(root;max_depth)
    _load_toml(file_path)
    _parse_requirements(file_path)
  deta/web/__init__.py:
  deta/web/app.py:
    e: _probe_status,_topology_summary,_topology_json_with_status,_compute_events,create_app,run_dashboard,ConnectionManager
    ConnectionManager: __init__(0),connect(1),disconnect(1),broadcast(1)
    _probe_status(probe)
    _topology_summary(topology;probes)
    _topology_json_with_status(topology;probes)
    _compute_events(prev_services;prev_probes;topology;probes;enabled)
    create_app(root;depth;config)
    run_dashboard(root;depth;config_file;host;port)
  tests/test_compose_env.py:
    e: test_env_driven_ports,test_env_file_layering,test_port_conflict_detected,test_compose_override_merging
    test_env_driven_ports(tmp_path)
    test_env_file_layering(tmp_path)
    test_port_conflict_detected(tmp_path)
    test_compose_override_merging(tmp_path)
  tests/test_dsl.py:
    e: test_service_up,test_service_down,test_port_added,test_port_removed,test_service_added,test_service_removed,test_status_summary,test_format_probe_change_up,test_format_probe_change_down,test_format_probe_change_no_change
    test_service_up()
    test_service_down()
    test_port_added()
    test_port_removed()
    test_service_added()
    test_service_removed()
    test_status_summary()
    test_format_probe_change_up()
    test_format_probe_change_down()
    test_format_probe_change_no_change()
  tests/test_env.py:
    e: test_interpolate_plain,test_interpolate_simple,test_interpolate_default_unset,test_interpolate_default_empty,test_interpolate_no_default_unset,test_interpolate_no_default_empty,test_interpolate_plus_alt,test_interpolate_plus_missing,test_interpolate_bare_dollar,test_interpolate_embedded,test_load_env_file
    test_interpolate_plain()
    test_interpolate_simple()
    test_interpolate_default_unset()
    test_interpolate_default_empty()
    test_interpolate_no_default_unset()
    test_interpolate_no_default_empty()
    test_interpolate_plus_alt()
    test_interpolate_plus_missing()
    test_interpolate_bare_dollar()
    test_interpolate_embedded()
    test_load_env_file(tmp_path)
  tests/test_ports.py:
    e: test_parse_port_single,test_parse_port_mapping,test_parse_port_with_host,test_parse_port_with_protocol,test_parse_port_env,test_parse_port_env_default,test_published_url,test_published_url_fallback_host
    test_parse_port_single()
    test_parse_port_mapping()
    test_parse_port_with_host()
    test_parse_port_with_protocol()
    test_parse_port_env()
    test_parse_port_env_default()
    test_published_url()
    test_published_url_fallback_host()
  tests/test_wup.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
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
def _extract_ports_snapshot(topology)  # CC=3, fan=2
def _log_port_changes(old_snapshot, new_snapshot)  # CC=4, fan=6
def _print_status_summary(topology, probe_results)  # CC=11, fan=7 ⚠
def _monitor_loop(root, interval, depth, config, output, formats, online)  # CC=7, fan=27
def diff(baseline, root, config)  # CC=9, fan=13
def main()  # CC=2, fan=15
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

*88 nodes · 98 edges · 16 modules · CC̄=2.3*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_monitor_loop` *(in deta.cli)* | 7 | 1 | 48 | **49** |
| `create_app` *(in deta.web.app)* | 5 | 1 | 46 | **47** |
| `_parse_config` *(in deta.config)* | 9 | 1 | 43 | **44** |
| `diff` *(in deta.cli)* | 9 | 1 | 27 | **28** |
| `generate_mermaid` *(in deta.formatter.graph)* | 17 ⚠ | 2 | 23 | **25** |
| `_build_service_def` *(in deta.scanner.compose)* | 5 | 1 | 23 | **24** |
| `generate_graph_yaml` *(in deta.formatter.graph)* | 23 ⚠ | 2 | 22 | **24** |
| `generate_toon` *(in deta.formatter.toon)* | 2 | 1 | 21 | **22** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/deta
# nodes: 88 | edges: 98 | modules: 16
# CC̄=2.3

HUBS[20]:
  deta.cli._monitor_loop
    CC=7  in:1  out:48  total:49
  deta.web.app.create_app
    CC=5  in:1  out:46  total:47
  deta.config._parse_config
    CC=9  in:1  out:43  total:44
  deta.cli.diff
    CC=9  in:1  out:27  total:28
  deta.formatter.graph.generate_mermaid
    CC=17  in:2  out:23  total:25
  deta.scanner.compose._build_service_def
    CC=5  in:1  out:23  total:24
  deta.formatter.graph.generate_graph_yaml
    CC=23  in:2  out:22  total:24
  deta.formatter.toon.generate_toon
    CC=2  in:1  out:21  total:22
  deta.scanner.python.scan_python
    CC=11  in:1  out:20  total:21
  deta.monitor.alerter.print_topology_table
    CC=8  in:1  out:19  total:20
  deta.formatter.graph.save_png
    CC=15  in:1  out:17  total:18
  deta.monitor.prober.probe_service
    CC=4  in:1  out:17  total:18
  deta.monitor.prober.probe_port
    CC=4  in:1  out:16  total:17
  deta.scanner.env.load_env_file
    CC=12  in:2  out:14  total:16
  deta.config.load_config
    CC=4  in:8  out:7  total:15
  deta.cli._write_outputs
    CC=8  in:3  out:12  total:15
  deta.scanner.openapi.scan_openapi
    CC=12  in:0  out:14  total:14
  deta.scanner.ports.parse_port
    CC=10  in:2  out:12  total:14
  deta.monitor.prober.probe_all
    CC=10  in:4  out:9  total:13
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
    _parse_config  CC=9  out:43
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
    _noop_probe  CC=1  out:1
    probe_all  CC=10  out:9
    probe_port  CC=4  out:16
    probe_service  CC=4  out:17
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
    create_app  CC=5  out:46
    run_dashboard  CC=4  out:5
  project.map.toon  [1 funcs]
    build_topology  CC=0  out:0

EDGES:
  deta.config.load_config → deta.config._load_yaml
  deta.config.load_config → deta.config._parse_config
  deta.cli._get_topology → project.map.toon.build_topology
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
  deta.monitor.alerter.alert_anomaly → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_failure → deta.monitor.alerter._get_console
  deta.monitor.alerter.alert_probe_success → deta.monitor.alerter._get_console
  deta.monitor.alerter.print_topology_table → deta.monitor.alerter._get_console
  deta.monitor.prober._first_resolved_binding → deta.scanner.ports.parse_port
  deta.monitor.prober._extract_health_url → deta.monitor.prober._first_resolved_binding
  deta.monitor.prober._extract_health_url → deta.scanner.ports.published_url
  deta.monitor.prober.probe_service → deta.monitor.prober._extract_health_url
  deta.monitor.prober.probe_service → deta.monitor.prober._extract_host_port_from_url
  deta.monitor.prober.probe_port → deta.scanner.ports.published_url
  deta.monitor.prober.probe_all → deta.monitor.prober._extract_health_url
  deta.monitor.prober.probe_all → deta.monitor.prober.probe_service
  deta.monitor.prober.probe_all → deta.monitor.prober._noop_probe
  deta.monitor.prober.probe_all → deta.scanner.ports.parse_ports
  deta.monitor.prober.probe_all → deta.monitor.prober.probe_port
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._is_config_file
  deta.monitor.watcher.watch_configs → deta.monitor.watcher._poll_configs
  deta.monitor.watcher._emit_changes → deta.monitor.watcher._detect_change_type
  deta.monitor.watcher._poll_configs → deta.monitor.watcher._scan_file_mtimes
  deta.monitor.watcher._poll_configs → deta.monitor.watcher._emit_changes
  deta.scanner.python.scan_python → deta.scanner.python._load_toml
  deta.scanner.python.scan_python → deta.scanner.python._parse_requirements
  deta.scanner.ports.parse_port → deta.scanner.env.interpolate
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Intent

Infrastructure anomaly detection and monitoring tool
