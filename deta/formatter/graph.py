"""Graph formatters for infrastructure topology."""

from __future__ import annotations

from pathlib import Path

from deta.builder.topology import InfraTopology
from deta.monitor.prober import ProbeResult


def _split_port_mapping(port: str) -> tuple[str, str]:
    brace_depth = 0
    split_idx = -1
    for idx, ch in enumerate(port):
        if ch == "{":
            brace_depth += 1
        elif ch == "}":
            brace_depth = max(0, brace_depth - 1)
        elif ch == ":" and brace_depth == 0:
            split_idx = idx
            break

    if split_idx == -1:
        value = port.strip()
        return value, value

    return port[:split_idx].strip(), port[split_idx + 1 :].strip()


def _resolve_host_port(host_port: str) -> str:
    if not host_port:
        return ""
    host_port = host_port.strip()

    if host_port.startswith("${") and host_port.endswith("}"):
        inner = host_port[2:-1]
        if ":-" in inner:
            default_val = inner.split(':-', 1)[1]
            return default_val if default_val.isdigit() else host_port
        if "-" in inner:
            default_val = inner.split('-', 1)[1]
            return default_val if default_val.isdigit() else host_port
        return host_port

    return host_port


def _parse_host_ports(ports: list[str]) -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for port in ports:
        if not port:
            continue
        host_port, container_port = _split_port_mapping(str(port))
        parsed.append(
            {
                "host": _resolve_host_port(host_port),
                "container": container_port,
            }
        )
    return parsed


def _safe_mermaid_id(name: str) -> str:
    return "n_" + "".join(ch if ch.isalnum() else "_" for ch in name)


def generate_graph_yaml(
    topology: InfraTopology,
    probe_results: dict[str, ProbeResult] | None = None,
) -> str:
    lines: list[str] = ["graph:", "  nodes:"]

    for service_name, svc in topology.services.items():
        online = None
        if probe_results and service_name in probe_results:
            online = probe_results[service_name].ok

        lines.append(f"    - id: {service_name}")
        lines.append(f"      image: {svc.image or ''}")
        lines.append("      hosts:")
        host_ports = _parse_host_ports(svc.ports)
        if host_ports:
            for hp in host_ports:
                lines.append(f"        - host: localhost")
                lines.append(f"          port: '{hp['host']}'")
                lines.append(f"          container_port: '{hp['container']}'")
        else:
            lines.append("        - host: localhost")
            lines.append("          port: ''")
            lines.append("          container_port: ''")

        if online is None:
            lines.append("      online: unknown")
        else:
            lines.append(f"      online: {'true' if online else 'false'}")

    lines.append("  edges:")
    for service_name, svc in topology.services.items():
        for dep in svc.depends_on:
            lines.append(f"    - from: {dep}")
            lines.append(f"      to: {service_name}")

    return "\n".join(lines) + "\n"


def save_graph_yaml(
    topology: InfraTopology,
    output_path: Path,
    probe_results: dict[str, ProbeResult] | None = None,
) -> None:
    output_path.write_text(generate_graph_yaml(topology, probe_results))


def generate_mermaid(
    topology: InfraTopology,
    probe_results: dict[str, ProbeResult] | None = None,
) -> str:
    lines = ["graph TD"]

    for service_name, svc in topology.services.items():
        node_id = _safe_mermaid_id(service_name)
        hosts = []
        for hp in _parse_host_ports(svc.ports):
            if hp["host"]:
                hosts.append(f"localhost:{hp['host']}")

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
        for service_name, result in probe_results.items():
            class_name = "online" if result.ok else "offline"
            lines.append(f"    class {_safe_mermaid_id(service_name)} {class_name}")

    return "\n".join(lines) + "\n"


def save_mermaid(
    topology: InfraTopology,
    output_path: Path,
    probe_results: dict[str, ProbeResult] | None = None,
) -> None:
    output_path.write_text(generate_mermaid(topology, probe_results))


def save_png(
    topology: InfraTopology,
    output_path: Path,
    probe_results: dict[str, ProbeResult] | None = None,
) -> None:
    try:
        from graphviz import Digraph
    except ImportError as exc:
        raise RuntimeError("graphviz python package is not installed") from exc

    dot = Digraph("infra", format="png")
    dot.attr(rankdir="LR")

    for service_name, svc in topology.services.items():
        hosts = []
        for hp in _parse_host_ports(svc.ports):
            if hp["host"]:
                hosts.append(f"localhost:{hp['host']}")

        label = service_name
        if hosts:
            label += "\n" + "\n".join(hosts[:3])

        attrs = {}
        if probe_results and service_name in probe_results:
            attrs["style"] = "filled"
            attrs["fillcolor"] = "#d1fae5" if probe_results[service_name].ok else "#fee2e2"

        dot.node(service_name, label, **attrs)

    for service_name, svc in topology.services.items():
        for dep in svc.depends_on:
            dot.edge(dep, service_name)

    rendered_path = dot.render(filename=output_path.stem, directory=str(output_path.parent), cleanup=True)
    if Path(rendered_path) != output_path:
        Path(rendered_path).rename(output_path)
