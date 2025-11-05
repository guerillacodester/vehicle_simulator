# Fleet Management API Reference

## Overview
The ArkNet Fleet Management API provides real-time observability and control over the transit simulator. It's embedded within the simulator process for zero-latency access to internal state.

**Base URL:** `http://localhost:5001` (configurable with `--api-port`)

**API Docs:** `http://localhost:5001/docs` (Swagger UI)

## Architecture
- **FastAPI** - Modern async web framework
- **Embedded Server** - Runs within simulator process (zero-latency)
- **Dependency Injection** - Direct memory access to simulator state
- **EventBus** - Real-time WebSocket event streaming
- **CORS Enabled** - Ready for web clients (future GUI)

## Starting the Simulator with API

```powershell
# Default (API enabled on port 5001)
python -m arknet_transit_simulator --mode depot

# Custom port
python -m arknet_transit_simulator --mode depot --api-port 8080

# Disable API
python -m arknet_transit_simulator --mode depot --no-api
```

## Endpoints

### Health & Status

#### `GET /health`
Check simulator and API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-20T10:30:00Z",
  "simulator_running": true,
  "active_vehicles": 3,
  "event_bus_stats": {
    "subscribers": 2,
    "total_events_emitted": 150
  }
}
```

---

### Vehicle State

#### `GET /api/vehicles`
List all vehicles with current state.

**Response:**
```json
{
  "vehicles": [
    {
      "vehicle_id": "ZR102",
      "driver_name": "Jane Doe",
      "route_id": 1,
      "current_position": {
        "latitude": 13.326607,
        "longitude": -59.615521
      },
      "driver_state": "DRIVING",
      "engine_running": true,
      "gps_running": true,
      "passenger_count": 0,
      "capacity": 45,
      "boarding_active": false
    }
  ],
  "count": 1
}
```

#### `GET /api/vehicles/{vehicle_id}`
Get detailed state for a specific vehicle.

**Example:** `GET /api/vehicles/ZR102`

**Response:**
```json
{
  "vehicle_id": "ZR102",
  "driver_name": "Jane Doe",
  "route_id": 1,
  "current_position": {
    "latitude": 13.326607,
    "longitude": -59.615521
  },
  "driver_state": "DRIVING",
  "engine_running": true,
  "gps_running": true,
  "passenger_count": 0,
  "capacity": 45,
  "boarding_active": false
}
```

---

### Conductor State

#### `GET /api/conductors`
List all conductors with current state.

**Response:**
```json
{
  "conductors": [
    {
      "conductor_id": "conductor_ZR102",
      "vehicle_id": "ZR102",
      "conductor_name": "Alex Johnson",
      "conductor_state": "ONBOARD",
      "passengers_on_board": 0,
      "capacity": 45,
      "boarding_active": false,
      "depot_boarding_active": false
    }
  ],
  "count": 1
}
```

#### `GET /api/conductors/{vehicle_id}`
Get detailed conductor state for a specific vehicle.

**Example:** `GET /api/conductors/ZR102`

**Response:**
```json
{
  "conductor_id": "conductor_ZR102",
  "vehicle_id": "ZR102",
  "conductor_name": "Alex Johnson",
  "conductor_state": "ONBOARD",
  "passengers_on_board": 0,
  "capacity": 45,
  "boarding_active": false,
  "depot_boarding_active": false
}
```

---

### Vehicle Control

#### `POST /api/vehicles/{vehicle_id}/start-engine`
Start the engine for a specific vehicle.

**Example:** `POST /api/vehicles/ZR102/start-engine`

**Response:**
```json
{
  "success": true,
  "message": "Engine started for vehicle ZR102",
  "data": {
    "result": true
  }
}
```

#### `POST /api/vehicles/{vehicle_id}/stop-engine`
Stop the engine for a specific vehicle.

**Example:** `POST /api/vehicles/ZR102/stop-engine`

**Response:**
```json
{
  "success": true,
  "message": "Engine stopped for vehicle ZR102",
  "data": {
    "result": true
  }
}
```

---

### Boarding Control

#### `POST /api/vehicles/{vehicle_id}/enable-boarding`
Enable passenger boarding for a specific vehicle.

**Example:** `POST /api/vehicles/ZR102/enable-boarding`

**Response:**
```json
{
  "success": true,
  "message": "Boarding enabled for vehicle ZR102"
}
```

#### `POST /api/vehicles/{vehicle_id}/disable-boarding`
Disable passenger boarding for a specific vehicle.

**Example:** `POST /api/vehicles/ZR102/disable-boarding`

**Response:**
```json
{
  "success": true,
  "message": "Boarding disabled for vehicle ZR102"
}
```

#### `POST /api/vehicles/{vehicle_id}/trigger-boarding`
Manually trigger passenger boarding check at current position.

**Example:** `POST /api/vehicles/ZR102/trigger-boarding`

**Response:**
```json
{
  "success": true,
  "message": "Boarding check completed for vehicle ZR102",
  "data": {
    "passengers_boarded": 3
  }
}
```

---

### Real-Time Events (WebSocket)

#### `WS /ws/events`
Stream real-time events from all vehicles.

**Connection:** `ws://localhost:5001/ws/events`

