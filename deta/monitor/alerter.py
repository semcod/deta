"""
Alerting module for displaying anomalies and probe results.
"""

from deta.builder.topology import InfraTopology
from deta.monitor.prober import ProbeResult

# Rich console for colored output
_console = None


def _get_console():
    """Get Rich console instance, fallback to basic print if unavailable."""
    global _console
    if _console is None:
        try:
            from rich.console import Console
            _console = Console()
        except ImportError:
            _console = False
    return _console


SEVERITY_COLORS = {
    "critical": "bold red",
    "error": "red",
    "warning": "yellow",
    "info": "cyan",
}


def alert_anomaly(anomaly: dict):
    """Display an anomaly with appropriate coloring."""
    console = _get_console()
    
    if console:
        from rich import print as rprint
        color = SEVERITY_COLORS.get(anomaly["severity"], "white")
        rprint(f"[{color}][{anomaly['severity'].upper()}][/{color}] "
               f"{anomaly['type']} → {anomaly.get('service', anomaly.get('services'))}")
        if "remediation_hints" in anomaly:
            rprint("   [cyan]➜ 🤖 Actionable for LLM (MCP hints):[/cyan]")
            for i, hint in enumerate(anomaly["remediation_hints"], 1):
                rprint(f"      {i}. {hint}")
    else:
        print(f"[{anomaly['severity'].upper()}] {anomaly['type']} → "
              f"{anomaly.get('service', anomaly.get('services'))}")
        if "remediation_hints" in anomaly:
            print("   ➜ 🤖 Actionable for LLM (MCP hints):")
            for i, hint in enumerate(anomaly["remediation_hints"], 1):
                print(f"      {i}. {hint}")


def alert_probe_failure(result: ProbeResult):
    """Display a failed probe result."""
    console = _get_console()

    hints = [
        f"Inspect logs: `docker logs --tail=100 {result.service}`",
    ]
    if result.url:
        hints.append(
            f"Verify the service binds to the correct host/port mapping for {result.url}"
        )
    else:
        hints.append(
            "Verify the service exposes a published port or explicit HTTP healthcheck URL."
        )
    hints.append("Ensure dependencies for this service are fully healthy.")

    if console:
        from rich import print as rprint
        rprint(f"[bold red][DOWN][/bold red] {result.service} "
               f"({result.url}) — {result.error or f'HTTP {result.status}'}")
        rprint("   [cyan]➜ 🤖 Actionable for LLM (MCP hints):[/cyan]")
        for i, hint in enumerate(hints, 1):
            rprint(f"      {i}. {hint}")
    else:
        print(f"[DOWN] {result.service} ({result.url}) — "
              f"{result.error or f'HTTP {result.status}'}")
        print("   ➜ 🤖 Actionable for LLM (MCP hints):")
        for i, hint in enumerate(hints, 1):
            print(f"      {i}. {hint}")


def alert_probe_success(result: ProbeResult):
    """Display a successful probe result."""
    console = _get_console()
    
    if console:
        from rich import print as rprint
        rprint(f"[green][UP][/green] {result.service} "
               f"({result.url}) — {result.latency_ms:.0f}ms")
    else:
        print(f"[UP] {result.service} ({result.url}) — {result.latency_ms:.0f}ms")


def print_topology_table(topology: InfraTopology):
    """Display infrastructure topology as a table."""
    console = _get_console()
    
    if console:
        from rich.table import Table
        table = Table(title="Infrastructure Map")
        table.add_column("Service", style="cyan")
        table.add_column("Image/Build")
        table.add_column("Ports")
        table.add_column("Healthcheck", style="green")
        table.add_column("Depends On")
        
        for name, svc in topology.services.items():
            table.add_row(
                name,
                svc.image or "[build]",
                ", ".join(svc.ports),
                "✓" if svc.healthcheck else "✗",
                ", ".join(svc.depends_on),
            )
        console.print(table)
    else:
        print("\n=== Infrastructure Map ===")
        print(f"{'Service':<20} {'Image/Build':<20} {'Ports':<15} {'Health':<10} {'Depends On'}")
        print("-" * 80)
        for name, svc in topology.services.items():
            print(f"{name:<20} {(svc.image or '[build]'):<20} {', '.join(svc.ports):<15} "
                  f"{'✓' if svc.healthcheck else '✗':<10} {', '.join(svc.depends_on)}")
