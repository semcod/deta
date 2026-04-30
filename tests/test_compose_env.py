"""Integration test: compose scanner with .env-driven ports."""

from pathlib import Path

from deta.scanner.compose import scan_compose
from deta.scanner.ports import parse_port


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
