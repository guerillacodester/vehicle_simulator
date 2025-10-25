# ArkNet Vehicle Simulator - Project Context

**Project**: ArkNet Fleet Manager & Vehicle Simulator  
**Repository**: vehicle_simulator  
**Branch**: branch-0.0.2.6  
**Date**: October 25, 2025  
**Status**: 🟡 Active Development - GeoJSON Import System

> **📌 Companion Document**: See `TODO.md` for step-by-step implementation tasks

---

## 🎯 **PROJECT MISSION**

Building a **GeoJSON import system** integrated with:
- **Strapi CMS v5** (PostgreSQL + PostGIS backend)
- **Redis** for fast reverse geocoding (lat/lon → address)
- **Real-time geofencing** via Socket.IO
- **Poisson/temporal passenger spawning** for realistic commuter simulation

**Goal**: Enable importing OpenStreetMap GeoJSON data (roads, POIs, landuse zones) to power intelligent passenger spawning in a vehicle transit simulator for Barbados.

---

## 📁 **PROJECT STRUCTURE**

```
vehicle_simulator/
├── arknet_fleet_manager/
│   └── arknet-fleet-api/              # Strapi CMS v5 backend
│       ├── src/
│       │   ├── api/
│       │   │   ├── country/           # Country content-type
│       │   │   ├── highway/           # Road network
│       │   │   ├── poi/               # Points of Interest
│       │   │   ├── landuse-zone/      # Land use zones
│       │   │   └── geofence/          # Geofencing controller
│       │   ├── plugins/
│       │   │   └── strapi-plugin-action-buttons/  # ✅ CUSTOM ARKNET PLUGIN
│       │   ├── services/              # Business logic
│       │   └── utils/                 # Utilities
│       ├── admin-extensions/          # Custom admin UI code
│       ├── scripts/                   # Test/utility scripts
│       └── package.json
│
├── arknet_transit_simulator/          # Vehicle simulator (Python)
│   ├── vehicle/
│   │   ├── gps_device.py             # GPS position tracking
│   │   └── socketio_client.py        # Real-time communication
│   ├── config/
│   └── main.py
│
├── commuter_service/                  # Passenger spawning (Python)
│   ├── depot_reservoir.py            # Depot-based spawning (FIFO queue)
│   ├── route_reservoir.py            # Route-based spawning (spatial grid)
│   ├── poisson_geojson_spawner.py    # Statistical spawning engine
│   ├── simple_spatial_cache.py       # Async zone loader (~5km buffer)
│   ├── spawning_coordinator.py       # Orchestrator
│   └── strapi_api_client.py          # API integration
│
├── sample_data/                       # 📂 GeoJSON FILES (OpenStreetMap export)
│   ├── highway.geojson               # 22,719 roads (43MB)
│   ├── amenity.geojson               # 1,427 POIs (3.8MB)
│   ├── landuse.geojson               # 2,267 zones (4.3MB)
│   ├── building.geojson              # ⚠️ 658MB (streaming required)
│   ├── admin_level_6_polygon.geojson # Parishes
│   ├── admin_level_8_polygon.geojson # Districts
│   ├── admin_level_9_polygon.geojson # Sub-districts
│   ├── admin_level_10_polygon.geojson # Localities
│   ├── natural.geojson               # Natural features
│   ├── name.geojson                  # Named locations
│   └── add_street_polygon.geojson    # Street polygons
│
├── CONTEXT.md                         # ← THIS FILE
├── TODO.md                            # Step-by-step implementation plan
├── PROJECT_STATUS.md                  # Historical project updates
└── ARCHITECTURE_DEFINITIVE.md         # System architecture
```

---

## 🔄 **SYSTEM INTEGRATION & WORKFLOW**

### **How All Subsystems Work Together**

This section explains the **end-to-end flow** from GeoJSON import to passenger pickup.

---

#### **1. Data Import Flow** (Strapi → PostgreSQL → Redis)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. ADMIN TRIGGERS IMPORT                                         │
│    User clicks [Import Highways] in Strapi admin                │
│    ↓                                                             │
│    window.importGeoJSON(countryId, {fileType: 'highway'})       │
│    ↓                                                             │
│    POST /api/geojson-import                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. IMPORT SERVICE PROCESSES DATA                                │
│    - Stream parse: sample_data/highway.geojson                  │
│    - Transform: LineString → midpoint coords                    │
│    - Batch insert: 100 records → PostgreSQL highway table       │
│    - Index: GEOADD highways:barbados → Redis                    │
│    - Progress: Emit Socket.IO events every 100 features         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. DATA AVAILABLE FOR QUERIES                                   │
│    PostgreSQL: Full data (geometry, properties)                 │
│    Redis: Fast geospatial lookups (lat/lon → nearby features)   │
└─────────────────────────────────────────────────────────────────┘
```

**After Import Complete**:
- **PostgreSQL** contains: All highway/POI/landuse records with full geometry
- **Redis** contains: Geospatial indexes for fast proximity queries (<200ms)
- **Strapi Admin** shows: Import status (completed, 22,719 highways imported)

---

#### **2. Passenger Spawning Flow** (Commuter Service → Strapi → Socket.IO)

```
┌─────────────────────────────────────────────────────────────────┐
│ SPAWNING COORDINATOR (commuter_service/spawning_coordinator.py) │
│                                                                  │
│  Every 1 minute:                                                │
│  ├─ Depot Spawner: Check depot queues                           │
│  └─ Route Spawner: Check route segments                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────────────────┐
             │                                                     │
             ▼                                                     ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ DEPOT SPAWNER            │              │ ROUTE SPAWNER            │
│ (depot_reservoir.py)     │              │ (route_reservoir.py)     │
│                          │              │                          │
│ 1. Load depot POIs       │              │ 1. Load active routes    │
│    from Strapi API       │              │    from Strapi API       │
│                          │              │                          │
│ 2. Calculate spawn rate: │              │ 2. Calculate spawn rate: │
│    base × 1.0x (depot)   │              │    base × 0.5x (route)   │
│    × temporal multiplier │              │    × temporal multiplier │
│                          │              │    × zone modifier       │
│ 3. Select depot nearby   │              │                          │
│    passenger origin      │              │ 3. Select route segment  │
│                          │              │    via spatial grid      │
│ 4. FIFO queue logic      │              │                          │
└────────────┬─────────────┘              └────────────┬─────────────┘
             │                                         │
             └──────────────┬──────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ POISSON GEOJSON SPAWNER (poisson_geojson_spawner.py)            │
