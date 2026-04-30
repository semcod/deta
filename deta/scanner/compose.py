"""
Docker-compose manifest scanner.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


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
    
    services = []
    patterns = ["docker-compose*.yml", "docker-compose*.yaml"]
    
    for pattern in patterns:
        for compose_file in root.rglob(pattern):
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
                
                for svc_name, svc in (data.get("services") or {}).items():
                    services.append(ServiceDef(
                        name=svc_name,
                        image=svc.get("image"),
                        ports=_parse_ports(svc.get("ports", [])),
                        healthcheck=svc.get("healthcheck"),
                        depends_on=_parse_depends_on(svc.get("depends_on", [])),
                        environment=_parse_env(svc.get("environment", {})),
                        labels=_parse_labels(svc.get("labels", {})),
                        source_file=str(compose_file),
                    ))
            except Exception as e:
                # Skip files that can't be parsed
                continue
    
    return services


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
