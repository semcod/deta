"""
HTTP health check prober for services.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Optional

from deta.scanner.compose import ServiceDef
from deta.scanner.ports import PortBinding, parse_port, published_url


@dataclass
class ProbeResult:
    """Result of a health check probe."""
    service: str
    url: str
    status: int | None
    ok: bool
    latency_ms: float
    error: Optional[str] = None


def _first_resolved_binding(service: ServiceDef) -> Optional[PortBinding]:
    for binding in service.resolved_ports or []:
        if binding.is_resolved:
            return binding
    if service.ports:
        binding = parse_port(service.ports[0], service.env_resolved)
        return binding if binding.is_resolved else None
    return None


def _extract_health_url(service: ServiceDef) -> Optional[str]:
    """
    Extract health check URL from service definition.

    Looks for healthcheck configuration and constructs URL from ports.
    Healthcheck strings are already env-interpolated by the scanner.
    """
    if service.healthcheck:
        test = service.healthcheck.get("test", [])
        if isinstance(test, list):
            for item in test:
                if not isinstance(item, str):
                    continue
                if item.startswith("http://") or item.startswith("https://"):
                    return item
                if "curl" in item and "http" in item:
                    match = re.search(r"https?://[^\s\"'`]+", item)
                    if match:
                        return match.group(0)

    binding = _first_resolved_binding(service)
    if binding is None:
        return None
    return published_url(binding, "/health")


async def probe_service(service: ServiceDef) -> ProbeResult:
    """
    Probe a single service's health check endpoint.
    
    Args:
        service: ServiceDef to probe
        
    Returns:
        ProbeResult with status and timing information
    """
    url = _extract_health_url(service)
    if not url:
        return ProbeResult(
            service=service.name,
            url="",
            status=None,
            ok=False,
            latency_ms=0,
            error="no healthcheck URL"
        )
    
    start = asyncio.get_event_loop().time()
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            latency = (asyncio.get_event_loop().time() - start) * 1000
            return ProbeResult(
                service=service.name,
                url=url,
                status=resp.status_code,
                ok=resp.is_success,
                latency_ms=latency,
            )
    except ImportError:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ProbeResult(
            service=service.name,
            url=url,
            status=None,
            ok=False,
            latency_ms=latency,
            error="httpx not installed"
        )
    except Exception as e:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ProbeResult(
            service=service.name,
            url=url,
            status=None,
            ok=False,
            latency_ms=latency,
            error=str(e)
        )


async def probe_all(services: list[ServiceDef]) -> list[ProbeResult]:
    """
    Probe all services concurrently.
    
    Args:
        services: List of ServiceDef objects to probe
        
    Returns:
        List of ProbeResult objects
    """
    return await asyncio.gather(*[probe_service(s) for s in services])
