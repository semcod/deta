"""
deta - Infrastructure anomaly detection and monitoring tool.
"""

from __future__ import annotations

import importlib

__version__ = "0.2.48"

_LAZY_EXPORTS = {
    "InfraTopology": ("deta.builder.topology", "InfraTopology"),
    "build_topology": ("deta.builder.topology", "build_topology"),
    "ServiceDef": ("deta.scanner.compose", "ServiceDef"),
    "scan_compose": ("deta.scanner.compose", "scan_compose"),
    "EndpointDef": ("deta.scanner.openapi", "EndpointDef"),
    "scan_openapi": ("deta.scanner.openapi", "scan_openapi"),
    "ProbeResult": ("deta.monitor.prober", "ProbeResult"),
    "probe_service": ("deta.monitor.prober", "probe_service"),
    "probe_all": ("deta.monitor.prober", "probe_all"),
}


def __getattr__(name: str):
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module 'deta' has no attribute '{name}'")
    module_name, attr_name = target
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted([*globals().keys(), *_LAZY_EXPORTS.keys()])

__all__ = [
    "__version__",
    "InfraTopology",
    "build_topology",
    "ServiceDef",
    "scan_compose",
    "EndpointDef",
    "scan_openapi",
    "ProbeResult",
    "probe_service",
    "probe_all",
]
