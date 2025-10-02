# 🚀 ArkNet Transit System - Quick Start Guide

**Last Updated**: October 3, 2025  
**Current Status**: Phase 2 Architecture Complete, Ready for Testing  
**Next Task**: Geographic Data Import Testing (30 minutes)

---

## 📊 Current System Status

### ✅ What's Complete

| Component | Status | Details |
|-----------|--------|---------|
| **PostGIS 3.5** | ✅ INSTALLED | Via Stack Builder, verified working |
| **Strapi 5.23.5** | ✅ RUNNING | Enterprise Edition, TypeScript, port 1337 |
| **Socket.IO Foundation** | ✅ COMPLETE | 4 namespaces, event routing, Python client |
| **Depot Reservoir** | ✅ COMPLETE | OUTBOUND-only, FIFO queue, Socket.IO integrated |
| **Route Reservoir** | ✅ COMPLETE | BIDIRECTIONAL, grid-based spatial indexing |
| **Geographic Data System** | ✅ COMPLETE | Country lifecycle hook, 4 GeoJSON processors |
| **Documentation** | ✅ COMPLETE | 8 comprehensive docs, 4000+ lines total |

### 🎯 What's Next

**IMMEDIATE TASK**: Phase 2.5 - Geographic Data Import Testing (30 minutes)

1. Create test GeoJSON files (10 features each)
2. Upload via Strapi Admin UI
3. Verify import status and data in database

---

## 🏗️ Architecture Overview

### Core Concept: Two-Reservoir System

```text
┌─────────────────┐         ┌─────────────────┐
│  DEPOT          │         │  ROUTE          │
│  RESERVOIR      │         │  RESERVOIR      │
├─────────────────┤         ├─────────────────┤
│ • OUTBOUND only │         │ • BIDIRECTIONAL │
│ • FIFO queue    │         │ • Grid-based    │
│ • (depot, route)│         │ • Direction     │
│   keys          │         │   filtering     │
└─────────────────┘         └─────────────────┘
        ▲                           ▲
        │                           │
        │    Socket.IO Events       │
        │                           │
        └───────────┬───────────────┘
                    │
            ┌───────▼────────┐
            │   CONDUCTOR    │
            │   (Vehicle)    │
            ├────────────────┤
            │ if is_at_depot │
            │   query depot  │
            │ else           │
            │   query route  │
            └────────────────┘
```

### Key Decision Logic

**Conductor Query Pattern**:

```python
if self.is_at_depot():  # Within 100m of depot
    query_depot_reservoir(depot_id, route_id)
else:  # On route
    query_route_reservoir(position, direction)
```

**Depot Reservoir**:

- Spawns OUTBOUND commuters at depots/terminals
- FIFO queue per (depot_id, route_id)
- Returns commuters when vehicle queries at depot

**Route Reservoir**:

- Spawns BIDIRECTIONAL commuters along route paths
- Grid-based spatial indexing (~1km cells)
- Direction filtering: OUTBOUND vs INBOUND
- Returns commuters within 1000m matching direction

---

## 📁 Key Files Quick Reference

### Strapi Backend (TypeScript)

```text
arknet_fleet_manager/arknet-fleet-api/
├── src/
│   ├── api/
│   │   ├── country/
│   │   │   ├── content-types/country/
│   │   │   │   ├── schema.json          # 4 GeoJSON file uploads
│   │   │   │   └── lifecycles.ts        # GeoJSON processors
│   │   └── place/
│   │       └── content-types/place/
│   │           └── schema.json          # Place names (separate from POIs)
│   └── socketio/
│       ├── config.ts                    # Socket.IO configuration
│       ├── types.ts                     # TypeScript interfaces
│       ├── message-format.ts            # Standardized message format
│       └── server.ts                    # Event routing logic
```

### Python Commuter Service

```text
commuter_service/
├── depot_reservoir.py                   # OUTBOUND commuters at depots
├── route_reservoir.py                   # BIDIRECTIONAL commuters on routes
├── socketio_client.py                   # Socket.IO Python client
├── poisson_geojson_spawner.py           # Statistical spawning engine
├── location_aware_commuter.py           # Individual commuter logic
└── commuter_config.py                   # Configuration settings
```

### Documentation Suite

