"""
File watcher for monitoring configuration changes.
"""

from pathlib import Path
from datetime import datetime
from typing import Callable, Awaitable

WATCHED_PATTERNS = {
    "docker-compose*.yml",
    "docker-compose*.yaml",
    "openapi*.yml",
    "openapi*.yaml",
    "openapi*.json",
    "package.json",
    "pyproject.toml",
    ".env",
    ".env.*",
}


async def watch_configs(root: Path, on_change: Callable[[dict], Awaitable[None]]):
    """
    Watch for configuration file changes and emit events.
    
    Args:
        root: Root directory to watch
        on_change: Async callback function that receives change events
    """
    try:
        from watchfiles import awatch
    except ImportError:
        # Fallback: simple polling if watchfiles not available
        import asyncio
        print("[WARN] watchfiles not installed, using polling fallback")
        await _poll_configs(root, on_change)
        return
    
    async for changes in awatch(root):
        for change_type, path in changes:
            if _is_config_file(path):
                await on_change({
                    "type": change_type.name if hasattr(change_type, "name") else str(change_type),
                    "path": str(path),
                    "timestamp": datetime.utcnow().isoformat(),
                })


async def _poll_configs(root: Path, on_change: Callable[[dict], Awaitable[None]], interval: int = 5):
    """
    Fallback polling implementation when watchfiles is not available.
    """
    import asyncio
    
    file_mtimes: dict[str, float] = {}
    
    # Initial scan
    for pattern in WATCHED_PATTERNS:
        for file_path in root.rglob(pattern):
            try:
                file_mtimes[str(file_path)] = file_path.stat().st_mtime
            except OSError:
                pass
    
    while True:
        await asyncio.sleep(interval)
        
        current_mtimes: dict[str, float] = {}
        for pattern in WATCHED_PATTERNS:
            for file_path in root.rglob(pattern):
                try:
                    current_mtimes[str(file_path)] = file_path.stat().st_mtime
                except OSError:
                    pass
        
        # Check for changes
        all_files = set(file_mtimes.keys()) | set(current_mtimes.keys())
        for file_path in all_files:
            old_mtime = file_mtimes.get(file_path)
            new_mtime = current_mtimes.get(file_path)
            
            if old_mtime is None and new_mtime is not None:
                await on_change({
                    "type": "added",
                    "path": file_path,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            elif old_mtime is not None and new_mtime is None:
                await on_change({
                    "type": "deleted",
                    "path": file_path,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            elif old_mtime is not None and new_mtime is not None and old_mtime != new_mtime:
                await on_change({
                    "type": "modified",
                    "path": file_path,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        
        file_mtimes = current_mtimes


def _is_config_file(path: str) -> bool:
    """Check if a file matches watched configuration patterns."""
    name = Path(path).name
    return any(
        Path(name).match(pattern)
        for pattern in WATCHED_PATTERNS
    )
