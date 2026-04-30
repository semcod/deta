"""Realtime web dashboard for deta infrastructure monitoring."""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from deta.builder.topology import InfraTopology, build_topology
from deta.config import DetaConfig, load_config
from deta.formatter.graph import generate_graph_yaml, generate_mermaid
from deta.monitor.prober import ProbeResult, probe_all
from deta.monitor.watcher import watch_configs

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>deta dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0b1020; color: #e5e7eb; }
    header { width: min(100%, 800px); box-sizing: border-box; margin: 0 auto; padding: 12px 16px; border-bottom: 1px solid #223; display:flex; align-items:center; justify-content:space-between; gap: 12px; flex-wrap: wrap; }
    main { width: min(100%, 800px); box-sizing: border-box; margin: 0 auto; display:flex; flex-direction:column; gap: 12px; padding: 12px; }
    .card { background: #11172a; border: 1px solid #223; border-radius: 10px; padding: 12px; }
    .status { display:flex; gap:10px; flex-wrap: wrap; }
    .pill { padding:4px 8px; border-radius: 999px; font-size: 12px; }
    .ok { background:#163a2a; color:#a7f3d0; }
    .bad { background:#3a1b1b; color:#fecaca; }
    .warn { background:#3a3318; color:#fde68a; }
    .row { display:flex; align-items:center; justify-content:space-between; gap: 8px; flex-wrap: wrap; }
    .actions { display:flex; gap: 8px; flex-wrap: wrap; }
    .btn { background: #1f2a44; color: #dbeafe; border: 1px solid #2f446e; border-radius: 8px; padding: 6px 10px; font-size: 12px; cursor: pointer; }
    .btn:hover { background: #253456; }
    #graph-wrap { width: 100%; overflow-x: auto; }
    #graph { min-width: 100%; }
    #graph svg { width: 100% !important; max-width: 100% !important; height: auto !important; }
    #alerts { max-height: 40vh; overflow:auto; }
    .alert { border-bottom:1px solid #223; padding: 8px 0; font-size: 13px; }
    .ts { color:#93a3b8; font-size:11px; }
    .dump { margin-top: 8px; max-height: 220px; overflow: auto; white-space: pre; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; background: #0b1328; border: 1px solid #223; border-radius: 8px; padding: 10px; }
  </style>
</head>
<body>
  <header>
    <div>
      <strong>deta dashboard</strong>
      <span id="root" class="ts"></span>
    </div>
    <div class="status">
      <span class="pill ok" id="services-pill">services: 0</span>
      <span class="pill warn" id="anomalies-pill">anomalies: 0</span>
      <span class="pill bad" id="offline-pill">offline: 0</span>
    </div>
  </header>
  <main>
    <section class="card">
      <div class="row">
        <h3>Service Map</h3>
        <div class="actions">
          <button class="btn" id="copy-mermaid">Copy Mermaid</button>
          <button class="btn" id="copy-png">Copy PNG</button>
        </div>
      </div>
      <div id="graph-wrap">
        <div id="graph" class="mermaid">graph LR; Boot[Loading] --> Wait[Waiting for data]</div>
      </div>
    </section>
    <section class="card">
      <div class="row">
        <h3>Current Map Data</h3>
        <div class="actions">
          <button class="btn" id="copy-json">Copy JSON</button>
          <button class="btn" id="copy-yaml">Copy YAML</button>
          <button class="btn" id="download-png">Download PNG</button>
        </div>
      </div>
      <pre id="json-dump" class="dump"></pre>
      <pre id="yaml-dump" class="dump"></pre>
    </section>
    <section class="card">
      <h3>Alerts</h3>
      <div id="alerts"></div>
    </section>
  </main>

  <script>
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      flowchart: {
        useMaxWidth: true,
        nodeSpacing: 40,
        rankSpacing: 70,
      },
    });

    const alerts = document.getElementById('alerts');
    const graph = document.getElementById('graph');
    const servicesPill = document.getElementById('services-pill');
    const anomaliesPill = document.getElementById('anomalies-pill');
    const offlinePill = document.getElementById('offline-pill');
    const rootInfo = document.getElementById('root');
    const jsonDump = document.getElementById('json-dump');
    const yamlDump = document.getElementById('yaml-dump');
    const copyMermaidBtn = document.getElementById('copy-mermaid');
    const copyPngBtn = document.getElementById('copy-png');
    const copyJsonBtn = document.getElementById('copy-json');
    const copyYamlBtn = document.getElementById('copy-yaml');
    const downloadPngBtn = document.getElementById('download-png');

    let latestPayload = null;

    function addAlert(message, severity, ts) {
      const div = document.createElement('div');
      div.className = 'alert';
      div.innerHTML = `<div>[${severity}] ${message}</div><div class="ts">${ts}</div>`;
      alerts.prepend(div);
      while (alerts.children.length > 200) alerts.removeChild(alerts.lastChild);
      if (Notification.permission === 'granted') {
        try { new Notification(`[deta] ${severity}`, { body: message }); } catch (e) {}
      }
    }

    function render(payload) {
      latestPayload = payload;
      rootInfo.textContent = payload.root || '';
      servicesPill.textContent = `services: ${payload.summary.services}`;
      anomaliesPill.textContent = `anomalies: ${payload.summary.anomalies}`;
      offlinePill.textContent = `offline: ${payload.summary.offline}`;

      graph.removeAttribute('data-processed');
      graph.textContent = payload.mermaid;
      mermaid.init(undefined, graph);

      jsonDump.textContent = payload.topology_json || '';
      yamlDump.textContent = payload.graph_yaml || '';

      (payload.events || []).forEach(ev => addAlert(ev.message, ev.severity, ev.timestamp));
    }

    async function copyText(label, value) {
      if (!value) {
        addAlert(`${label} is empty`, 'warning', new Date().toISOString());
        return;
      }
      try {
        await navigator.clipboard.writeText(value);
        addAlert(`${label} copied`, 'info', new Date().toISOString());
      } catch (error) {
        addAlert(`Failed to copy ${label}`, 'error', new Date().toISOString());
      }
    }

    function getGraphSvg() {
      return graph.querySelector('svg');
    }

    async function renderPngBlob() {
      const svg = getGraphSvg();
      if (!svg) return null;

      const serialized = new XMLSerializer().serializeToString(svg);
      const svgBlob = new Blob([serialized], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);

      const img = new Image();
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = url;
      });

      const width = Math.max(1, Math.round(svg.viewBox.baseVal.width || img.width || 1200));
      const height = Math.max(1, Math.round(svg.viewBox.baseVal.height || img.height || 800));

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        URL.revokeObjectURL(url);
        return null;
      }

      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0, width, height);
      URL.revokeObjectURL(url);

      return await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
    }

    async function copyPng() {
      try {
        const blob = await renderPngBlob();
        if (!blob) {
          addAlert('PNG not ready yet', 'warning', new Date().toISOString());
          return;
        }

        if (navigator.clipboard && window.ClipboardItem) {
          await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
          addAlert('PNG copied', 'info', new Date().toISOString());
          return;
        }

        downloadBlob(blob, 'infra-map.png');
        addAlert('Clipboard image unsupported, downloaded PNG', 'warning', new Date().toISOString());
      } catch (error) {
        addAlert('Failed to copy PNG', 'error', new Date().toISOString());
      }
    }

    function downloadBlob(blob, filename) {
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(objectUrl);
    }

    async function downloadPng() {
      const blob = await renderPngBlob();
      if (!blob) {
        addAlert('PNG not ready yet', 'warning', new Date().toISOString());
        return;
      }
      downloadBlob(blob, 'infra-map.png');
      addAlert('PNG downloaded', 'info', new Date().toISOString());
    }

    copyMermaidBtn.addEventListener('click', () => copyText('Mermaid', latestPayload?.mermaid || ''));
    copyJsonBtn.addEventListener('click', () => copyText('JSON', latestPayload?.topology_json || ''));
    copyYamlBtn.addEventListener('click', () => copyText('YAML', latestPayload?.graph_yaml || ''));
    copyPngBtn.addEventListener('click', copyPng);
    downloadPngBtn.addEventListener('click', downloadPng);

    Notification.requestPermission().catch(() => {});
    const wsScheme = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${wsScheme}://${location.host}/ws`);
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      render(payload);
    };
    ws.onclose = () => addAlert('WebSocket disconnected', 'warning', new Date().toISOString());
  </script>
</body>
</html>
"""


class ConnectionManager:
    def __init__(self) -> None:
        self._connections = set()

    async def connect(self, websocket):
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        if not self._connections:
            return
        message = json.dumps(payload)
        dead = []
        for conn in self._connections:
            try:
                await conn.send_text(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


def _topology_summary(topology: InfraTopology, probes: dict[str, ProbeResult] | None) -> dict:
    anomalies = topology.detect_anomalies()
    offline = 0
    if probes:
        offline = sum(1 for r in probes.values() if not r.ok)
    return {
        "services": len(topology.services),
        "anomalies": len(anomalies),
        "offline": offline,
    }


def _topology_json_with_status(
    topology: InfraTopology,
    probes: dict[str, ProbeResult] | None,
) -> str:
    services: dict[str, dict] = {}
    for service_name, service in topology.services.items():
        payload = asdict(service)
        probe = probes.get(service_name) if probes else None
        payload["status"] = "unknown" if probe is None else ("online" if probe.ok else "offline")
        if probe is not None:
            payload["probe"] = {
                "url": probe.url,
                "ok": probe.ok,
                "status": probe.status,
                "latency_ms": probe.latency_ms,
                "error": probe.error,
            }
        services[service_name] = payload

    map_payload = {
        "services": services,
        "endpoints": [asdict(endpoint) for endpoint in topology.endpoints],
        "anomalies": topology.detect_anomalies(),
        "cycles": topology.detect_cycles(),
        "hubs": topology.find_hubs(),
    }
    return json.dumps(map_payload, indent=2)


def _compute_events(
    prev_services: set[str],
    prev_probes: dict[str, ProbeResult] | None,
    topology: InfraTopology,
    probes: dict[str, ProbeResult] | None,
    enabled: set[str],
) -> list[dict]:
    events = []
    ts = datetime.utcnow().isoformat()

    current_services = set(topology.services.keys())

    for svc in sorted(current_services - prev_services):
        if "service_added" in enabled:
            events.append({"severity": "info", "message": f"service added: {svc}", "timestamp": ts})

    for svc in sorted(prev_services - current_services):
        if "service_removed" in enabled:
            events.append({"severity": "warning", "message": f"service removed: {svc}", "timestamp": ts})

    if probes and prev_probes is not None:
        for svc, current in probes.items():
            previous = prev_probes.get(svc)
            if previous is None:
                continue
            if previous.ok and not current.ok and "service_down" in enabled:
                events.append({"severity": "error", "message": f"service down: {svc}", "timestamp": ts})
            elif not previous.ok and current.ok and "service_up" in enabled:
                events.append({"severity": "info", "message": f"service up: {svc}", "timestamp": ts})

    return events


# Import at module level to avoid postponed evaluation issues with WebSocket endpoint
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
except ImportError as exc:
    FastAPI = WebSocket = WebSocketDisconnect = None  # type: ignore
    HTMLResponse = None  # type: ignore


def create_app(root: Path, depth: int, config: DetaConfig):
    if FastAPI is None or WebSocket is None or WebSocketDisconnect is None or HTMLResponse is None:
        raise RuntimeError(
            "fastapi is not installed for this interpreter: "
            f"{sys.executable}. Install with: {sys.executable} -m pip install -e '.[web]'"
        )

    app = FastAPI(title=config.web.title)
    manager = ConnectionManager()

    state = {
        "prev_services": set(),
        "prev_probes": None,
    }

    async def collect_payload(events: list[dict] | None = None) -> dict:
        topology = build_topology(root, depth)
        probes = None
        if config.monitor.probe_online:
            results = await probe_all(list(topology.services.values()))
            probes = {r.service: r for r in results}

        payload = {
            "root": str(root),
            "summary": _topology_summary(topology, probes),
            "mermaid": generate_mermaid(topology, probes),
            "graph_yaml": generate_graph_yaml(topology, probes),
            "topology_json": _topology_json_with_status(topology, probes),
            "events": events or [],
        }

        current_services = set(topology.services.keys())
        payload_events = _compute_events(
            state["prev_services"],
            state["prev_probes"],
            topology,
            probes,
            set(config.web.push_events),
        )
        if payload_events:
            payload["events"] = payload["events"] + payload_events

        state["prev_services"] = current_services
        state["prev_probes"] = probes
        return payload

    async def monitor_loop() -> None:
        payload = await collect_payload()
        await manager.broadcast(payload)

        async def on_change(change: dict):
            payload = await collect_payload(events=[{
                "severity": "warning",
                "message": f"config change: {change.get('path', '')}",
                "timestamp": change.get("timestamp", ""),
            }])
            await manager.broadcast(payload)

        await watch_configs(root, on_change)

    @app.on_event("startup")
    async def startup_event():
        app.state.monitor_task = asyncio.create_task(monitor_loop())

    @app.on_event("shutdown")
    async def shutdown_event():
        task = getattr(app.state, "monitor_task", None)
        if task:
            task.cancel()
            try:
                await task
            except BaseException:
                pass

    @app.get("/")
    async def index():
        return HTMLResponse(HTML.replace("deta dashboard", config.web.title))

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            payload = await collect_payload()
            await websocket.send_text(json.dumps(payload))
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception:
            manager.disconnect(websocket)

    return app


def run_dashboard(
    root: Path = Path("."),
    depth: int = 3,
    config_file: Path | None = None,
    host: str | None = None,
    port: int | None = None,
) -> None:
    config = load_config(config_file)
    app = create_app(root=root, depth=depth, config=config)

    bind_host = host or config.web.host
    bind_port = port or config.web.port

    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError(
            "uvicorn is not installed for this interpreter: "
            f"{sys.executable}. Install with: {sys.executable} -m pip install -e '.[web]'"
        ) from exc

    uvicorn.run(app, host=bind_host, port=bind_port)
