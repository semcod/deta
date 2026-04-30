"""Realtime web dashboard for deta infrastructure monitoring."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from deta.builder.cache import TopologyCache
from deta.builder.topology import InfraTopology, build_topology
from deta.config import DetaConfig, load_config
from deta.formatter.graph import generate_graph_yaml, generate_mermaid
from deta.monitor.prober import ProbeResult, close_client, probe_all
from deta.monitor.watcher import watch_configs

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>deta dashboard</title>
  <link rel="icon" href="data:,">
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; }
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: #0b1020; color: #e5e7eb; display: flex; flex-direction: column; }
    /* ── header ── */
    header { flex: 0 0 auto; padding: 8px 16px; border-bottom: 1px solid #223; display:flex; align-items:center; justify-content:space-between; gap: 12px; flex-wrap: wrap; }
    .status { display:flex; gap:8px; flex-wrap: wrap; }
    .pill { padding:3px 8px; border-radius: 999px; font-size: 12px; }
    .ok { background:#163a2a; color:#a7f3d0; }
    .bad { background:#3a1b1b; color:#fecaca; }
    .warn { background:#3a3318; color:#fde68a; }
    .restart { background:#3a2e18; color:#fcd34d; }
    .ts { color:#93a3b8; font-size:11px; }
    /* ── main tab bar ── */
    #main-tabs { flex: 0 0 auto; display:flex; gap:0; border-bottom: 1px solid #223; background: #0d1324; padding: 0 12px; }
    .main-tab-btn { background: none; border: none; border-bottom: 2px solid transparent; color: #6b7ea0; padding: 8px 16px; font-size: 13px; cursor: pointer; transition: color .15s, border-color .15s; }
    .main-tab-btn:hover { color: #dbeafe; }
    .main-tab-btn.active { color: #dbeafe; border-bottom-color: #4f83cc; }
    /* ── panels ── */
    #panels { flex: 1 1 0; min-height: 0; position: relative; }
    .panel { display: none; position: absolute; inset: 0; overflow: hidden; flex-direction: column; padding: 12px; gap: 8px; }
    .panel.active { display: flex; }
    /* ── shared ── */
    .row { display:flex; align-items:center; justify-content:space-between; gap: 8px; flex-wrap: wrap; }
    .actions { display:flex; gap: 6px; flex-wrap: wrap; }
    .btn { background: #1f2a44; color: #dbeafe; border: 1px solid #2f446e; border-radius: 8px; padding: 5px 10px; font-size: 12px; cursor: pointer; }
    .btn:hover { background: #253456; }
    h3 { margin: 0; font-size: 14px; color: #93c5fd; }
    /* ── sub-tabs (map data / monitor) ── */
    .sub-tabs { display:flex; gap:6px; }
    .sub-tab-btn { background: #1f2a44; color: #93a3b8; border: 1px solid #2f446e; border-radius: 6px; padding: 4px 10px; font-size: 12px; cursor: pointer; }
    .sub-tab-btn.active { background: #2f446e; color: #dbeafe; }
    /* ── graph panel ── */
    #graph-wrap { flex: 1 1 0; overflow: hidden; background: #0f1526; border: 1px solid #223; border-radius: 8px; cursor: grab; position: relative; }
    #graph-wrap.dragging { cursor: grabbing; }
    #graph { position: absolute; top: 0; left: 0; transform-origin: 0 0; }
    #graph svg { display: block; width: auto !important; max-width: none !important; height: auto !important; }
    #zoom-controls { position: absolute; bottom: 10px; right: 10px; display: flex; flex-direction: column; gap: 4px; z-index: 10; }
    .zoom-btn { background: #1f2a44; color: #dbeafe; border: 1px solid #2f446e; border-radius: 6px; width: 28px; height: 28px; font-size: 16px; line-height: 1; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    .zoom-btn:hover { background: #253456; }
    /* ── map data panel ── */
    #sub-json-dump, #sub-yaml-dump { flex: 1 1 0; overflow: auto; white-space: pre; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; background: #0b1328; border: 1px solid #223; border-radius: 8px; padding: 10px; display:none; }
    #sub-json-dump.active, #sub-yaml-dump.active { display: block; }
    #sub-png-dump { flex: 1 1 0; overflow: auto; display: none; }
    #sub-png-dump.active { display: flex; align-items: flex-start; justify-content: center; }
    #sub-png-dump img { max-width: 100%; height: auto; }
    /* ── alerts panel ── */
    #alerts { flex: 1 1 0; overflow: auto; }
    .alert { border-bottom:1px solid #223; padding: 8px 0; font-size: 13px; }
    /* ── monitor panel ── */
    #monitor-table-wrap { flex: 1 1 0; overflow: auto; background: #0b1328; border: 1px solid #223; border-radius: 8px; }
    #monitor-table-wrap table { width:100%; border-collapse:collapse; font-size:12px; }
    #monitor-table-wrap thead th { position: sticky; top: 0; background: #111827; text-align:left; border-bottom:1px solid #223; padding:7px 8px; font-size:11px; color:#6b7ea0; text-transform: uppercase; letter-spacing:.05em; }
    #notify-panel { display:none; flex-direction:column; gap:10px; padding: 8px; }
    #notify-panel.active { display: flex; }
    /* ── status colors ── */
    .s-online { color:#a7f3d0; font-weight:600; }
    .s-offline { color:#fca5a5; font-weight:600; }
    .s-unknown { color:#93a3b8; }
    .s-restarting { color:#fcd34d; font-weight:600; }
    .row-changed-online  { background: #0d2a1a !important; transition: background 1s ease-out; }
    .row-changed-offline  { background: #2a0d0d !important; transition: background 1s ease-out; }
    .row-changed-restarting { background: #2a220d !important; transition: background 1s ease-out; }
    .row-changed { background: #1e2d4a !important; transition: background 1s ease-out; }
  </style>
</head>
<body>
  <header>
    <div style="display:flex;align-items:center;gap:12px;">
      <strong>deta dashboard</strong>
      <span id="root" class="ts"></span>
      <span id="refresh-countdown" class="ts">refresh in: 10s</span>
    </div>
    <div class="status">
      <span class="pill ok" id="services-pill">services: 0</span>
      <span class="pill warn" id="anomalies-pill">anomalies: 0</span>
      <span class="pill restart" id="restarting-pill">restarting: 0</span>
      <span class="pill bad" id="offline-pill">offline: 0</span>
    </div>
  </header>

  <nav id="main-tabs">
    <button class="main-tab-btn active" data-panel="panel-map">Service Map</button>
    <button class="main-tab-btn" data-panel="panel-data">Map Data</button>
    <button class="main-tab-btn" data-panel="panel-alerts">Alerts</button>
    <button class="main-tab-btn" data-panel="panel-monitor">Monitor</button>
  </nav>

  <div id="panels">

    <!-- SERVICE MAP -->
    <section id="panel-map" class="panel active">
      <div class="row">
        <h3>Service Map</h3>
        <div class="actions">
          <button class="btn" id="copy-mermaid">Copy Mermaid</button>
          <button class="btn" id="copy-png">Copy PNG</button>
        </div>
      </div>
      <div id="graph-wrap">
        <div id="graph" class="mermaid">graph LR; Boot[Loading] --> Wait[Waiting for data]</div>
        <div id="zoom-controls">
          <button class="zoom-btn" id="zoom-in" title="Zoom in">+</button>
          <button class="zoom-btn" id="zoom-reset" title="Reset" style="font-size:11px;">⌂</button>
          <button class="zoom-btn" id="zoom-out" title="Zoom out">−</button>
        </div>
      </div>
    </section>

    <!-- MAP DATA -->
    <section id="panel-data" class="panel">
      <div class="row">
        <div class="sub-tabs">
          <button class="sub-tab-btn active" data-sub="sub-json-dump">JSON</button>
          <button class="sub-tab-btn" data-sub="sub-yaml-dump">YAML</button>
          <button class="sub-tab-btn" data-sub="sub-png-dump">PNG</button>
        </div>
        <div class="actions">
          <button class="btn" id="copy-json">Copy JSON</button>
          <button class="btn" id="copy-yaml">Copy YAML</button>
          <button class="btn" id="download-png">Download PNG</button>
        </div>
      </div>
      <pre id="sub-json-dump" class="active"></pre>
      <pre id="sub-yaml-dump"></pre>
      <div id="sub-png-dump"><img id="png-dump" alt="infra map png" style="max-width:100%;height:auto;"></div>
    </section>

    <!-- ALERTS -->
    <section id="panel-alerts" class="panel">
      <div class="row"><h3>Alerts</h3></div>
      <div id="alerts"></div>
    </section>

    <!-- MONITOR -->
    <section id="panel-monitor" class="panel">
      <div class="row">
        <div class="sub-tabs">
          <button class="sub-tab-btn active" data-sub="monitor-table-wrap">Table</button>
          <button class="sub-tab-btn" data-sub="notify-panel">Notifications</button>
        </div>
        <div class="actions">
          <button class="btn" id="copy-monitor-json">Copy JSON</button>
          <button class="btn" id="copy-monitor-csv">Copy CSV</button>
          <button class="btn" id="download-monitor-csv">Download CSV</button>
        </div>
      </div>
      <div id="monitor-table-wrap" class="active">
        <table>
          <thead>
            <tr>
              <th>Service</th>
              <th>Status</th>
              <th>Host</th>
              <th>Port</th>
              <th>Latency</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody id="monitor-table-body"></tbody>
        </table>
      </div>
      <div id="notify-panel">
        <label><input type="checkbox" id="notify-enabled" checked /> Enable browser notifications</label>
        <label>Minimum severity:
          <select id="notify-severity" class="btn" style="margin-left:6px;">
            <option value="info">info</option>
            <option value="warning">warning</option>
            <option value="error">error</option>
          </select>
        </label>
        <button class="btn" id="notify-permission">Request permission</button>
      </div>
    </section>

  </div>

  <script>
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
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
    const refreshCountdown = document.getElementById('refresh-countdown');
    const jsonDump = document.getElementById('sub-json-dump');
    const yamlDump = document.getElementById('sub-yaml-dump');
    const pngDump = document.getElementById('png-dump');
    const monitorTableBody = document.getElementById('monitor-table-body');
    const notifyEnabled = document.getElementById('notify-enabled');
    const notifySeverity = document.getElementById('notify-severity');
    const notifyPermissionBtn = document.getElementById('notify-permission');
    const copyMermaidBtn = document.getElementById('copy-mermaid');
    const copyPngBtn = document.getElementById('copy-png');
    const copyJsonBtn = document.getElementById('copy-json');
    const copyYamlBtn = document.getElementById('copy-yaml');
    const downloadPngBtn = document.getElementById('download-png');

    let latestPayload = null;
    let latestFullPayload = null;
    let latestPngUrl = null;
    let lastGraphHash = null;
    let serviceStatusCache = {};
    let monitorRows = {};
    let refreshSeconds = 10;
    let refreshRemaining = 10;

    const severityWeight = { info: 0, warning: 1, error: 2 };

    function addAlert(message, severity, ts) {
      const div = document.createElement('div');
      div.className = 'alert';
      div.innerHTML = `<div>[${severity}] ${message}</div><div class="ts">${ts}</div>`;
      alerts.prepend(div);
      while (alerts.children.length > 200) alerts.removeChild(alerts.lastChild);
      const minSeverity = notifySeverity?.value || 'info';
      const canNotify = notifyEnabled?.checked && (severityWeight[severity] || 0) >= (severityWeight[minSeverity] || 0);
      if (canNotify && Notification.permission === 'granted') {
        try { new Notification(`[deta] ${severity}`, { body: message }); } catch (e) {}
      }
    }

    const STATUS_ICON = { online: '\u25cf', offline: '\u25cb', restarting: '\u21bb', unknown: '?' };
    const STATUS_CLASS = { online: 's-online', offline: 's-offline', restarting: 's-restarting', unknown: 's-unknown' };

    function fmtLatency(ms) {
      if (ms == null || ms === '-' || ms === 0 && typeof ms === 'string') return '-';
      const n = parseFloat(ms);
      if (isNaN(n)) return '-';
      return n < 1 ? '<1' : Math.round(n) + ' ms';
    }

    function fmtTs(ts) {
      if (!ts) return '-';
      try {
        const d = new Date(ts);
        return d.toLocaleTimeString();
      } catch (e) { return ts; }
    }

    let _prevRowStatus = {};
    const _rowChangeTimers = {};
    const STATUS_HIGHLIGHT = { online: 'row-changed-online', offline: 'row-changed-offline', restarting: 'row-changed-restarting' };

    function _flashRow(tr, status) {
      const cls = STATUS_HIGHLIGHT[status] || 'row-changed';
      tr.classList.remove('row-changed-online', 'row-changed-offline', 'row-changed-restarting', 'row-changed');
      void tr.offsetWidth;
      tr.classList.add(cls);
      const svcId = tr.id;
      if (_rowChangeTimers[svcId]) clearTimeout(_rowChangeTimers[svcId]);
      _rowChangeTimers[svcId] = setTimeout(() => {
        tr.classList.remove(cls);
        delete _rowChangeTimers[svcId];
      }, refreshSeconds * 1000);
    }

    function monitorRowsToSortedArray() {
      return Object.values(monitorRows).sort((a, b) => a.service.localeCompare(b.service));
    }

    function monitorRowsToJson() {
      return JSON.stringify(monitorRowsToSortedArray(), null, 2);
    }

    function monitorRowsToCsv() {
      const rows = monitorRowsToSortedArray();
      const header = 'service,status,host,port,latency_ms,updated_at';
      const lines = rows.map(r => {
        const lat = r.latency_ms != null ? Math.round(parseFloat(r.latency_ms)) : '';
        return `${r.service},${r.status || ''},${r.host || ''},${r.port || ''},${lat},${r.updated_at || ''}`;
      });
      return [header, ...lines].join(String.fromCharCode(10));
    }

    function renderMonitorTable() {
      const rows = monitorRowsToSortedArray();
      const changedRows = [];
      const fragment = document.createDocumentFragment();
      rows.forEach(row => {
        const status = row.status || 'unknown';
        const cls = STATUS_CLASS[status] || 's-unknown';
        const icon = STATUS_ICON[status] || '?';
        const changed = _prevRowStatus[row.service] !== status;
        _prevRowStatus[row.service] = status;
        const trId = `mtr-${row.service.replace(/[^a-z0-9]/gi, '_')}`;
        let tr = document.getElementById(trId);
        if (!tr) {
          tr = document.createElement('tr');
          tr.id = trId;
        }
        tr.innerHTML = `
          <td style="padding:6px; border-bottom:1px solid #1a2540; font-size:12px;">${row.service}</td>
          <td style="padding:6px; border-bottom:1px solid #1a2540;"><span class="${cls}">${icon} ${status}</span></td>
          <td style="padding:6px; border-bottom:1px solid #1a2540; font-size:12px; color:#93a3b8;">${row.host || '-'}</td>
          <td style="padding:6px; border-bottom:1px solid #1a2540; font-size:12px; color:#93a3b8;">${row.port || '-'}</td>
          <td style="padding:6px; border-bottom:1px solid #1a2540; font-size:12px; color:#93a3b8;">${fmtLatency(row.latency_ms)}</td>
          <td style="padding:6px; border-bottom:1px solid #1a2540; font-size:11px; color:#6b7ea0;">${fmtTs(row.updated_at)}</td>
        `;
        if (changed) changedRows.push({ tr, status });
        fragment.appendChild(tr);
      });
      monitorTableBody.innerHTML = '';
      monitorTableBody.appendChild(fragment);
      changedRows.forEach(({ tr, status }) => _flashRow(tr, status));
    }

    function rebuildMonitorRowsFromPayload(payload) {
      const parsed = payload.topology_json ? JSON.parse(payload.topology_json) : { services: {} };
      const nowTs = new Date().toISOString();
      const rows = {};
      Object.entries(parsed.services || {}).forEach(([service, svc]) => {
        const probes = svc.probes || [];
        const firstProbe = probes[0] || {};
        rows[service] = {
          service,
          status: svc.status || 'unknown',
          latency_ms: firstProbe.latency_ms ?? '-',
          updated_at: nowTs,
        };
      });
      return rows;
    }

    async function render(payload) {
      const isDelta = payload.type === 'delta';
      const summary = payload.summary || {};

      if (isDelta) {
        if (payload.status_delta) {
          serviceStatusCache = { ...serviceStatusCache, ...payload.status_delta };
          Object.entries(payload.status_delta).forEach(([service, status]) => {
            if (status === 'removed') { delete monitorRows[service]; }
          });
        }
        if (payload.service_rows && payload.service_rows.length > 0) {
          payload.service_rows.forEach((row) => {
            if (payload.status_delta && payload.status_delta[row.service] === 'removed') return;
            monitorRows[row.service] = row;
          });
        }
      }

      latestPayload = payload;
      rootInfo.textContent = payload.root || '';
      if (payload.refresh_seconds) {
        refreshSeconds = payload.refresh_seconds;
      }
      refreshRemaining = refreshSeconds;
      servicesPill.textContent = `services: ${summary.services || 0}`;
      anomaliesPill.textContent = `anomalies: ${summary.anomalies || 0}`;
      const restartPill = document.getElementById('restarting-pill');
      if (restartPill) restartPill.textContent = `restarting: ${summary.restarting || 0}`;
      offlinePill.textContent = `offline: ${summary.offline || 0}`;

      const graphHash = payload.graph_hash || null;
      if (!isDelta && graphHash !== lastGraphHash) {
        lastGraphHash = graphHash;
        graph.removeAttribute('data-processed');
        graph.textContent = payload.mermaid;
        await mermaid.init(undefined, graph);
        setTimeout(() => window._graphFit && window._graphFit(), 50);

        try {
          const pngBlob = await renderPngBlob();
          if (pngBlob) {
            if (latestPngUrl) URL.revokeObjectURL(latestPngUrl);
            latestPngUrl = URL.createObjectURL(pngBlob);
            pngDump.src = latestPngUrl;
          }
        } catch (pngErr) {
          if (!(pngErr && pngErr.name === 'SecurityError')) {
            console.warn('[PNG] renderPngBlob error:', pngErr);
          }
        }
      }

      if (!isDelta) {
        latestFullPayload = payload;
        jsonDump.textContent = payload.topology_json || '';
        yamlDump.textContent = payload.graph_yaml || '';
        const serviceRows = payload.service_rows || [];
        if (serviceRows.length > 0) {
          monitorRows = {};
          serviceRows.forEach((row) => {
            monitorRows[row.service] = row;
          });
        } else {
          monitorRows = rebuildMonitorRowsFromPayload(payload);
        }
      }

      renderMonitorTable();

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

    // ── pan/zoom ──
    (function initPanZoom() {
      const wrap = document.getElementById('graph-wrap');
      const g = document.getElementById('graph');
      let scale = 1, tx = 0, ty = 0;
      let dragging = false, startX = 0, startY = 0, startTx = 0, startTy = 0;

      function applyTransform() {
        g.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`;
      }

      function fitToWrap() {
        const svg = g.querySelector('svg');
        if (!svg) return;
        const ww = wrap.clientWidth, wh = wrap.clientHeight;
        const sw = svg.getBoundingClientRect().width / scale;
        const sh = svg.getBoundingClientRect().height / scale;
        if (!sw || !sh) return;
        scale = Math.min(ww / sw, wh / sh, 1);
        tx = (ww - sw * scale) / 2;
        ty = 8;
        applyTransform();
      }

      window._graphFit = fitToWrap;

      wrap.addEventListener('wheel', (e) => {
        e.preventDefault();
        const rect = wrap.getBoundingClientRect();
        const mx = e.clientX - rect.left - tx;
        const my = e.clientY - rect.top - ty;
        const delta = e.deltaY < 0 ? 1.12 : 1 / 1.12;
        scale = Math.min(Math.max(scale * delta, 0.1), 10);
        tx -= mx * (delta - 1);
        ty -= my * (delta - 1);
        applyTransform();
      }, { passive: false });

      wrap.addEventListener('pointerdown', (e) => {
        if (e.button !== 0) return;
        dragging = true; startX = e.clientX; startY = e.clientY; startTx = tx; startTy = ty;
        wrap.setPointerCapture(e.pointerId);
        wrap.classList.add('dragging');
      });
      wrap.addEventListener('pointermove', (e) => {
        if (!dragging) return;
        tx = startTx + (e.clientX - startX);
        ty = startTy + (e.clientY - startY);
        applyTransform();
      });
      wrap.addEventListener('pointerup', () => { dragging = false; wrap.classList.remove('dragging'); });

      document.getElementById('zoom-in').addEventListener('click', () => {
        const cx = wrap.clientWidth / 2, cy = wrap.clientHeight / 2;
        const mx = cx - tx, my = cy - ty;
        const d = 1.25;
        scale = Math.min(scale * d, 10);
        tx -= mx * (d - 1); ty -= my * (d - 1);
        applyTransform();
      });
      document.getElementById('zoom-out').addEventListener('click', () => {
        const cx = wrap.clientWidth / 2, cy = wrap.clientHeight / 2;
        const mx = cx - tx, my = cy - ty;
        const d = 1 / 1.25;
        scale = Math.max(scale * d, 0.1);
        tx -= mx * (d - 1); ty -= my * (d - 1);
        applyTransform();
      });
      document.getElementById('zoom-reset').addEventListener('click', fitToWrap);
    })();

    copyMermaidBtn.addEventListener('click', () => copyText('Mermaid', latestFullPayload?.mermaid || ''));
    copyJsonBtn.addEventListener('click', () => copyText('JSON', latestFullPayload?.topology_json || ''));
    copyYamlBtn.addEventListener('click', () => copyText('YAML', latestFullPayload?.graph_yaml || ''));
    copyPngBtn.addEventListener('click', copyPng);
    downloadPngBtn.addEventListener('click', downloadPng);
    notifyPermissionBtn.addEventListener('click', () => Notification.requestPermission().catch(() => {}));

    document.getElementById('copy-monitor-json').addEventListener('click', () => copyText('Monitor JSON', monitorRowsToJson()));
    document.getElementById('copy-monitor-csv').addEventListener('click', () => copyText('Monitor CSV', monitorRowsToCsv()));
    document.getElementById('download-monitor-csv').addEventListener('click', () => {
      const csv = monitorRowsToCsv();
      if (!csv) { addAlert('Monitor data is empty', 'warning', new Date().toISOString()); return; }
      downloadBlob(new Blob([csv], { type: 'text/csv' }), 'monitor.csv');
      addAlert('monitor.csv downloaded', 'info', new Date().toISOString());
    });

    document.querySelectorAll('.main-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.main-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.panel).classList.add('active');
      });
    });

    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const panel = btn.closest('.panel');
        panel.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
        panel.querySelectorAll('[id]').forEach(el => {
          if (el.dataset && el.id && panel.querySelector(`.sub-tab-btn[data-sub="${el.id}"]`)) {
            el.classList.remove('active');
          }
        });
        btn.classList.add('active');
        document.getElementById(btn.dataset.sub).classList.add('active');
      });
    });

    setInterval(() => {
      refreshRemaining = Math.max(0, refreshRemaining - 1);
      if (refreshRemaining === 0) {
        refreshRemaining = refreshSeconds;
      }
      refreshCountdown.textContent = `refresh in: ${refreshRemaining}s`;
    }, 1000);

    Notification.requestPermission().catch(() => {});
    const wsScheme = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${wsScheme}://${location.host}/ws`);
    ws.onopen = () => console.log('[WS] Connected');
    ws.onmessage = async (event) => {
      console.log('[WS] Received data, length:', event.data.length);
      try {
        const payload = JSON.parse(event.data);
        console.log('[WS] Payload keys:', Object.keys(payload));
        console.log('[WS] Summary:', payload.summary);
        await render(payload);
        console.log('[WS] Render completed');
      } catch (err) {
        console.error('[WS] Error processing message:', err);
        addAlert('WebSocket error: ' + err.message, 'error', new Date().toISOString());
      }
    };
    ws.onerror = (err) => console.error('[WS] Error:', err);
    ws.onclose = (ev) => {
      console.log('[WS] Closed:', ev.code, ev.reason);
      addAlert('WebSocket disconnected', 'warning', new Date().toISOString());
    };
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

    def has_connections(self) -> bool:
        return bool(self._connections)

    def disconnect(self, websocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> tuple[int, int]:
        if not self._connections:
            return 0, 0
        message = json.dumps(payload)
        message_size = len(message.encode("utf-8"))
        dead = []
        connections = list(self._connections)
        results = await asyncio.gather(
            *(conn.send_text(message) for conn in connections),
            return_exceptions=True,
        )
        delivered = 0
        for conn, result in zip(connections, results):
            if isinstance(result, Exception):
                dead.append(conn)
            else:
                delivered += 1
        for conn in dead:
            self.disconnect(conn)
        return delivered, message_size


def _probe_status(probe: ProbeResult | None) -> str:
    if probe is None:
        return "unknown"
    if probe.ok:
        return "online"
    if probe.status is not None and probe.status >= 500:
        return "restarting"
    return "offline"


def _topology_summary(
    topology: InfraTopology,
    probes: list[ProbeResult] | None,
    anomaly_count: int | None = None,
) -> dict:
    if anomaly_count is None:
        anomaly_count = len(topology.detect_anomalies())
    offline = 0
    restarting = 0
    if probes:
        for r in probes:
            if r.ok:
                continue
            if r.status is not None and r.status >= 500:
                restarting += 1
            else:
                offline += 1
    return {
        "services": len(topology.services),
        "anomalies": anomaly_count,
        "offline": offline,
        "restarting": restarting,
    }


def _topology_json_with_status(
    topology: InfraTopology,
    probes: list[ProbeResult] | None,
    static_services: dict[str, dict] | None = None,
    static_meta: dict | None = None,
) -> str:
    services: dict[str, dict] = {}
    source_services = static_services or {
        service_name: asdict(service)
        for service_name, service in topology.services.items()
    }
    for service_name, base_payload in source_services.items():
        payload = dict(base_payload)
        # Get all probes for this service (may be multiple, one per port)
        service_probes = [p for p in (probes or []) if p.service == service_name]

        # Overall status: online if any port is online
        if not service_probes:
            status = "unknown"
        elif any(p.ok for p in service_probes):
            status = "online"
        elif any(p.status is not None and p.status >= 500 for p in service_probes):
            status = "restarting"
        else:
            status = "offline"

        payload["status"] = status

        # Add probe info for each port
        if service_probes:
            payload["probes"] = [
                {
                    "url": p.url,
                    "ok": p.ok,
                    "status": p.status,
                    "latency_ms": p.latency_ms,
                    "error": p.error,
                    "host_port": p.host_port,
                }
                for p in service_probes
            ]

        services[service_name] = payload

    if static_meta is None:
        static_meta = {
            "endpoints": [asdict(endpoint) for endpoint in topology.endpoints],
            "anomalies": topology.detect_anomalies(),
            "cycles": topology.detect_cycles(),
            "hubs": topology.find_hubs(),
        }

    map_payload = {
        "services": services,
        "endpoints": static_meta.get("endpoints", []),
        "anomalies": static_meta.get("anomalies", []),
        "cycles": static_meta.get("cycles", []),
        "hubs": static_meta.get("hubs", []),
    }
    return json.dumps(map_payload, indent=2)


def _service_status_map(
    topology: InfraTopology,
    probes: list[ProbeResult] | None,
) -> dict[str, str]:
    probes_by_service: dict[str, list[ProbeResult]] = {}
    for probe in probes or []:
        probes_by_service.setdefault(probe.service, []).append(probe)

    statuses: dict[str, str] = {}
    for service_name in topology.services.keys():
        service_probes = probes_by_service.get(service_name, [])
        if not service_probes:
            statuses[service_name] = "unknown"
        elif any(p.ok for p in service_probes):
            statuses[service_name] = "online"
        elif any(p.status is not None and p.status >= 500 for p in service_probes):
            statuses[service_name] = "restarting"
        else:
            statuses[service_name] = "offline"
    return statuses


def _compute_events(
    prev_services: set[str],
    prev_probes: list[ProbeResult] | None,
    topology: InfraTopology,
    probes: list[ProbeResult] | None,
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
        # Group probes by service
        prev_by_service = {}
        for p in prev_probes:
            prev_by_service.setdefault(p.service, []).append(p)

        current_by_service = {}
        for p in probes:
            current_by_service.setdefault(p.service, []).append(p)

        # Check each service's overall status change
        for svc in set(prev_by_service) | set(current_by_service):
            prev_list = prev_by_service.get(svc, [])
            curr_list = current_by_service.get(svc, [])

            # Determine overall status: online if any port is online
            prev_ok = any(p.ok for p in prev_list)
            curr_ok = any(p.ok for p in curr_list)

            if prev_ok and not curr_ok:
                if any(p.status is not None and p.status >= 500 for p in curr_list) and "service_restarting" in enabled:
                    events.append({"severity": "warning", "message": f"service restarting: {svc}", "timestamp": ts})
                elif "service_down" in enabled:
                    events.append({"severity": "error", "message": f"service down: {svc}", "timestamp": ts})
            elif not prev_ok and curr_ok and "service_up" in enabled:
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
    topology_cache = TopologyCache(ttl_seconds=config.web.cache_ttl_seconds)

    state = {
        "prev_services": set(),
        "prev_probes": None,
        "prev_service_status": {},
        "payload_version": 0,
        "topology": None,
        "topology_services": {},
        "topology_meta": {},
        "anomaly_count": 0,
        "mermaid": "",
        "graph_yaml": "",
        "graph_hash": "",
        "topology_dirty": True,
        "pending_change_events": [],
        "debounce_task": None,
        "probes_cache": None,
        "probes_cache_ts": 0,
        "telemetry": {
            "full_count": 0,
            "delta_count": 0,
            "full_bytes": 0,
            "delta_bytes": 0,
            "last_log_ts": datetime.utcnow().timestamp(),
            "log_interval_seconds": 30,
        },
    }

    async def _refresh_topology():
        topology = await topology_cache.get(root, depth, build_topology)
        anomalies = topology.detect_anomalies()
        cycles = topology.detect_cycles()
        hubs = topology.find_hubs()
        static_services = {
            service_name: asdict(service)
            for service_name, service in topology.services.items()
        }
        static_meta = {
            "endpoints": [asdict(endpoint) for endpoint in topology.endpoints],
            "anomalies": anomalies,
            "cycles": cycles,
            "hubs": hubs,
        }

        mermaid_code = generate_mermaid(topology, state["prev_probes"])
        graph_hash = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
        state["topology"] = topology
        state["topology_services"] = static_services
        state["topology_meta"] = static_meta
        state["anomaly_count"] = len(anomalies)
        state["mermaid"] = mermaid_code
        state["graph_yaml"] = generate_graph_yaml(topology, state["prev_probes"])
        state["graph_hash"] = graph_hash
        state["topology_dirty"] = False
        return topology

    def _record_telemetry(payload: dict, delivered: int, message_size: int) -> None:
        if delivered <= 0 or message_size <= 0:
            return

        telemetry = state["telemetry"]
        payload_type = payload.get("type", "full")
        total_bytes = delivered * message_size
        if payload_type == "delta":
            telemetry["delta_count"] += delivered
            telemetry["delta_bytes"] += total_bytes
        else:
            telemetry["full_count"] += delivered
            telemetry["full_bytes"] += total_bytes

        now_ts = datetime.utcnow().timestamp()
        if now_ts - telemetry["last_log_ts"] < telemetry["log_interval_seconds"]:
            return

        full_count = telemetry["full_count"]
        delta_count = telemetry["delta_count"]
        total_count = full_count + delta_count
        full_bytes = telemetry["full_bytes"]
        delta_bytes = telemetry["delta_bytes"]
        total_bytes_window = full_bytes + delta_bytes
        delta_ratio = (delta_count / total_count * 100.0) if total_count else 0.0
        avg_full = int(full_bytes / full_count) if full_count else 0
        avg_delta = int(delta_bytes / delta_count) if delta_count else 0

        print(
            "[web.telemetry] "
            f"window={int(telemetry['log_interval_seconds'])}s "
            f"msgs full={full_count} delta={delta_count} delta_ratio={delta_ratio:.1f}% "
            f"bytes total={total_bytes_window} avg_full={avg_full} avg_delta={avg_delta}"
        )

        telemetry["full_count"] = 0
        telemetry["delta_count"] = 0
        telemetry["full_bytes"] = 0
        telemetry["delta_bytes"] = 0
        telemetry["last_log_ts"] = now_ts

    async def collect_payload(
        events: list[dict] | None = None,
        force_rescan: bool = False,
        prefer_delta: bool = False,
    ) -> dict | None:
        if state["topology_dirty"] or force_rescan or state["topology"] is None:
            topology = await _refresh_topology()
        else:
            topology = state["topology"]

        graph_changed = False
        probes = None
        if config.monitor.probe_online:
            # Invalidate probes cache on topology rescan
            if force_rescan or state["topology_dirty"]:
                state["probes_cache"] = None
            # Use cached probes if still valid (half of refresh_interval)
            cache_ttl = config.web.refresh_seconds / 2
            now = datetime.utcnow().timestamp()
            if state["probes_cache"] and (now - state["probes_cache_ts"]) < cache_ttl:
                probes = state["probes_cache"]
            else:
                probes = await probe_all(list(topology.services.values()), max_concurrency=config.monitor.max_concurrency)
                state["probes_cache"] = probes
                state["probes_cache_ts"] = now

            if probes and state["topology_dirty"] is False:
                mermaid_code = generate_mermaid(topology, probes)
                graph_hash = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
                if graph_hash != state["graph_hash"]:
                    graph_changed = True
                    state["mermaid"] = mermaid_code
                    state["graph_yaml"] = generate_graph_yaml(topology, probes)
                    state["graph_hash"] = graph_hash

        summary = {
            **_topology_summary(topology, probes, state["anomaly_count"]),
            "anomalies": state["anomaly_count"],
        }
        merged_events = list(events or [])

        current_services = set(topology.services.keys())
        payload_events = _compute_events(
            state["prev_services"],
            state["prev_probes"],
            topology,
            probes,
            set(config.web.push_events),
        )
        if payload_events:
            merged_events.extend(payload_events)

        current_status = _service_status_map(topology, probes)
        previous_status = dict(state["prev_service_status"])
        status_delta = {
            service: status
            for service, status in current_status.items()
            if previous_status.get(service) != status
        }
        for service in previous_status.keys() - current_status.keys():
            status_delta[service] = "removed"

        state["prev_services"] = current_services
        state["prev_probes"] = probes
        state["prev_service_status"] = current_status
        state["payload_version"] += 1

        now_ts = datetime.utcnow().isoformat()
        service_rows = []
        for service_name, service_status in current_status.items():
            service_probes = [p for p in (probes or []) if p.service == service_name]
            first_probe = service_probes[0] if service_probes else None
            svc_def = topology.services.get(service_name)

            # Collect all published host ports from resolved_ports
            resolved = svc_def.resolved_ports if svc_def else []
            pub_ports = [b.host_port for b in resolved if b.is_resolved]
            pub_hosts = [b.host or "localhost" for b in resolved if b.is_resolved]

            # Best host: from probe URL, fallback to resolved binding host
            probe_url = first_probe.url if first_probe else ""
            try:
                probe_host = urlparse(probe_url).hostname or ""
            except Exception:
                probe_host = ""
            host = probe_host or (pub_hosts[0] if pub_hosts else "localhost")

            # Best port: probe host_port if it matches a published port, else use all published ports
            probe_hp = first_probe.host_port if first_probe else ""
            if probe_hp and probe_hp in pub_ports:
                port = probe_hp
            elif pub_ports:
                port = ",".join(pub_ports)
            else:
                port = probe_hp

            service_rows.append(
                {
                    "service": service_name,
                    "status": service_status,
                    "latency_ms": first_probe.latency_ms if first_probe else None,
                    "updated_at": now_ts,
                    "host": host,
                    "port": port,
                }
            )

        if prefer_delta and not force_rescan and not graph_changed:
            return {
                "type": "delta",
                "v": state["payload_version"],
                "root": str(root),
                "refresh_seconds": config.web.refresh_seconds,
                "summary": summary,
                "graph_hash": state["graph_hash"],
                "status_delta": status_delta,
                "service_rows": service_rows,
                "events": merged_events,
            }

        return {
            "type": "full",
            "v": state["payload_version"],
            "root": str(root),
            "refresh_seconds": config.web.refresh_seconds,
            "summary": summary,
            "mermaid": state["mermaid"],
            "graph_yaml": state["graph_yaml"],
            "graph_hash": state["graph_hash"],
            "service_rows": service_rows,
            "topology_json": _topology_json_with_status(
                topology,
                probes,
                state["topology_services"],
                state["topology_meta"],
            ),
            "events": merged_events,
        }

    async def monitor_loop() -> None:
        payload = await collect_payload(force_rescan=True)
        delivered, message_size = await manager.broadcast(payload)
        _record_telemetry(payload, delivered, message_size)

        async def periodic_refresh():
            while True:
                await asyncio.sleep(config.web.refresh_seconds)
                if not manager.has_connections():
                    continue
                payload = await collect_payload(prefer_delta=True)
                delivered, message_size = await manager.broadcast(payload)
                _record_telemetry(payload, delivered, message_size)

        async def flush_changes_after_debounce(debounce_seconds: float = None):
            if debounce_seconds is None:
                debounce_seconds = config.web.debounce_seconds
            try:
                await asyncio.sleep(debounce_seconds)
            except asyncio.CancelledError:
                return

            pending_events = list(state["pending_change_events"])
            state["pending_change_events"].clear()
            payload = await collect_payload(events=pending_events)
            delivered, message_size = await manager.broadcast(payload)
            _record_telemetry(payload, delivered, message_size)

        async def on_change(change: dict):
            topology_cache.invalidate()
            state["topology_dirty"] = True
            state["pending_change_events"].append({
                "severity": "warning",
                "message": f"config change: {change.get('path', '')}",
                "timestamp": change.get("timestamp", ""),
            })

            task = state.get("debounce_task")
            if task and not task.done():
                task.cancel()
            state["debounce_task"] = asyncio.create_task(flush_changes_after_debounce())

        await asyncio.gather(
            periodic_refresh(),
            watch_configs(root, on_change),
        )

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
        await close_client()

    @app.get("/")
    async def index():
        return HTMLResponse(HTML.replace("deta dashboard", config.web.title))

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        client = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
        print(f"[WS] Client connected: {client}")
        try:
            if state["topology"] is not None:
                payload = await collect_payload()
            else:
                payload = await collect_payload(force_rescan=True)
            message = json.dumps(payload)
            print(f"[WS] Sending payload to {client}: {len(message)} bytes, {len(payload.get('summary', {}))} summary fields")
            await websocket.send_text(message)
            _record_telemetry(payload, 1, len(message.encode("utf-8")))
            print(f"[WS] Payload sent to {client}")
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            print(f"[WS] Client disconnected: {client}")
            manager.disconnect(websocket)
        except Exception as e:
            print(f"[WS] Error with client {client}: {e}")
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

    try:
        uvicorn.run(app, host=bind_host, port=bind_port)
    except KeyboardInterrupt:
        print("\n[deta.web] Stopped by Ctrl+C")
