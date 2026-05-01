"""
Monitor module for real-time infrastructure monitoring.
"""

from deta.monitor.watcher import watch_configs, WATCHED_PATTERNS
from deta.monitor.prober import probe_service, probe_all, ProbeResult, resolve_service_status, group_probes_by_service
from deta.monitor.alerter import alert_anomaly, alert_probe_failure, print_topology_table

__all__ = [
    "watch_configs",
    "WATCHED_PATTERNS",
    "probe_service",
    "probe_all",
    "ProbeResult",
    "resolve_service_status",
    "group_probes_by_service",
    "alert_anomaly",
    "alert_probe_failure",
    "print_topology_table",
]
