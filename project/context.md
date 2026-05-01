# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/deta
- **Primary Language**: python
- **Languages**: python: 24, yaml: 11, yml: 3, shell: 2, json: 1
- **Analysis Mode**: static
- **Total Functions**: 307
- **Total Classes**: 15
- **Modules**: 43
- **Entry Points**: 186

## Architecture by Module

### project.map.toon
- **Functions**: 169
- **File**: `map.toon.yaml`

### deta.cli
- **Functions**: 19
- **File**: `cli.py`

### deta.monitor.prober
- **Functions**: 16
- **Classes**: 1
- **File**: `prober.py`

### deta.dsl.commands
- **Functions**: 16
- **Classes**: 1
- **File**: `commands.py`

### deta.web.app
- **Functions**: 14
- **Classes**: 1
- **File**: `app.py`

### deta.scanner.compose
- **Functions**: 13
- **Classes**: 1
- **File**: `compose.py`

### deta.formatter.toon
- **Functions**: 13
- **File**: `toon.py`

### deta.formatter.graph
- **Functions**: 11
- **File**: `graph.py`

### deta.monitor.watcher
- **Functions**: 6
- **File**: `watcher.py`

### deta.monitor.alerter
- **Functions**: 5
- **File**: `alerter.py`

### deta.scanner.env
- **Functions**: 5
- **File**: `env.py`

### deta.scanner.ports
- **Functions**: 4
- **Classes**: 1
- **File**: `ports.py`

### deta.integration.semcod
- **Functions**: 4
- **File**: `semcod.py`

### deta.config
- **Functions**: 3
- **Classes**: 8
- **File**: `config.py`

### deta.core
- **Functions**: 3
- **Classes**: 1
- **File**: `core.py`

### deta.scanner.python
- **Functions**: 3
- **File**: `python.py`

### deta.scanner.openapi
- **Functions**: 2
- **Classes**: 1
- **File**: `openapi.py`

### deta.scanner.npm
- **Functions**: 1
- **File**: `npm.py`

## Key Entry Points

Main execution flows into the system:

### deta.cli.main
- **Calls**: typer.Typer, app.command, app.command, app.command, app.command, app, typer.Argument, typer.Option

### deta.scanner.npm.scan_npm
> Scan for package.json files and extract package information.

Args:
    root: Root directory to scan
    max_depth: Maximum directory depth to scan
  
- **Calls**: root.rglob, len, json.loads, result.append, pkg.relative_to, pkg.read_text, data.get, data.get

### deta.scanner.openapi.scan_openapi
> Scan for OpenAPI files and extract endpoint definitions.

Args:
    root: Root directory to scan
    max_depth: Maximum directory depth to scan
    
R
- **Calls**: root.rglob, len, deta.scanner.openapi._load, None.get, data.get, None.items, api_file.relative_to, data.get

### deta.dsl.commands.format_probe_change
> Compare probe results and generate DSL commands for status changes.

Returns list of SERVICE_UP/SERVICE_DOWN commands.
- **Calls**: deta.monitor.prober.group_probes_by_service, deta.monitor.prober.group_probes_by_service, set, set, prev_by_svc.get, curr_by_svc.get, any, any

### deta.web.app.ConnectionManager.broadcast
- **Calls**: json.dumps, len, list, zip, message.encode, asyncio.gather, isinstance, self.disconnect

### deta.integration.semcod.pre_deploy_check
> Run pre-deployment infrastructure validation.

This function checks for critical anomalies before deployment and returns
a pass/fail status along with
- **Calls**: Path, project.map.toon.build_topology, topology.detect_anomalies, issues.append, issues.append, len, a.get, a.get

### deta.dsl.commands.format_service_changes
> Compare services between topologies and generate DSL commands.

Returns list of SERVICE_ADDED/SERVICE_REMOVED commands.
- **Calls**: set, set, old_topology.services.keys, new_topology.services.keys, commands.append, commands.append, deta.dsl.commands.service_added, deta.dsl.commands.service_removed

### deta.scanner.compose.scan_compose
> Scan for docker-compose files and extract service definitions.

Args:
    root: Root directory to scan
    max_depth: Maximum directory depth to scan

