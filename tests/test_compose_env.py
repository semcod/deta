"""Integration test: compose scanner with .env-driven ports."""

from pathlib import Path

from deta.config import load_config
from deta.scanner.compose import scan_compose


def test_env_driven_ports(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("MY_PORT=7777\n")
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "${MY_PORT}:80"\n'
        "    healthcheck:\n"
        '      test: ["CMD", "curl", "http://localhost:${MY_PORT}/health"]\n'
    )

    services = scan_compose(tmp_path, max_depth=1)
    assert len(services) == 1
    svc = services[0]
    assert svc.name == "web"
    assert svc.image == "nginx"
    assert svc.resolved_ports
    binding = svc.resolved_ports[0]
    assert binding.host_port == "7777"
    assert binding.container_port == "80"
    # healthcheck interpolated
    test_cmd = svc.healthcheck.get("test", [])
    assert "http://localhost:7777/health" in test_cmd


def test_env_file_layering(tmp_path: Path):
    root_env = tmp_path / ".env"
    root_env.write_text("SHARED=root\n")

    sub = tmp_path / "sub"
    sub.mkdir()
    sub_env = sub / ".env"
    sub_env.write_text("SHARED=override\nEXTRA=yes\n")
    compose = sub / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  app:\n"
        "    image: ${EXTRA:-noextra}\n"
        "    env_file:\n"
        "      - .env\n"
        "    environment:\n"
        '      - HOST=${SHARED}\n'
    )

    services = scan_compose(tmp_path, max_depth=2)
    svc = next((s for s in services if s.name == "app"), None)
    assert svc is not None
    # image from .env in sub
    assert svc.image == "yes"
    # environment HOST should use the overridden value from service-level .env
    assert svc.environment.get("HOST") == "override"


def test_port_conflict_detected(tmp_path: Path):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  a:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "9000:80"\n'
        "  b:\n"
        "    image: httpd\n"
        "    ports:\n"
        '      - "9000:80"\n'
    )

    from deta.builder.topology import InfraTopology
    services = scan_compose(tmp_path, max_depth=1)
    topo = InfraTopology()
    topo.add_services(services)
    anomalies = topo.detect_anomalies()
    conflict = [a for a in anomalies if a["type"] == "port_conflict"]
    assert len(conflict) == 1
    assert set(conflict[0]["services"]) == {"a", "b"}
    assert conflict[0]["port"] == "9000"


def test_compose_override_merging(tmp_path: Path):
    """Active override files should merge with base, not replace."""
    # Base file defines postgres with ports
    base = tmp_path / "docker-compose.yml"
    base.write_text(
        "services:\n"
        "  postgres:\n"
        "    image: postgres:16\n"
        "    ports:\n"
        '      - "5432:5432"\n'
        "    environment:\n"
        '      POSTGRES_DB: app\n'
    )

    # Active override file redefines postgres with extra env but NO ports
    override = tmp_path / "docker-compose.override.yml"
    override.write_text(
        "services:\n"
        "  postgres:\n"
        "    environment:\n"
        '      POSTGRES_PASSWORD: secret\n'
    )

    services = scan_compose(tmp_path, max_depth=1)
    svc = next((s for s in services if s.name == "postgres"), None)
    assert svc is not None
    # Ports should be preserved from base file
    assert len(svc.ports) == 1
    assert svc.resolved_ports
    assert svc.resolved_ports[0].host_port == "5432"
    # Environment should be merged
    assert svc.environment.get("POSTGRES_DB") == "app"
    assert svc.environment.get("POSTGRES_PASSWORD") == "secret"


def test_non_active_compose_variants_ignored_unless_included(tmp_path: Path):
    base = tmp_path / "docker-compose.yml"
    base.write_text(
        "services:\n"
        "  app:\n"
        "    image: nginx\n"
    )

    variant = tmp_path / "docker-compose.prod.yml"
    variant.write_text(
        "services:\n"
        "  prod-only:\n"
        "    image: httpd\n"
    )

    default_services = scan_compose(tmp_path, max_depth=1)
    assert {svc.name for svc in default_services} == {"app"}

    included_services = scan_compose(
        tmp_path,
        max_depth=1,
        include_patterns=["docker-compose*.yml"],
    )
    assert {svc.name for svc in included_services} == {"app", "prod-only"}


