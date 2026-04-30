"""Realtime web dashboard for deta infrastructure monitoring."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from deta.builder.topology import InfraTopology, build_topology
from deta.config import DetaConfig, load_config
from deta.formatter.graph import generate_mermaid
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
    header { padding: 12px 16px; border-bottom: 1px solid #223; display:flex; align-items:center; justify-content:space-between; }
    main { display:grid; grid-template-columns: 2fr 1fr; gap: 12px; padding: 12px; }
    .card { background: #11172a; border: 1px solid #223; border-radius: 10px; padding: 12px; }
    .status { display:flex; gap:10px; flex-wrap: wrap; }
    .pill { padding:4px 8px; border-radius: 999px; font-size: 12px; }
    .ok { background:#163a2a; color:#a7f3d0; }
    .bad { background:#3a1b1b; color:#fecaca; }
    .warn { background:#3a3318; color:#fde68a; }
    #alerts { max-height: 70vh; overflow:auto; }
    .alert { border-bottom:1px solid #223; padding: 8px 0; font-size: 13px; }
    .ts { color:#93a3b8; font-size:11px; }
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
      <h3>Service Map</h3>
      <div id="graph" class="mermaid">graph TD; Boot[Loading] --> Wait[Waiting for data]</div>
    </section>
    <aside class="card">
      <h3>Alerts</h3>
      <div id="alerts"></div>
    </aside>
  </main>

  <script>
    mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });

    const alerts = document.getElementById('alerts');
    const graph = document.getElementById('graph');
    const servicesPill = document.getElementById('services-pill');
    const anomaliesPill = document.getElementById('anomalies-pill');
    const offlinePill = document.getElementById('offline-pill');
    const rootInfo = document.getElementById('root');

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
      rootInfo.textContent = payload.root || '';
      servicesPill.textContent = `services: ${payload.summary.services}`;
      anomaliesPill.textContent = `anomalies: ${payload.summary.anomalies}`;
      offlinePill.textContent = `offline: ${payload.summary.offline}`;

      graph.removeAttribute('data-processed');
      graph.textContent = payload.mermaid;
      mermaid.init(undefined, graph);

      (payload.events || []).forEach(ev => addAlert(ev.message, ev.severity, ev.timestamp));
    }

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


def create_app(root: Path, depth: int, config: DetaConfig):
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import HTMLResponse
    except ImportError as exc:
        raise RuntimeError("fastapi is not installed. Install with: pip install 'deta[web]'") from exc

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
        raise RuntimeError("uvicorn is not installed. Install with: pip install 'deta[web]'") from exc

    uvicorn.run(app, host=bind_host, port=bind_port)
