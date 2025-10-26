# Commuter Service (Passenger Spawning Engine)

Production-grade spawning for depot and route reservoirs using Poisson-based GeoJSON demand, with Strapi for persistence and Socket.IO for events.

## What it does

- Spawns passengers automatically at configurable intervals (default 30s)
- Two reservoirs:
  - DepotReservoir: outbound passengers from depots (queues per depot-route)
  - RouteReservoir: passengers along route polylines (bidirectional)
- Persists to Strapi `active-passengers` endpoints and emits Socket.IO events
- Expiration manager cleans up stale passengers; statistics tracked

## Prerequisites

- Strapi running with:
  - Active depots and routes (with route shapes loaded)
  - `active-passengers` routes enabled (CRUD + mark-boarded/mark-alighted/near-location/etc.)
- Socket.IO hub available at the same base URL (or specify URL)
- Python 3.10+
- Environment variable (optional): `ARKNET_API_URL` (e.g., <http://localhost:1337>)

## Quickstart (Windows PowerShell)

```powershell
# 1) (Optional) set base URL once for both Strapi and Socket.IO
$env:ARKNET_API_URL = 'http://localhost:1337'

# 2) Run Depot reservoir only (outbound passengers)
python -m commuter_service --depot-only

# 3) Run Route reservoir only (spawn along routes)
python -m commuter_service --route-only

# 4) Run both (default)
python -m commuter_service
```

Flags:

- `--socketio-url http://host:port` override Socket.IO URL
- `--strapi-url http://host:port` override Strapi base URL
- `--debug` verbose logging

## How spawning works

- PoissonGeoJSONSpawner loads zones via `StrapiApiClient` or from `SimpleSpatialZoneCache` (filtered within ±5km of routes/depots for performance)
- `SpawningCoordinator` triggers generation every N seconds (default 30s)
- Spawn requests include snapped-on-route spawn points and on-route destinations to ensure feasible trips
- Depot spawns are attached to the nearest depot connected to the route

## Configuration knobs

- Spawn interval (seconds):
  - Depot: `commuter_service.spawning.depot_spawn_interval_seconds`
  - Route: `commuter_service.spawning.route_spawn_interval_seconds`
  - Fetched from `arknet_transit_simulator.services.config_service` when available, else default 30s
- Activity multipliers from Strapi:
  - `route.activity_level` (0.5–2.0)
  - `depot.activity_level` (0.5–2.0)
- Temporal patterns differ for depot vs route to reflect real-world flow

## Operational expectations (SLOs)

- At evening peak, expect 90–180 passengers/hour total (tunable via multipliers)
- Engine stability: background loop runs continuously; expiration every 10s; default 30 min TTL
- Socket.IO events for spawned/picked-up/expired

## Troubleshooting

- No spawns: ensure routes have geometry points; check depots are within 5km of a route; review logs for “connected to route” checks
- Strapi errors inserting passengers: verify `active-passengers` routes; inspect console for HTTP status and endpoint URL
- Low spawn rates: increase route/depot `activity_level` and/or reduce spawn interval
- High CPU: reduce spatial buffer (default 5km) in `SimpleSpatialZoneCache`

## Testing

- Unit and integration tests under `commuter_service/tests`
- Golden tests can be added to verify spawn counts by time-of-day and zone types

## Next steps (optional)

- Integrate reverse geocoding labels from new Strapi geospatial endpoints
- Add batch geofencing checks for faster vehicle matching
