"""
Command-line interface for deta infrastructure monitoring tool.
"""

import asyncio
import json
import sys
from pathlib import Path

from deta.builder.topology import build_topology, InfraTopology
from deta.config import load_config, DetaConfig
from deta.formatter.graph import save_graph_yaml, save_mermaid, save_png
from deta.formatter.toon import save_toon
from deta.monitor.alerter import (
    alert_anomaly,
    alert_probe_failure,
    alert_probe_success,
    print_topology_table,
)
from deta.monitor.prober import probe_all
from deta.monitor.watcher import watch_configs
from deta.web import run_dashboard


def _get_topology(root: Path, depth: int, config: DetaConfig = None) -> InfraTopology:
    return build_topology(root, depth)


def _filter_anomalies(anomalies: list, config: DetaConfig) -> list:
    if not config.anomaly:
        return anomalies
    
    filtered = []
    for anomaly in anomalies:
        anomaly_type = anomaly.get("type")
        
        if anomaly_type == "missing_healthcheck" and not config.anomaly.check_missing_healthcheck:
            continue
        if anomaly_type == "port_conflict" and not config.anomaly.check_port_conflicts:
            continue
        if anomaly_type == "dependency_cycle" and not config.anomaly.check_dependency_cycles:
            continue
        if anomaly_type == "hardcoded_secret" and not config.anomaly.check_hardcoded_secrets:
            continue
        
        if config.anomaly.severity_levels and anomaly_type in config.anomaly.severity_levels:
            anomaly["severity"] = config.anomaly.severity_levels[anomaly_type]
        
        min_severity = config.alert.min_severity if config.alert else "info"
        severity_order = {"info": 0, "warning": 1, "error": 2, "critical": 3}
        if severity_order.get(anomaly.get("severity", "info"), 0) >= severity_order.get(min_severity, 0):
            filtered.append(anomaly)
    
    return filtered


def _print_summary(topology: InfraTopology, output: Path, config: DetaConfig = None):
    anomalies = getattr(topology, "_filtered_anomalies", None)
    if anomalies is None:
        anomalies = topology.detect_anomalies()
    
    print_topology_table(topology)
    
    if anomalies:
        print(f"\n=== Anomalies Detected ({len(anomalies)}) ===")
        for a in anomalies:
            alert_anomaly(a)
    else:
        print("\n✓ No anomalies detected")
    
    print(f"\n✓ Found {len(topology.services)} services, "
          f"{len(topology.endpoints)} endpoints, "
          f"{len(anomalies)} anomalies → {output}")


def _resolve_formats(formats: list[str] | None, config: DetaConfig) -> list[str]:
    selected = formats if formats else list(config.output.formats)
    normalized = []
    for item in selected:
        value = item.strip().lower()
        if value == "graph_yaml":
            value = "yaml"
        normalized.append(value)
    return normalized


def _probe_once(topology: InfraTopology) -> dict:
    services = list(topology.services.values())
    if not services:
        return {}
    results = asyncio.run(probe_all(services))
    by_service = {r.service: r for r in results}
    for result in results:
        if result.ok:
            alert_probe_success(result)
        else:
            alert_probe_failure(result)
    return by_service


def _write_outputs(
    topology: InfraTopology,
    config: DetaConfig,
    output: Path,
    formats: list[str],
    probe_results: list | None,
) -> None:
    if "json" in formats:
        output.write_text(topology.to_json())

    if "toon" in formats and config.output.toon_enabled:
        save_toon(topology, Path(config.output.toon_path), config.project.get("name"))

    if "yaml" in formats:
        save_graph_yaml(topology, Path(config.output.graph_yaml_path), probe_results)

    if "mermaid" in formats:
        save_mermaid(topology, Path(config.output.mermaid_path), probe_results)

    if "png" in formats:
        try:
            save_png(topology, Path(config.output.png_path), probe_results)
        except RuntimeError as exc:
            print(f"WARNING: {exc}; skipping PNG export")


def scan(
    root: Path = Path("."),
    depth: int = 3,
    output: Path = Path("infra-map.json"),
    config: DetaConfig = None,
    formats: list[str] | None = None,
    online: bool | None = None,
):
    if config is None:
        config = load_config()

    selected_formats = _resolve_formats(formats, config)
    online_enabled = config.monitor.probe_online if online is None else online
    
    topology = _get_topology(root, depth, config)
    
    if config.anomaly:
        anomalies = topology.detect_anomalies()
        filtered_anomalies = _filter_anomalies(anomalies, config)
        topology._filtered_anomalies = filtered_anomalies
    
    probe_results = _probe_once(topology) if online_enabled else None
    _write_outputs(topology, config, output, selected_formats, probe_results)
    
    _print_summary(topology, output, config)


