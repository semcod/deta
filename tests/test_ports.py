"""Tests for centralized port parsing."""

from deta.scanner.ports import parse_port, published_url


def test_parse_port_single():
    b = parse_port("8080")
    assert b.host_port == "8080"
    assert b.container_port == "8080"
    assert b.host == ""


def test_parse_port_mapping():
    b = parse_port("8080:80")
    assert b.host_port == "8080"
    assert b.container_port == "80"


def test_parse_port_with_host():
    b = parse_port("127.0.0.1:8080:80")
    assert b.host == "127.0.0.1"
    assert b.host_port == "8080"
    assert b.container_port == "80"


def test_parse_port_with_protocol():
    b = parse_port("8080:80/tcp")
    assert b.protocol == "tcp"
    assert b.host_port == "8080"
    assert b.container_port == "80"


def test_parse_port_env():
    b = parse_port("${PORT:-8080}:80", {"PORT": "9090"})
    assert b.host_port == "9090"
    assert b.container_port == "80"


def test_parse_port_env_default():
    b = parse_port("${PORT:-8080}:80", {})
    assert b.host_port == "8080"
    assert b.container_port == "80"


def test_published_url():
    b = parse_port("127.0.0.1:3000:80")
    assert published_url(b, "/health") == "http://127.0.0.1:3000/health"


def test_published_url_fallback_host():
    b = parse_port("8080:80")
    assert published_url(b) == "http://localhost:8080/health"
