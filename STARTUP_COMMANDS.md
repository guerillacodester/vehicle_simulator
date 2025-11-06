# ArkNet Services Manual Startup Commands

Run each command in a separate terminal window.

## Service Startup Commands

### 1. Vehicle Simulator (Depot Mode)

```bash
python -m arknet_transit_simulator --mode depot
```

**Purpose:** Vehicle transit simulator with boarding conductor  
**Port:** 5001 (Fleet API)  
**Features:** Engine control, boarding management, GPS telemetry

### 2. Geospatial Service

```bash
python -m geospatial_service
```

**Purpose:** PostGIS spatial queries, reverse geocoding, building proximity searches  
**Port:** 6000  
**Features:** Route geometry, depot catchments, building queries

### 3. GPS CentCom Server

```bash
python -m gpscentcom_server
```

**Purpose:** GPS device telemetry collection and WebSocket streaming  
**Port:** 5000  
**Features:** Real-time device tracking, location updates, analytics

### 4. Commuter Service

```bash
python -m commuter_service
```

**Purpose:** Passenger spawning, manifest API, conductor management  
**Port:** 4000  
**Features:** Passenger lifecycle, boarding orchestration, route management

---

## Recommended Startup Sequence

Use separate terminal windows for each service, start in this order:

**Terminal 1: Geospatial Service**
```bash
python -m geospatial_service
```

**Terminal 2: GPS CentCom Server**
```bash
python -m gpscentcom_server
```

**Terminal 3: Commuter Service**
```bash
python -m commuter_service
```

**Terminal 4: Vehicle Simulator (Depot Mode)**
```bash
python -m arknet_transit_simulator --mode depot
```

**Terminal 5: Fleet Console**
```bash
python -m clients.fleet --url http://localhost:5001
```

---

## Alternative: Automated Startup via Host Server

### Option A: Start Host Server and all services automatically

**Terminal 1: Start Host Server**
```bash
python scripts/start_all.py
```

**Terminal 2: Connect Fleet Console**
```bash
python -m clients.fleet --url http://localhost:6000
```

Then in Fleet Console:
```
fleet> start-service all
```

---

## Quick Reference Table

| Service | Command | Port | Purpose |
|---------|---------|------|---------|
| Vehicle Simulator | `python -m arknet_transit_simulator --mode depot` | 5001 | Simulation engine |
| Geospatial | `python -m geospatial_service` | 6000 | Spatial queries |
| GPS CentCom | `python -m gpscentcom_server` | 5000 | GPS telemetry |
| Commuter | `python -m commuter_service` | 4000 | Passenger management |
| Host Server | `python -m services.host_server --port 6000` | 6000 | Service orchestration |

---

## Fleet Console Commands

Once connected to the host server via Fleet Console:

```
# Check service status
fleet> services

# Start individual service
fleet> start-service simulator

# Start all services
fleet> start-service all

# Stop all services
fleet> stop-service all

# View vehicles
fleet> vehicles

# View live events
fleet> stream
```