def monitor(
    root: Path = Path("."),
    interval: int = 30,
    depth: int = 3,
    config: DetaConfig = None,
    output: Path = Path("infra-map.json"),
    formats: list[str] | None = None,
    online: bool | None = None,
):
    asyncio.run(_monitor_loop(root, interval, depth, config, output, formats, online))


def _extract_ports_snapshot(topology: InfraTopology) -> dict[str, list[str]]:
    """Extract port bindings snapshot for change detection."""
    snapshot: dict[str, list[str]] = {}
    for svc in topology.services.values():
        ports = [f"{p.host}:{p.host_port}->{p.container_port}" for p in svc.resolved_ports]
        snapshot[svc.name] = sorted(ports)
    return snapshot


def _log_port_changes(
    old_snapshot: dict[str, list[str]], new_snapshot: dict[str, list[str]]
):
    """Log port changes between snapshots."""
    all_services = set(old_snapshot.keys()) | set(new_snapshot.keys())
    for svc in sorted(all_services):
        old_ports = set(old_snapshot.get(svc, []))
        new_ports = set(new_snapshot.get(svc, []))
        added = new_ports - old_ports
        removed = old_ports - new_ports
        if added:
            print(f"[PORT ADD] {svc}: +{', '.join(sorted(added))}")
        if removed:
            print(f"[PORT REMOVED] {svc}: -{', '.join(sorted(removed))}")


def _print_status_summary(topology: InfraTopology, probe_results: list | None):
    """Print compact status summary of all services."""
    print(f"\n=== STATUS [{datetime.now().strftime('%H:%M:%S')}] ===")
    services = sorted(topology.services.values(), key=lambda s: s.name)
    for svc in services:
        ports = ",".join(p.host_port for p in svc.resolved_ports) or "-"
        health = "✓" if svc.healthcheck else "✗"
        if probe_results:
            service_probes = [p for p in probe_results if p.service == svc.name]
            if service_probes:
                # Overall status: UP if any port is UP
                ok = any(p.ok for p in service_probes)
                status = "UP" if ok else "DOWN"
                print(f"  {svc.name:<20} {status:<5} ports={ports:<12} health={health}")
            else:
                print(f"  {svc.name:<20} -     ports={ports:<12} health={health}")
        else:
            print(f"  {svc.name:<20} -     ports={ports:<12} health={health}")
    print("")


async def _monitor_loop(
    root: Path,
    interval: int,
    depth: int,
    config: DetaConfig = None,
    output: Path = Path("infra-map.json"),
    formats: list[str] | None = None,
    online: bool | None = None,
):
    from datetime import datetime
    if config is None:
        config = load_config()

    selected_formats = _resolve_formats(formats, config)
    online_enabled = config.monitor.probe_online if online is None else online

    print(f"Starting monitoring on {root} (interval: {interval}s)")
    print("Press Ctrl+C to stop\n")

    # State for change detection
    ports_snapshot: dict[str, list[str]] = {}
    last_status_time = 0.0

    async def on_change(change: dict):
        nonlocal ports_snapshot, last_status_time
        print(f"\n[CHANGE] {change['type']}: {change['path']}")
        topology = _get_topology(root, depth, config)
        new_snapshot = _extract_ports_snapshot(topology)
        _log_port_changes(ports_snapshot, new_snapshot)
        ports_snapshot = new_snapshot

        anomalies = topology.detect_anomalies()
        filtered_anomalies = _filter_anomalies(anomalies, config)
        topology._filtered_anomalies = filtered_anomalies

        for a in filtered_anomalies:
            alert_anomaly(a)

        probe_results = None
        if online_enabled:
            services = list(topology.services.values())
            probe_results = await probe_all(services)
            for r in probe_results:
                if r.ok:
                    alert_probe_success(r)
                else:
                    alert_probe_failure(r)

        # Print status if minute elapsed
        now = datetime.utcnow().timestamp()
        if now - last_status_time >= 60:
            _print_status_summary(topology, probe_results)
            last_status_time = now

        _write_outputs(topology, config, output, selected_formats, probe_results)
    
    topology = _get_topology(root, depth, config)
    anomalies = topology.detect_anomalies()
    topology._filtered_anomalies = _filter_anomalies(anomalies, config)

    initial_probe_results = None
    if online_enabled:
        services = list(topology.services.values())
        initial_probe_results = await probe_all(services)
        for r in initial_probe_results:
            if r.ok:
                alert_probe_success(r)
            else:
                alert_probe_failure(r)

    _write_outputs(topology, config, output, selected_formats, initial_probe_results)
    _print_summary(topology, output, config)

    # Initialize snapshot for port change tracking
    ports_snapshot = _extract_ports_snapshot(topology)

    try:
        await watch_configs(root, on_change)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")


