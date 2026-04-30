"""Topology caching with file-based invalidation."""

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from deta.builder.topology import InfraTopology


@dataclass
class CachedTopology:
    """Cached topology with metadata."""
    topology: InfraTopology
    file_mtimes: dict[str, float]
    timestamp: float


class TopologyCache:
    """Cache for topology with mtime-based invalidation."""

    def __init__(self, ttl_seconds: float = 30.0):
        self._cache: Optional[CachedTopology] = None
        self._lock = asyncio.Lock()
        self.ttl = ttl_seconds

    def _get_current_mtimes(self, root: Path, max_depth: int) -> dict[str, float]:
        """Get current modification times of compose files."""
        mtimes: dict[str, float] = {}
        patterns = [
            "docker-compose*.yml",
            "docker-compose*.yaml",
            "compose.yml",
            "compose.yaml",
        ]
        for pattern in patterns:
            for f in root.rglob(pattern):
                depth = len(f.relative_to(root).parts)
                if depth <= max_depth:
                    try:
                        mtimes[str(f)] = f.stat().st_mtime
                    except OSError:
                        pass
        return mtimes

    def _is_valid(self, current: CachedTopology, root: Path, max_depth: int) -> bool:
        """Check if cache is still valid."""
        # TTL check
        if time.time() - current.timestamp > self.ttl:
            return False

        # File change check
        current_mtimes = self._get_current_mtimes(root, max_depth)
        return current.file_mtimes == current_mtimes

    async def get(
        self,
        root: Path,
        max_depth: int,
        builder_func: Callable[[Path, int], InfraTopology],
    ) -> InfraTopology:
        """Get topology from cache or rebuild if invalid."""
        async with self._lock:
            if self._cache and self._is_valid(self._cache, root, max_depth):
                return self._cache.topology

            # Run blocking scan in thread pool
            loop = asyncio.get_event_loop()
            topology = await loop.run_in_executor(
                None, builder_func, root, max_depth
            )

            self._cache = CachedTopology(
                topology=topology,
                file_mtimes=self._get_current_mtimes(root, max_depth),
                timestamp=time.time(),
            )
            return topology

    def invalidate(self):
        """Force cache invalidation."""
        self._cache = None
