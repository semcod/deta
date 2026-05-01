"""
DSL command generators for infrastructure changes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from deta.builder.topology import InfraTopology
from deta.monitor.prober import ProbeResult, group_probes_by_service
from deta.scanner.compose import ServiceDef


@dataclass
class ChangeDSL:
    """Represents a DSL command."""
    command: str
    target: str
    params: dict[str, str]
    timestamp: str

    def __str__(self) -> str:
        params_str = " ".join(f"{k}={v}" for k, v in sorted(self.params.items()) if v)
        if params_str:
            return f"[{self.timestamp}] {self.command} {self.target} {params_str}"
        return f"[{self.timestamp}] {self.command} {self.target}"


def _escape_value(value: str) -> str:
    """Escape special characters in values."""
    value = str(value)
    if " " in value or "=" in value or '"' in value:
        value = value.replace('"', '\\"')
        return f'"{value}"'
    return value


def service_up(service: str, port: str = "", latency_ms: float = 0, url: str = "") -> ChangeDSL:
    """Generate SERVICE_UP command."""
    return ChangeDSL(
        command="SERVICE_UP",
        target=service,
        params={
            "port": port,
            "latency_ms": f"{latency_ms:.0f}",
            "url": url,
        },
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def service_down(
    service: str,
    port: str = "",
    error: str = "",
    status: Optional[int] = None,
    url: str = "",
) -> ChangeDSL:
    """Generate SERVICE_DOWN command."""
    params: dict[str, str] = {"port": port, "url": url}
    if error:
        params["error"] = _escape_value(error[:50])  # Truncate long errors
    if status is not None:
        params["status"] = str(status)
    return ChangeDSL(
        command="SERVICE_DOWN",
        target=service,
        params=params,
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def port_added(service: str, host_port: str, container_port: str, host: str = "") -> ChangeDSL:
    """Generate PORT_ADDED command."""
    port_mapping = f"{host}:{host_port}->{container_port}" if host else f"{host_port}->{container_port}"
    return ChangeDSL(
        command="PORT_ADDED",
        target=service,
        params={"mapping": port_mapping, "host": host, "host_port": host_port, "container_port": container_port},
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def port_removed(service: str, host_port: str, container_port: str, host: str = "") -> ChangeDSL:
    """Generate PORT_REMOVED command."""
    port_mapping = f"{host}:{host_port}->{container_port}" if host else f"{host_port}->{container_port}"
    return ChangeDSL(
        command="PORT_REMOVED",
        target=service,
        params={"mapping": port_mapping, "host": host, "host_port": host_port, "container_port": container_port},
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def service_added(service: str, image: str = "", source: str = "") -> ChangeDSL:
    """Generate SERVICE_ADDED command."""
    return ChangeDSL(
        command="SERVICE_ADDED",
        target=service,
        params={"image": image, "source": source},
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def service_removed(service: str) -> ChangeDSL:
    """Generate SERVICE_REMOVED command."""
    return ChangeDSL(
        command="SERVICE_REMOVED",
        target=service,
        params={},
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def status_summary(up: int, down: int, unknown: int, total: int) -> ChangeDSL:
    """Generate STATUS_SUMMARY command."""
    return ChangeDSL(
        command="STATUS_SUMMARY",
        target="",
        params={
            "up": str(up),
            "down": str(down),
            "unknown": str(unknown),
            "total": str(total),
        },
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def format_probe_change(
    prev_probes: list[ProbeResult],
    current_probes: list[ProbeResult],
) -> list[ChangeDSL]:
    """
    Compare probe results and generate DSL commands for status changes.

    Returns list of SERVICE_UP/SERVICE_DOWN commands.
    """
    commands: list[ChangeDSL] = []

    prev_by_svc = group_probes_by_service(prev_probes)
    curr_by_svc = group_probes_by_service(current_probes)

    for svc in set(prev_by_svc) | set(curr_by_svc):
        prev_list = prev_by_svc.get(svc, [])
        curr_list = curr_by_svc.get(svc, [])

        prev_ok = any(p.ok for p in prev_list)
        curr_ok = any(p.ok for p in curr_list)
        curr_probe = curr_list[0] if curr_list else None

        if not prev_ok and curr_ok and curr_probe:
            commands.append(service_up(
                svc,
                port=curr_probe.host_port,
                latency_ms=curr_probe.latency_ms,
                url=curr_probe.url,
            ))
        elif prev_ok and not curr_ok and curr_probe:
            commands.append(service_down(
                svc,
                port=curr_probe.host_port,
                error=curr_probe.error or "",
                status=curr_probe.status,
                url=curr_probe.url,
            ))

    return commands


def _port_key(p) -> tuple[str, str, str]:
    return (p.host, p.host_port, p.container_port)


def _diff_service_ports(
    svc_name: str,
    old_svc: ServiceDef | None,
    new_svc: ServiceDef | None,
) -> list[ChangeDSL]:
    """Generate PORT_ADDED/PORT_REMOVED commands for a single service."""
    if not old_svc and new_svc:
        return [port_added(svc_name, p.host_port, p.container_port, p.host) for p in new_svc.resolved_ports]
    if old_svc and not new_svc:
        return [port_removed(svc_name, p.host_port, p.container_port, p.host) for p in old_svc.resolved_ports]
    if not old_svc or not new_svc:
        return []

    old_keys = {_port_key(p) for p in old_svc.resolved_ports}
    new_keys = {_port_key(p) for p in new_svc.resolved_ports}

    cmds: list[ChangeDSL] = []
    for p in new_svc.resolved_ports:
        if _port_key(p) not in old_keys:
            cmds.append(port_added(svc_name, p.host_port, p.container_port, p.host))
    for p in old_svc.resolved_ports:
        if _port_key(p) not in new_keys:
            cmds.append(port_removed(svc_name, p.host_port, p.container_port, p.host))
    return cmds


def format_port_changes(
    old_topology: InfraTopology,
    new_topology: InfraTopology,
) -> list[ChangeDSL]:
    """
    Compare port bindings between topologies and generate DSL commands.

    Returns list of PORT_ADDED/PORT_REMOVED commands.
    """
    commands: list[ChangeDSL] = []
    for svc_name in set(old_topology.services) | set(new_topology.services):
        commands.extend(_diff_service_ports(
            svc_name,
            old_topology.services.get(svc_name),
            new_topology.services.get(svc_name),
        ))
    return commands


def format_service_changes(
    old_topology: InfraTopology,
    new_topology: InfraTopology,
) -> list[ChangeDSL]:
    """
    Compare services between topologies and generate DSL commands.

    Returns list of SERVICE_ADDED/SERVICE_REMOVED commands.
    """
    commands: list[ChangeDSL] = []

    old_services = set(old_topology.services.keys())
    new_services = set(new_topology.services.keys())

    for svc_name in new_services - old_services:
        svc = new_topology.services[svc_name]
        commands.append(service_added(
            svc_name,
            image=svc.image or "",
            source=svc.source_file,
        ))

    for svc_name in old_services - new_services:
        commands.append(service_removed(svc_name))

    return commands