```text
Root Directory/
├── FULL_MVP_ARCHITECTURE.md             # Complete technical architecture (600+ lines)
├── COMMUTER_SPAWNING_SUMMARY.md         # Depot vs Route explained (500+ lines)
├── HOW_IT_WORKS_SIMPLE.md               # Layman's explanation (1000+ lines)
├── CONDUCTOR_ACCESS_MECHANISM.md        # Socket.IO query/response (600+ lines)
├── CONDUCTOR_QUERY_LOGIC_CONFIRMED.md   # Conditional logic (300+ lines)
├── INTEGRATION_CHECKLIST.md             # Step-by-step integration (500+ lines)
├── GEODATA_IMPORT_COMPLETE.md           # GeoJSON import system
└── MVP_ROADMAP.md                       # Phase-by-phase plan
```

---

## ⚡ Quick Commands

### Start Strapi Development Server

```powershell
cd E:\projects\arknettransit\arknet_transit_system\arknet_fleet_manager\arknet-fleet-api
npm run develop
```

**Access**: <http://localhost:1337/admin>

### Build TypeScript

```powershell
cd E:\projects\arknettransit\arknet_transit_system\arknet_fleet_manager\arknet-fleet-api
npm run build
```

### Activate Python Virtual Environment

```powershell
cd E:\projects\arknettransit\arknet_transit_system
& .\.venv\Scripts\Activate.ps1
```

### Run Socket.IO Quick Test

```powershell
# Terminal 1: Start Strapi
cd arknet_fleet_manager\arknet-fleet-api
npm run develop

# Terminal 2: Run Python test
cd E:\projects\arknettransit\arknet_transit_system
& .\.venv\Scripts\Activate.ps1
python quick_test_socketio.py
```

### PostgreSQL Connection

- **Host**: localhost
- **Port**: 5432
- **Database**: arknettransit
- **User**: postgres
- **PostGIS Version**: 3.5

---

## 🎯 Next Steps (In Order)

### 1. Create Test GeoJSON Files (10 minutes)

**Create**: `test_data/test_pois.geojson`

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-59.6152, 13.0975]
      },
      "properties": {
        "name": "Test POI 1",
        "amenity": "bus_station"
      }
    }
    // ... 9 more features
  ]
}
```

**Create**: `test_data/test_places.geojson` (same structure, place_type: "city")  
**Create**: `test_data/test_landuse.geojson` (Polygon geometry, landuse: "residential")  
**Create**: `test_data/test_regions.geojson` (Polygon geometry, admin_level: "8")

### 2. Upload via Strapi Admin (10 minutes)

1. Navigate to <http://localhost:1337/admin>
2. Content Manager → Countries → Create new entry
3. Fill in country details (name, code)
4. Upload all 4 GeoJSON files
5. Save and publish
6. Check `geodata_import_status` shows "✅ POIs, ✅ Places, ✅ Landuse, ✅ Regions"

### 3. Verify Data Import (10 minutes)

```powershell
# Query POIs
curl http://localhost:1337/api/pois

# Query Places
curl http://localhost:1337/api/places

# Query Landuse Zones
curl http://localhost:1337/api/landuse-zones

# Query Regions
curl http://localhost:1337/api/regions
```

**Expected**: 40 total records (10 per content type)

### 4. Configure API Permissions (15 minutes)

1. Strapi Admin → Settings → Users & Permissions Plugin → Roles
2. Select **Public** role
3. Enable for each content type:
   - ✅ find
   - ✅ findOne
4. Content types: Country, POI, Place, Landuse-zone, Region
5. Save

### 5. Connect Spawner to Strapi (45 minutes)

Modify `commuter_service/poisson_geojson_spawner.py`:

```python
# Instead of loading from local files:
# self.pois = self._load_geojson('data/pois.geojson')

# Query from Strapi:
import requests

class PoissonGeoJSONSpawner:
    def __init__(self, strapi_url='http://localhost:1337'):
        self.strapi_url = strapi_url
        self.pois = self._fetch_pois()
        self.landuse_zones = self._fetch_landuse()
        self.regions = self._fetch_regions()
    
    def _fetch_pois(self):
        response = requests.get(f'{self.strapi_url}/api/pois')
        data = response.json()
        return [self._convert_to_feature(poi) for poi in data['data']]
    
    def _convert_to_feature(self, strapi_record):
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [strapi_record['lon'], strapi_record['lat']]
            },
            'properties': strapi_record
        }
