"""
HTTP health check prober for services.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Callable, Coroutine, Optional

from deta.scanner.compose import ServiceDef
from deta.scanner.ports import PortBinding, parse_port, published_url

_shared_client: Optional["httpx.AsyncClient"] = None


async def _get_client():
    global _shared_client
    try:
        import httpx
        if _shared_client is None or _shared_client.is_closed:
            limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
            _shared_client = httpx.AsyncClient(
                timeout=1.5,
                limits=limits,
                http2=True,
            )
        return _shared_client
    except ImportError:
        return None


async def close_client():
    """Close the shared HTTP client."""
    global _shared_client
    if _shared_client and not _shared_client.is_closed:
        await _shared_client.aclose()
        _shared_client = None


@dataclass
class ProbeResult:
    """Result of a health check probe."""
    service: str
    url: str
    status: int | None
    ok: bool
    latency_ms: float
    error: Optional[str] = None
    host_port: str = ""


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


def _extract_host_port_from_url(url: str) -> str:
    """Extract port number from a URL, defaulting to 80/443 based on scheme."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.port:
            return str(parsed.port)
        return "443" if parsed.scheme == "https" else "80"
    except Exception:
        return ""


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
    host_port = _extract_host_port_from_url(url)

    client = await _get_client()
    if client is None:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ProbeResult(
            service=service.name,
            url=url,
            status=None,
            ok=False,
            latency_ms=latency,
            error="httpx not installed",
            host_port=host_port,
        )
    try:
        resp = await client.get(url)
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ProbeResult(
            service=service.name,
            url=url,
            status=resp.status_code,
            ok=resp.is_success,
            latency_ms=latency,
            host_port=host_port,
        )
    except Exception as e:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ProbeResult(
            service=service.name,
            url=url,
            status=None,
            ok=False,
            latency_ms=latency,
            error=str(e),
            host_port=host_port,
        )


async def probe_port(service: ServiceDef, binding: PortBinding, path: str = "/health") -> ProbeResult:
    """Probe a specific port binding, trying /health, /healthz and / in order."""
    base_url = published_url(binding, "")
    if not base_url:
        return ProbeResult(
            service=service.name,
            url="",
            status=None,
            ok=False,
            latency_ms=0,
            error=f"cannot build URL for port {binding.host_port}",
            host_port=binding.host_port,
        )

    client = await _get_client()
    if client is None:
        return ProbeResult(
            service=service.name,
            url=published_url(binding, path),
            status=None,
            ok=False,
            latency_ms=0,
            error="httpx not installed",
            host_port=binding.host_port,
        )

    paths_to_try = [path] if path != "/health" else ["/health", "/healthz", "/"]
    last_result: Optional[ProbeResult] = None

    for probe_path in paths_to_try:
        url = published_url(binding, probe_path)
        start = asyncio.get_event_loop().time()
        try:
            resp = await client.get(url)
            latency = (asyncio.get_event_loop().time() - start) * 1000
            result = ProbeResult(
                service=service.name,
                url=url,
                status=resp.status_code,
                ok=resp.is_success,
                latency_ms=latency,
                host_port=binding.host_port,
            )
            if result.ok:
                return result
            last_result = result
        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start) * 1000
            last_result = ProbeResult(
                service=service.name,
                url=url,
                status=None,
                ok=False,
                latency_ms=latency,
                error=str(e),
                host_port=binding.host_port,
            )

    return last_result  # type: ignore[return-value]


async def _noop_probe(service: ServiceDef) -> ProbeResult:
    """Return a ProbeResult indicating no ports to probe."""
    return ProbeResult(
        service=service.name,
        url="",
        status=None,
        ok=False,
        latency_ms=0,
        error="no ports to probe",
        host_port="",
    )


async def probe_all(
    services: list[ServiceDef],
    max_concurrency: int = 20,
) -> list[ProbeResult]:
    """
    Probe all services concurrently.

    Args:
        services: List of ServiceDef objects to probe

    Returns:
        List of ProbeResult objects (one per resolved port per service)
    """
    probe_factories: list[Callable[[], Coroutine[None, None, ProbeResult]]] = []
    semaphore = asyncio.Semaphore(max(1, max_concurrency))

    async def _run_limited(
        probe_factory: Callable[[], Coroutine[None, None, ProbeResult]],
    ) -> ProbeResult:
        async with semaphore:
            return await probe_factory()

    for service in services:
        # Use healthcheck URL if defined, otherwise probe each resolved port
        healthcheck_url = _extract_health_url(service)
        if healthcheck_url:
            # Probe the explicit healthcheck
            probe_factories.append(lambda service=service: probe_service(service))
        else:
            # Probe each resolved port
            bindings = service.resolved_ports or []
            if not bindings and service.ports:
                # Fallback to raw ports parsing
                from deta.scanner.ports import parse_ports
                bindings = [b for b in parse_ports(service.ports, service.env_resolved) if b.is_resolved]

            if bindings:
                for binding in bindings:
                    probe_factories.append(
                        lambda service=service, binding=binding: probe_port(service, binding)
                    )
            else:
                # No ports to probe
                probe_factories.append(lambda service=service: _noop_probe(service))

    tasks = [asyncio.create_task(_run_limited(factory)) for factory in probe_factories]
    return await asyncio.gather(*tasks)
