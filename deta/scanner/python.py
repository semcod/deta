"""
Python pyproject.toml and requirements.txt manifest scanner.
"""

from pathlib import Path
import sys


def scan_python(root: Path, max_depth: int = 3) -> list[dict]:
    """
    Scan for pyproject.toml and requirements.txt files.
    
    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth to scan
        
    Returns:
        List of project dictionaries with name, version, dependencies
    """
    result = []
    
    # Scan pyproject.toml files
    for pyproject in root.rglob("pyproject.toml"):
        depth = len(pyproject.relative_to(root).parts)
        if depth > max_depth:
            continue
        
        try:
            data = _load_toml(pyproject)
            proj = data.get("project", {})
            deps = proj.get("dependencies", [])
            
            # Also check tool.poetry.dependencies for poetry projects
            if not deps and "tool" in data:
                poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                deps = [k for k in poetry_deps.keys() if k != "python"]
            
            result.append({
                "name": proj.get("name"),
                "version": proj.get("version"),
                "deps": deps,
                "source_file": str(pyproject),
            })
        except Exception:
            # Skip files that can't be parsed
            continue
    
    # Scan requirements*.txt files
    for req_file in root.rglob("requirements*.txt"):
        depth = len(req_file.relative_to(root).parts)
        if depth > max_depth:
            continue
        
        try:
            deps = _parse_requirements(req_file)
            result.append({
                "name": req_file.stem,
                "version": None,
                "deps": deps,
                "source_file": str(req_file),
            })
        except Exception:
            continue
    
    return result


def _load_toml(file_path: Path) -> dict:
    """Load TOML file using appropriate parser."""
    try:
        import tomllib
        with open(file_path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        # Python < 3.11 fallback
        try:
            import tomli
            with open(file_path, "rb") as f:
                return tomli.load(f)
        except ImportError:
            try:
                import toml
                with open(file_path) as f:
                    return toml.load(f)
            except ImportError:
                return {}


def _parse_requirements(file_path: Path) -> list[str]:
    """Parse requirements.txt file and extract package names."""
    deps = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Extract package name (before version specifiers)
            pkg_name = line.split(">=")[0].split("==")[0].split("<")[0].split(">")[0].split("~=")[0].strip()
            if pkg_name:
                deps.append(pkg_name)
    return deps