- **Calls**: deta.scanner.compose._get_yaml_loader, deta.scanner.compose._collect_compose_files, project_files.items, deta.scanner.compose._merge_services, merged_services.items, deta.scanner.compose._build_service_def, all_services.append

### deta.dsl.commands.status_summary
> Generate STATUS_SUMMARY command.
- **Calls**: ChangeDSL, None.strftime, str, str, str, str, datetime.now

### deta.integration.semcod.generate_for_pyqual
> Generate dependency data for pyqual (Python quality checker).

Args:
    root: Root directory to scan
    depth: Maximum scan depth
    
Returns:
    
- **Calls**: Path, deta.scanner.python.scan_python, list, set, None.append, None.update

### deta.dsl.commands.format_port_changes
> Compare port bindings between topologies and generate DSL commands.

Returns list of PORT_ADDED/PORT_REMOVED commands.
- **Calls**: set, set, commands.extend, deta.dsl.commands._diff_service_ports, old_topology.services.get, new_topology.services.get

### deta.integration.semcod.generate_for_sumd
> Generate infrastructure report for sumd pipeline.

This function creates a toon-formatted infrastructure report that can be
consumed by sumd (Semcod u
- **Calls**: Path, Path, project.map.toon.build_topology, deta.formatter.toon.save_toon

### deta.integration.semcod.generate_for_vallm
> Generate service metadata for vallm (validation LLM).

Args:
    root: Root directory to scan
    depth: Maximum scan depth
    
Returns:
    Dictiona
- **Calls**: Path, project.map.toon.build_topology, topology.detect_anomalies, topology.services.items

### deta.dsl.commands.ChangeDSL.__str__
- **Calls**: None.join, sorted, self.params.items

### deta.web.app.ConnectionManager.connect
- **Calls**: self._connections.add, websocket.accept

### deta.web.app.ConnectionManager.__init__
- **Calls**: set

### deta.web.app.ConnectionManager.has_connections
- **Calls**: bool

### deta.web.app.ConnectionManager.disconnect
- **Calls**: self._connections.discard

### deta.web.app._probe_status
- **Calls**: deta.monitor.prober.resolve_service_status

### deta.core.Wup.__init__
> Initialize a Wup instance.

Args:
    name: The name of the wup
    dosage: The dosage information (optional)

### deta.core.Wup.__repr__

### deta.core.Wup.get_info
> Return wup information.

### project.map.toon._port_in_use

### project.map.toon._pid_on_port

### project.map.toon._terminate_pid

### project.map.toon._get_topology

### project.map.toon._is_anomaly_enabled

### project.map.toon._meets_severity_threshold

### project.map.toon._filter_anomalies

### project.map.toon._print_summary

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [deta.cli]
```

### Flow 2: scan_npm
```
scan_npm [deta.scanner.npm]
```

### Flow 3: scan_openapi
```
scan_openapi [deta.scanner.openapi]
  └─> _load
```

### Flow 4: format_probe_change
```
format_probe_change [deta.dsl.commands]
  └─ →> group_probes_by_service
  └─ →> group_probes_by_service
```

### Flow 5: broadcast
```
broadcast [deta.web.app.ConnectionManager]
```

### Flow 6: pre_deploy_check
```
pre_deploy_check [deta.integration.semcod]
  └─ →> build_topology
```

### Flow 7: format_service_changes
```
format_service_changes [deta.dsl.commands]
```

### Flow 8: scan_compose
```
scan_compose [deta.scanner.compose]
  └─> _get_yaml_loader
  └─> _collect_compose_files
```

### Flow 9: status_summary
```
status_summary [deta.dsl.commands]
```

### Flow 10: generate_for_pyqual
```
generate_for_pyqual [deta.integration.semcod]
  └─ →> scan_python
      └─> _load_toml
```

## Key Classes

### deta.web.app.ConnectionManager
- **Methods**: 5
- **Key Methods**: deta.web.app.ConnectionManager.__init__, deta.web.app.ConnectionManager.connect, deta.web.app.ConnectionManager.has_connections, deta.web.app.ConnectionManager.disconnect, deta.web.app.ConnectionManager.broadcast

### deta.core.Wup
> Base class for wup operations.
- **Methods**: 3
- **Key Methods**: deta.core.Wup.__init__, deta.core.Wup.__repr__, deta.core.Wup.get_info

### deta.scanner.ports.PortBinding
> Resolved view of a single port mapping.
- **Methods**: 1
- **Key Methods**: deta.scanner.ports.PortBinding.is_resolved

### deta.dsl.commands.ChangeDSL
> Represents a DSL command.
- **Methods**: 1
- **Key Methods**: deta.dsl.commands.ChangeDSL.__str__

### deta.config.WatchConfig
> Watch configuration for file monitoring.
- **Methods**: 0

### deta.config.ScanConfig
> Scan configuration.
- **Methods**: 0

### deta.config.AnomalyConfig
> Anomaly detection configuration.
- **Methods**: 0

### deta.config.MonitorConfig
> Real-time monitoring configuration.
- **Methods**: 0

### deta.config.OutputConfig
> Output configuration.
- **Methods**: 0

### deta.config.AlertConfig
> Alert configuration.
- **Methods**: 0

### deta.config.WebConfig
> Web dashboard configuration.
- **Methods**: 0

### deta.config.DetaConfig
> Main deta configuration.
- **Methods**: 0

### deta.monitor.prober.ProbeResult
> Result of a health check probe.
- **Methods**: 0

### deta.scanner.openapi.EndpointDef
> Definition of an OpenAPI endpoint.
- **Methods**: 0

### deta.scanner.compose.ServiceDef
> Definition of a Docker Compose service.
- **Methods**: 0

## Data Transformation Functions

Key functions that process and transform data:

### deta.config._parse_config
> Parse configuration dictionary into DetaConfig object.
- **Output to**: DetaConfig, WatchConfig, ScanConfig, AnomalyConfig, MonitorConfig

### deta.scanner.python._parse_requirements
> Parse requirements.txt file and extract package names.
- **Output to**: open, line.strip, None.strip, line.startswith, line.startswith

### deta.scanner.ports.parse_port
> Parse a compose-style port string and resolve ``${VAR}`` references.
- **Output to**: None.strip, PortBinding, PortBinding, deta.scanner.env.interpolate, interpolated.rsplit

### deta.scanner.ports.parse_ports
- **Output to**: deta.scanner.ports.parse_port

### deta.scanner.compose._parse_ports
> Parse ports from various formats.
- **Output to**: isinstance, isinstance, result.append, isinstance, port.get

### deta.scanner.compose._parse_depends_on
> Parse depends_on from list or dict format.
- **Output to**: isinstance, isinstance, list, str, dep.keys

### deta.scanner.compose._parse_env
> Parse environment from list or dict format.
- **Output to**: isinstance, isinstance, isinstance, item.split

### deta.scanner.compose._parse_labels
> Parse labels from list or dict format.
- **Output to**: isinstance, isinstance, isinstance, item.split

### deta.formatter.toon._format_header
> Generate header section.
- **Output to**: None.strftime, datetime.now

### deta.formatter.toon._format_health
> Generate HEALTH section.
- **Output to**: sum, len, len, len

### deta.formatter.toon._format_alert_line
> Format single alert line.
- **Output to**: None.get, None.join, alert.get, Path, None.join

### deta.formatter.toon._format_alerts
> Generate ALERTS section.
- **Output to**: sorted, lines.extend, lines.append, deta.formatter.toon._format_alert_line, severity_order.get

### deta.formatter.toon._format_service_line
> Format single service line.
- **Output to**: None.join, None.join

### deta.formatter.toon._format_services
> Generate SERVICES section.
- **Output to**: lines.extend, lines.append, deta.formatter.toon._format_service_line, len

### deta.formatter.toon._format_endpoint_line
> Format single endpoint line.
- **Output to**: None.join, Path

### deta.formatter.toon._format_endpoints
> Generate ENDPOINTS section.
- **Output to**: deta.formatter.toon._group_endpoints_by_service, by_service.items, lines.append, lines.append, len

### deta.formatter.toon._format_cycles
> Generate CYCLES section.
- **Output to**: lines.extend, lines.append, len, None.join

### deta.formatter.toon._format_hubs
> Generate HUBS section.
- **Output to**: lines.extend, lines.append, len

### project.map.toon._resolve_formats

### project.map.toon._parse_config

### project.map.toon.format_probe_change

### project.map.toon.format_port_changes

### project.map.toon.format_service_changes

### project.map.toon._format_header

### project.map.toon._format_health

## Behavioral Patterns

### recursion__deep_merge
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: deta.scanner.compose._deep_merge

### recursion_interpolate_recursive
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: deta.scanner.env.interpolate_recursive

### state_machine_ConnectionManager
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: deta.web.app.ConnectionManager.__init__, deta.web.app.ConnectionManager.connect, deta.web.app.ConnectionManager.has_connections, deta.web.app.ConnectionManager.disconnect, deta.web.app.ConnectionManager.broadcast

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `deta.web.app.create_app` - 121 calls
- `deta.cli.main` - 66 calls
- `deta.cli.diff` - 27 calls
- `deta.monitor.prober.probe_port` - 21 calls
- `deta.formatter.toon.generate_toon` - 21 calls
- `deta.formatter.graph.generate_mermaid` - 21 calls
- `deta.scanner.python.scan_python` - 20 calls
- `deta.monitor.alerter.print_topology_table` - 19 calls
- `deta.monitor.prober.probe_service` - 19 calls
- `deta.formatter.graph.save_png` - 19 calls
- `deta.scanner.npm.scan_npm` - 18 calls
- `deta.monitor.prober.probe_all` - 14 calls
- `deta.scanner.openapi.scan_openapi` - 14 calls
- `deta.scanner.env.load_env_file` - 14 calls
- `deta.scanner.ports.parse_port` - 12 calls
- `deta.dsl.commands.format_probe_change` - 12 calls
- `deta.web.app.ConnectionManager.broadcast` - 10 calls
- `deta.monitor.alerter.alert_anomaly` - 10 calls
- `deta.monitor.watcher.watch_configs` - 10 calls
- `deta.integration.semcod.pre_deploy_check` - 10 calls
- `deta.formatter.graph.generate_graph_yaml` - 10 calls
- `deta.cli.scan` - 10 calls
- `deta.scanner.env.discover_env` - 9 calls
- `deta.dsl.commands.format_service_changes` - 8 calls
- `deta.config.load_config` - 7 calls
- `deta.scanner.compose.scan_compose` - 7 calls
- `deta.scanner.env.interpolate_recursive` - 7 calls
- `deta.dsl.commands.status_summary` - 7 calls
- `deta.web.app.run_dashboard` - 6 calls
- `deta.scanner.env.interpolate` - 6 calls
- `deta.integration.semcod.generate_for_pyqual` - 6 calls
- `deta.dsl.commands.format_port_changes` - 6 calls
- `deta.dsl.commands.service_down` - 5 calls
- `deta.scanner.env.merge_env_files` - 4 calls
- `deta.integration.semcod.generate_for_sumd` - 4 calls
- `deta.integration.semcod.generate_for_vallm` - 4 calls
- `deta.cli.monitor` - 4 calls
- `deta.monitor.alerter.alert_probe_failure` - 3 calls
- `deta.monitor.alerter.alert_probe_success` - 3 calls
- `deta.dsl.commands.service_up` - 3 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> Typer
    main --> command
    scan_npm --> rglob
    scan_npm --> len
    scan_npm --> loads
    scan_npm --> append
    scan_npm --> relative_to
    scan_openapi --> rglob
    scan_openapi --> len
    scan_openapi --> _load
    scan_openapi --> get
    format_probe_change --> group_probes_by_serv
    format_probe_change --> set
    format_probe_change --> get
    broadcast --> dumps
    broadcast --> len
    broadcast --> list
    broadcast --> zip
    broadcast --> encode
    pre_deploy_check --> Path
    pre_deploy_check --> build_topology
    pre_deploy_check --> detect_anomalies
    pre_deploy_check --> append
    format_service_chang --> set
    format_service_chang --> keys
    format_service_chang --> append
    scan_compose --> _get_yaml_loader
    scan_compose --> _collect_compose_fil
    scan_compose --> items
    scan_compose --> _merge_services
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.