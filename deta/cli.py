"""
Command-line interface for deta infrastructure monitoring tool.
"""

import asyncio
import json
import sys
from pathlib import Path

from deta.builder.topology import build_topology, InfraTopology
from deta.config import load_config, DetaConfig
from deta.formatter.toon import save_toon
from deta.monitor.alerter import (
    alert_anomaly,
    alert_probe_failure,
    alert_probe_success,
    print_topology_table,
)
from deta.monitor.prober import probe_all
from deta.monitor.watcher import watch_configs


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


def scan(root: Path = Path("."), depth: int = 3, output: Path = Path("infra-map.json"), config: DetaConfig = None):
    if config is None:
        config = load_config()
    
    topology = _get_topology(root, depth, config)
    
    if config.anomaly:
        anomalies = topology.detect_anomalies()
        filtered_anomalies = _filter_anomalies(anomalies, config)
        topology._filtered_anomalies = filtered_anomalies
    
    output.write_text(topology.to_json())
    
    if config.output and config.output.toon_enabled:
        toon_path = Path(config.output.toon_path) if config.output.toon_path else Path("infra.toon.yaml")
        save_toon(topology, toon_path, config.project.get("name"))
    
    _print_summary(topology, output, config)


def monitor(root: Path = Path("."), interval: int = 30, depth: int = 3, config: DetaConfig = None):
    asyncio.run(_monitor_loop(root, interval, depth, config))


async def _monitor_loop(root: Path, interval: int, depth: int, config: DetaConfig = None):
    if config is None:
        config = load_config()
    
    print(f"Starting monitoring on {root} (interval: {interval}s)")
    print("Press Ctrl+C to stop\n")
    
    async def on_change(change: dict):
        print(f"\n[CHANGE] {change['type']}: {change['path']}")
        topology = _get_topology(root, depth, config)
        anomalies = topology.detect_anomalies()
        filtered_anomalies = _filter_anomalies(anomalies, config)
        
        for a in filtered_anomalies:
            alert_anomaly(a)
        
        if config.monitor and config.monitor.enabled:
            services = list(topology.services.values())
            results = await probe_all(services)
            for r in results:
                if r.ok:
                    alert_probe_success(r)
                else:
                    alert_probe_failure(r)
    
    topology = _get_topology(root, depth, config)
    _print_summary(topology, Path("infra-map.json"), config)
    
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
        config_file: Path = typer.Option(None, "--config", "-c", help="Path to deta.yaml config file"),
    ):
        config = load_config(config_file)
        
        if depth is None:
            depth = config.scan.max_depth if config.scan else 3
        if output is None:
            output = Path(config.output.json_path) if config.output else Path("infra-map.json")
        
        scan(root, depth, output, config)
    
    @app.command("monitor")
    def monitor_cmd(
        root: Path = typer.Argument(Path("."), help="Root directory to monitor"),
        interval: int = typer.Option(None, help="Probe interval in seconds"),
        depth: int = typer.Option(None, help="Max scan depth"),
        config_file: Path = typer.Option(None, "--config", "-c", help="Path to deta.yaml config file"),
    ):
        config = load_config(config_file)
        
        if interval is None:
            interval = config.monitor.interval_seconds if config.monitor else 30
        if depth is None:
            depth = config.scan.max_depth if config.scan else 3
        
        monitor(root, interval, depth, config)
    
    @app.command("diff")
    def diff_cmd(
        baseline: Path = typer.Option(Path("infra-map.json"), help="Baseline file"),
        root: Path = typer.Argument(Path("."), help="Root directory to scan"),
        config_file: Path = typer.Option(None, "--config", "-c", help="Path to deta.yaml config file"),
    ):
        config = load_config(config_file)
        diff(baseline, root, config)
    
    app()


if __name__ == "__main__":
    main()