│                                                                  │
│ For each spawn candidate:                                       │
│  1. Get nearby POIs from SimpleSpatialZoneCache                 │
│  2. Select POI based on activity_level (mall: 0.34, etc.)       │
│  3. Apply temporal multiplier (morning: 3.0x, evening: 2.5x)    │
│  4. Calculate Poisson probability                               │
│  5. Roll dice: spawn or skip                                    │
│                                                                  │
│ Spawn Rate Formula:                                             │
│   rate = (base × peak × zone × activity) / 18.0                 │
│                                                                  │
│ If spawn successful:                                            │
│  ├─ Create passenger record in database                         │
│  ├─ Assign destination (another random POI)                     │
│  └─ Emit Socket.IO: passenger:spawned                           │
└─────────────────────────────────────────────────────────────────┘
```

**SimpleSpatialZoneCache** (simple_spatial_cache.py):
- **Loads**: All landuse zones + POIs from Strapi API
- **Filters**: Only zones within ±5km of active routes
- **Refreshes**: Auto-reloads when data changes in Strapi
- **Strategy**: Async-only (no threading)

**Critical Dependencies**:
1. Depot spawner needs: `poi` table populated with depot locations
2. Route spawner needs: `landuse_zone` table with spawn_weight values
3. Poisson spawner needs: POIs with `activity_level` assigned

---

#### **3. Vehicle Movement Flow** (Vehicle Simulator → Redis → Geofencing)

```
┌─────────────────────────────────────────────────────────────────┐
│ VEHICLE SIMULATOR (arknet_transit_simulator/main.py)            │
│                                                                  │
│ For each vehicle (V123, V456, ...):                             │
│  ├─ GPS Device: Update position every 1 second                  │
│  │   ├─ Calculate new lat/lon (route following)                 │
│  │   ├─ Redis Publish: vehicle:position                         │
│  │   │   {                                                       │
│  │   │     vehicleId: "V123",                                   │
│  │   │     lat: 13.0806,                                        │
│  │   │     lon: -59.5905,                                       │
│  │   │     speed: 45,                                           │
│  │   │     heading: 90                                          │
│  │   │   }                                                       │
│  │   └─ Socket.IO Emit: vehicle:position (to admin dashboard)   │
│  │                                                               │
│  └─ Passenger Manager: Track onboard passengers                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ GEOFENCE NOTIFIER SERVICE (Strapi backend)                      │
│ (src/services/geofence-notifier.service.js)                     │
│                                                                  │
│ Redis Subscriber: vehicle:position channel                      │
│  ↓                                                               │
│  On message received:                                           │
│   1. Parse vehicle position {vehicleId, lat, lon}               │
│   2. Query Redis geospatial indexes:                            │
│      ├─ GEORADIUS highways:barbados lon lat 50 m                │
│      └─ GEORADIUS pois:barbados lon lat 100 m                   │
│   3. Compare with previous state (Redis):                       │
│      ├─ GET vehicle:V123:current_highway → highway:5172465      │
│      └─ GET vehicle:V123:current_poi → poi:123                  │
│   4. Detect transitions:                                        │
│      ├─ Entered new highway? → geofence:entered                 │
│      ├─ Exited highway? → geofence:exited                       │
│      ├─ Entered POI zone? → geofence:entered                    │
│      └─ Exited POI zone? → geofence:exited                      │
│   5. Update vehicle state:                                      │
│      ├─ SET vehicle:V123:current_highway highway:9876           │
│      └─ SET vehicle:V123:current_poi poi:456                    │
│   6. Reverse geocode (cache-first):                             │
│      ├─ GET geo:13.0806:-59.5905 → cache hit?                   │
│      └─ If miss: Format "Highway Name, near POI Name"           │
│   7. Socket.IO Emit: geofence:entered                           │
│      {                                                           │
│        vehicleId: "V123",                                       │
│        highway: {id: 9876, name: "Highway 1", type: "primary"}, │
│        poi: {id: 456, name: "Mall", type: "mall"},              │
│        address: "Highway 1, near Mall"                          │
│      }                                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ VEHICLE SIMULATOR RECEIVES NOTIFICATION                         │
│ (arknet_transit_simulator/vehicle/socketio_client.py)           │
│                                                                  │
│ @sio.on('geofence:entered')                                     │
│ def on_geofence_entered(data):                                  │
│     print(f"Entered: {data['address']}")                        │
│     # Announce to passengers                                    │
│     # Update vehicle display                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Latency Target**: <10ms (GPS update → geofence notification)

---

#### **4. Reverse Geocoding Flow** (Redis Cache → Compute → Cache)

