"""
NPM package.json manifest scanner.
"""

from pathlib import Path
import json


def scan_npm(root: Path, max_depth: int = 3) -> list[dict]:
    """
    Scan for package.json files and extract package information.
    
    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth to scan
        
    Returns:
        List of package dictionaries with name, version, scripts, dependencies
    """
    result = []
    
    for pkg in root.rglob("package.json"):
        # Skip node_modules directories
        if "node_modules" in pkg.parts:
            continue
        
        depth = len(pkg.relative_to(root).parts)
        if depth > max_depth:
            continue
        
        try:
            data = json.loads(pkg.read_text())
            result.append({
                "name": data.get("name"),
                "version": data.get("version"),
                "scripts": list(data.get("scripts", {}).keys()),
                "deps": list(data.get("dependencies", {}).keys()),
                "dev_deps": list(data.get("devDependencies", {}).keys()),
                "source_file": str(pkg),
            })
        except (json.JSONDecodeError, IOError):
            # Skip files that can't be parsed
            continue
    
    return result
