"""
DSL (Domain Specific Language) for infrastructure change notifications.

Generates machine-readable commands describing changes:
- SERVICE_UP <name> port=<port> latency=<ms>
- SERVICE_DOWN <name> port=<port> error=<msg>
- PORT_ADDED <service> <host_port>:<container_port>
- PORT_REMOVED <service> <host_port>:<container_port>
- SERVICE_ADDED <name>
- SERVICE_REMOVED <name>
- STATUS_SUMMARY <time> up=<n> down=<n> total=<n>
"""

from .commands import (
    ChangeDSL,
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

__all__ = [
    "ChangeDSL",
    "service_up",
    "service_down",
    "port_added",
    "port_removed",
    "service_added",
    "service_removed",
    "status_summary",
    "format_probe_change",
    "format_port_changes",
    "format_service_changes",
]