```
┌─────────────────────────────────────────────────────────────────┐
│ REQUEST: GET /api/reverse-geocode?lat=13.0806&lon=-59.5905      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ REVERSE GEOCODE CONTROLLER                                      │
│ (src/api/reverse-geocode/controllers/reverse-geocode.js)        │
│                                                                  │
│ 1. CHECK CACHE                                                  │
│    GET geo:13.0806:-59.5905                                     │
│    ├─ Cache HIT → Return address (source: 'cache') <10ms ✅     │
│    └─ Cache MISS → Continue to compute                          │
│                                                                  │
│ 2. COMPUTE ADDRESS (if cache miss)                              │
│    ├─ GEORADIUS highways:barbados -59.5905 13.0806 50 m         │
│    │   → [{id: highway:5172465, distance: 0.0}]                 │
│    │   → HGETALL highway:5172465                                │
│    │   → {name: "Tom Adams Highway", type: "trunk"}             │
│    │                                                             │
│    ├─ GEORADIUS pois:barbados -59.5905 13.0806 100 m            │
│    │   → [{id: poi:123, distance: 45.2}]                        │
│    │   → HGETALL poi:123                                        │
│    │   → {name: "Bridgetown Mall", type: "mall"}                │
│    │                                                             │
│    └─ FORMAT ADDRESS                                            │
│        if (highway && poi):                                     │
│          address = "Tom Adams Highway, near Bridgetown Mall"    │
│        else if (highway):                                       │
│          address = "Tom Adams Highway"                          │
│        else if (poi):                                           │
│          address = "Near Bridgetown Mall"                       │
│        else:                                                    │
│          address = "Unknown location"                           │
│                                                                  │
│ 3. CACHE RESULT (TTL: 1 hour)                                   │
│    SETEX geo:13.0806:-59.5905 3600 "Tom Adams Highway, near..." │
│                                                                  │
│ 4. RETURN RESPONSE (source: 'computed') <200ms ✅                │
│    {                                                             │
│      address: "Tom Adams Highway, near Bridgetown Mall",        │
│      source: "computed",                                        │
│      highway: {...},                                            │
│      poi: {...}                                                 │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Performance**:
- Cache hit: <10ms (target) ✅
- Cache miss: <200ms (target) ✅
- vs PostgreSQL: ~2000ms (current) → 10-100x improvement

---

#### **5. Conductor Communication Flow** (Spawners → Conductor → Vehicles)

```
┌─────────────────────────────────────────────────────────────────┐
│ PASSENGER SPAWNED                                               │
│ (depot_reservoir.py OR route_reservoir.py)                      │
│                                                                  │
│ Socket.IO Emit: passenger:spawned                               │
│ {                                                                │
│   passengerId: "P12345",                                        │
│   origin: {lat: 13.0806, lon: -59.5905, name: "Bridgetown"},    │
│   destination: {lat: 13.1050, lon: -59.6100, name: "Airport"},  │
│   timestamp: 1729872000000,                                     │
│   spawner: "depot" | "route"                                    │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ CONDUCTOR SERVICE (location TBD - needs discovery)              │
│                                                                  │
│ @sio.on('passenger:spawned')                                    │
│ def on_passenger_spawned(data):                                 │
│   1. Receive passenger request                                  │
│   2. Find eligible vehicles:                                    │
│      ├─ Query vehicles near origin (±2km)                       │
│      ├─ Check vehicle capacity (seats available)                │
│      └─ Check vehicle route compatibility                       │
│   3. Select best vehicle (closest + route match)                │
│   4. Assign passenger to vehicle:                               │
│      └─ Socket.IO Emit: passenger:assigned                      │
│         {                                                        │
│           passengerId: "P12345",                                │
│           vehicleId: "V123",                                    │
│           estimatedPickupTime: 180 (seconds)                    │
│         }                                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ VEHICLE SIMULATOR RECEIVES ASSIGNMENT                           │
│ (arknet_transit_simulator/vehicle/socketio_client.py)           │
│                                                                  │
│ @sio.on('passenger:assigned')                                   │
│ def on_passenger_assigned(data):                                │
│   1. Add passenger to pickup queue                              │
│   2. Navigate to pickup location                                │
│   3. On arrival:                                                │
│      └─ Socket.IO Emit: passenger:picked_up                     │
│         {passengerId: "P12345", vehicleId: "V123"}              │
│   4. Navigate to destination                                    │
│   5. On arrival:                                                │
│      └─ Socket.IO Emit: passenger:delivered                     │
│         {passengerId: "P12345", vehicleId: "V123"}              │
└─────────────────────────────────────────────────────────────────┘
```

**⚠️ NOTE**: Conductor service location needs to be discovered in Phase 6

---

#### **6. Complete End-to-End Flow**

```
ADMIN IMPORTS DATA
    ↓
PostgreSQL + Redis populated
    ↓
SimpleSpatialZoneCache loads zones
    ↓
Spawning Coordinator starts
    ├─ Depot Spawner: Generates passenger at depot POI
    └─ Route Spawner: Generates passenger along route
         ↓
    Socket.IO: passenger:spawned
         ↓
    Conductor assigns to vehicle
         ↓
    Socket.IO: passenger:assigned
         ↓
    Vehicle navigates to pickup
         ↓
    Vehicle GPS publishes position
         ↓
    Redis Pub/Sub: vehicle:position
         ↓
    Geofence Service detects proximity
         ↓
    Socket.IO: geofence:entered ("Near Bridgetown Depot")
         ↓
    Vehicle picks up passenger
         ↓
    Socket.IO: passenger:picked_up
         ↓
    Vehicle navigates to destination
         ↓
    Geofence Service detects arrival
         ↓
    Socket.IO: geofence:entered ("Near Airport Terminal")
         ↓
    Vehicle delivers passenger
         ↓
    Socket.IO: passenger:delivered
         ↓
    CYCLE COMPLETE ✅
```

---

#### **7. Data Flow Diagram**

```
┌──────────────┐
│   STRAPI     │  ← Admin imports GeoJSON
│   CMS API    │  ← SimpleSpatialZoneCache queries zones
└──────┬───────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│PostgreSQL│  │  Redis   │  │Socket.IO │
│ (master) │  │  (fast)  │  │(real-time)
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │              │
     │             │              │
     ▼             ▼              ▼
┌─────────────────────────────────────┐
│   COMMUTER SERVICE (Python)         │
│   ├─ Depot Spawner                  │
│   ├─ Route Spawner                  │
│   ├─ Poisson Spawner                │
│   └─ SimpleSpatialZoneCache         │
└─────────────────┬───────────────────┘
                  │
                  ▼ (passenger:spawned)
┌─────────────────────────────────────┐
│   CONDUCTOR SERVICE (Python?)       │
│   └─ Passenger → Vehicle assignment │
└─────────────────┬───────────────────┘
                  │
                  ▼ (passenger:assigned)
┌─────────────────────────────────────┐
│   VEHICLE SIMULATOR (Python)        │
│   ├─ GPS Device                     │
│   ├─ Passenger Manager              │
│   └─ Socket.IO Client               │
└─────────────────┬───────────────────┘
                  │
                  ▼ (vehicle:position)
┌─────────────────────────────────────┐
│   GEOFENCE NOTIFIER (Node.js)       │
│   └─ Redis Pub/Sub subscriber       │
└─────────────────────────────────────┘
```

---

#### **8. Critical Subsystem Dependencies**

| Subsystem | Depends On | Provides To |
|-----------|------------|-------------|
| **Strapi CMS** | PostgreSQL, Redis | REST API for all services |
| **PostgreSQL** | - | Master data storage |
| **Redis** | - | Fast geospatial lookups, cache, Pub/Sub |
| **SimpleSpatialZoneCache** | Strapi API | Zones to Poisson Spawner |
| **Depot Spawner** | Strapi API (depots), SimpleSpatialZoneCache | Passenger spawn events |
| **Route Spawner** | Strapi API (routes), SimpleSpatialZoneCache | Passenger spawn events |
| **Poisson Spawner** | SimpleSpatialZoneCache (POIs) | Spawn probability calculations |
| **Conductor** | Socket.IO (passenger:spawned) | Vehicle assignments |
| **Vehicle Simulator** | Socket.IO (passenger:assigned) | GPS positions, passenger events |
| **Geofence Notifier** | Redis (vehicle:position), Redis (geospatial) | Geofence events |

---

#### **9. Socket.IO Events Reference**

**Events Emitted**:
- `passenger:spawned` - New passenger waiting
- `passenger:assigned` - Passenger assigned to vehicle
- `passenger:picked_up` - Passenger boarded vehicle
- `passenger:delivered` - Passenger reached destination
- `vehicle:position` - Vehicle GPS update
- `geofence:entered` - Vehicle entered highway/POI zone
- `geofence:exited` - Vehicle exited zone
- `import:progress` - GeoJSON import progress update

**Event Subscribers**:
- Conductor: `passenger:spawned`
- Vehicle Simulator: `passenger:assigned`, `geofence:entered`, `geofence:exited`
- Admin Dashboard: `import:progress`, `vehicle:position`, all passenger events
- Geofence Notifier: (Redis Pub/Sub `vehicle:position`, not Socket.IO)

---

#### **10. Startup Sequence**

**Correct order to start services**:

1. **PostgreSQL** (database must be running first)
2. **Redis** (cache/indexes must be available)
3. **Strapi CMS** (`npm run develop` in arknet-fleet-api/)
4. **Import GeoJSON data** (if not already done)
5. **Commuter Service** (spawning_coordinator.py)
   - Loads SimpleSpatialZoneCache from Strapi
   - Starts depot_reservoir.py
   - Starts route_reservoir.py
6. **Conductor Service** (if exists - TBD)
7. **Vehicle Simulators** (main.py for each vehicle)
   - Connects to Socket.IO
   - Starts GPS device
   - Listens for passenger assignments

**Health Check**:
```bash
# Check PostgreSQL
psql -U postgres -c "SELECT 1;"

# Check Redis
redis-cli ping

# Check Strapi
curl http://localhost:1337/api/countries

# Check spawning
# (Look for passenger:spawned events in Socket.IO logs)

# Check vehicles
# (Look for vehicle:position in Redis MONITOR)
```

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Technology Stack**

#### **Backend**
- **Strapi CMS v5**: Headless CMS with PostgreSQL + PostGIS
- **PostgreSQL 15+**: Relational database with spatial extensions
- **PostGIS**: Spatial database (geometry types, ST_* functions)
- **Redis 7.x**: In-memory data store (geospatial indexes, caching)
- **Node.js 18+**: JavaScript runtime
- **ioredis**: Redis client library

#### **Frontend/Admin**
- **Strapi Admin Panel**: React-based CMS admin UI
- **strapi-plugin-action-buttons**: Custom ArkNet plugin for UI buttons

#### **Vehicle Simulator**
- **Python 3.9+**: Vehicle simulation logic
- **Socket.IO Client**: Real-time communication
- **Redis Client**: Position publishing

#### **Commuter Service**
- **Python 3.9+**: Passenger spawning logic
- **Poisson distribution**: Statistical spawning algorithm
- **Async I/O**: Non-blocking zone loading

---

## 🔑 **KEY COMPONENTS**

### **1. Strapi Plugin: strapi-plugin-action-buttons**

**Location**: `arknet_fleet_manager/arknet-fleet-api/src/plugins/strapi-plugin-action-buttons/`

**Purpose**: Custom field type that renders clickable buttons in Strapi admin panel

**Architecture**:
```
Strapi Admin UI
│
├─ Country Content-Type Edit View
│  │
│  ├─ [Import Highways] ← Action Button
│  ├─ [Import Amenities] ← Action Button
│  ├─ [Import Landuse] ← Action Button
│  └─ ...
│
└─ Button Click
   │
   └─ window.importGeoJSON(entityId, metadata)
      │
      └─ POST /api/geojson-import
```

**Field Configuration**:
```json
{
  "type": "customField",
  "customField": "plugin::action-buttons.button-group",
  "options": {
    "buttons": [
      {
        "buttonLabel": "Import Highways",
        "onClick": "importGeoJSON",
        "metadata": { "fileType": "highway" }
      }
    ]
  }
}
```

**Window Handlers**: Global JavaScript functions triggered by button clicks
- `window.importGeoJSON(entityId, metadata)` - Start import job
- `window.viewImportStats(entityId, metadata)` - View import statistics
- `window.clearRedisCache(entityId, metadata)` - Clear Redis cache

---

### **2. Database Schemas**

#### **Country** (Main entity)
```javascript
{
  name: String,
  iso_code: String,
  geometry: JSON,  // Country boundary
  geodata_import_buttons: CustomField,  // Action buttons UI
  geodata_import_status: JSON  // Import tracking
}
```

**geodata_import_status structure**:
```json
{
  "highway": {
    "status": "not_imported" | "importing" | "completed" | "failed",
    "lastImportDate": "2025-10-25T12:00:00Z",
    "featureCount": 22719,
    "lastJobId": "uuid-1234"
  },
  "amenity": { ... },
  "landuse": { ... },
  "building": { ... },
  "admin": { ... }
}
```

#### **Highway** (Road network)
```javascript
{
  osm_id: String (unique),
  highway_type: Enum ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'unclassified'],
  name: String,
  ref: String,  // Route number (e.g., "ABC", "H4")
  oneway: Boolean,
  lanes: Integer,
  maxspeed: String,
  surface: String,
  geometry_geojson: JSON,  // Full LineString geometry
  center_latitude: Float,  // Midpoint (for indexing)
  center_longitude: Float,
  country: Relation(Country)
}
```

#### **POI** (Points of Interest)
```javascript
{
  osm_id: String (unique),
  poi_type: String,  // OSM amenity type (mall, school, hospital, etc.)
  name: String,
  latitude: Float,  // Point coordinates OR centroid of MultiPolygon
  longitude: Float,
  address: String,
  activity_level: Float,  // Spawning activity (0.0-1.0)
  metadata: JSON,  // Additional OSM properties
  country: Relation(Country)
}
```

**⚠️ CRITICAL ISSUE**: POI schema expects Point (lat/lon) but amenity.geojson contains **MultiPolygon** geometries
- **Solution**: Calculate centroid using Turf.js during import
- **Alternative**: Create separate `poi_shape` table for full polygon geometries

#### **Landuse Zone**
```javascript
{
  osm_id: String (unique),
  landuse_type: String,  // residential, commercial, industrial, farmland, etc.
  name: String,
  geometry_geojson: JSON,  // Full MultiPolygon geometry
  center_latitude: Float,  // Centroid
  center_longitude: Float,
  population_density: Float,
  spawn_weight: Float,  // Spawning probability weight
  peak_hour_multiplier: Float,
  country: Relation(Country)
}
```

#### **Import Job** (Tracking)
```javascript
{
  id: UUID,
  country: Relation(Country),
  file_type: String,  // 'highway', 'amenity', 'landuse', etc.
  status: Enum ['pending', 'processing', 'completed', 'failed'],
  total_features: Integer,
  processed_features: Integer,
  failed_features: Integer,
  error_log: JSON,
  started_at: Timestamp,
  completed_at: Timestamp
}
```

---

### **3. Redis Data Structures**

**Purpose**: Fast geospatial lookups (<200ms vs ~2sec PostgreSQL)

#### **Geospatial Indexes**
```redis
# Highways by country
GEOADD highways:barbados {lon} {lat} highway:{id}

