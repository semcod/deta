"""
Command-line interface for deta infrastructure monitoring tool.
"""

import asyncio
import json
import os
import signal
import socket
import subprocess
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


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _pid_on_port(host: str, port: int) -> int | None:
    import re as _re

    # ss: output contains users:(("name",pid=NNN,fd=N))
    try:
        proc = subprocess.run(
            ["ss", "-ltnp", f"( sport = :{port} )"],
            capture_output=True, text=True, check=False,
        )
        for m in _re.finditer(r"pid=(\d+)", proc.stdout or ""):
            pid = int(m.group(1))
            if pid > 1:
                return pid
    except FileNotFoundError:
        pass

    # lsof -t prints one PID per line
    try:
        proc = subprocess.run(
            ["lsof", "-t", f"-iTCP@{host}:{port}", "-sTCP:LISTEN"],
            capture_output=True, text=True, check=False,
        )
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if pid > 1:
                    return pid
    except FileNotFoundError:
        pass

    return None


def _terminate_pid(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False
    return True


def _get_topology(root: Path, depth: int, config: DetaConfig = None) -> InfraTopology:
    return build_topology(root, depth, config)


_ANOMALY_CHECK_MAP = {
    "missing_healthcheck": "check_missing_healthcheck",
    "port_conflict": "check_port_conflicts",
    "dependency_cycle": "check_dependency_cycles",
    "hardcoded_secret": "check_hardcoded_secrets",
}

_SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2, "critical": 3}


def _is_anomaly_enabled(anomaly_type: str, anomaly_config) -> bool:
    attr = _ANOMALY_CHECK_MAP.get(anomaly_type)
    return getattr(anomaly_config, attr, True) if attr else True


def _meets_severity_threshold(severity: str, min_severity: str) -> bool:
    return _SEVERITY_ORDER.get(severity, 0) >= _SEVERITY_ORDER.get(min_severity, 0)


def _filter_anomalies(anomalies: list, config: DetaConfig) -> list:
    if not config.anomaly:
        return anomalies
    
    min_severity = config.alert.min_severity if config.alert else "info"
    filtered = []
    for anomaly in anomalies:
        anomaly_type = anomaly.get("type")
        if not _is_anomaly_enabled(anomaly_type, config.anomaly):
            continue
        if config.anomaly.severity_levels and anomaly_type in config.anomaly.severity_levels:
            anomaly["severity"] = config.anomaly.severity_levels[anomaly_type]
        if _meets_severity_threshold(anomaly.get("severity", "info"), min_severity):
            filtered.append(anomaly)
    
    return filtered


