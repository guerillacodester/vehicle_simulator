"""
Visualizer mini-app
-------------------

FastAPI service that:
- Serves a simple Leaflet map page for visual testing
- Aggregates route geometry (from GeospatialService) and spawned passengers (from Strapi)

Env vars:
- STRAPI_URL (default: http://localhost:1337)
- STRAPI_TOKEN (optional, for protected Strapi APIs)
- GEO_URL (default: http://localhost:8001)

Run:
  uvicorn visualizer.app:app --host 0.0.0.0 --port 8010 --reload
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse


STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337").rstrip("/")
STRAPI_TOKEN = os.getenv("STRAPI_TOKEN")
GEO_URL = os.getenv("GEO_URL", "http://localhost:8001").rstrip("/")

app = FastAPI(title="Passenger Visualizer", version="0.2.0")


def _auth_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if STRAPI_TOKEN:
        headers["Authorization"] = f"Bearer {STRAPI_TOKEN}"
    return headers


# ===============
# REST (fallbacks)
# ===============

@app.get("/api/route/{route_id}/data")
async def route_data(
    route_id: str,
    start: Optional[str] = Query(None, description="ISO8601 start time for spawned_at filter"),
    end: Optional[str] = Query(None, description="ISO8601 end time for spawned_at filter"),
    page_size: int = Query(1000, ge=1, le=1000),
) -> JSONResponse:
    """Return route geometry and passengers for a time window.

    Response JSON:
    {
      "route": {"type":"LineString","coordinates":[[lat,lon], ...]},
      "passengers": [{ id, passenger_id, latitude, longitude, spawned_at, destination_name, destination_lat, destination_lon }],
      "meta": {"count": N}
    }
    """
    # Validate time filters if provided
    params: Dict[str, Any] = {
        "filters[route_id][$eq]": route_id,
        "filters[status][$eq]": "WAITING",
        "pagination[pageSize]": page_size,
        "sort": "spawned_at:asc",
    }
    if start:
        try:
            datetime.fromisoformat(start.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid 'start' time; use ISO8601")
        params["filters[spawned_at][$gte]"] = start
    if end:
        try:
            datetime.fromisoformat(end.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid 'end' time; use ISO8601")
        params["filters[spawned_at][$lte]"] = end

    async with httpx.AsyncClient(timeout=20.0, headers=_auth_headers()) as client:
        # Fetch route geometry
        geo_url = f"{GEO_URL}/spatial/route-geometry/{route_id}"
        geo_resp = await client.get(geo_url)
        if geo_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"GeospatialService error {geo_resp.status_code}")
        route_geom = geo_resp.json()

        # Fetch passengers from Strapi
        strapi_url = f"{STRAPI_URL}/api/active-passengers"
        pax_resp = await client.get(strapi_url, params=params)
        if pax_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Strapi error {pax_resp.status_code}: {pax_resp.text[:200]}")
        pax_json = pax_resp.json()
        passengers: List[Dict[str, Any]] = []
        for p in pax_json.get("data", []):
            attrs = p.get("attributes", p)
            passengers.append({
                "id": p.get("id"),
                "passenger_id": attrs.get("passenger_id"),
                "latitude": attrs.get("latitude"),
                "longitude": attrs.get("longitude"),
                "spawned_at": attrs.get("spawned_at"),
                "destination_name": attrs.get("destination_name"),
                "destination_lat": attrs.get("destination_lat"),
                "destination_lon": attrs.get("destination_lon"),
            })

    return JSONResponse({
        "route": route_geom,
        "passengers": passengers,
        "meta": {"count": len(passengers)}
    })


@app.get("/api/depot/{depot_id}/data")
async def depot_data(
    depot_id: str,
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    page_size: int = Query(1000, ge=1, le=1000),
) -> JSONResponse:
    """Return passengers for a depot time window.

    Response JSON:
    {
      "passengers": [...],
      "meta": {"count": N}
    }
    """
    params: Dict[str, Any] = {
        "filters[depot_id][$eq]": depot_id,
        "filters[status][$eq]": "WAITING",
        "pagination[pageSize]": page_size,
        "sort": "spawned_at:asc",
    }
    if start:
        params["filters[spawned_at][$gte]"] = start
    if end:
        params["filters[spawned_at][$lte]"] = end

    async with httpx.AsyncClient(timeout=20.0, headers=_auth_headers()) as client:
        strapi_url = f"{STRAPI_URL}/api/active-passengers"
        pax_resp = await client.get(strapi_url, params=params)
        if pax_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Strapi error {pax_resp.status_code}: {pax_resp.text[:200]}")
        pax_json = pax_resp.json()
        passengers: List[Dict[str, Any]] = []
        for p in pax_json.get("data", []):
            attrs = p.get("attributes", p)
            passengers.append({
                "id": p.get("id"),
                "passenger_id": attrs.get("passenger_id"),
                "latitude": attrs.get("latitude"),
                "longitude": attrs.get("longitude"),
                "spawned_at": attrs.get("spawned_at"),
                "destination_name": attrs.get("destination_name"),
                "destination_lat": attrs.get("destination_lat"),
                "destination_lon": attrs.get("destination_lon"),
            })

    return JSONResponse({
        "passengers": passengers,
        "meta": {"count": len(passengers)}
    })


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Passenger Visualizer - Route</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    html, body, #map { height: 100%; margin: 0; padding: 0; }
    .panel { position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
    .stats { margin-top: 8px; font-size: 12px; color: #333; }
  </style>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    function getParam(name){ const url = new URL(window.location.href); return url.searchParams.get(name); }
    async function loadData() {
      const routeId = getParam('route_id');
      const start = getParam('start');
      const end = getParam('end');
      if (!routeId) { alert('Missing route_id in query params'); return; }
      const url = new URL(window.location.origin + '/api/route/' + routeId + '/data');
      if (start) url.searchParams.set('start', start);
      if (end) url.searchParams.set('end', end);
      const res = await fetch(url);
      if (!res.ok) { const t = await res.text(); alert('Error loading data: ' + t); return; }
      const data = await res.json();

      const map = L.map('map').setView([13.1900, -59.5432], 11);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      // Draw route
      const coords = (data.route && data.route.coordinates) ? data.route.coordinates : [];
      if (coords.length > 0) {
        const latlngs = coords.map(c => L.latLng(c[0], c[1]));
        const line = L.polyline(latlngs, {color: 'blue', weight: 4}).addTo(map);
        map.fitBounds(line.getBounds(), {padding: [20, 20]});
      }

      // Draw passengers
      const pax = data.passengers || [];
      pax.forEach(p => {
        if (p.latitude != null && p.longitude != null) {
          const m = L.circleMarker([p.latitude, p.longitude], {radius: 5, color: '#d33'}).addTo(map);
          const s = p.spawned_at ? new Date(p.spawned_at).toLocaleString() : 'N/A';
          m.bindPopup(`<b>${p.passenger_id || 'PASSENGER'}</b><br/>Spawned: ${s}<br/>Dest: ${p.destination_name || 'N/A'}`);
        }
      });

      document.getElementById('count').innerText = pax.length;
    }
    window.addEventListener('load', loadData);
  </script>
  </head>
  <body>
    <div class="panel">
      <div><b>Route Viewer</b></div>
      <div class="stats">Passengers: <span id="count">0</span></div>
      <div class="stats">Query params: route_id, start, end (ISO8601)</div>
    </div>
    <div id="map"></div>
  </body>
  </html>
"""