# POIs by country
GEOADD pois:barbados {lon} {lat} poi:{id}

# Query nearby (GEORADIUS returns sorted by distance)
GEORADIUS highways:barbados -59.5905 13.0806 50 m WITHDIST ASC
```

#### **Feature Metadata**
```redis
# Highway details
HSET highway:5172465 name "Tom Adams Highway" type "trunk" ref "ABC"

# POI details
HSET poi:123 name "Bridgetown Mall" type "mall" activity "0.34"
```

#### **Reverse Geocode Cache**
```redis
# Cache formatted addresses (TTL: 1 hour)
SETEX geo:13.0806:-59.5905 3600 "Tom Adams Highway, near Bridgetown Mall"

# Lookup
GET geo:13.0806:-59.5905
```

#### **Vehicle State** (for geofencing)
```redis
# Track current geofence
SET vehicle:V123:current_highway highway:5172465
SET vehicle:V123:current_poi poi:123
```

**Memory Estimate**: ~16MB per country (Barbados)
- Geospatial indexes: ~5MB
- Metadata hashes: ~1MB
- Reverse geocode cache: ~10MB (LRU eviction)

---

### **4. Poisson Spawning System**

**Purpose**: Statistically realistic passenger spawning based on location, time, and amenity type

#### **Components**

**depot_reservoir.py**: Depot-based spawning
- **Mechanism**: FIFO queue, proximity-based selection
- **Temporal Multiplier**: 1.0x (journey starts at depot)
- **Use Case**: Passengers waiting at bus depots/terminals

**route_reservoir.py**: Route-based spawning
- **Mechanism**: Grid-based spatial indexing
- **Temporal Multiplier**: 0.5x (already traveling on route)
- **Use Case**: Passengers flagging down vehicles along routes

**poisson_geojson_spawner.py**: Statistical engine
- **Algorithm**: Poisson distribution with temporal/spatial modifiers
- **Base Rate**: 1800/hr (theoretical) → 100/hr (calibrated with 18x reduction)
- **Temporal Multipliers**:
  ```python
  {
    'morning_peak': 3.0,    # 6-9 AM
    'evening_peak': 2.5,    # 4-7 PM
    'midday': 1.0,          # 9 AM-4 PM
    'night': 0.1-0.2        # 7 PM-6 AM
  }
  ```
- **Activity Levels** (by amenity type):
  ```python
  {
    'mall': 0.34,           # High activity
    'university': 0.27,
    'bus_station': 0.30,
    'restaurant': 0.25,
    'cafe': 0.20,
    'school': 0.17,
    'hospital': 0.12,
    'bank': 0.15,
    'pharmacy': 0.18,
    'parking': 0.08,
    'fuel': 0.10
    # ... expand with all OSM amenity types
  }
  ```

**Spawn Rate Formula**:
```
spawn_rate = (base_rate × peak_multiplier × zone_modifier × activity_multiplier) / 18.0
```

**Current Calibration** (as of Oct 13, 2025):
- Evening 9 PM: **100 spawns/hour** (target: 90-180/hr) ✅
- Reduction factor: **18x** (from theoretical 1800/hr)

**simple_spatial_cache.py**: Zone loader
- **Strategy**: Async-only, no threading
- **Filter**: ±5km buffer around active routes
- **Refresh**: Auto-reloads from Strapi API when zones change
- **Challenge**: Now 3,694 zones (was ~50) - may need pagination/lazy-loading

---

### **5. Geofencing System**

**Current State**: `/api/geofence/find-nearby-features-fast` exists (PostgreSQL)
- **Performance**: ~2 seconds per query
- **Function**: `find_nearby_features_fast()` SQL function
- **Radius**: 50m → 500m (expanding search)

**Planned Architecture** (Redis Pub/Sub):

```
Vehicle GPS Update
│
├─ Redis Publish: vehicle:position
│  {
│    vehicleId: "V123",
│    lat: 13.0806,
│    lon: -59.5905,
│    timestamp: 1729872000000
│  }
│
└─ Geofence Service (Subscriber)
   │
   ├─ GEORADIUS highways:barbados -59.5905 13.0806 50 m
   ├─ GEORADIUS pois:barbados -59.5905 13.0806 100 m
   │
   ├─ Detect Enter/Exit (compare with previous state)
   │
   └─ Socket.IO Emit: geofence:entered
      {
        vehicleId: "V123",
        highway: { id: 5172465, name: "Tom Adams Highway", type: "trunk" },
        poi: { id: 123, name: "Bridgetown Mall", type: "mall" },
        address: "Tom Adams Highway, near Bridgetown Mall"
      }
