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


def _is_hardcoded_secret_value(value: str) -> bool:
    """Detect literal secret values while allowing compose env interpolation syntax."""
    if not value:
        return False
    stripped = value.strip()
    if not stripped:
        return False
    if stripped.startswith("${") and stripped.endswith("}"):
        return False
    return True


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
                    "remediation_hints": [
                        f"Add a 'healthcheck' block to {name} in {svc.source_file}",
                        "Ensure the service implements a /health endpoint"
                    ],
                    "recommended_mcp_tools": [
                        {"tool": "view_file", "args": {"path": svc.source_file}}
                    ]
                })
        
        # Dependency cycles
        for cycle in self.detect_cycles():
            anomalies.append({
                "type": "dependency_cycle",
                "services": cycle,
                "severity": "error",
            })
        
        # Port conflicts (using resolved host:port pairs)
        port_map: dict[str, str] = {}
        for name, svc in self.services.items():
            seen_keys: set[str] = set()
            bindings = list(svc.resolved_ports or [])
            if not bindings:
                # Fallback: best-effort raw split for legacy ServiceDefs
                for port in svc.ports:
                    raw_host_port = port.split(":")[0]
                    if not raw_host_port or not raw_host_port.isdigit():
                        continue
                    key = f"localhost:{raw_host_port}"
                    if key in port_map and port_map[key] != name:
                        anomalies.append({
                            "type": "port_conflict",
                            "port": raw_host_port,
                            "services": [port_map[key], name],
                            "severity": "error",
                            "remediation_hints": [
                                f"Change the host port mapping for {name} or {port_map[key]} to avoid collision on port {raw_host_port}"
                            ],
                            "recommended_mcp_tools": [
                                {"tool": "view_file", "args": {"path": svc.source_file}}
                            ]
                        })
                    port_map[key] = name
                continue

            for binding in bindings:
                if not binding.is_resolved:
                    continue
                host = binding.host or "localhost"
                key = f"{host}:{binding.host_port}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                if key in port_map and port_map[key] != name:
                    anomalies.append({
                        "type": "port_conflict",
                        "port": binding.host_port,
                        "host": host,
                        "services": [port_map[key], name],
                        "severity": "error",
                        "remediation_hints": [
                            f"Change the host port mapping for {name} or {port_map[key]} to avoid collision on port {binding.host_port}"
                        ],
                        "recommended_mcp_tools": [
                            {"tool": "view_file", "args": {"path": svc.source_file}}
                        ]
                    })
                port_map[key] = name
        
        # Hardcoded secrets
        for name, svc in self.services.items():
            raw_environment = svc.environment_raw or svc.environment
            for key, val in raw_environment.items():
                if "secret" in key.lower() and _is_hardcoded_secret_value(str(val)):
                    anomalies.append({
                        "type": "hardcoded_secret",
                        "service": name,
                        "env_key": key,
                        "severity": "critical",
                        "file": svc.source_file,
                        "remediation_hints": [
                            f"Move {key} in {name} to environment/.env and reference it as ${{{key}}}",
                            "Avoid literal secrets in docker-compose files."
                        ],
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


def build_topology(root: Path, max_depth: int = 3, config: Any = None) -> InfraTopology:
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
    include_patterns = None
    exclude_patterns = None
    use_dc_config = True
    if config and getattr(config, "scan", None):
        include_patterns = getattr(config.scan, "include_patterns", None)
        exclude_patterns = getattr(config.scan, "exclude_patterns", None)
        use_dc_config = getattr(config.scan, "use_dc_config", True)

    services = scan_compose(
        root,
        max_depth,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        use_dc_config=use_dc_config,
    )
    topology.add_services(services)
    
    # Scan and add endpoints
    endpoints = scan_openapi(root, max_depth)
    topology.add_endpoints(endpoints)
    
    return topology
