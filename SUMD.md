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
- **version**: `0.2.1`
- **python_requires**: `>=3.8`
- **license**: Apache-2.0
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
  version: 0.2.1
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
# deta | 24f 2181L | python:21,shell:2,less:1 | 2026-04-30
# stats: 55 func | 12 cls | 24 mod | CC̄=6.1 | critical:10 | cycles:0
# alerts[5]: CC generate_toon=30; CC _extract_health_url=16; CC _poll_configs=16; CC _filter_anomalies=15; CC save_png=12
# hotspots[5]: _monitor_loop fan=16; scan_compose fan=16; main fan=14; generate_toon fan=14; diff fan=13
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[24]:
  app.doql.less,28
  deta/__init__.py,24
  deta/builder/__init__.py,8
  deta/builder/topology.py,137
  deta/cli.py,344
  deta/config.py,236
  deta/core.py,27
  deta/formatter/__init__.py,23
  deta/formatter/graph.py,194
  deta/formatter/toon.py,132
  deta/integration/__init__.py,18
  deta/integration/semcod.py,130
  deta/monitor/__init__.py,19
  deta/monitor/alerter.py,100
  deta/monitor/prober.py,162
  deta/monitor/watcher.py,111
  deta/scanner/__init__.py,18
  deta/scanner/compose.py,131
  deta/scanner/npm.py,46
  deta/scanner/openapi.py,90
  deta/scanner/python.py,103
  project.sh,50
  scan-infra.sh,38
  tests/test_wup.py,12
D:
  deta/__init__.py:
  deta/builder/__init__.py:
  deta/builder/topology.py:
    e: build_topology,InfraTopology
    InfraTopology: __init__(0),add_services(1),add_endpoints(1),detect_cycles(0),find_hubs(1),detect_anomalies(0),to_json(0)  # Represents the infrastructure topology with services and dep
    build_topology(root;max_depth)
  deta/cli.py:
    e: _get_topology,_filter_anomalies,_print_summary,_resolve_formats,_probe_once,_write_outputs,scan,monitor,_monitor_loop,diff,main
    _get_topology(root;depth;config)
    _filter_anomalies(anomalies;config)
    _print_summary(topology;output;config)
    _resolve_formats(formats;config)
    _probe_once(topology)
    _write_outputs(topology;config;output;formats;probe_results)
    scan(root;depth;output;config;formats;online)
    monitor(root;interval;depth;config;output;formats;online)
    _monitor_loop(root;interval;depth;config;output;formats;online)
    diff(baseline;root;config)
    main()
  deta/config.py:
    e: load_config,_load_yaml,_parse_config,WatchConfig,ScanConfig,AnomalyConfig,MonitorConfig,OutputConfig,AlertConfig,DetaConfig
    WatchConfig:  # Watch configuration for file monitoring.
    ScanConfig:  # Scan configuration.
    AnomalyConfig:  # Anomaly detection configuration.
    MonitorConfig:  # Real-time monitoring configuration.
    OutputConfig:  # Output configuration.
    AlertConfig:  # Alert configuration.
    DetaConfig:  # Main deta configuration.
    load_config(config_path)
    _load_yaml(file_path)
    _parse_config(data)
  deta/core.py:
    e: Wup
    Wup: __init__(2),__repr__(0),get_info(0)  # Base class for wup operations.
  deta/formatter/__init__.py:
  deta/formatter/graph.py:
    e: _split_port_mapping,_resolve_host_port,_parse_host_ports,_safe_mermaid_id,generate_graph_yaml,save_graph_yaml,generate_mermaid,save_mermaid,save_png
    _split_port_mapping(port)
    _resolve_host_port(host_port)
    _parse_host_ports(ports)
    _safe_mermaid_id(name)
    generate_graph_yaml(topology;probe_results)
    save_graph_yaml(topology;output_path;probe_results)
    generate_mermaid(topology;probe_results)
    save_mermaid(topology;output_path;probe_results)
    save_png(topology;output_path;probe_results)
  deta/formatter/toon.py:
    e: generate_toon,save_toon
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
    e: _split_port_mapping,_extract_health_url,probe_service,probe_all,ProbeResult
    ProbeResult:  # Result of a health check probe.
    _split_port_mapping(port)
    _extract_health_url(service)
    probe_service(service)
    probe_all(services)
  deta/monitor/watcher.py:
    e: watch_configs,_poll_configs,_is_config_file
    watch_configs(root;on_change)
    _poll_configs(root;on_change;interval)
    _is_config_file(path)
  deta/scanner/__init__.py:
  deta/scanner/compose.py:
    e: scan_compose,_parse_ports,_parse_depends_on,_parse_env,_parse_labels,ServiceDef
    ServiceDef:  # Definition of a Docker Compose service.
    scan_compose(root;max_depth)
    _parse_ports(ports)
    _parse_depends_on(dep)
    _parse_env(env)
    _parse_labels(labels)
  deta/scanner/npm.py:
    e: scan_npm
    scan_npm(root;max_depth)
  deta/scanner/openapi.py:
    e: scan_openapi,_load,EndpointDef
    EndpointDef:  # Definition of an OpenAPI endpoint.
    scan_openapi(root;max_depth)
    _load(file_path)
  deta/scanner/python.py:
    e: scan_python,_load_toml,_parse_requirements
    scan_python(root;max_depth)
    _load_toml(file_path)
    _parse_requirements(file_path)
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

## Intent

Infrastructure anomaly detection and monitoring tool