```

**Target Latency**: <10ms (publish → notification)

---

## 📊 **GEOJSON DATA INVENTORY**

### **Files in sample_data/**

| File | Features | Size | Priority | Status |
|------|----------|------|----------|--------|
| `highway.geojson` | 22,719 | 43 MB | 🔴 High | Not Imported |
| `amenity.geojson` | 1,427 | 3.8 MB | 🔴 High | Not Imported |
| `landuse.geojson` | 2,267 | 4.3 MB | 🔴 High | Not Imported |
| `admin_level_6_polygon.geojson` | ? | ? | 🟡 Medium | Not Imported |
| `admin_level_8_polygon.geojson` | ? | ? | 🟡 Medium | Not Imported |
| `admin_level_9_polygon.geojson` | ? | ? | 🟡 Medium | Not Imported |
| `admin_level_10_polygon.geojson` | ? | ? | 🟡 Medium | Not Imported |
| `building.geojson` | ? | 658 MB | 🟢 Low | ⚠️ Requires streaming |
| `natural.geojson` | ? | ? | 🟢 Low | Not Imported |
| `name.geojson` | ? | ? | 🟢 Low | Not Imported |
| `add_street_polygon.geojson` | ? | ? | 🟢 Low | Not Imported |

**Excluded**: `barbados_geocoded_stops_utm.geojson` (separate use case)

---

### **GeoJSON Property Mapping**

#### **highway.geojson → highway table**
```javascript
// GeoJSON Feature
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[-59.5905, 13.0806], [-59.5910, 13.0810], ...]
  },
  "properties": {
    "full_id": "w5172465",
    "osm_id": "5172465",
    "osm_type": "way",
    "highway": "trunk",       // → highway_type
    "name": "Tom Adams Highway",
    "ref": "ABC",
    "oneway": "yes",          // → true
    "lanes": "2",             // → 2 (int)
    "maxspeed": "80",
    "surface": "asphalt"
  }
}

