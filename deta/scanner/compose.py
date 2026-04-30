"""
Docker-compose manifest scanner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deta.scanner.env import (
    discover_env,
    interpolate,
    interpolate_recursive,
    merge_env_files,
)
from deta.scanner.ports import PortBinding, parse_ports


@dataclass
class ServiceDef:
    """Definition of a Docker Compose service."""
    name: str
    image: str | None
    ports: list[str] = field(default_factory=list)
    healthcheck: dict | None = None
    depends_on: list[str] = field(default_factory=list)
    environment: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    source_file: str = ""
    resolved_ports: list[PortBinding] = field(default_factory=list)
    env_resolved: dict[str, str] = field(default_factory=dict)


def scan_compose(root: Path, max_depth: int = 3) -> list[ServiceDef]:
    """
    Scan for docker-compose files and extract service definitions.
    
    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth to scan
        
    Returns:
        List of ServiceDef objects
    """
    try:
        from ruamel.yaml import YAML
    except ImportError:
        from yaml import safe_load as yaml_load
        YAML = None
    
    services: list[ServiceDef] = []
    patterns = [
        "docker-compose*.yml",
        "docker-compose*.yaml",
        "compose.yml",
        "compose.yaml",
    ]

    seen: set[Path] = set()
    for pattern in patterns:
        for compose_file in root.rglob(pattern):
            if compose_file in seen:
                continue
            seen.add(compose_file)
            depth = len(compose_file.relative_to(root).parts)
            if depth > max_depth:
                continue

            try:
                with open(compose_file) as f:
                    if YAML is not None:
                        yaml = YAML()
                        data = yaml.load(f) or {}
                    else:
                        import yaml
                        data = yaml.safe_load(f) or {}

                base_env = discover_env(compose_file, root)

                for svc_name, svc in (data.get("services") or {}).items():
                    service_env_files = _resolve_env_files(
                        svc.get("env_file"), compose_file.parent
                    )
                    layered_env = merge_env_files(base_env, service_env_files)
                    raw_environment = _parse_env(svc.get("environment", {}))
                    interpolated_env = {
                        k: interpolate(str(v), layered_env)
                        for k, v in raw_environment.items()
                    }
                    effective_env = {**layered_env, **interpolated_env}

                    raw_ports = _parse_ports(svc.get("ports", []))
                    resolved_ports = parse_ports(raw_ports, effective_env)
                    healthcheck = interpolate_recursive(
                        svc.get("healthcheck"), effective_env
                    )
                    image = interpolate(
                        str(svc.get("image") or ""), effective_env
                    ) or None

                    services.append(ServiceDef(
                        name=svc_name,
                        image=image,
                        ports=raw_ports,
                        healthcheck=healthcheck,
                        depends_on=_parse_depends_on(svc.get("depends_on", [])),
                        environment=interpolated_env,
                        labels=_parse_labels(svc.get("labels", {})),
                        source_file=str(compose_file),
                        resolved_ports=resolved_ports,
                        env_resolved=effective_env,
                    ))
            except Exception:
                # Skip files that can't be parsed
                continue

    return services


def _resolve_env_files(value: Any, base_dir: Path) -> list[Path]:
    if not value:
        return []
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, list):
        candidates = [str(item) for item in value]
    else:
        return []

    resolved: list[Path] = []
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = base_dir / path
        resolved.append(path)
    return resolved


def _parse_ports(ports: Any) -> list[str]:
    """Parse ports from various formats."""
    if isinstance(ports, list):
        result = []
        for port in ports:
            if isinstance(port, str):
                result.append(port)
            elif isinstance(port, dict):
                # Handle published: target format
                published = port.get("published")
                target = port.get("target")
                if published and target:
                    result.append(f"{published}:{target}")
        return result
    return []


def _parse_depends_on(dep: Any) -> list[str]:
    """Parse depends_on from list or dict format."""
    if isinstance(dep, list):
        return [str(d) for d in dep]
    if isinstance(dep, dict):
        return list(dep.keys())
    return []


def _parse_env(env: Any) -> dict:
    """Parse environment from list or dict format."""
    if isinstance(env, dict):
        return env
    if isinstance(env, list):
        result = {}
        for item in env:
            if isinstance(item, str):
                if "=" in item:
                    key, val = item.split("=", 1)
                    result[key] = val
                else:
                    result[item] = ""
        return result
    return {}


def _parse_labels(labels: Any) -> dict:
    """Parse labels from list or dict format."""
    if isinstance(labels, dict):
        return labels
    if isinstance(labels, list):
        result = {}
        for item in labels:
            if isinstance(item, str) and "=" in item:
                key, val = item.split("=", 1)
                result[key] = val
        return result
    return {}
