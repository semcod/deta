"""
OpenAPI/Swagger manifest scanner.
"""

from pathlib import Path
from dataclasses import dataclass


@dataclass
class EndpointDef:
    """Definition of an OpenAPI endpoint."""
    path: str
    methods: list[str]
    service_hint: str  # From info.title or x-service
    source_file: str


def scan_openapi(root: Path, max_depth: int = 3) -> list[EndpointDef]:
    """
    Scan for OpenAPI files and extract endpoint definitions.
    
    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth to scan
        
    Returns:
        List of EndpointDef objects
    """
    endpoints = []
    patterns = ["openapi*.yml", "openapi*.yaml", "openapi*.json"]
    
    for pattern in patterns:
        for api_file in root.rglob(pattern):
            depth = len(api_file.relative_to(root).parts)
            if depth > max_depth:
                continue
            
            try:
                data = _load(api_file)
                if not data:
                    continue
                
                # Get service name from info.title or x-service
                title = data.get("info", {}).get("title", api_file.stem)
                x_service = data.get("x-service")
                service_hint = x_service if x_service else title
                
                # Extract paths and methods
                for path, methods in (data.get("paths") or {}).items():
                    valid_methods = [
                        m.upper() for m in methods.keys()
                        if m not in ["parameters", "$ref", "summary", "description"]
                    ]
                    if valid_methods:
                        endpoints.append(EndpointDef(
                            path=path,
                            methods=valid_methods,
                            service_hint=service_hint,
                            source_file=str(api_file),
                        ))
            except Exception:
                # Skip files that can't be parsed
                continue
    
    return endpoints


def _load(file_path: Path) -> dict:
    """Load YAML or JSON file."""
    suffix = file_path.suffix.lower()
    
    if suffix in [".yml", ".yaml"]:
        try:
            from ruamel.yaml import YAML
            yaml = YAML()
            with open(file_path) as f:
                data = yaml.load(f)
                return data or {}
        except ImportError:
            import yaml
            with open(file_path) as f:
                data = yaml.safe_load(f)
                return data or {}
    elif suffix == ".json":
        import json
        with open(file_path) as f:
            return json.load(f)
    
    return {}
