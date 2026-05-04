"""E2E tests: full scan pipeline from compose fixtures to YAML stdout.

Tests cover:
- YAML output format (no icons, plain text)
- Probe injection into output (probe_status / probe_latency_ms)
- Anomaly detection pipeline through CLI functions
- Offline mode (--online=false)
- Multi-module recursive scanning
- Dependency cycle detection
- Missing healthcheck detection
- Config-driven anomaly filtering
- Examples directory fixtures
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from deta.builder.topology import InfraTopology, build_topology
from deta.cli import _print_summary, _filter_anomalies, _get_topology, scan
from deta.config import load_config, DetaConfig, AnomalyConfig
from deta.scanner.compose import scan_compose
from deta.monitor.prober import ProbeResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compose(tmp_path: Path, content: str) -> Path:
    f = tmp_path / "docker-compose.yml"
    f.write_text(content)
    return f


def _scan_topo(tmp_path: Path, **kwargs) -> InfraTopology:
    services = scan_compose(tmp_path, max_depth=1, **kwargs)
    topo = InfraTopology()
    topo.add_services(services)
    return topo


# ---------------------------------------------------------------------------
# 1. YAML output — plain text, no icons
# ---------------------------------------------------------------------------

def test_print_summary_yaml_plain_text(tmp_path: Path, capsys):
    _compose(tmp_path, (
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "8080:80"\n'
        "    healthcheck:\n"
        '      test: ["CMD", "wget", "-q", "http://localhost/health"]\n'
        "      interval: 30s\n"
    ))
    topo = _scan_topo(tmp_path)
    _print_summary(topo, tmp_path / "out.json")
    captured = capsys.readouterr().out

    # Must be parseable YAML
    parsed = yaml.safe_load(captured)
    assert "services" in parsed
    assert "web" in parsed["services"]

    # No unicode icons
    for icon in ("✓", "✗", "→", "🤖", "➜", "[UP]", "[DOWN]"):
        assert icon not in captured


def test_print_summary_yaml_has_anomalies_key(tmp_path: Path, capsys):
    """anomalies key must always be present in YAML output."""
    _compose(tmp_path, "services:\n  svc:\n    image: alpine\n")
    topo = _scan_topo(tmp_path)
    _print_summary(topo, tmp_path / "out.json")
    parsed = yaml.safe_load(capsys.readouterr().out)
    assert "anomalies" in parsed


def test_print_summary_yaml_missing_healthcheck_in_anomalies(tmp_path: Path, capsys):
    """Service without healthcheck must appear in anomalies list."""
    _compose(tmp_path, (
        "services:\n"
        "  no-hc:\n"
        "    image: alpine\n"
        "    ports:\n"
        '      - "9000:80"\n'
    ))
    topo = _scan_topo(tmp_path)
    _print_summary(topo, tmp_path / "out.json")
    parsed = yaml.safe_load(capsys.readouterr().out)
    types = [a["type"] for a in parsed["anomalies"]]
    assert "missing_healthcheck" in types


# ---------------------------------------------------------------------------
# 2. Probe injection into YAML output
# ---------------------------------------------------------------------------

def test_print_summary_injects_probe_status_online(tmp_path: Path, capsys):
    _compose(tmp_path, (
        "services:\n"
        "  api:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "8080:80"\n'
    ))
    topo = _scan_topo(tmp_path)
    fake_probe = {
        "api": ProbeResult(
            service="api", url="http://localhost:8080/health",
            status=200, ok=True, latency_ms=12.5, error=None,
        )
    }
    _print_summary(topo, tmp_path / "out.json", probe_results=fake_probe)
    parsed = yaml.safe_load(capsys.readouterr().out)
    svc = parsed["services"]["api"]
    assert svc["probe_status"] == "online"
    assert svc["probe_latency_ms"] == pytest.approx(12.5, rel=0.01)


def test_print_summary_injects_probe_status_offline(tmp_path: Path, capsys):
    _compose(tmp_path, (
        "services:\n"
        "  db:\n"
        "    image: postgres\n"
        "    ports:\n"
        '      - "5432:5432"\n'
    ))
    topo = _scan_topo(tmp_path)
    fake_probe = {
        "db": ProbeResult(
            service="db", url="tcp://localhost:5432",
            status=None, ok=False, latency_ms=0, error="Connection refused",
        )
    }
    _print_summary(topo, tmp_path / "out.json", probe_results=fake_probe)
    parsed = yaml.safe_load(capsys.readouterr().out)
    svc = parsed["services"]["db"]
    assert svc["probe_status"] == "offline"
    assert svc["probe_error"] == "Connection refused"


def test_print_summary_no_probe_results_has_no_probe_keys(tmp_path: Path, capsys):
    """Without probe_results, services must not have probe_status keys."""
    _compose(tmp_path, "services:\n  svc:\n    image: alpine\n")
    topo = _scan_topo(tmp_path)
    _print_summary(topo, tmp_path / "out.json")
    parsed = yaml.safe_load(capsys.readouterr().out)
    svc = parsed["services"]["svc"]
    assert "probe_status" not in svc
    assert "probe_latency_ms" not in svc


# ---------------------------------------------------------------------------
# 3. Anomaly filtering via DetaConfig
# ---------------------------------------------------------------------------

def test_filter_anomalies_disables_missing_healthcheck(tmp_path: Path):
    _compose(tmp_path, "services:\n  svc:\n    image: alpine\n    ports:\n      - \"9000:80\"\n")
    topo = _scan_topo(tmp_path)
    anomalies = topo.detect_anomalies()

    cfg = DetaConfig()
    cfg.anomaly = AnomalyConfig(check_missing_healthcheck=False)
    filtered = _filter_anomalies(anomalies, cfg)
    assert not any(a["type"] == "missing_healthcheck" for a in filtered)


def test_filter_anomalies_disables_port_conflicts(tmp_path: Path):
    _compose(tmp_path, (
        "services:\n"
        "  a:\n    image: nginx\n    ports:\n      - \"8080:80\"\n"
        "  b:\n    image: httpd\n    ports:\n      - \"8080:80\"\n"
    ))
    topo = _scan_topo(tmp_path)
    anomalies = topo.detect_anomalies()

    cfg = DetaConfig()
    cfg.anomaly = AnomalyConfig(check_port_conflicts=False)
    filtered = _filter_anomalies(anomalies, cfg)
    assert not any(a["type"] == "port_conflict" for a in filtered)


def test_filter_anomalies_min_severity_filters_warnings(tmp_path: Path):
    _compose(tmp_path, "services:\n  svc:\n    image: alpine\n")
    topo = _scan_topo(tmp_path)
    anomalies = topo.detect_anomalies()

    cfg = DetaConfig()
    cfg.alert.min_severity = "error"
    filtered = _filter_anomalies(anomalies, cfg)
    # missing_healthcheck is "warning", should be excluded
    assert not any(a["type"] == "missing_healthcheck" for a in filtered)


# ---------------------------------------------------------------------------
# 4. Dependency cycle detection
# ---------------------------------------------------------------------------

def test_dependency_cycle_detected(tmp_path: Path):
    _compose(tmp_path, (
        "services:\n"
        "  a:\n"
        "    image: alpine\n"
        "    depends_on:\n"
        "      - b\n"
        "  b:\n"
        "    image: alpine\n"
        "    depends_on:\n"
        "      - a\n"
    ))
    topo = _scan_topo(tmp_path)
    cycles = topo.detect_cycles()
    assert len(cycles) >= 1
    cycle_services = {svc for cycle in cycles for svc in cycle}
    assert "a" in cycle_services
    assert "b" in cycle_services


def test_dependency_cycle_in_anomalies(tmp_path: Path):
    _compose(tmp_path, (
        "services:\n"
        "  x:\n    image: alpine\n    depends_on:\n      - y\n"
        "  y:\n    image: alpine\n    depends_on:\n      - x\n"
    ))
    topo = _scan_topo(tmp_path)
    anomalies = topo.detect_anomalies()
    cycle_anomalies = [a for a in anomalies if a["type"] == "dependency_cycle"]
    assert len(cycle_anomalies) >= 1


def test_linear_dependency_no_cycle(tmp_path: Path):
    _compose(tmp_path, (
        "services:\n"
        "  frontend:\n    image: nginx\n    depends_on:\n      - backend\n"
        "  backend:\n    image: flask\n    depends_on:\n      - db\n"
        "  db:\n    image: postgres\n"
    ))
    topo = _scan_topo(tmp_path)
    cycles = topo.detect_cycles()
    assert cycles == []


# ---------------------------------------------------------------------------
# 5. Multi-module recursive scanning
# ---------------------------------------------------------------------------

def test_multi_module_recursive_scan(tmp_path: Path):
    """Scanner finds services in nested subdirectories when include_patterns spans subdirs."""
    root_compose = tmp_path / "docker-compose.yml"
    root_compose.write_text(
        "services:\n  frontend:\n    image: nginx\n    ports:\n      - \"8100:80\"\n"
    )

    mod_a = tmp_path / "module-a"
    mod_a.mkdir()
    (mod_a / "docker-compose.yml").write_text(
        "services:\n  service-a:\n    image: python:3.11\n    ports:\n      - \"8200:8000\"\n"
    )

    mod_b = tmp_path / "module-b"
    mod_b.mkdir()
    (mod_b / "docker-compose.yml").write_text(
        "services:\n  service-b:\n    image: node:20\n    ports:\n      - \"8300:3000\"\n"
    )

    # include_patterns forces scanning all sub-directories
    services = scan_compose(
        tmp_path,
        max_depth=2,
        include_patterns=["docker-compose.yml", "*/docker-compose.yml"],
    )
    names = {s.name for s in services}
    assert "frontend" in names
    assert "service-a" in names
    assert "service-b" in names


def test_multi_module_port_conflicts_across_modules(tmp_path: Path):
    """Port conflicts detected across services in separate compose files (with explicit include)."""
    root_compose = tmp_path / "docker-compose.yml"
    root_compose.write_text(
        "services:\n  svc-root:\n    image: nginx\n    ports:\n      - \"9000:80\"\n"
    )
    sub = tmp_path / "module"
    sub.mkdir()
    (sub / "docker-compose.yml").write_text(
        "services:\n  svc-sub:\n    image: httpd\n    ports:\n      - \"9000:80\"\n"
    )

    services = scan_compose(
        tmp_path,
        max_depth=2,
        include_patterns=["docker-compose.yml", "*/docker-compose.yml"],
    )
    topo = InfraTopology()
    topo.add_services(services)
    conflicts = [a for a in topo.detect_anomalies() if a["type"] == "port_conflict"]
    assert len(conflicts) >= 1
    involved = set()
    for c in conflicts:
        involved.update(c["services"])
    assert "svc-root" in involved or "svc-sub" in involved


# ---------------------------------------------------------------------------
# 6. Hardcoded secrets
# ---------------------------------------------------------------------------

def test_hardcoded_secret_in_environment_map(tmp_path: Path):
    _compose(tmp_path, (
        "services:\n"
        "  app:\n"
        "    image: myapp\n"
        "    environment:\n"
        "      SECRET_KEY: super-secret-value\n"
        "      DB_HOST: postgres\n"
    ))
    topo = _scan_topo(tmp_path)
    anomalies = topo.detect_anomalies()
    secrets = [a for a in anomalies if a["type"] == "hardcoded_secret"]
    assert len(secrets) == 1
    assert secrets[0]["service"] == "app"
    assert secrets[0]["env_key"] == "SECRET_KEY"


def test_env_interpolation_not_flagged_as_hardcoded(tmp_path: Path):
    _compose(tmp_path, (
        "services:\n"
        "  app:\n"
        "    image: myapp\n"
        "    environment:\n"
        "      - SECRET_KEY=${SECRET_KEY:-change-me}\n"
    ))
    topo = _scan_topo(tmp_path)
    anomalies = topo.detect_anomalies()
    assert not any(a["type"] == "hardcoded_secret" for a in anomalies)


# ---------------------------------------------------------------------------
# 7. Offline mode — no probes performed
# ---------------------------------------------------------------------------

def test_scan_offline_mode_does_not_probe(tmp_path: Path, capsys):
    _compose(tmp_path, (
        "services:\n"
        "  api:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "8080:80"\n'
        "    healthcheck:\n"
        '      test: ["CMD", "wget", "-q", "http://localhost/health"]\n'
        "      interval: 30s\n"
    ))
    output = tmp_path / "out.json"
    with patch("deta.cli.probe_all", new_callable=AsyncMock) as mock_probe:
        scan(root=tmp_path, depth=1, output=output, online=False)
        mock_probe.assert_not_called()


def test_scan_online_false_yaml_has_no_probe_fields(tmp_path: Path, capsys):
    _compose(tmp_path, (
        "services:\n"
        "  api:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "8080:80"\n'
    ))
    output = tmp_path / "out.json"
    with patch("deta.cli._probe_once", return_value=None):
        scan(root=tmp_path, depth=1, output=output, online=False)
    parsed = yaml.safe_load(capsys.readouterr().out)
    assert "probe_status" not in parsed["services"].get("api", {})


# ---------------------------------------------------------------------------
# 8. JSON output file written correctly
# ---------------------------------------------------------------------------

def test_scan_writes_json_output_file(tmp_path: Path, capsys):
    _compose(tmp_path, (
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "8080:80"\n'
    ))
    output_file = tmp_path / "result.json"
    scan(root=tmp_path, depth=1, output=output_file, online=False)

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert "services" in data
    assert "web" in data["services"]


# ---------------------------------------------------------------------------
# 9. Examples fixture tests
# ---------------------------------------------------------------------------

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@pytest.mark.skipif(
    not (EXAMPLES_DIR / "basic" / "api-stack" / "docker-compose.yml").exists(),
    reason="basic/api-stack example not found",
)
def test_example_basic_api_stack():
    """basic/api-stack example scans without error and has expected services."""
    path = EXAMPLES_DIR / "basic" / "api-stack"
    services = scan_compose(path, max_depth=1)
    names = {s.name for s in services}
    assert "api" in names
    assert "db" in names


@pytest.mark.skipif(
    not (EXAMPLES_DIR / "anomalies" / "port-conflict" / "docker-compose.yml").exists(),
    reason="anomalies/port-conflict example not found",
)
def test_example_port_conflict_anomaly():
    """anomalies/port-conflict example produces a port_conflict anomaly."""
    path = EXAMPLES_DIR / "anomalies" / "port-conflict"
    services = scan_compose(path, max_depth=1)
    topo = InfraTopology()
    topo.add_services(services)
    anomalies = topo.detect_anomalies()
    assert any(a["type"] == "port_conflict" for a in anomalies)


@pytest.mark.skipif(
    not (EXAMPLES_DIR / "env-driven" / "docker-compose.yml").exists(),
    reason="env-driven example not found",
)
def test_example_env_driven_resolves_ports():
    """env-driven example resolves ports from .env file."""
    path = EXAMPLES_DIR / "env-driven"
    services = scan_compose(path, max_depth=1)
    port_map = {}
    for svc in services:
        for binding in svc.resolved_ports:
            if binding.host_port:
                port_map[svc.name] = binding.host_port
    # .env defines SERVICE_ID_PILOT_PORT=8111
    assert port_map.get("service-id-pilot") == "8111"
    # .env defines DB_PORT=5433
    assert port_map.get("db") == "5433"


@pytest.mark.skipif(
    not (EXAMPLES_DIR / "anomalies" / "hardcoded-secrets" / "docker-compose.yml").exists(),
    reason="anomalies/hardcoded-secrets example not found",
)
def test_example_hardcoded_secrets_anomaly():
    """anomalies/hardcoded-secrets example detects secret anomalies."""
    path = EXAMPLES_DIR / "anomalies" / "hardcoded-secrets"
    services = scan_compose(path, max_depth=1)
    topo = InfraTopology()
    topo.add_services(services)
    anomalies = topo.detect_anomalies()
    assert any(a["type"] == "hardcoded_secret" for a in anomalies)


@pytest.mark.skipif(
    not (EXAMPLES_DIR / "anomalies" / "missing-healthcheck" / "docker-compose.yml").exists(),
    reason="anomalies/missing-healthcheck example not found",
)
def test_example_missing_healthcheck_anomaly():
    """anomalies/missing-healthcheck example detects missing healthcheck."""
    path = EXAMPLES_DIR / "anomalies" / "missing-healthcheck"
    services = scan_compose(path, max_depth=1)
    topo = InfraTopology()
    topo.add_services(services)
    anomalies = topo.detect_anomalies()
    assert any(a["type"] == "missing_healthcheck" for a in anomalies)


@pytest.mark.skipif(
    not (EXAMPLES_DIR / "microservices" / "docker-compose.yml").exists(),
    reason="microservices example not found",
)
def test_example_microservices_topology():
    """microservices example resolves all expected services."""
    path = EXAMPLES_DIR / "microservices"
    services = scan_compose(path, max_depth=2)
    assert len(services) >= 3


# ---------------------------------------------------------------------------
# 10. Hub detection
# ---------------------------------------------------------------------------

def test_hub_detection_identifies_heavily_depended_service(tmp_path: Path):
    """Service depended on by >= 5 others is identified as a hub."""
    services_yaml = "services:\n  db:\n    image: postgres\n"
    for i in range(6):
        services_yaml += (
            f"  svc{i}:\n    image: alpine\n    depends_on:\n      - db\n"
        )
    _compose(tmp_path, services_yaml)
    topo = _scan_topo(tmp_path)
    hubs = topo.find_hubs(threshold=5)
    assert "db" in hubs
