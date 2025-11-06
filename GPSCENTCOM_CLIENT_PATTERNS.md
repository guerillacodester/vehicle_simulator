# GPSCentCom Client Connection Patterns
## How to Connect and Receive Live Telemetry

**Date:** November 6, 2025  
**Scope:** Understanding GPSCentCom server architecture for Phase 1A GUI integration

---

## 1. Executive Summary: The Telemetry Flow

```
┌─────────────────────┐
│ Vehicle Simulator   │
│  (GPS Device)       │
│  (Port 5001)        │
└──────────┬──────────┘
           │
           │ WebSocket: /device
           │ Sends: { deviceId, lat, lon, speed, route, ... }
           │
           ▼
┌──────────────────────────────┐
│   GPSCentCom Server          │
│   (Port 5000)                │
├──────────────────────────────┤
│                              │
│  WebSocket Endpoint:         │
│  POST /device                │
│  • Accepts device telemetry  │
│  • Stores in memory (Store)  │
│  • Maintains 120s TTL        │
│                              │
│  REST API Endpoints:         │
│  GET /api/devices            │
│  GET /api/device/{id}        │
│  GET /api/route/{code}       │
│  GET /api/analytics          │
│                              │
└──────────────────────────────┘
           ▲
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────────┐ ┌────────────┐
│Next.js GUI │ │Other Clients│
│(HTTP REST) │ │(HTTP/WS)    │
│Port 3000   │ └────────────┘
└────────────┘
```

---

## 2. GPSCentCom Architecture: Three Connection Types

### **Type A: Device Input (WebSocket) ← Vehicle Simulator**

**Endpoint:** `ws://localhost:5000/device`

**Participants:** GPS devices (or simulators pretending to be GPS devices)

**Flow:**

```
1. Vehicle Simulator connects via WebSocket to /device endpoint
2. Sends telemetry packet: { deviceId: "ZR102", lat: 13.1, lon: -59.6, speed: 45, route: "Route1" }
3. GPSCentCom receives and stores in memory (Store)
4. Data is immediately available to all REST clients
5. Data expires after 120 seconds (stale_after parameter)
```

**Server Code (rx_handler.py):**

```python
@device_router.websocket("/device")
async def device_endpoint(websocket: WebSocket):
    """WebSocket endpoint for GPS devices"""
    await websocket.accept()
    
    try:
        while True:
            message = await websocket.receive()
            
            # Handle text telemetry
            if message["type"] == "websocket.receive" and "text" in message:
                data = json.loads(message["text"])
                await manager.handle_message(websocket, data)
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
```

**Key Points:**

- ✅ One-way: Device sends data to server
- ✅ Asynchronous: Fire and forget
- ✅ No authentication required (yet)
- ✅ Handles both text (JSON) and binary telemetry

---

### **Type B: Data Query (HTTP REST) ← Next.js Dashboard**

**Endpoints:**

| Endpoint | Method | Returns | Use Case |
|----------|--------|---------|----------|
| `/api/devices` | GET | `Vehicle[]` | Fetch all active vehicles (fleet view) |
| `/api/device/{id}` | GET | `Vehicle` | Fetch single vehicle detail |
| `/api/route/{code}` | GET | `Vehicle[]` | Fetch all vehicles on specific route |
| `/api/analytics` | GET | Aggregates | Get route-level statistics |
| `/health` | GET | Status | Check if server is alive |

**Example Request/Response:**

```bash
# Request
curl http://localhost:5000/api/devices

# Response
[
  {
    "deviceId": "ZR102",
    "route": "Route1",
    "vehicleReg": "ABC-123",
    "lat": 13.1234,
    "lon": -59.5678,
    "speed": 45.5,
    "heading": 270,
    "driverId": "DRV001",
    "driverName": "John Doe",
    "timestamp": "2025-11-06T15:30:45Z",
    "lastSeen": "2025-11-06T15:30:45Z"
  },
  ...
]
```

**Server Code (api_router.py):**

```python
@api_router.get("/devices")
async def get_devices(request: Request):
    """Fetch all active devices from Store"""
    try:
        states = await request.app.state.store.list_states()
        return [s.model_dump() for s in states]
    except Exception:
        return ErrorRegistry.format(ErrorRegistry.UNKNOWN_ERROR)

@api_router.get("/device/{device_id}")
async def get_device(device_id: str, request: Request):
    """Fetch specific device from Store"""
    state = await request.app.state.store.get_state(device_id)
    if not state:
        return ErrorRegistry.format(ErrorRegistry.DEVICE_NOT_FOUND)
    return state.model_dump()
```

