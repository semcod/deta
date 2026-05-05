"""
Docker-compose manifest scanner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import fnmatch
import json
from pathlib import Path
import subprocess
from typing import Any

from deta.scanner.env import (
    discover_env,
    interpolate,
    interpolate_recursive,
    merge_env_files,
)
from deta.scanner.ports import PortBinding, parse_ports


_ACTIVE_COMPOSE_FILENAMES = {
    "compose.yml",
    "compose.yaml",
    "compose.override.yml",
    "compose.override.yaml",
    "docker-compose.yml",
    "docker-compose.yaml",
    "docker-compose.override.yml",
    "docker-compose.override.yaml",
}

_DISCOVERY_GLOBS = [
    "docker-compose*.yml",
    "docker-compose*.yaml",
    "compose*.yml",
    "compose*.yaml",
]


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
    project_files: dict[Path, list[Path]] = {}
    include_mode, root_only_mode, active_only_mode = _compose_discovery_modes(root, include_patterns)

    for compose_file in _iter_discovered_compose_files(root):
        if not _should_collect_compose_file(
            compose_file,
            root,
            max_depth,
            include_patterns,
            exclude_patterns,
            include_mode,
            root_only_mode,
            active_only_mode,
        ):
            continue
        project_dir = compose_file.parent
        project_files.setdefault(project_dir, []).append(compose_file)

    # Sort files in each project for consistent ordering.
    # Base files first, then overrides, then any explicitly-included variants.
    for files in project_files.values():
        files.sort(
            key=lambda p: (
                p.name.endswith(".override.yml") or p.name.endswith(".override.yaml"),
                p.name,
            )
        )

    return project_files


def _compose_discovery_modes(
    root: Path,
    include_patterns: list[str] | None,
) -> tuple[bool, bool, bool]:
    include_mode = bool(include_patterns)
    has_root_active_compose = any((root / filename).exists() for filename in _ACTIVE_COMPOSE_FILENAMES)
    root_only_mode = not include_mode and has_root_active_compose
    active_only_mode = not include_mode
    return include_mode, root_only_mode, active_only_mode


def _iter_discovered_compose_files(root: Path):
    seen: set[Path] = set()
    for pattern in _DISCOVERY_GLOBS:
        for compose_file in root.rglob(pattern):
            if compose_file in seen:
                continue
            seen.add(compose_file)
            yield compose_file


def _should_collect_compose_file(
    compose_file: Path,
    root: Path,
    max_depth: int,
    include_patterns: list[str] | None,
    exclude_patterns: list[str] | None,
    include_mode: bool,
    root_only_mode: bool,
    active_only_mode: bool,
) -> bool:
    if root_only_mode and compose_file.parent != root:
        return False
    if active_only_mode and compose_file.name not in _ACTIVE_COMPOSE_FILENAMES:
        return False
    if _matches_any_pattern(compose_file, root, exclude_patterns):
        return False
    if include_mode and not _matches_any_pattern(compose_file, root, include_patterns):
        return False
    depth = len(compose_file.relative_to(root).parts)
    if depth > max_depth:
        return False
    return True


def _source_priority(service: ServiceDef, root: Path) -> tuple[int, int, int, str]:
    source_path = Path(service.source_file)
    try:
        depth = len(source_path.relative_to(root).parts)
    except ValueError:
        depth = 10_000
    has_healthcheck = 1 if service.healthcheck else 0
    resolved_bindings = sum(1 for binding in service.resolved_ports if binding.is_resolved)
    return (depth, -has_healthcheck, -resolved_bindings, service.source_file)


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


def _load_services_from_docker_compose_config(
    project_dir: Path,
    compose_files: list[Path],
    yaml_loader,
) -> dict[str, dict] | None:
    """Load resolved services from `docker compose config` output.

    Returns None when docker compose is unavailable or config cannot be resolved.
    """
    if not compose_files:
        return None

    for cmd in _docker_compose_config_commands(project_dir, compose_files):
        payload = _run_compose_config_command(cmd, project_dir)
        if payload is None:
            continue
        data = _parse_compose_config_payload(payload, yaml_loader)
        if not data:
            continue
        resolved = _extract_compose_services(data)
        if resolved is not None:
            return resolved

    return None


def _docker_compose_config_commands(project_dir: Path, compose_files: list[Path]) -> list[list[str]]:
    base_cmd = ["docker", "compose"]
    for compose_file in compose_files:
        base_cmd.extend(["-f", str(compose_file)])
    base_cmd.extend(["--project-directory", str(project_dir), "config"])
    return [
        [*base_cmd, "--format", "json"],
        base_cmd,
    ]


def _run_compose_config_command(cmd: list[str], project_dir: Path) -> str | None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None

    if proc.returncode != 0:
        return None
    payload = proc.stdout.strip()
    if not payload:
        return None
    return payload


def _parse_compose_config_payload(payload: str, yaml_loader) -> dict[str, Any] | None:
    try:
        loaded = json.loads(payload)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        pass

    try:
        if yaml_loader is not None:
            loaded = yaml_loader.load(payload) or {}
        else:
            import yaml

            loaded = yaml.safe_load(payload) or {}
    except Exception:
        return None

    if isinstance(loaded, dict):
        return loaded
    return None


def _extract_compose_services(data: dict[str, Any]) -> dict[str, dict] | None:
    services = data.get("services")
    if not isinstance(services, dict):
        return None

    resolved: dict[str, dict] = {}
    for name, definition in services.items():
        if isinstance(definition, dict):
            resolved[str(name)] = dict(definition)
    return resolved


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
        compose_env_source = compose_files[0] if compose_files else (project_dir / "docker-compose.yml")
        base_env = discover_env(compose_env_source, root)
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
        resolved_ports = parse_ports(raw_ports, base_env)
        healthcheck = interpolate_recursive(
            svc.get("healthcheck"), base_env
        )
        image = interpolate(
            str(svc.get("image") or ""), base_env
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
    use_dc_config: bool = True,
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
    deduplicated_services: dict[str, ServiceDef] = {}

    for project_dir in sorted(
        project_files.keys(), key=lambda p: (len(p.relative_to(root).parts), p.as_posix())
    ):
        compose_files = project_files[project_dir]
        merged_services = _merge_services(compose_files, yaml_loader)
        resolved_services = {}
        if use_dc_config:
            resolved_services = _load_services_from_docker_compose_config(
                project_dir,
                compose_files,
                yaml_loader,
            ) or {}

        all_names = list(dict.fromkeys([*merged_services.keys(), *resolved_services.keys()]))

        for svc_name in all_names:
            merged = merged_services.get(svc_name)
            resolved = resolved_services.get(svc_name)

            svc: dict[str, Any] = dict(merged) if isinstance(merged, dict) else {}
            if isinstance(resolved, dict):
                for key in ("ports", "healthcheck", "depends_on", "image"):
                    if key in resolved:
                        svc[key] = resolved[key]
            if not svc:
                continue

            service_def = _build_service_def(
                svc_name, svc, project_dir, compose_files, yaml_loader, root
            )
            if service_def:
                existing = deduplicated_services.get(service_def.name)
                if existing is None:
                    deduplicated_services[service_def.name] = service_def
                    continue

                if _source_priority(service_def, root) < _source_priority(existing, root):
                    deduplicated_services[service_def.name] = service_def

    return list(deduplicated_services.values())


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
                if published is not None and target is not None:
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