```

---

## 📚 Documentation Deep Dive

### Understanding the System

**Start Here**: `HOW_IT_WORKS_SIMPLE.md`  

- Layman's explanation, no jargon
- Real-world analogies (coffee shop, bus stops)
- Perfect for high-level understanding

**Then Read**: `COMMUTER_SPAWNING_SUMMARY.md`  

- Why two reservoirs?
- Depot (OUTBOUND) vs Route (BIDIRECTIONAL)
- Statistical spawning explained

**Technical Details**: `FULL_MVP_ARCHITECTURE.md`  

- Complete technical architecture
- Code examples with line numbers
- Data flow diagrams
- Socket.IO event patterns

**Implementation Guide**: `INTEGRATION_CHECKLIST.md`  

- Step-by-step integration instructions
- Code examples for each step
- Testing procedures

### Specific Topics

**Socket.IO Communication**: `CONDUCTOR_ACCESS_MECHANISM.md`  

- How conductor queries reservoirs
- Event-driven query/response pattern
- Real-time messaging flow

**Conditional Logic**: `CONDUCTOR_QUERY_LOGIC_CONFIRMED.md`  

- When to query depot vs route
- is_at_depot() threshold logic
- Real-world timeline example

**GeoJSON Import**: `GEODATA_IMPORT_COMPLETE.md`  

- Lifecycle hook implementation
- Chunked processing strategy
- Cascade delete behavior

---

## 🐛 Troubleshooting

### Strapi Won't Start

```powershell
# Check if TypeScript compiled successfully
cd arknet_fleet_manager\arknet-fleet-api
npm run build

# If errors, check:
# - Node version: node --version (should be 22.15.0)
# - Dependencies: npm install
```

### PostGIS Errors

```sql
-- Verify PostGIS installed
SELECT PostGIS_Version();

-- Should return: 3.5.x
```

### Socket.IO Connection Failures

```python
# Check Strapi is running on port 1337
# Check firewall settings
# Verify Socket.IO server started in Strapi logs
```

### Import Status Not Updating

- Check Strapi logs for processing errors
- Verify GeoJSON file format is valid (use geojson.io)
- Check file size (large files may timeout)
- Look for TypeScript errors in lifecycle hook

---

## 💡 Key Concepts Recap

### Two-Reservoir Philosophy

**Why Not One Reservoir?**

- Depot: Queue-based (FIFO), route-specific
- Route: Proximity-based, direction-aware
- Different data structures for different behaviors

### OUTBOUND vs BIDIRECTIONAL

**Depot Commuters**: OUTBOUND only

- Morning: Leave home → Go to work
- Evening: Leave work → Go home
- Always departing from depot, not arriving

**Route Commuters**: BIDIRECTIONAL

- Morning: Some travel OUTBOUND (to city)
- Evening: Same people travel INBOUND (from city)
- Spawn along route in both directions

### Conductor Decision Logic

```text
```text
Vehicle at depot (< 100m)?
├─ YES → Query Depot Reservoir
│         • Depot ID + Route ID
│         • FIFO queue
│         • All commuters OUTBOUND
│
└─ NO → Query Route Reservoir
          • Current position + direction
          • Proximity (1000m radius)
          • Direction filtering
```

---

## 📞 Quick Reference Links

- **Strapi Admin**: <http://localhost:1337/admin>
- **Strapi API**: <http://localhost:1337/api>
- **PostgreSQL**: localhost:5432/arknettransit
- **Project Root**: E:\projects\arknettransit\arknet_transit_system

---

## ✅ Pre-Flight Checklist

Before starting work, verify:

- [ ] PostgreSQL 17 running
- [ ] PostGIS 3.5 installed (`SELECT PostGIS_Version();`)
- [ ] Strapi development server started (`npm run develop`)
- [ ] Python virtual environment activated
- [ ] Socket.IO foundation tested (`python quick_test_socketio.py`)
- [ ] All documentation reviewed for context

---

## 🎯 Current Phase: 2.5 (Geographic Data Import Testing)

**Estimated Time**: 30 minutes  
**Blocking**: None  
**Dependencies**: PostGIS ✅, Strapi ✅, Lifecycle hooks ✅

**Immediate Action**: Create 4 test GeoJSON files and upload via Strapi Admin UI

**Success Criteria**:

1. All 4 files upload successfully
2. Import status shows "✅" for all content types
3. API queries return 40 total records
4. No errors in Strapi logs

---

*Last session ended with: User confirmed understanding of conductor query logic (depot when parked, route when traveling). Documentation suite complete. Ready for testing phase.*