**Key Points:**

- ✅ Synchronous HTTP: Client polls for current state
- ✅ No WebSocket needed for this pattern
- ✅ Stateless: Each request is independent
- ✅ Scaling: Multiple clients can query simultaneously

---

### **Type C: Real-Time Broadcast (WebSocket) ← Future Enhancement**

**Not Currently Implemented** but architecturally possible:

```python
# Pseudo-code: Broadcasting telemetry to all connected clients
class DeviceConnectionManager:
    def __init__(self):
        self.active_connections = []  # List of client WebSockets
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            await connection.send_json(message)
```

**Use Case:** Real-time vehicle tracking on map (future Phase 1C)

---

## 3. Data Storage: In-Memory Store

### **How GPSCentCom Stores Telemetry**

```python
class Store:
    def __init__(self, stale_after: int = 120):
        self._states = {}        # { deviceId: DeviceState, ... }
        self.stale_after = 120   # seconds
    
    async def set_state(self, state: DeviceState):
        """Called when device sends new telemetry"""
        self._states[state.deviceId] = state
    
    async def get_state(self, device_id: str) -> DeviceState:
        """Fetch latest known state for device"""
        return self._states.get(device_id)
    
    async def list_states(self) -> List[DeviceState]:
        """Fetch all known devices"""
        return list(self._states.values())
    
    async def prune_stale(self):
        """Called every 30 seconds to remove old data"""
        cutoff = time.time() - self.stale_after
        to_delete = [
            did for did, state in self._states.items()
            if state.lastSeen < cutoff  # Older than 120 seconds
        ]
        for did in to_delete:
            self._states.pop(did, None)
```

**Key Characteristics:**

- ✅ **In-Memory Only:** Resets on server restart (for testing/dev)
- ✅ **Latest-Known:** Stores only the most recent update per vehicle
- ✅ **TTL-Based:** Automatically removes stale entries (120 sec default)
- ✅ **Thread-Safe:** Uses asyncio locks for concurrent access

---

## 4. Vehicle Simulator Integration: How It Sends Telemetry

### **The Vehicle Simulator acts as a "GPS Device Client"**

**What it does:**

1. Connects via WebSocket to `ws://localhost:5000/device`
2. Periodically sends telemetry: `{ deviceId, lat, lon, speed, route, ... }`
3. GPSCentCom receives and stores immediately
4. Dashboard polls `/api/devices` to get current positions

### **Example Telemetry Packet**

```json
{
  "deviceId": "ZR102",
  "route": "Route1",
  "vehicleReg": "ZR-102",
  "lat": 13.193947,
  "lon": -59.543247,
  "speed": 35.2,
  "heading": 180,
  "driverId": "DRV_001",
  "driverName": { "first": "John", "last": "Doe" },
  "timestamp": "2025-11-06T15:30:45.123Z",
  "lastSeen": "2025-11-06T15:30:45.123Z"
}
```

**Sending Pattern (Simulator Code):**

```python
# Pseudo: How Vehicle Simulator sends data
import asyncio
import websockets
import json

async def send_telemetry():
    uri = "ws://localhost:5000/device"
    async with websockets.connect(uri) as websocket:
        while True:
            # Get current vehicle state
            position = simulator.get_position()
            
            # Format as telemetry packet
            packet = {
                "deviceId": "ZR102",
                "route": "Route1",
                "lat": position.latitude,
                "lon": position.longitude,
                "speed": position.speed,
                ...
            }
            
            # Send to GPSCentCom
            await websocket.send(json.dumps(packet))
            
            # Wait before next update
            await asyncio.sleep(1)  # Send every 1 second
```

---

## 5. Next.js Dashboard: How It Receives Telemetry

### **Two Strategies for Phase 1A**

#### **Strategy A: Polling (Current osm-viewer Pattern) ✅ RECOMMENDED for MVP**

