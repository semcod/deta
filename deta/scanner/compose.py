"""
Docker-compose manifest scanner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import fnmatch
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
    environment_raw: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    source_file: str = ""
    resolved_ports: list[PortBinding] = field(default_factory=list)
    env_resolved: dict[str, str] = field(default_factory=dict)


def _matches_any_pattern(path: Path, root: Path, patterns: list[str] | None) -> bool:
    """Return True when file path matches any glob pattern (name or relative path)."""
    if not patterns:
        return False

    rel_path = path.relative_to(root).as_posix()
    filename = path.name
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(filename, pattern):
            return True
    return False


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries. Lists are replaced, dicts are merged."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _get_yaml_loader():
    """Get YAML loader (ruamel.yaml or fallback to pyyaml)."""
    try:
        from ruamel.yaml import YAML
        return YAML()
    except ImportError:
        return None


def _load_yaml_file(file_path: Path, yaml_loader) -> dict:
    """Load a YAML file and return parsed data."""
    try:
        with open(file_path) as f:
            if yaml_loader is not None:
                return yaml_loader.load(f) or {}
            else:
                import yaml
                return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _collect_compose_files(
    root: Path,
    max_depth: int,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> dict[Path, list[Path]]:
    """
    Group compose files by their directory (project).
    Files in the same directory are merged (Docker Compose behavior).
    """
    patterns = [
        "docker-compose*.yml",
        "docker-compose*.yaml",
        "compose.yml",
        "compose.yaml",
    ]

    project_files: dict[Path, list[Path]] = {}
    seen: set[Path] = set()

    for pattern in patterns:
        for compose_file in root.rglob(pattern):
            if compose_file in seen:
                continue
            seen.add(compose_file)

            if _matches_any_pattern(compose_file, root, exclude_patterns):
                continue
            if include_patterns and not _matches_any_pattern(compose_file, root, include_patterns):
                continue

            depth = len(compose_file.relative_to(root).parts)
            if depth > max_depth:
                continue

            project_dir = compose_file.parent
            project_files.setdefault(project_dir, []).append(compose_file)

    # Sort files in each project for consistent ordering
    # Base files first, then overrides
    for files in project_files.values():
        files.sort(key=lambda p: (not p.name.startswith("docker-compose"), p.name))

    return project_files


def _merge_services(compose_files: list[Path], yaml_loader) -> dict[str, dict]:
    """Merge all compose files in a project into single service definitions."""
    merged_services: dict[str, dict] = {}

    for compose_file in compose_files:
        data = _load_yaml_file(compose_file, yaml_loader)
        for svc_name, svc in (data.get("services") or {}).items():
            if svc_name in merged_services:
                merged_services[svc_name] = _deep_merge(merged_services[svc_name], dict(svc))
            else:
                merged_services[svc_name] = dict(svc)

    return merged_services


def _find_primary_source(
    svc_name: str, compose_files: list[Path], yaml_loader, project_dir: Path
) -> str:
    """Find the primary source file (first one defining this service)."""
    default = str(project_dir / "docker-compose.yml")
    for cf in compose_files:
        data = _load_yaml_file(cf, yaml_loader)
        if svc_name in (data.get("services") or {}):
            return str(cf)
    return default


def _build_service_def(
    svc_name: str,
    svc: dict,
    project_dir: Path,
    compose_files: list[Path],
    yaml_loader,
    root: Path,
) -> ServiceDef | None:
    """Build ServiceDef from service dictionary."""
    try:
        base_env = discover_env(project_dir, root)
        service_env_files = _resolve_env_files(svc.get("env_file"), project_dir)
        layered_env = merge_env_files(base_env, service_env_files)
        raw_environment = _parse_env(svc.get("environment", {}))
        interpolated_env = {
            k: interpolate(str(v), layered_env)
            for k, v in raw_environment.items()
        }
        raw_environment_as_str = {
            k: str(v)
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

        primary_source = _find_primary_source(svc_name, compose_files, yaml_loader, project_dir)

        return ServiceDef(
            name=svc_name,
            image=image,
            ports=raw_ports,
            healthcheck=healthcheck,
            depends_on=_parse_depends_on(svc.get("depends_on", [])),
            environment=interpolated_env,
            environment_raw=raw_environment_as_str,
            labels=_parse_labels(svc.get("labels", {})),
            source_file=primary_source,
            resolved_ports=resolved_ports,
            env_resolved=effective_env,
        )
    except Exception:
        return None


def scan_compose(
    root: Path,
    max_depth: int = 3,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> list[ServiceDef]:
    """
    Scan for docker-compose files and extract service definitions.

    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth to scan

    Returns:
        List of ServiceDef objects
    """
    yaml_loader = _get_yaml_loader()
    project_files = _collect_compose_files(
        root,
        max_depth,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )
    all_services: list[ServiceDef] = []

    for project_dir, compose_files in project_files.items():
        merged_services = _merge_services(compose_files, yaml_loader)

        for svc_name, svc in merged_services.items():
            service_def = _build_service_def(
                svc_name, svc, project_dir, compose_files, yaml_loader, root
            )
            if service_def:
                all_services.append(service_def)

    return all_services


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