@app.get("/route-viewer", response_class=HTMLResponse)
async def route_viewer() -> HTMLResponse:
    """Serve a simple Leaflet page that fetches route + passengers via the API.

    Use like:
      http://localhost:8010/route-viewer?route_id=gg3pv3z19hhm117v9xth5ezq&start=2025-10-29T09:00:00Z&end=2025-10-29T10:00:00Z
    """
    return HTMLResponse(content=HTML_TEMPLATE)


# ========================
# Pub/Sub stream (LISTEN)
# ========================

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect

PG_DSN = os.getenv("PG_DSN")  # e.g., postgresql://user:pass@host:5432/db

_clients_lock = asyncio.Lock()
_ws_clients: set[WebSocket] = set()
_event_queue: "asyncio.Queue[str]" = asyncio.Queue(maxsize=10000)
_pg_task: Optional[asyncio.Task] = None
_broadcast_task: Optional[asyncio.Task] = None


async def _broadcast_loop():
    while True:
        msg = await _event_queue.get()
        # Broadcast to all connected clients, drop dead sockets
        to_remove: list[WebSocket] = []
        async with _clients_lock:
            for ws in list(_ws_clients):
                try:
                    await ws.send_text(msg)
                except Exception:
                    to_remove.append(ws)
            for ws in to_remove:
                _ws_clients.discard(ws)


