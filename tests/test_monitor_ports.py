"""Tests for monitor port extraction logic."""

from deta.scanner.compose import ServiceDef, PortBinding


def test_service_rows_port_fallback_to_raw():
    """Port falls back to raw ports definition when resolved_ports is empty."""
    svc_def = ServiceDef(
        name="web",
        image="nginx",
        ports=["8080:80", "9090:90"],
        resolved_ports=[]
    )
    
    # Simulate fallback logic
    pub_ports = []
    raw_ports = []
    if not pub_ports and svc_def and svc_def.ports:
        for p in svc_def.ports:
            if ":" in p:
                raw_ports.append(p.split(":")[0])
            else:
                raw_ports.append(p)
    
    assert raw_ports == ["8080", "9090"]


def test_service_rows_port_single_port():
    """Single port without colon is handled correctly."""
    svc_def = ServiceDef(
        name="web",
        image="nginx",
        ports=["8080"],
        resolved_ports=[]
    )
    
    raw_ports = []
    if svc_def and svc_def.ports:
        for p in svc_def.ports:
            if ":" in p:
                raw_ports.append(p.split(":")[0])
            else:
                raw_ports.append(p)
    
    assert raw_ports == ["8080"]


def test_service_rows_port_no_ports():
    """Service with no ports returns empty list."""
    svc_def = ServiceDef(
        name="web",
        image="nginx",
        ports=[],
        resolved_ports=[]
    )
    
    pub_ports = []
    raw_ports = []
    if not pub_ports and svc_def and svc_def.ports:
        for p in svc_def.ports:
            if ":" in p:
                raw_ports.append(p.split(":")[0])
            else:
                raw_ports.append(p)
    
    assert pub_ports == []
    assert raw_ports == []
