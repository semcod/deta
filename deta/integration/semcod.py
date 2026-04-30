"""
Semcod ecosystem integration hooks.
"""

from pathlib import Path
from typing import Optional

from deta.builder.topology import build_topology
from deta.formatter.toon import save_toon


def generate_for_sumd(root: Path = Path("."), depth: int = 3, output: Path = Path("infra.toon.yaml")):
    """
    Generate infrastructure report for sumd pipeline.
    
    This function creates a toon-formatted infrastructure report that can be
    consumed by sumd (Semcod unified monitoring daemon) for infrastructure
    health tracking and alerting.
    
    Args:
        root: Root directory to scan
        depth: Maximum scan depth
        output: Output file path for toon format
    """
    topology = build_topology(root, depth)
    project_name = root.name
    save_toon(topology, output, project_name)
    return output


def generate_for_pyqual(root: Path = Path("."), depth: int = 3) -> dict:
    """
    Generate dependency data for pyqual (Python quality checker).
    
    Args:
        root: Root directory to scan
        depth: Maximum scan depth
        
    Returns:
        Dictionary with Python project dependencies
    """
    from deta.scanner.python import scan_python
    
    python_projects = scan_python(root, depth)
    
    result = {
        "projects": [],
        "total_deps": set(),
    }
    
    for proj in python_projects:
        result["projects"].append({
            "name": proj["name"],
            "version": proj["version"],
            "deps": proj["deps"],
            "source_file": proj["source_file"],
        })
        result["total_deps"].update(proj["deps"])
    
    result["total_deps"] = list(result["total_deps"])
    return result


def generate_for_vallm(root: Path = Path("."), depth: int = 3) -> dict:
    """
    Generate service metadata for vallm (validation LLM).
    
    Args:
        root: Root directory to scan
        depth: Maximum scan depth
        
    Returns:
        Dictionary with service metadata for LLM validation
    """
    topology = build_topology(root, depth)
    
    return {
        "services": [
            {
                "name": name,
                "image": svc.image,
                "ports": svc.ports,
                "healthcheck": svc.healthcheck is not None,
                "dependencies": svc.depends_on,
            }
            for name, svc in topology.services.items()
        ],
        "endpoints": [
            {
                "path": ep.path,
                "methods": ep.methods,
                "service": ep.service_hint,
            }
            for ep in topology.endpoints
        ],
        "anomalies": topology.detect_anomalies(),
    }


def pre_deploy_check(root: Path = Path("."), depth: int = 3) -> tuple[bool, list[str]]:
    """
    Run pre-deployment infrastructure validation.
    
    This function checks for critical anomalies before deployment and returns
    a pass/fail status along with any issues found.
    
    Args:
        root: Root directory to scan
        depth: Maximum scan depth
        
    Returns:
        Tuple of (passed: bool, issues: list[str])
    """
    topology = build_topology(root, depth)
    anomalies = topology.detect_anomalies()
    
    critical_issues = [a for a in anomalies if a["severity"] == "critical"]
    error_issues = [a for a in anomalies if a["severity"] == "error"]
    
    issues = []
    
    for a in critical_issues:
        issues.append(f"CRITICAL: {a['type']} - {a.get('service', a.get('services'))}")
    
    for a in error_issues:
        issues.append(f"ERROR: {a['type']} - {a.get('service', a.get('services'))}")
    
    passed = len(critical_issues) == 0
    return passed, issues