async def _pg_listen_loop():
    import asyncpg
    conn = await asyncpg.connect(PG_DSN)
    # Ensure channel exists (LISTEN will implicitly create subscription)
    await conn.add_listener("active_passengers", lambda *args: None)

    # asyncpg doesn't expose a direct awaitable on NOTIFY; use a polling loop on notifications
    # Workaround: register a listener callback that enqueues payloads
    def _on_notify(connection, pid, channel, payload):
        try:
            # Validate JSON payload minimally
            json.loads(payload)
            _event_queue.put_nowait(payload)
        except Exception:
            # Non-JSON payloads are still forwarded as text
            try:
                _event_queue.put_nowait(json.dumps({"channel": channel, "payload": payload}))
            except Exception:
                pass

    await conn.remove_listener("active_passengers", lambda *args: None)
    await conn.add_listener("active_passengers", _on_notify)

    # Keep connection alive
    try:
        while True:
            await asyncio.sleep(60)
            # lightweight keepalive
            await conn.execute("SELECT 1")
    finally:
        try:
            await conn.close()
        except Exception:
            pass


@app.on_event("startup")
async def _startup():
    global _pg_task, _broadcast_task
    if PG_DSN:
        _broadcast_task = asyncio.create_task(_broadcast_loop())
        _pg_task = asyncio.create_task(_pg_listen_loop())


@app.on_event("shutdown")
async def _shutdown():
    global _pg_task, _broadcast_task
    if _pg_task:
        _pg_task.cancel()
    if _broadcast_task:
        _broadcast_task.cancel()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    async with _clients_lock:
        _ws_clients.add(ws)
    try:
        # Keep the connection open; client doesn't have to send anything
        while True:
            # Receive and ignore pings or messages
            await ws.receive_text()
    except WebSocketDisconnect:
        async with _clients_lock:
            _ws_clients.discard(ws)
    except Exception:
        async with _clients_lock:
            _ws_clients.discard(ws)


STREAM_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Passenger Stream Viewer</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    html, body, #map { height: 100%; margin: 0; padding: 0; }
    .panel { position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
    .stats { margin-top: 8px; font-size: 12px; color: #333; }
  </style>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    let map, layer;
    function init() {
      map = L.map('map').setView([13.1900, -59.5432], 11);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);
      layer = L.layerGroup().addTo(map);

      const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${wsProto}://${location.host}/ws`);
      ws.onmessage = (e) => {
        try {
          const ev = JSON.parse(e.data);
          // Expected payload shape: { action, id, passenger_id, route_id, depot_id, latitude, longitude, spawned_at, ... }
          if (ev.latitude != null && ev.longitude != null) {
            const m = L.circleMarker([ev.latitude, ev.longitude], {radius: 5, color: '#d33'}).addTo(layer);
            const s = ev.spawned_at ? new Date(ev.spawned_at).toLocaleString() : 'N/A';
            m.bindPopup(`<b>${ev.passenger_id || 'PASSENGER'}</b><br/>Route: ${ev.route_id || 'N/A'}<br/>Depot: ${ev.depot_id || 'N/A'}<br/>Spawned: ${s}`);
          }
          const c = document.getElementById('count');
          c.textContent = String(Number(c.textContent||'0') + 1);
        } catch(err) {
          console.warn('Bad event', err);
        }
      };
      ws.onopen = () => console.log('WS connected');
      ws.onclose = () => console.log('WS closed');
    }
    window.addEventListener('load', init);
  </script>
  </head>
  <body>
    <div class="panel">
      <div><b>Passenger Stream Viewer</b></div>
      <div class="stats">Events: <span id="count">0</span></div>
      <div class="stats">Connects to /ws and plots passengers live (decoupled from Strapi/Geo)</div>
    </div>
    <div id="map"></div>
  </body>
  </html>
"""


@app.get("/stream-viewer", response_class=HTMLResponse)
async def stream_viewer() -> HTMLResponse:
    return HTMLResponse(STREAM_HTML)