// Transformed Database Record
{
  osm_id: "5172465",
  highway_type: "trunk",
  name: "Tom Adams Highway",
  ref: "ABC",
  oneway: true,
  lanes: 2,
  maxspeed: "80",
  surface: "asphalt",
  geometry_geojson: { type: "LineString", coordinates: [...] },
  center_latitude: 13.0808,   // Calculated midpoint
  center_longitude: -59.59075,
  country_id: 1
}
```

#### **amenity.geojson → poi table**
```javascript
// GeoJSON Feature (⚠️ MultiPolygon, not Point!)
{
  "type": "Feature",
  "geometry": {
    "type": "MultiPolygon",  // ← CRITICAL: Need centroid
    "coordinates": [[[[...]]]]
  },
  "properties": {
    "full_id": "w123456",
    "osm_id": "123456",
    "amenity": "mall",        // → poi_type
    "name": "Bridgetown Mall",
    "addr:street": "Broad Street",
    "addr:city": "Bridgetown",
    "addr:housenumber": "123",
    "building": "commercial",
    "opening_hours": "Mo-Sa 09:00-18:00"
  }
}

// Transformed Database Record
{
  osm_id: "123456",
  poi_type: "mall",
  name: "Bridgetown Mall",
  latitude: 13.0947,          // Centroid of MultiPolygon (Turf.js)
  longitude: -59.6016,
  address: "123 Broad Street, Bridgetown",
  activity_level: 0.34,       // Assigned by amenity type
  metadata: {                 // All other properties
    building: "commercial",
    opening_hours: "Mo-Sa 09:00-18:00"
  },
  country_id: 1
}
```

#### **landuse.geojson → landuse_zone table**
```javascript
// GeoJSON Feature
{
  "type": "Feature",
  "geometry": {
    "type": "MultiPolygon",
    "coordinates": [[[[...]]]]
  },
  "properties": {
    "full_id": "w789012",
    "osm_id": "789012",
    "landuse": "residential",  // → landuse_type
    "name": "Green Acres",
    "population": "2500"
  }
}

