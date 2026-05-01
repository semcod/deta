"""Graph formatters for infrastructure topology."""

from __future__ import annotations

from pathlib import Path

from deta.builder.topology import InfraTopology
from deta.monitor.prober import ProbeResult, resolve_service_status, group_probes_by_service
from deta.scanner.compose import ServiceDef
from deta.scanner.ports import PortBinding, parse_ports


def _service_bindings(service: ServiceDef) -> list[PortBinding]:
    if service.resolved_ports:
        return service.resolved_ports
    return parse_ports(service.ports, service.env_resolved)


def _binding_host(binding: PortBinding) -> str:
    return binding.host or "localhost"


def _safe_mermaid_id(name: str) -> str:
    return "n_" + "".join(ch if ch.isalnum() else "_" for ch in name)


def _port_probe_status(probe: ProbeResult | None) -> str | None:
    """Resolve status for a single port probe. Returns None if no probe."""
    if probe is None:
        return None
    return resolve_service_status([probe])


def _graph_yaml_node(
    service_name: str,
    svc: ServiceDef,
    service_probes: list[ProbeResult],
) -> list[str]:
    """Generate YAML lines for a single service node."""
    lines: list[str] = []
    lines.append(f"    - id: {service_name}")
    lines.append(f"      image: {svc.image or ''}")
    lines.append("      hosts:")
    bindings = _service_bindings(svc)

    if bindings:
        for binding in bindings:
            lines.append(f"        - host: {_binding_host(binding)}")
            lines.append(f"          port: '{binding.host_port}'")
            lines.append(f"          container_port: '{binding.container_port}'")
            port_probe = next((p for p in service_probes if p.host_port == binding.host_port), None) if binding.host_port else None
            port_status = _port_probe_status(port_probe)
            if port_status:
                lines.append(f"          status: {port_status}")
    else:
        lines.append("        - host: localhost")
        lines.append("          port: ''")
        lines.append("          container_port: ''")

    lines.append(f"      status: {resolve_service_status(service_probes)}")
    return lines


def generate_graph_yaml(
    topology: InfraTopology,
    probe_results: list[ProbeResult] | None = None,
) -> str:
    probes_by_svc = group_probes_by_service(probe_results)
    lines: list[str] = ["graph:", "  nodes:"]

    for service_name, svc in topology.services.items():
        lines.extend(_graph_yaml_node(service_name, svc, probes_by_svc.get(service_name, [])))

    lines.append("  edges:")
    for service_name, svc in topology.services.items():
        for dep in svc.depends_on:
            lines.append(f"    - from: {dep}")
            lines.append(f"      to: {service_name}")

    return "\n".join(lines) + "\n"


def _save_output(output_path: Path, content: str) -> None:
    """Write content to file."""
    output_path.write_text(content)


def save_graph_yaml(
    topology: InfraTopology,
    output_path: Path,
    probe_results: list[ProbeResult] | None = None,
) -> None:
    _save_output(output_path, generate_graph_yaml(topology, probe_results))


def generate_mermaid(
    topology: InfraTopology,
    probe_results: list[ProbeResult] | None = None,
) -> str:
    lines = ["graph LR"]

    for service_name, svc in topology.services.items():
        node_id = _safe_mermaid_id(service_name)
        hosts = []
        for binding in _service_bindings(svc):
            if binding.host_port:
                hosts.append(f"{_binding_host(binding)}:{binding.host_port}")

        label = service_name
        if hosts:
            label = f"{service_name}\\n" + "\\n".join(hosts[:3])

        lines.append(f'    {node_id}["{label}"]')

    for service_name, svc in topology.services.items():
        dst = _safe_mermaid_id(service_name)
        for dep in svc.depends_on:
            src = _safe_mermaid_id(dep)
            lines.append(f"    {src} --> {dst}")

    if probe_results:
        lines.append("    classDef online fill:#d1fae5,stroke:#059669,stroke-width:2px")
        lines.append("    classDef offline fill:#fee2e2,stroke:#dc2626,stroke-width:2px")
        lines.append("    classDef restarting fill:#fef3c7,stroke:#d97706,stroke-width:2px")

        probes_by_svc = group_probes_by_service(probe_results)
        for service_name in topology.services.keys():
            status = resolve_service_status(probes_by_svc.get(service_name, []))
            if status != "unknown":
                lines.append(f"    class {_safe_mermaid_id(service_name)} {status}")

    return "\n".join(lines) + "\n"


def save_mermaid(
    topology: InfraTopology,
    output_path: Path,
    probe_results: list[ProbeResult] | None = None,
) -> None:
    _save_output(output_path, generate_mermaid(topology, probe_results))


def save_png(
    topology: InfraTopology,
    output_path: Path,
    probe_results: list[ProbeResult] | None = None,
) -> None:
    try:
        from graphviz import Digraph
    except ImportError as exc:
        raise RuntimeError("graphviz python package is not installed") from exc

    dot = Digraph("infra", format="png")
    dot.attr(rankdir="LR")

    probes_by_svc = group_probes_by_service(probe_results)
    for service_name, svc in topology.services.items():
        hosts = []
        for binding in _service_bindings(svc):
            if binding.host_port:
                hosts.append(f"{_binding_host(binding)}:{binding.host_port}")

        label = service_name
        if hosts:
            label += "\n" + "\n".join(hosts[:3])

        attrs = {}
        service_probes = probes_by_svc.get(service_name, [])
        if service_probes:
            ok = resolve_service_status(service_probes) == "online"
            attrs["style"] = "filled"
            attrs["fillcolor"] = "#d1fae5" if ok else "#fee2e2"

        dot.node(service_name, label, **attrs)

    for service_name, svc in topology.services.items():
        for dep in svc.depends_on:
            dot.edge(dep, service_name)

    rendered_path = dot.render(filename=output_path.stem, directory=str(output_path.parent), cleanup=True)
    if Path(rendered_path) != output_path:
        Path(rendered_path).rename(output_path)
