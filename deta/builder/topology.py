"""
Infrastructure topology builder with anomaly detection.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import networkx as nx
except ImportError:
    nx = None

from deta.scanner.compose import ServiceDef, scan_compose
from deta.scanner.openapi import EndpointDef, scan_openapi


class InfraTopology:
    """Represents the infrastructure topology with services and dependencies."""
    
    def __init__(self):
        self.graph = None
        if nx is not None:
            self.graph = nx.DiGraph()
        self.services: dict[str, ServiceDef] = {}
        self.endpoints: list[EndpointDef] = []
    
    def add_services(self, services: list[ServiceDef]):
        """Add services to the topology graph."""
        for svc in services:
            self.services[svc.name] = svc
            if self.graph is not None:
                self.graph.add_node(svc.name, **asdict(svc))
                for dep in svc.depends_on:
                    self.graph.add_edge(svc.name, dep)
    
    def add_endpoints(self, endpoints: list[EndpointDef]):
        """Add endpoints to the topology."""
        self.endpoints.extend(endpoints)
    
    def detect_cycles(self) -> list[list[str]]:
        """Detect dependency cycles in the graph."""
        if self.graph is None:
            return []
        return list(nx.simple_cycles(self.graph))
    
    def find_hubs(self, threshold: int = 5) -> list[str]:
        """Find services with high fan-in (many dependents)."""
        if self.graph is None:
            return []
        return [n for n, d in self.graph.in_degree() if d >= threshold]
    
    def detect_anomalies(self) -> list[dict]:
        """Detect various infrastructure anomalies."""
        anomalies = []
        
        # Missing healthcheck
        for name, svc in self.services.items():
            if svc.healthcheck is None:
                anomalies.append({
                    "type": "missing_healthcheck",
                    "service": name,
                    "severity": "warning",
                    "file": svc.source_file,
                })
        
        # Dependency cycles
        for cycle in self.detect_cycles():
            anomalies.append({
                "type": "dependency_cycle",
                "services": cycle,
                "severity": "error",
            })
        
        # Port conflicts
        port_map: dict[str, str] = {}
        for name, svc in self.services.items():
            for port in svc.ports:
                host_port = port.split(":")[0]
                if host_port in port_map:
                    anomalies.append({
                        "type": "port_conflict",
                        "port": host_port,
                        "services": [port_map[host_port], name],
                        "severity": "error",
                    })
                port_map[host_port] = name
        
        # Hardcoded secrets
        for name, svc in self.services.items():
            for key, val in svc.environment.items():
                if "secret" in key.lower() and val and not val.startswith("${"):
                    anomalies.append({
                        "type": "hardcoded_secret",
                        "service": name,
                        "env_key": key,
                        "severity": "critical",
                        "file": svc.source_file,
                    })
        
        return anomalies
    
    def to_json(self) -> str:
        """Export topology to JSON format."""
        return json.dumps({
            "services": {k: asdict(v) for k, v in self.services.items()},
            "endpoints": [asdict(e) for e in self.endpoints],
            "anomalies": self.detect_anomalies(),
            "cycles": self.detect_cycles(),
            "hubs": self.find_hubs(),
        }, indent=2)


def build_topology(root: Path, max_depth: int = 3) -> InfraTopology:
    """
    Build complete infrastructure topology from scanned manifests.
    
    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth to scan
        
    Returns:
        InfraTopology object with services, endpoints, and anomalies
    """
    topology = InfraTopology()
    
    # Scan and add services
    services = scan_compose(root, max_depth)
    topology.add_services(services)
    
    # Scan and add endpoints
    endpoints = scan_openapi(root, max_depth)
    topology.add_endpoints(endpoints)
    
    return topology