// Transformed Database Record
{
  osm_id: "789012",
  landuse_type: "residential",
  name: "Green Acres",
  geometry_geojson: { type: "MultiPolygon", coordinates: [...] },
  center_latitude: 13.1050,   // Centroid
  center_longitude: -59.6100,
  population_density: 2500,   // From properties or default
  spawn_weight: 0.8,          // Default by landuse type
  peak_hour_multiplier: 1.0,
  country_id: 1
}
```

**Default Spawn Weights by Landuse Type**:
```javascript
{
  'residential': 0.8,
  'commercial': 0.6,
  'industrial': 0.3,
  'farmland': 0.1,
  'grass': 0.05,
  'meadow': 0.05,
  'forest': 0.02
}
```

---

## 🔧 **IMPLEMENTATION STRATEGY**

### **6-Phase Approach** (validate at each step)

1. **✅ Country Schema + Action Buttons** → Migrate & verify UI
2. **✅ Redis + Reverse Geocoding** → Benchmark <200ms performance
3. **✅ Geofencing** → Test real-time notifications
4. **✅ POI-Based Spawning** → Integrate with Poisson system
5. **✅ Depot/Route Spawners** → Verify commuter generation specs
6. **✅ Conductor Communication** → End-to-end validation

### **Import Flow Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│ STRAPI ADMIN UI (Country Content-Type)                          │
│                                                                  │
│  [Import Highways] [Import Amenities] [Import Landuse] ...      │
│         ↓ onClick                                                │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ window.importGeoJSON(countryId, { fileType: 'highway' })        │
│         ↓                                                        │
│  POST /api/geojson-import                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ GeoJSON Import Service                                           │
│  1. Validate: country exists, file exists                        │
│  2. Create import_job record (status: 'pending')                 │
│  3. Start async import (don't block response)                    │
│  4. Return job ID                                                │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Streaming Import Worker (async)                                 │
│  1. Stream parse: JSONStream.parse('features.*')                 │
│  2. Transform: highway.transformer.js                            │
│  3. Batch insert: 100 records at a time                          │
│  4. Update Redis: GEOADD highways:barbados                       │
│  5. Update progress: import_job (every 100 features)             │
│  6. Emit Socket.IO: import:progress                              │
│  7. On complete: Update geodata_import_status                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚨 **CRITICAL DECISIONS & ISSUES**

### **Decision 1: POI Geometry Handling**

**Problem**: POI schema expects Point (lat/lon) but amenity.geojson has MultiPolygon

**Options**:
- **A**: Extract centroid only, lose polygon shape
- **B**: Create `poi_shape` table for full geometry + `poi` for centroid ✅ RECOMMENDED
- **C**: Store both in metadata JSON

**Chosen**: Option B (data integrity)

```sql
CREATE TABLE poi_shape (
  id SERIAL PRIMARY KEY,
  poi_id INTEGER REFERENCES poi(id) ON DELETE CASCADE,
  geometry_geojson JSON NOT NULL,
  geometry_type VARCHAR(50)  -- 'Point', 'Polygon', 'MultiPolygon'
);
```

---

### **Decision 2: Redis Architecture**

**Options**:
- **A**: Geospatial indexes only (GEOADD/GEORADIUS)
- **B**: Reverse geocode cache only (SET/GET)
- **C**: Hybrid (geospatial + hash + cache) ✅ RECOMMENDED

**Chosen**: Option C (flexibility)

**Rationale**: 
- Geospatial for proximity queries
- Hashes for feature metadata
- Cache for formatted addresses
- Total memory: ~16MB per country

---

### **Decision 3: Import Scope**

**Options**:
- **A**: All 11 files immediately
- **B**: Top 3 only (highway/amenity/landuse MVP)
- **C**: Phased (3 core → 5 admin → 3 supporting) ✅ RECOMMENDED

**Chosen**: Option C (validate incrementally)

**Phase 1 Import**: highway.geojson, amenity.geojson, landuse.geojson

---

### **Decision 4: Geofencing Implementation**

**Options**:
- **A**: Polling (simple, high latency)
- **B**: Redis Pub/Sub (real-time, <10ms) ✅ RECOMMENDED
- **C**: PostgreSQL NOTIFY/LISTEN (no new infra, slower)

**Chosen**: Option B (aligns with Redis infrastructure)

---

## 📈 **PERFORMANCE TARGETS**

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Reverse geocoding (cache miss) | ~2000ms (PostgreSQL) | <200ms | 🔴 Not implemented |
| Reverse geocoding (cache hit) | N/A | <10ms | 🔴 Not implemented |
| Geofence notification latency | N/A | <10ms | 🔴 Not implemented |
| Import throughput | N/A | >1000 features/sec | 🔴 Not implemented |
| Redis memory usage | N/A | <50MB per country | 🔴 Not measured |
| Spawn rate | 100/hr ✅ | 90-180/hr | 🟢 Calibrated |
| SimpleSpatialZoneCache load time | Unknown | <5 seconds | 🟡 Needs testing |

---

## 🛠️ **CURRENT STATE**

### **What Exists** ✅

1. **Strapi CMS v5**: Running with PostgreSQL + PostGIS
2. **strapi-plugin-action-buttons**: Custom plugin at `src/plugins/strapi-plugin-action-buttons/`
3. **Poisson Spawning System**: Operational with 18x rate reduction, temporal multipliers
4. **SimpleSpatialZoneCache**: Loads zones from Strapi API (~5km buffer)
5. **Geofence API**: `/api/geofence/find-nearby-features-fast` (PostgreSQL, slow)
6. **GeoJSON Files**: 11 files in `sample_data/` ready for import
7. **Database Schemas**: highway, poi, landuse_zone tables exist
8. **Vehicle Simulator**: Python-based with GPS tracking, Socket.IO

### **What's Missing** ❌

1. **Redis Server**: Not installed
2. **Redis Geospatial Service**: Not implemented
3. **GeoJSON Import System**: Not implemented
4. **Action Buttons in Country Schema**: Not added
5. **Window Handlers**: Not created
6. **Real-time Geofencing**: Not implemented (only slow PostgreSQL query)
7. **Reverse Geocoding API**: Not implemented
8. **Import Job Tracking**: No `import_job` table

### **What Needs Calibration** ⚠️

1. **Activity Levels**: Only 5 amenity types defined, need all OSM types
2. **Spawn Weights**: Landuse zones need tuning with full dataset (3,694 zones)
3. **Temporal Multipliers**: May need adjustment with new POI data
4. **SimpleSpatialZoneCache**: May need pagination for 3,694 zones (currently ~50)

---

## 📝 **KEY ARCHITECTURAL PATTERNS**

### **1. Streaming JSON Parsing** (for large files)

```javascript
const JSONStream = require('JSONStream');
const fs = require('fs');

async function streamParseGeoJSON(filePath, onFeature) {
  return new Promise((resolve, reject) => {
    const stream = fs.createReadStream(filePath);
    const parser = JSONStream.parse('features.*');
    
    let count = 0;
    
    parser.on('data', async (feature) => {
      await onFeature(feature);
      count++;
      if (count % 100 === 0) {
        console.log(`Processed ${count} features...`);
      }
    });
    
    parser.on('end', () => resolve(count));
    parser.on('error', reject);
    
    stream.pipe(parser);
  });
}
```

### **2. Centroid Calculation** (Turf.js)

```javascript
const turf = require('@turf/turf');

