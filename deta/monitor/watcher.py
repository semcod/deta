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


def _scan_file_mtimes(root: Path) -> dict[str, float]:
    """Scan for config files and return dict of path -> mtime."""
    mtimes: dict[str, float] = {}
    for pattern in WATCHED_PATTERNS:
        for file_path in root.rglob(pattern):
            try:
                mtimes[str(file_path)] = file_path.stat().st_mtime
            except OSError:
                pass
    return mtimes


def _detect_change_type(
    file_path: str, old_mtime: float | None, new_mtime: float | None
) -> str | None:
    """Detect the type of change for a file."""
    if old_mtime is None and new_mtime is not None:
        return "added"
    if old_mtime is not None and new_mtime is None:
        return "deleted"
    if old_mtime is not None and new_mtime is not None and old_mtime != new_mtime:
        return "modified"
    return None


async def _emit_changes(
    old_mtimes: dict[str, float],
    new_mtimes: dict[str, float],
    on_change: Callable[[dict], Awaitable[None]],
):
    """Emit change events for files that have changed."""
    all_files = set(old_mtimes.keys()) | set(new_mtimes.keys())
    for file_path in all_files:
        change_type = _detect_change_type(
            file_path,
            old_mtimes.get(file_path),
            new_mtimes.get(file_path),
        )
        if change_type:
            await on_change({
                "type": change_type,
                "path": file_path,
                "timestamp": datetime.utcnow().isoformat(),
            })


async def _poll_configs(root: Path, on_change: Callable[[dict], Awaitable[None]], interval: int = 5):
    """
    Fallback polling implementation when watchfiles is not available.
    """
    import asyncio
    
    file_mtimes = _scan_file_mtimes(root)
    
    while True:
        await asyncio.sleep(interval)
        current_mtimes = _scan_file_mtimes(root)
        await _emit_changes(file_mtimes, current_mtimes, on_change)
        file_mtimes = current_mtimes


def _is_config_file(path: str) -> bool:
    """Check if a file matches watched configuration patterns."""
    name = Path(path).name
    return any(
        Path(name).match(pattern)
        for pattern in WATCHED_PATTERNS
    )
