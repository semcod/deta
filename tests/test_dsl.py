"""Tests for DSL command generators."""

import pytest

from deta.dsl import (
    service_up,
    service_down,
    port_added,
    port_removed,
    service_added,
    service_removed,
    status_summary,
    format_probe_change,
    format_port_changes,
    format_service_changes,
)
from deta.monitor.prober import ProbeResult
from deta.builder.topology import InfraTopology
from deta.scanner.compose import ServiceDef


def test_service_up():
    cmd = service_up("api", port="8080", latency_ms=45.5, url="http://localhost:8080")
    assert cmd.command == "SERVICE_UP"
    assert cmd.target == "api"
    assert cmd.params["port"] == "8080"
    assert cmd.params["latency_ms"] == "46"


def test_service_down():
    cmd = service_down("db", port="5432", error="Connection refused", status=503)
    assert cmd.command == "SERVICE_DOWN"
    assert cmd.params["error"] == '"Connection refused"'
    assert cmd.params["status"] == "503"


def test_port_added():
    cmd = port_added("web", "8080", "80", "0.0.0.0")
    assert cmd.command == "PORT_ADDED"
    assert cmd.target == "web"
    assert cmd.params["mapping"] == "0.0.0.0:8080->80"


def test_port_removed():
    cmd = port_removed("cache", "6379", "6379")
    assert cmd.command == "PORT_REMOVED"
    assert cmd.params["host_port"] == "6379"


def test_service_added():
    cmd = service_added("worker", image="worker:v1", source="/app/docker-compose.yml")
    assert cmd.command == "SERVICE_ADDED"
    assert cmd.params["image"] == "worker:v1"


def test_service_removed():
    cmd = service_removed("old-service")
    assert cmd.command == "SERVICE_REMOVED"
    assert cmd.target == "old-service"


def test_status_summary():
    cmd = status_summary(up=5, down=2, unknown=1, total=8)
    assert cmd.command == "STATUS_SUMMARY"
    assert cmd.params["up"] == "5"
    assert cmd.params["down"] == "2"


def test_format_probe_change_up():
    prev = [ProbeResult(service="api", url="http://api", status=None, ok=False, latency_ms=0, error="timeout")]
    curr = [ProbeResult(service="api", url="http://api", status=200, ok=True, latency_ms=50, error=None)]
    changes = format_probe_change(prev, curr)
    assert len(changes) == 1
    assert changes[0].command == "SERVICE_UP"


def test_format_probe_change_down():
    prev = [ProbeResult(service="api", url="http://api", status=200, ok=True, latency_ms=50, error=None)]
    curr = [ProbeResult(service="api", url="http://api", status=None, ok=False, latency_ms=0, error="timeout")]
    changes = format_probe_change(prev, curr)
    assert len(changes) == 1
    assert changes[0].command == "SERVICE_DOWN"


def test_format_probe_change_no_change():
    prev = [ProbeResult(service="api", url="http://api", status=200, ok=True, latency_ms=50, error=None)]
    curr = [ProbeResult(service="api", url="http://api", status=200, ok=True, latency_ms=55, error=None)]
    changes = format_probe_change(prev, curr)
    assert len(changes) == 0