```typescript
// src/services/gpsService.ts
export async function fetchVehicles(apiUrl: string): Promise<Vehicle[]> {
  const res = await fetch(`${apiUrl}/api/devices`, { cache: "no-store" });
  if (!res.ok) throw new Error(`fetchVehicles: ${res.status}`);
  return res.json();
}

// src/components/providers/GpsDataProvider.tsx
export function GpsDataProvider({ children, apiUrl, intervalMs = 500 }: Props) {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  
  useEffect(() => {
    const load = async () => {
      const data = await fetchVehicles(apiUrl);
      setVehicles(data);  // UI updates
    };
    
    load();  // Immediate first load
    const interval = setInterval(load, intervalMs);  // 500ms polling
    
    return () => clearInterval(interval);
  }, [intervalMs, apiUrl]);
  
  return <GpsDataContext.Provider value={{ vehicles }}>{children}</GpsDataContext.Provider>;
}
```

**Characteristics:**

- ✅ Simple HTTP polling
- ✅ No WebSocket complexity
- ✅ Works with existing REST endpoints
- ✅ Configurable frequency (500ms default = ~2 updates/sec per vehicle)
- ⚠️ Network overhead if polling too frequently

---

#### **Strategy B: WebSocket Streaming (Phase 1C) 🚀 Future**

```typescript
// Pseudo: Real-time streaming from GPSCentCom
import { io } from "socket.io-client";

const socket = io("http://localhost:5000");

socket.on("vehicle:update", (vehicle: Vehicle) => {
  setVehicles((prev) => {
    const idx = prev.findIndex((v) => v.deviceId === vehicle.deviceId);
    if (idx >= 0) prev[idx] = vehicle;
    else prev.push(vehicle);
    return [...prev];
  });
});
```

**Characteristics:**

- ✅ True real-time (sub-100ms latency)
- ✅ Efficient (only sends deltas)
- ✅ Requires GPSCentCom to implement broadcast
- ⚠️ More complex server-side code

---

## 6. Complete Data Flow Diagram

```
╔════════════════════════════════════════════════════════════════════════════╗
║                      COMPLETE TELEMETRY FLOW                              ║
╚════════════════════════════════════════════════════════════════════════════╝

1. TELEMETRY INGESTION (Vehicle Simulator → GPSCentCom)
   ┌──────────────────────┐
   │ Vehicle Simulator    │
   │ Position: 13.19, -59.54
   │ Speed: 35 km/h       │
   └──────────┬───────────┘
              │
              │ WebSocket /device
              │ Sends: { deviceId: "ZR102", lat: 13.19, lon: -59.54, speed: 35 }
              │
              ▼
   ┌──────────────────────────────────────────┐
   │ GPSCentCom Server (5000)                 │
   ├──────────────────────────────────────────┤
   │ rx_handler.py (/device endpoint)         │
   │   ├─ Accepts WebSocket connection        │
   │   ├─ Parses telemetry JSON               │
   │   └─ Calls connection_manager.handle()   │
   │                                          │
   │ connection_manager.py                    │
   │   ├─ Validates packet structure          │
   │   ├─ Creates DeviceState object          │
   │   └─ Calls store.set_state()             │
   │                                          │
   │ store.py                                 │
   │   ├─ Stores in memory: _states["ZR102"]  │
   │   ├─ Updates lastSeen timestamp          │
   │   └─ Automatically expires after 120s    │
   └──────────────────────────────────────────┘

2. DATA QUERY (Next.js Dashboard → GPSCentCom)
   ┌──────────────────────┐
   │ Next.js Dashboard    │
   │ Port 3000            │
   └──────────┬───────────┘
              │
              │ HTTP GET /api/devices
              │ Every 500ms (polling interval)
              │
              ▼
   ┌──────────────────────────────────────────┐
   │ GPSCentCom Server (5000)                 │
   ├──────────────────────────────────────────┤
   │ api_router.py (/api/devices)             │
   │   ├─ Calls store.list_states()           │
   │   └─ Returns Vehicle[] JSON              │
   └──────────────────────────────────────────┘
              │
              │ HTTP 200 OK
              │ Returns: [
              │   { deviceId: "ZR102", lat: 13.19, lon: -59.54, speed: 35, ... },
              │   { deviceId: "ZR103", lat: 13.20, lon: -59.55, speed: 42, ... }
              │ ]
              │
              ▼
   ┌──────────────────────┐
   │ GpsDataProvider Hook │
   │ (React Context)      │
   ├──────────────────────┤
   │ setVehicles(data)    │
   │ Component re-renders │
   └──────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │ Vehicle Map/Table    │
   │ Displays current     │
   │ positions on screen  │
   └──────────────────────┘

3. DATA EXPIRATION (Background Cleanup)
   Every 30 seconds:
   ┌──────────────────────────────────────────┐
   │ store.prune_stale()                      │
   ├──────────────────────────────────────────┤
   │ For each vehicle in _states:             │
   │   if now - lastSeen > 120 seconds:       │
   │     remove from memory                   │
   └──────────────────────────────────────────┘
   
   Result: Devices offline >2 minutes disappear from dashboard
```