def diff(baseline: Path = Path("infra-map.json"), root: Path = Path("."), config: DetaConfig = None):
    if config is None:
        config = load_config()
    
    if not baseline.exists():
        print(f"ERROR: Baseline file {baseline} not found")
        return
    
    try:
        baseline_data = json.loads(baseline.read_text())
        depth = config.scan.max_depth if config.scan else 3
        current_topology = _get_topology(root, depth, config)
        current_data = json.loads(current_topology.to_json())
        
        baseline_services = set(baseline_data.get("services", {}).keys())
        current_services = set(current_data.get("services", {}).keys())
        
        added = current_services - baseline_services
        removed = baseline_services - current_services
        
        if added:
            print(f"\n[+] Added services: {', '.join(added)}")
        if removed:
            print(f"[-] Removed services: {', '.join(removed)}")
        
        if not added and not removed:
            print("\n✓ No service changes detected")
        
        baseline_anomalies = len(baseline_data.get("anomalies", []))
        current_anomalies = len(current_data.get("anomalies", []))
        
        print(f"\nAnomalies: {baseline_anomalies} → {current_anomalies}")
        
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in baseline file {baseline}")


def main():
    try:
        import typer
    except ImportError:
        print("ERROR: typer not installed. Install with: pip install typer")
        sys.exit(1)
    
    app = typer.Typer(help="Infrastructure anomaly monitor")
    
    @app.command("scan")
    def scan_cmd(
        root: Path = typer.Argument(Path("."), help="Root directory to scan"),
        depth: int = typer.Option(None, help="Max scan depth (overrides deta.yaml)"),
        output: Path = typer.Option(None, help="Output file (overrides deta.yaml)"),
        watch: bool = typer.Option(False, help="Run continuously and regenerate outputs on changes"),
        interval: int = typer.Option(None, help="Watch/probe interval in seconds"),
        online: bool = typer.Option(True, help="Check what is online via HTTP probes"),
        formats: str = typer.Option(None, help="Comma-separated formats: json,toon,yaml,mermaid,png"),
        config_file: Path = typer.Option(None, "--config", "-c", help="Path to deta.yaml config file"),
    ):
        config = load_config(config_file)
        
        if depth is None:
            depth = config.scan.max_depth if config.scan else 3
        if output is None:
            output = Path(config.output.json_path) if config.output else Path("infra-map.json")

        selected_formats = None
        if formats:
            selected_formats = [f.strip() for f in formats.split(",") if f.strip()]

        if watch:
            if interval is None:
                interval = config.monitor.interval_seconds if config.monitor else 30
            monitor(root, interval, depth, config, output, selected_formats, online)
            return
        
        scan(root, depth, output, config, selected_formats, online)
    
    @app.command("monitor")
    def monitor_cmd(
        root: Path = typer.Argument(Path("."), help="Root directory to monitor"),
        interval: int = typer.Option(None, help="Probe interval in seconds"),
        depth: int = typer.Option(None, help="Max scan depth"),
        output: Path = typer.Option(None, help="Output file (overrides deta.yaml)"),
        online: bool = typer.Option(True, help="Check what is online via HTTP probes"),
        formats: str = typer.Option(None, help="Comma-separated formats: json,toon,yaml,mermaid,png"),
        config_file: Path = typer.Option(None, "--config", "-c", help="Path to deta.yaml config file"),
    ):
        config = load_config(config_file)
        
        if interval is None:
            interval = config.monitor.interval_seconds if config.monitor else 30
        if depth is None:
            depth = config.scan.max_depth if config.scan else 3
        if output is None:
            output = Path(config.output.json_path) if config.output else Path("infra-map.json")

        selected_formats = None
        if formats:
            selected_formats = [f.strip() for f in formats.split(",") if f.strip()]
        
        monitor(root, interval, depth, config, output, selected_formats, online)
    
    @app.command("diff")
    def diff_cmd(
        baseline: Path = typer.Option(Path("infra-map.json"), help="Baseline file"),
        root: Path = typer.Argument(Path("."), help="Root directory to scan"),
        config_file: Path = typer.Option(None, "--config", "-c", help="Path to deta.yaml config file"),
    ):
        config = load_config(config_file)
        diff(baseline, root, config)

    @app.command("web")
    def web_cmd(
        root: Path = typer.Argument(Path("."), help="Root directory to monitor"),
        depth: int = typer.Option(None, help="Max scan depth"),
        host: str = typer.Option(None, help="Bind host"),
        port: int = typer.Option(None, help="Bind port"),
        config_file: Path = typer.Option(None, "--config", "-c", help="Path to deta.yaml config file"),
    ):
        config = load_config(config_file)
        if depth is None:
            depth = config.scan.max_depth if config.scan else 3
        run_dashboard(root=root, depth=depth, config_file=config_file, host=host, port=port)
    
    app()


if __name__ == "__main__":
    main()