function calculateCentroid(geometry) {
  const feature = turf.feature(geometry);
  const centroid = turf.centroid(feature);
  return {
    latitude: centroid.geometry.coordinates[1],
    longitude: centroid.geometry.coordinates[0]
  };
}
```

### **3. Batch Database Insert**

```javascript
async function batchInsert(tableName, records, batchSize = 100) {
  const batches = [];
  for (let i = 0; i < records.length; i += batchSize) {
    batches.push(records.slice(i, i + batchSize));
  }
  
  for (const batch of batches) {
    await strapi.db.query(tableName).createMany({ data: batch });
  }
}
```

### **4. Redis Geospatial Operations**

```javascript
// Add to geospatial index
await redis.geoadd('highways:barbados', lon, lat, `highway:${id}`);

// Query nearby (radius in meters)
const results = await redis.georadius(
  'highways:barbados', 
  -59.5905, 
  13.0806, 
  50, 
  'm', 
  'WITHDIST', 
  'ASC'
);
// Returns: [['highway:5172465', '0.0123'], ['highway:9876', '25.5432'], ...]

// Get metadata
const metadata = await redis.hgetall('highway:5172465');
// Returns: { name: 'Tom Adams Highway', type: 'trunk', ref: 'ABC' }
```

---

## 🔗 **API ENDPOINTS**

### **Existing**
- `GET /api/countries` - List countries
- `GET /api/countries/:id` - Get country details
- `GET /api/highways` - List highways
- `GET /api/pois` - List POIs
- `GET /api/landuse-zones` - List landuse zones
- `POST /api/geofence/find-nearby-features-fast` - Find features (PostgreSQL, slow)

### **To Be Implemented**
- `POST /api/geojson-import` - Start GeoJSON import
- `GET /api/geojson-import/:jobId` - Get import job status
- `GET /api/geojson-import/stats/:countryId` - Get import statistics
- `GET /api/reverse-geocode?lat={lat}&lon={lon}` - Reverse geocode (Redis)
- `DELETE /api/redis-cache/:countryCode` - Clear Redis cache

---

## 🐛 **KNOWN ISSUES**

1. **POI Geometry Mismatch**: amenity.geojson has MultiPolygon, schema expects Point
   - **Impact**: Import will fail without centroid extraction
   - **Fix**: Implement Turf.js centroid calculation in transformer

2. **Building File Size**: 658MB requires streaming parser
   - **Impact**: Cannot load entire file into memory
   - **Fix**: Use JSONStream for memory-efficient parsing

3. **SimpleSpatialZoneCache Scale**: Now 3,694 zones (was ~50)
   - **Impact**: May cause memory issues or slow loading
   - **Fix**: Implement pagination or lazy-loading

4. **No Import Validation**: No schema validation before import
   - **Impact**: Malformed GeoJSON could crash import
   - **Fix**: Add JSON schema validation before processing

5. **No Import Rollback**: Failed imports leave partial data
   - **Impact**: Database inconsistency on failure
   - **Fix**: Implement transaction-based import with rollback

---

## 📚 **REFERENCE DOCUMENTATION**

### **Internal Docs**
- `arknet_fleet_manager/arknet-fleet-api/src/plugins/strapi-plugin-action-buttons/ARCHITECTURE.md` - Plugin architecture
- `arknet_fleet_manager/arknet-fleet-api/src/plugins/strapi-plugin-action-buttons/EXAMPLES.ts` - Usage examples
- `PROJECT_STATUS.md` - Historical updates (last: Oct 13, 2025)
- `ARCHITECTURE_DEFINITIVE.md` - System architecture

### **External Docs**
- Strapi v5: https://docs.strapi.io/
- PostGIS: https://postgis.net/documentation/
- Redis Geospatial: https://redis.io/commands/geoadd/
- Turf.js: https://turfjs.org/
- OpenStreetMap Tags: https://wiki.openstreetmap.org/wiki/Map_features

---

## 🎯 **NEXT STEPS**

See `TODO.md` for detailed step-by-step implementation plan.

**Immediate Next Task**: 
1. Read country schema (`src/api/country/content-types/country/schema.json`)
2. Verify action-buttons plugin enabled
3. Add `geodata_import_buttons` field to country schema
4. Migrate schema
5. Verify buttons render in Strapi admin

**Quick Start Command**:
```bash
cd arknet_fleet_manager/arknet-fleet-api
npm run develop
```

---

## 💡 **TIPS FOR NEW AGENTS**

1. **Always check TODO.md first** - Step-by-step plan with checkboxes
2. **This is a feasibility study** - Analyze before implementing
3. **Validate at each phase** - Don't proceed until previous phase works
4. **Update TODO.md** - Mark checkboxes as you complete tasks
5. **Document issues immediately** - Add to "Session Notes" in TODO.md
6. **Ask questions** - User emphasizes clarity over speed
7. **GeoJSON files are LARGE** - Use streaming parsers, not fs.readFileSync()
8. **Centroid calculation is critical** - POI schema expects Point, data is MultiPolygon
9. **Spawn rate is already calibrated** - Don't break the 100/hr rate without discussion
10. **Redis is greenfield** - No existing Redis code, build from scratch

---

## 🏁 **SUCCESS CRITERIA**

**Project Complete When**:
- [x] All 11 GeoJSON files imported successfully
- [x] Redis reverse geocoding <200ms (cache miss), <10ms (cache hit)
- [x] Real-time geofencing <10ms latency
- [x] POI-based spawning maintains 90-180 commuters/hour
- [x] Depot/route spawners using imported data correctly
- [x] Conductor receives spawn events from all sources
- [x] Action buttons functional in Strapi admin
- [x] System stable under load (10+ concurrent vehicles)
- [x] End-to-end passenger flow validated (spawn → assign → pickup → deliver)

---

**Document Version**: 1.0  
**Last Updated**: October 25, 2025  
**Maintainer**: Update this document as architecture evolves
