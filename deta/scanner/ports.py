"""
Centralised parsing and resolution of docker-compose port mappings.

Compose accepts the following short-form syntaxes::

    "8080"
    "8080:80"
    "8080:80/tcp"
    "127.0.0.1:8080:80"
    "${PORT:-8080}:80"
    "${HOST:-127.0.0.1}:${PORT}:80"

This module centralises splitting and ``${VAR}`` resolution so that all
downstream consumers (probe, formatter, anomaly detection) see the same
host / host_port / container_port view.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from deta.scanner.env import interpolate

_HOST_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass
class PortBinding:
    """Resolved view of a single port mapping."""

    raw: str = ""
    host: str = ""
    host_port: str = ""
    container_port: str = ""
    protocol: str = ""

    @property
    def is_resolved(self) -> bool:
        return self.host_port.isdigit()


def _split_top_level(value: str, separator: str) -> list[str]:
    depth = 0
    parts: list[str] = []
    current: list[str] = []
    for char in value:
        if char == "{":
            depth += 1
            current.append(char)
        elif char == "}":
            depth = max(0, depth - 1)
            current.append(char)
        elif char == separator and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def parse_port(raw: str, env: dict[str, str] | None = None) -> PortBinding:
    """Parse a compose-style port string and resolve ``${VAR}`` references."""
    if not raw:
        return PortBinding()

    text = str(raw).strip()
    interpolated = interpolate(text, env or {}) if env else text

    protocol = ""
    if "/" in interpolated:
        interpolated, protocol = interpolated.rsplit("/", 1)

    parts = [part.strip() for part in _split_top_level(interpolated, ":")]

    host = ""
    host_port = ""
    container_port = ""

    if len(parts) == 1:
        host_port = container_port = parts[0]
    elif len(parts) == 2:
        host_port, container_port = parts
    else:
        host_candidate = parts[0]
        host_port = parts[1]
        container_port = parts[2]
        if _HOST_PATTERN.match(host_candidate or ""):
            host = host_candidate
        else:
            host = host_candidate

    return PortBinding(
        raw=str(raw),
        host=host,
        host_port=host_port,
        container_port=container_port,
        protocol=protocol,
    )


def parse_ports(
    ports: list[str] | None,
    env: dict[str, str] | None = None,
) -> list[PortBinding]:
    return [parse_port(p, env) for p in (ports or []) if p]


def published_url(binding: PortBinding, path: str = "/health") -> str | None:
    """Build a probe URL for the given binding, if it is fully resolved."""
    if not binding.is_resolved:
        return None
    host = binding.host or "localhost"
    suffix = path if path.startswith("/") else f"/{path}"
    return f"http://{host}:{binding.host_port}{suffix}"
