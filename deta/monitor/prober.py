"""
HTTP health check prober for services.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from deta.scanner.compose import ServiceDef


@dataclass
class ProbeResult:
    """Result of a health check probe."""
    service: str
    url: str
    status: int | None
    ok: bool
    latency_ms: float
    error: Optional[str] = None


def _extract_health_url(service: ServiceDef) -> Optional[str]:
    """
    Extract health check URL from service definition.
    
    Looks for healthcheck configuration and constructs URL from ports.
    """
    if not service.healthcheck:
        return None
    
    healthcheck = service.healthcheck
    test = healthcheck.get("test", [])
    
    if isinstance(test, list) and len(test) > 0:
        # Parse healthcheck test command
        for item in test:
            if isinstance(item, str):
                # Look for URL patterns in healthcheck
                if item.startswith("http://") or item.startswith("https://"):
                    return item
                # Look for curl commands
                if "curl" in item and "http" in item:
                    # Extract URL from curl command
                    import re
                    match = re.search(r'https?://[^\s"\'`]+', item)
                    if match:
                        return match.group(0)
    
    # Fallback: construct URL from ports
    if service.ports:
        # Use first published port
        port_str = service.ports[0]
        if ":" in port_str:
            host_port = port_str.split(":")[0]
        else:
            host_port = port_str
        
        # Default to localhost
        return f"http://localhost:{host_port}/health"
    
    return None


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