def test_scan_compose_respects_include_exclude_patterns(tmp_path: Path):
    root_compose = tmp_path / "docker-compose.yml"
    root_compose.write_text(
        "services:\n"
        "  root:\n"
        "    image: nginx\n"
    )

    sub = tmp_path / "module"
    sub.mkdir()
    sub_compose = sub / "docker-compose.yml"
    sub_compose.write_text(
        "services:\n"
        "  sub:\n"
        "    image: httpd\n"
    )

    services = scan_compose(
        tmp_path,
        max_depth=2,
        include_patterns=["module/docker-compose*.yml"],
    )
    assert {svc.name for svc in services} == {"sub"}

    services = scan_compose(
        tmp_path,
        max_depth=2,
        exclude_patterns=["module/**"],
    )
    assert {svc.name for svc in services} == {"root"}


def test_hardcoded_secret_detection_ignores_compose_interpolation(tmp_path: Path):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  app:\n"
        "    image: nginx\n"
        "    environment:\n"
        "      - SECRET_KEY=${SECRET_KEY:-dev-secret-key-change-me}\n"
    )

    from deta.builder.topology import InfraTopology

    services = scan_compose(tmp_path, max_depth=1)
    topo = InfraTopology()
    topo.add_services(services)
    anomalies = topo.detect_anomalies()

    assert not any(a["type"] == "hardcoded_secret" for a in anomalies)


def test_hardcoded_secret_detection_flags_literal_value(tmp_path: Path):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  app:\n"
        "    image: nginx\n"
        "    environment:\n"
        "      - SECRET_KEY=plain-text-secret\n"
    )

    from deta.builder.topology import InfraTopology

    services = scan_compose(tmp_path, max_depth=1)
    topo = InfraTopology()
    topo.add_services(services)
    anomalies = topo.detect_anomalies()

    hardcoded = [a for a in anomalies if a["type"] == "hardcoded_secret"]
    assert len(hardcoded) == 1
    assert hardcoded[0]["service"] == "app"


def test_scan_compose_can_disable_dc_runtime_resolution(tmp_path: Path, monkeypatch):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  app:\n"
        "    image: nginx\n"
        "    ports:\n"
        "      - \"1111:80\"\n"
    )

    import deta.scanner.compose as compose_scanner

    def fake_runtime_services(*_args, **_kwargs):
        return {
            "app": {
                "ports": [
                    {"published": 2222, "target": 80},
                ],
            }
        }

    monkeypatch.setattr(
        compose_scanner,
        "_load_services_from_docker_compose_config",
        fake_runtime_services,
    )

    enabled = scan_compose(tmp_path, max_depth=1, use_dc_config=True)
    enabled_svc = next(s for s in enabled if s.name == "app")
    assert enabled_svc.resolved_ports[0].host_port == "2222"

    disabled = scan_compose(tmp_path, max_depth=1, use_dc_config=False)
    disabled_svc = next(s for s in disabled if s.name == "app")
    assert disabled_svc.resolved_ports[0].host_port == "1111"


def test_config_parses_use_dc_config_flag(tmp_path: Path):
    cfg = tmp_path / "deta.yaml"
    cfg.write_text(
        "scan:\n"
        "  use_dc_config: false\n"
    )

    parsed = load_config(cfg)
    assert parsed.scan.use_dc_config is False


def test_config_defaults_use_dc_config_to_true(tmp_path: Path):
    cfg = tmp_path / "deta.yaml"
    cfg.write_text(
        "scan:\n"
        "  max_depth: 2\n"
    )

    parsed = load_config(cfg)
    assert parsed.scan.use_dc_config is True
