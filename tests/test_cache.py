"""Tests for topology caching with mtime invalidation."""

import asyncio
import time
from pathlib import Path

from deta.builder.cache import TopologyCache
from deta.builder.topology import build_topology


def test_cache_basic(tmp_path: Path):
    """Basic cache test: first call scans, second call uses cache."""
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "8080:80"\n'
    )

    cache = TopologyCache(ttl_seconds=30.0)

    async def _run():
        topo1 = await cache.get(tmp_path, max_depth=1, builder_func=build_topology)
        assert "web" in topo1.services
        topo2 = await cache.get(tmp_path, max_depth=1, builder_func=build_topology)
        assert topo2 is topo1

    asyncio.run(_run())


def test_cache_mtime_invalidation(tmp_path: Path):
    """Cache is invalidated when file is modified."""
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
        "    ports:\n"
        '      - "8080:80"\n'
    )

    cache = TopologyCache(ttl_seconds=30.0)

    async def _run():
        topo1 = await cache.get(tmp_path, max_depth=1, builder_func=build_topology)
        assert len(topo1.services) == 1
        time.sleep(0.01)
        compose.write_text(
            "services:\n"
            "  web:\n"
            "    image: nginx\n"
            "    ports:\n"
            '      - "8080:80"\n'
            "  db:\n"
            "    image: postgres\n"
            "    ports:\n"
            '      - "5432:5432"\n'
        )
        topo2 = await cache.get(tmp_path, max_depth=1, builder_func=build_topology)
        assert len(topo2.services) == 2
        assert topo2 is not topo1

    asyncio.run(_run())


def test_cache_ttl_expiration(tmp_path: Path):
    """Cache expires after TTL."""
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
    )

    cache = TopologyCache(ttl_seconds=0.1)

    async def _run():
        topo1 = await cache.get(tmp_path, max_depth=1, builder_func=build_topology)
        topo2 = await cache.get(tmp_path, max_depth=1, builder_func=build_topology)
        assert topo2 is topo1
        time.sleep(0.15)
        topo3 = await cache.get(tmp_path, max_depth=1, builder_func=build_topology)
        assert topo3 is not topo1

    asyncio.run(_run())