---

## 7. Key Insights for Phase 1A Implementation

### **Connection Types Summary**

| Connection | Protocol | Direction | Purpose | Current |
|-----------|----------|-----------|---------|---------|
| Device Input | WebSocket | Vehicle → GPSCentCom | Send telemetry | ✅ Implemented |
| Data Query | HTTP REST | Dashboard → GPSCentCom | Fetch positions | ✅ Implemented |
| Broadcasting | WebSocket | GPSCentCom → Clients | Real-time stream | ❌ TODO (Phase 1C) |

### **For Next.js Dashboard to Work**

✅ **Already Available:**
- Vehicle Simulator connects via WebSocket and sends telemetry
- GPSCentCom stores data in memory (120s TTL)
- REST API endpoints return vehicle arrays
- CORS is configurable

✅ **What Next.js Dashboard Needs:**
1. `useGpsData()` hook (polling from `/api/devices` every 500ms)
2. Display component showing vehicle positions
3. Status cards showing fleet metrics
4. Service control integration (separate)

✅ **What We Need to Build:**
1. Service control endpoints (POST `/api/services/{name}/start|stop`)
2. Service status endpoint (GET `/api/services/status`)
3. Proxy or gateway in Host Server (Port 7000) to forward to GPSCentCom

---

## 8. Recommended Next Step: Create Service Control Layer

For **Phase 1A MVP**, we need to add to **Host Server** (Port 7000):

```python
# In launcher/api_router.py (or new service_control_router.py)

@app.get("/api/services/status")
async def get_services_status():
    """Return status of all services"""
    return {
        "gpscentcom": {
            "name": "GPSCentCom",
            "port": 5000,
            "status": "running",  # or "stopped"
            "uptime_seconds": 3600,
            "health_url": "http://localhost:5000/health"
        },
        "simulator": {
            "name": "Vehicle Simulator",
            "port": 5001,
            "status": "running",
            "uptime_seconds": 1800,
            "health_url": "http://localhost:5001/health"
        },
        ...
    }

@app.post("/api/services/{service_name}/start")
async def start_service(service_name: str):
    """Start a service"""
    # Delegate to launch.py manager.start_service()
    return {"status": "starting", "service": service_name}

@app.post("/api/services/{service_name}/stop")
async def stop_service(service_name: str):
    """Stop a service"""
    # Delegate to launch.py manager.stop_service()
    return {"status": "stopped", "service": service_name}
```

Then Next.js Dashboard can:

```typescript
// Fetch fleet positions
const vehicles = await fetch("http://localhost:7000/api/vehicles").then(r => r.json());

// Fetch service status
const services = await fetch("http://localhost:7000/api/services/status").then(r => r.json());

// Control services
await fetch("http://localhost:7000/api/services/gpscentcom/start", { method: "POST" });
```

---

## 9. Answer to Your Question

**Q: Do you understand how clients can connect to gpscentcom server to receive telemetry sent via gps_device in the simulator?**

**A: Yes, completely. Here's the architecture:**

1. **Vehicle Simulator** (acting as GPS device) connects via **WebSocket** to GPSCentCom's `/device` endpoint
2. Sends telemetry packets every ~1 second: `{ deviceId, lat, lon, speed, route, ... }`
3. **GPSCentCom Server** receives, validates, and stores in memory (120s TTL)
4. **Next.js Dashboard** (or any client) queries via **HTTP REST** to `/api/devices` endpoint
5. Gets current vehicle positions: `Vehicle[]` array
6. Dashboard polls every 500ms, re-renders when data changes
7. Background janitor removes stale entries every 30s

**The telemetry flow is unidirectional:**
- ✅ Simulator → GPSCentCom (WebSocket input)
- ✅ Dashboard ← GPSCentCom (HTTP REST queries)
- Future: GPSCentCom → Dashboards (WebSocket broadcast, Phase 1C)

This pattern is already working in osm-viewer and ready for Phase 1A GUI implementation.