**Event Format:**
```json
{
  "event_type": "engine_started",
  "vehicle_id": "ZR102",
  "timestamp": "2025-01-20T10:30:15Z",
  "data": {
    "driver_name": "Jane Doe",
    "route_id": 1
  }
}
```

**Event Types:**
- `engine_started` - Vehicle engine started
- `engine_stopped` - Vehicle engine stopped
- `position_update` - GPS position updated
- `passenger_boarded` - Passenger boarded vehicle
- `passenger_alighted` - Passenger left vehicle
- `boarding_enabled` - Boarding system activated
- `boarding_disabled` - Boarding system deactivated

#### `GET /ws/status`
Get WebSocket connection statistics.

**Response:**
```json
{
  "active_connections": 2,
  "endpoints": ["/ws/events"]
}
```

---

## Error Responses

All endpoints return standard error responses:

### 404 Not Found
```json
{
  "detail": "Vehicle ZR999 not found"
}
```

### 500 Internal Error
```json
{
  "success": false,
  "message": "Failed to start engine: Engine malfunction"
}
```

---

## Usage Examples

### PowerShell (Invoke-RestMethod)

```powershell
# Get all vehicles
$vehicles = Invoke-RestMethod -Uri "http://localhost:5001/api/vehicles"
$vehicles.vehicles | Format-Table

# Start engine
Invoke-RestMethod -Method POST -Uri "http://localhost:5001/api/vehicles/ZR102/start-engine"

# Enable boarding
Invoke-RestMethod -Method POST -Uri "http://localhost:5001/api/vehicles/ZR102/enable-boarding"

# Trigger boarding
$result = Invoke-RestMethod -Method POST -Uri "http://localhost:5001/api/vehicles/ZR102/trigger-boarding"
Write-Host "Boarded: $($result.data.passengers_boarded) passengers"
```

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:5001"

# Get all vehicles
response = requests.get(f"{BASE_URL}/api/vehicles")
vehicles = response.json()["vehicles"]

for vehicle in vehicles:
    print(f"{vehicle['vehicle_id']}: {vehicle['passenger_count']}/{vehicle['capacity']}")

# Start engine
response = requests.post(f"{BASE_URL}/api/vehicles/ZR102/start-engine")
print(response.json()["message"])

# WebSocket streaming
import websockets
import asyncio

async def stream_events():
    async with websockets.connect(f"ws://localhost:5001/ws/events") as ws:
        while True:
            event = await ws.recv()
            print(event)

asyncio.run(stream_events())
```

### curl

```bash
# Health check
curl http://localhost:5001/health

# Get vehicles
curl http://localhost:5001/api/vehicles

# Start engine
curl -X POST http://localhost:5001/api/vehicles/ZR102/start-engine

# Enable boarding
curl -X POST http://localhost:5001/api/vehicles/ZR102/enable-boarding

# Trigger boarding
curl -X POST http://localhost:5001/api/vehicles/ZR102/trigger-boarding
```

---

## Next Steps

### Remote Fleet Console (CLI)
A dedicated CLI client will be created in `clients/fleet/` to provide an interactive console for fleet management:

```powershell
# Future CLI (not yet implemented)
python -m clients.fleet status                    # Show all vehicles
python -m clients.fleet start ZR102               # Start engine
python -m clients.fleet enable-boarding ZR102     # Enable boarding
python -m clients.fleet trigger-boarding ZR102    # Manual boarding check
python -m clients.fleet stream                    # Live event stream
```

### Web GUI (Next.js)
The same API will power a future web-based GUI for visual fleet monitoring and control.

---

## Architecture Notes

### Why Embedded API?
- **Zero Latency** - Direct memory access to simulator objects
- **No Serialization** - Access internal state without marshalling
- **Simpler Deployment** - Single process, no service coordination
- **Proven Pattern** - Same architecture as `clients/commuter/` service

### Port Assignment
- **5001** - Fleet Management API (default, configurable)
- **5000** - GPS CentCom Server
- **4000** - Commuter Service API
- **1337** - Strapi CMS API

### Future Enhancements
- [ ] Authentication & authorization
- [ ] Rate limiting
- [ ] Request logging & metrics
- [ ] OpenAPI spec export
- [ ] Event replay & history
- [ ] Batch operations
- [ ] Scheduled commands
