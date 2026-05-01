"""
HTTP health check prober for services.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Callable, Coroutine, Optional
from urllib.parse import urlparse

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


# Known database ports that need TCP connect check instead of HTTP
DATABASE_PORTS = {
    "5432",   # PostgreSQL
    "3306",   # MySQL
    "3307",   # MySQL alternate
    "6379",   # Redis
    "27017",  # MongoDB
    "27018",  # MongoDB shard
    "27019",  # MongoDB config
    "1433",   # SQL Server
    "1521",   # Oracle
    "5433",   # PostgreSQL alternate
    "6378",   # Redis alternate
    "5984",   # CouchDB
    "9042",   # Cassandra
    "8123",   # ClickHouse
}


def _is_database_port(port: str) -> bool:
    """Check if port is a known database port."""
    return port in DATABASE_PORTS


async def _tcp_connect_check(host: str, port: int, timeout: float = 2.0) -> tuple[bool, float, Optional[str]]:
    """
    Perform TCP connect check.

    Returns: (ok, latency_ms, error)
    """
    start = asyncio.get_event_loop().time()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        latency = (asyncio.get_event_loop().time() - start) * 1000
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True, latency, None
    except asyncio.TimeoutError:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return False, latency, "TCP connect timeout"
    except Exception as e:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return False, latency, str(e)


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


def resolve_service_status(probes: list["ProbeResult"]) -> str:
    """Determine overall service status from a list of per-port probes.

    Returns one of: 'online', 'offline', 'restarting', 'unknown'.
    """
    if not probes:
        return "unknown"
    if any(p.ok for p in probes):
        return "online"
    if any(p.status is not None and p.status >= 500 for p in probes):
        return "restarting"
    return "offline"


def group_probes_by_service(
    probes: list["ProbeResult"] | None,
) -> dict[str, list["ProbeResult"]]:
    """Group probe results by service name."""
    grouped: dict[str, list["ProbeResult"]] = {}
    for p in probes or []:
        grouped.setdefault(p.service, []).append(p)
    return grouped


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


def _has_explicit_healthcheck_url(service: ServiceDef) -> bool:
    """Return True when service healthcheck explicitly contains an HTTP URL."""
    if not service.healthcheck:
        return False
    test = service.healthcheck.get("test", [])
    if not isinstance(test, list):
        return False
    for item in test:
        if not isinstance(item, str):
            continue
        if item.startswith("http://") or item.startswith("https://"):
            return True
        if "curl" in item and "http" in item:
            if re.search(r"https?://[^\s\"'`]+", item):
                return True
    return False


def _is_http_reachable(status_code: int) -> bool:
    """Treat any non-5xx response as reachable service."""
    return status_code < 500


def _service_probe_targets(service: ServiceDef, url: str) -> list[tuple[str, str]]:
    """
    Build probe targets for service health URL.

    If healthcheck points at localhost/127.0.0.1/0.0.0.0 (often container-internal),
    also map the same path onto published host port.
    """
    parsed = urlparse(url)
    targets: list[tuple[str, str]] = []

    # Always include original healthcheck target first
    targets.append((url, _extract_host_port_from_url(url)))

    binding = _first_resolved_binding(service)
    if binding is not None:
        hostname = (parsed.hostname or "").lower()
        if hostname in {"", "localhost", "127.0.0.1", "0.0.0.0"}:
            mapped_url = published_url(binding, parsed.path or "/health")
            if mapped_url:
                targets.append((mapped_url, binding.host_port))

    unique_targets: list[tuple[str, str]] = []
    seen: set[str] = set()
    for target_url, host_port in targets:
        if target_url in seen:
            continue
        seen.add(target_url)
        unique_targets.append((target_url, host_port))

    return unique_targets


def _extract_host_port_from_url(url: str) -> str:
    """Extract port number from a URL, defaulting to 80/443 based on scheme."""
    try:
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

    client = await _get_client()
    if client is None:
        return ProbeResult(
            service=service.name,
            url=url,
            status=None,
            ok=False,
            latency_ms=0,
            error="httpx not installed",
            host_port=_extract_host_port_from_url(url),
        )

    last_result: Optional[ProbeResult] = None

    for target_url, target_host_port in _service_probe_targets(service, url):
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        original_path = parsed.path or "/health"

        paths_to_try = [original_path]
        if original_path == "/health":
            paths_to_try.extend(["/healthz", "/"])

        for path in paths_to_try:
            test_url = f"{base_url}{path}"
            start = asyncio.get_event_loop().time()
            try:
                resp = await client.get(test_url)
                latency = (asyncio.get_event_loop().time() - start) * 1000
                result = ProbeResult(
                    service=service.name,
                    url=test_url,
                    status=resp.status_code,
                    ok=_is_http_reachable(resp.status_code),
                    latency_ms=latency,
                    host_port=target_host_port,
                )
                if result.ok:
                    return result
                last_result = result
            except Exception as e:
                latency = (asyncio.get_event_loop().time() - start) * 1000
                last_result = ProbeResult(
                    service=service.name,
                    url=test_url,
                    status=None,
                    ok=False,
                    latency_ms=latency,
                    error=str(e),
                    host_port=target_host_port,
                )

    return last_result  # type: ignore[return-value]


async def probe_port(service: ServiceDef, binding: PortBinding, path: str = "/health") -> ProbeResult:
    """Probe a specific port binding, trying /health, /healthz and / in order."""
    # Use TCP connect check for known database ports
    if binding.host_port and _is_database_port(binding.host_port):
        host = binding.host or "localhost"
        try:
            port_num = int(binding.host_port)
        except ValueError:
            port_num = 0
        if port_num > 0:
            ok, latency, error = await _tcp_connect_check(host, port_num)
            return ProbeResult(
                service=service.name,
                url=f"tcp://{host}:{binding.host_port}",
                status=200 if ok else None,
                ok=ok,
                latency_ms=latency,
                error=error,
                host_port=binding.host_port,
            )

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
                ok=_is_http_reachable(resp.status_code),
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
        # Use explicit healthcheck URL if defined, otherwise probe each resolved port
        if _has_explicit_healthcheck_url(service):
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