def _print_summary(topology: InfraTopology, output: Path, config: DetaConfig = None, probe_results: dict | None = None):
    import json
    import yaml
    anomalies = getattr(topology, "_filtered_anomalies", None)
    if anomalies is None:
        anomalies = topology.detect_anomalies()
    
    data = json.loads(topology.to_json())
    data["anomalies"] = anomalies
    
    if probe_results:
        # inject probe results into services
        for svc_name, r in probe_results.items():
            if svc_name in data["services"]:
                data["services"][svc_name]["probe_status"] = "online" if r.ok else "offline"
                data["services"][svc_name]["probe_latency_ms"] = r.latency_ms
                if r.error:
                    data["services"][svc_name]["probe_error"] = r.error

    print(yaml.dump(data, sort_keys=False, default_flow_style=False))


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
    
    _print_summary(topology, output, config, probe_results)


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
    print("DSL commands enabled: SERVICE_UP, SERVICE_DOWN, PORT_ADDED, PORT_REMOVED, SERVICE_ADDED, SERVICE_REMOVED\n")

    # State for change detection
    ports_snapshot: dict[str, list[str]] = {}
    last_status_time = 0.0
    prev_topology: InfraTopology | None = None
    prev_probes: list = []

    async def on_change(change: dict):
        nonlocal ports_snapshot, last_status_time, prev_topology, prev_probes
        print(f"\n[CHANGE] {change['type']}: {change['path']}")

        topology = _get_topology(root, depth, config)
        new_snapshot = _extract_ports_snapshot(topology)
        _log_port_changes(ports_snapshot, new_snapshot)
        ports_snapshot = new_snapshot

        # DSL: Service changes (added/removed)
        if prev_topology:
            from deta.dsl import format_service_changes
            svc_changes = format_service_changes(prev_topology, topology)
            for cmd in svc_changes:
                print(f"  DSL> {cmd}")

        # DSL: Port changes
        if prev_topology:
            from deta.dsl import format_port_changes
            port_changes = format_port_changes(prev_topology, topology)
            for cmd in port_changes:
                print(f"  DSL> {cmd}")

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

            # DSL: Probe status changes
            if prev_probes:
                from deta.dsl import format_probe_change
                probe_changes = format_probe_change(prev_probes, probe_results)
                for cmd in probe_changes:
                    print(f"  DSL> {cmd}")

        # Print status if minute elapsed
        now = datetime.utcnow().timestamp()
        if now - last_status_time >= 60:
            _print_status_summary(topology, probe_results)
            # DSL: Status summary
            if probe_results:
                up = sum(1 for p in probe_results if p.ok)
                down = len(probe_results) - up
                unknown = len(topology.services) - len(probe_results)
                from deta.dsl import status_summary
                sum_cmd = status_summary(up, down, unknown, len(topology.services))
                print(f"  DSL> {sum_cmd}")
            last_status_time = now

        _write_outputs(topology, config, output, selected_formats, probe_results)
        prev_topology = topology
        prev_probes = probe_results or []
    
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


def diff(baseline: Path = Path("infra-map.json"), root: Path = Path("."), config: DetaConfig = None, toon: bool = False, output: Path = None):
    if config is None:
        config = load_config()
    
    if not baseline.exists():
        print(f"ERROR: Baseline file {baseline} not found")
        return
    
    try:
        baseline_data = json.loads(baseline.read_text())
        depth = config.scan.max_depth if config.scan else 3
        current_topology = _get_topology(root, depth, config)
        
        if toon:
            from deta.formatter.toon import generate_toon_diff
            content = generate_toon_diff(baseline_data, current_topology, config.project.get("name"))
            print(content)
            
            out_file = output if output else Path("infra-diff.toon.yaml")
            out_file.write_text(content)
            print(f"Saved changes to {out_file}")
            return

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
        output: Path = typer.Option(None, "-o", "--output", help="Output file (overrides deta.yaml)"),
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
        output: Path = typer.Option(None, "-o", "--output", help="Output file (overrides deta.yaml)"),
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
        toon: bool = typer.Option(False, "--toon", help="Output only changed services in toon format"),
        output: Path = typer.Option(None, "-o", "--output", help="Output file for toon format (optional)"),
    ):
        config = load_config(config_file)
        diff(baseline, root, config, toon, output)

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
        bind_host = host or config.web.host
        bind_port = port or config.web.port

        if _port_in_use(bind_host, bind_port):
            print(f"WARNING: Address {bind_host}:{bind_port} is already in use")
            pid = _pid_on_port(bind_host, bind_port)
            if pid:
                print(f"Detected PID on port {bind_port}: {pid}")
            should_kill = typer.confirm(
                f"Port {bind_port} is busy. Kill the current process and start deta web?",
                default=False,
            )
            if should_kill:
                if pid and _terminate_pid(pid):
                    print(f"Sent SIGTERM to PID {pid}")
                else:
                    print("Could not identify/terminate process automatically. Start aborted.")
                    raise typer.Exit(code=1)
            else:
                print("Start aborted by user.")
                raise typer.Exit(code=1)

        from deta.web import run_dashboard
        run_dashboard(
            root=root,
            depth=depth,
            config_file=config_file,
            host=bind_host,
            port=bind_port,
        )
    
    app()


if __name__ == "__main__":
    main()