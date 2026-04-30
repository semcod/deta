"""
Configuration loader for deta.yaml manifest.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional
import sys


@dataclass
class WatchConfig:
    """Watch configuration for file monitoring."""
    paths: list[str] = field(default_factory=lambda: ["."])
    exclude_patterns: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=lambda: [
        "docker-compose*.yml",
        "docker-compose*.yaml",
        "openapi*.yml",
        "openapi*.yaml",
        "openapi*.json",
        "package.json",
        "pyproject.toml",
        "requirements*.txt",
    ])
    max_depth: int = 3


@dataclass
class ScanConfig:
    """Scan configuration."""
    enabled: bool = True
    max_depth: int = 3
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=lambda: [
        "node_modules/**",
        ".git/**",
        "__pycache__/**",
        "*.pyc",
        ".pytest_cache/**",
        ".venv/**",
        "venv/**",
        "build/**",
        "dist/**",
    ])


@dataclass
class AnomalyConfig:
    """Anomaly detection configuration."""
    check_missing_healthcheck: bool = True
    check_port_conflicts: bool = True
    check_dependency_cycles: bool = True
    check_hardcoded_secrets: bool = True
    secret_patterns: list[str] = field(default_factory=lambda: [
        "secret",
        "password",
        "api_key",
        "token",
        "private_key",
    ])
    severity_levels: dict[str, str] = field(default_factory=lambda: {
        "missing_healthcheck": "warning",
        "port_conflict": "error",
        "dependency_cycle": "error",
        "hardcoded_secret": "critical",
    })


@dataclass
class MonitorConfig:
    """Real-time monitoring configuration."""
    enabled: bool = False
    interval_seconds: int = 30
    probe_timeout_seconds: int = 5
    probe_retries: int = 3


@dataclass
class OutputConfig:
    """Output configuration."""
    formats: list[str] = field(default_factory=lambda: ["json"])
    json_path: str = "infra-map.json"
    toon_path: str = "infra.toon.yaml"
    toon_enabled: bool = True


@dataclass
class AlertConfig:
    """Alert configuration."""
    console_enabled: bool = True
    colors_enabled: bool = True
    min_severity: str = "info"  # info, warning, error, critical


@dataclass
class DetaConfig:
    """Main deta configuration."""
    project: dict = field(default_factory=dict)
    watch: WatchConfig = field(default_factory=WatchConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    anomaly: AnomalyConfig = field(default_factory=AnomalyConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    alert: AlertConfig = field(default_factory=AlertConfig)


def load_config(config_path: Optional[Path] = None) -> DetaConfig:
    """
    Load deta.yaml configuration file.
    
    Args:
        config_path: Path to deta.yaml file. If None, searches in current directory.
        
    Returns:
        DetaConfig object with loaded configuration
    """
    if config_path is None:
        config_path = Path("deta.yaml")
    
    if not config_path.exists():
        return DetaConfig()
    
    try:
        data = _load_yaml(config_path)
        return _parse_config(data)
    except Exception as e:
        print(f"WARNING: Failed to load deta.yaml: {e}")
        return DetaConfig()


def _load_yaml(file_path: Path) -> dict:
    """Load YAML file."""
    try:
        import tomllib
        with open(file_path, "rb") as f:
            return tomllib.load(f)
    except (ImportError, ValueError):
        pass
    
    try:
        import tomli
        with open(file_path, "rb") as f:
            return tomli.load(f)
    except (ImportError, ValueError):
        pass
    
    try:
        import toml
        with open(file_path) as f:
            return toml.load(f)
    except (ImportError, ValueError):
        pass
    
    try:
        from ruamel.yaml import YAML
        yaml = YAML()
        with open(file_path) as f:
            return yaml.load(f) or {}
    except ImportError:
        import yaml
        with open(file_path) as f:
            return yaml.safe_load(f) or {}


def _parse_config(data: dict) -> DetaConfig:
    """Parse configuration dictionary into DetaConfig object."""
    config = DetaConfig()
    
    if "project" in data:
        config.project = data["project"]
    
    if "watch" in data:
        watch_data = data["watch"]
        config.watch = WatchConfig(
            paths=watch_data.get("paths", ["."]),
            exclude_patterns=watch_data.get("exclude_patterns", []),
            file_patterns=watch_data.get("file_patterns", config.watch.file_patterns),
            max_depth=watch_data.get("max_depth", 3),
        )
    
    if "scan" in data:
        scan_data = data["scan"]
        config.scan = ScanConfig(
            enabled=scan_data.get("enabled", True),
            max_depth=scan_data.get("max_depth", 3),
            include_patterns=scan_data.get("include_patterns", []),
            exclude_patterns=scan_data.get("exclude_patterns", config.scan.exclude_patterns),
        )
    
    if "anomaly" in data:
        anomaly_data = data["anomaly"]
        config.anomaly = AnomalyConfig(
            check_missing_healthcheck=anomaly_data.get("check_missing_healthcheck", True),
            check_port_conflicts=anomaly_data.get("check_port_conflicts", True),
            check_dependency_cycles=anomaly_data.get("check_dependency_cycles", True),
            check_hardcoded_secrets=anomaly_data.get("check_hardcoded_secrets", True),
            secret_patterns=anomaly_data.get("secret_patterns", config.anomaly.secret_patterns),
            severity_levels=anomaly_data.get("severity_levels", config.anomaly.severity_levels),
        )
    
    if "monitor" in data:
        monitor_data = data["monitor"]
        config.monitor = MonitorConfig(
            enabled=monitor_data.get("enabled", False),
            interval_seconds=monitor_data.get("interval_seconds", 30),
            probe_timeout_seconds=monitor_data.get("probe_timeout_seconds", 5),
            probe_retries=monitor_data.get("probe_retries", 3),
        )
    
    if "output" in data:
        output_data = data["output"]
        config.output = OutputConfig(
            formats=output_data.get("formats", ["json"]),
            json_path=output_data.get("json_path", "infra-map.json"),
            toon_path=output_data.get("toon_path", "infra.toon.yaml"),
            toon_enabled=output_data.get("toon_enabled", True),
        )
    
    if "alert" in data:
        alert_data = data["alert"]
        config.alert = AlertConfig(
            console_enabled=alert_data.get("console_enabled", True),
            colors_enabled=alert_data.get("colors_enabled", True),
            min_severity=alert_data.get("min_severity", "info"),
        )
    
    return config
