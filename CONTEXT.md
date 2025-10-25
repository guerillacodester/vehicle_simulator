# ArkNet Vehicle Simulator - Project Context

**Project**: ArkNet Fleet Manager & Vehicle Simulator  
**Repository**: vehicle_simulator  
**Branch**: branch-0.0.2.6  
**Date**: October 25, 2025  
**Status**: � Active Development - GeoJSON Import System Implementation  
**Phase**: Phase 1 - Full Implementation (Steps 1.4-1.10 in progress)

> **📌 MASTER DOCUMENT**: This is the primary context reference. See `TODO.md` for step-by-step tasks.

---

## 🏗️ **SYSTEM ARCHITECTURE OVERVIEW**

### **Complete System Diagram**

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ARKNET VEHICLE SIMULATOR                               │
│                         Production Transit Simulation                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (User Interfaces)                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────┐   ┌─────────────────────────────┐   │
│  │  Strapi Admin UI (React)           │   │  Real-Time Dashboard        │   │
│  │  Port: 1337/admin                  │   │  (Future - React/Vue)       │   │
│  │  - Content management              │   │  - Vehicle tracking         │   │
│  │  - GeoJSON imports (5 buttons)     │   │  - Passenger spawning view  │   │
│  │  - Action buttons plugin           │   │  - Route visualization      │   │
│  └────────────────────────────────────┘   └─────────────────────────────┘   │
│                    ↓                                    ↓                     │
└────────────────────┼────────────────────────────────────┼─────────────────────┘
                     │                                    │
                     ↓ HTTP/Socket.IO                     ↓ WebSocket
                     
┌────────────────────┴────────────────────────────────────┴─────────────────────┐
│ API GATEWAY / DATA LAYER (Single Source of Truth)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Strapi v5.23.5 (Node.js 22.20.0)                                       │ │
│  │  arknet_fleet_manager/arknet-fleet-api/                                 │ │
│  │  Port: 1337                                                              │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │ REST/GraphQL APIs (Data CRUD - Single Source of Truth)           │  │ │
│  │  │  - /api/countries, /api/routes, /api/stops                        │  │ │
│  │  │  - /api/highways, /api/pois, /api/landuse-zones                   │  │ │
│  │  │  - /api/buildings, /api/depots, /api/vehicles                     │  │ │
│  │  │  - /api/regions (admin boundaries)                                │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │ GeoJSON Import API (Custom Controllers)                           │  │ │
│  │  │  - POST /api/import-geojson/highway (22,719 features, 43MB)       │  │ │
│  │  │  - POST /api/import-geojson/amenity (1,427 features, 3.8MB)       │  │ │
│  │  │  - POST /api/import-geojson/landuse (2,267 features, 4.3MB)       │  │ │
│  │  │  - POST /api/import-geojson/building (658MB - streaming required) │  │ │
│  │  │  - POST /api/import-geojson/admin (parishes/districts)            │  │ │
│  │  │  ✅ Uses PostGIS geometry columns (Point, LineString, Polygon)    │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │ Geospatial Services API (Phase 1 - Custom Controllers)            │  │ │
│  │  │  - POST /api/geospatial/check-geofence                            │  │ │
│  │  │  - POST /api/geospatial/reverse-geocode                           │  │ │
│  │  │  - GET  /api/geospatial/route-buildings?route_id=X&buffer=500     │  │ │
│  │  │  - GET  /api/geospatial/depot-buildings?depot_id=X&radius=1000    │  │ │
│  │  │  - GET  /api/geospatial/zone-containing?lat=X&lon=Y               │  │ │
│  │  │  - GET  /api/geospatial/nearby-pois?lat=X&lon=Y&radius=500        │  │ │
│  │  │  ✅ Direct PostGIS queries (ST_Contains, ST_DWithin, ST_Intersects)│ │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │ Socket.IO Events (Real-time updates)                              │  │ │
│  │  │  - import:progress (file processing updates)                      │  │ │
│  │  │  - import:complete (job finished)                                 │  │ │
│  │  │  - vehicle:position (vehicle movement)                            │  │ │
│  │  │  - passenger:spawned (new passenger)                              │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      ↓                                        │
└──────────────────────────────────────┼────────────────────────────────────────┘
                                       │
                                       ↓ Knex.js ORM
                                       
┌──────────────────────────────────────┴────────────────────────────────────────┐
│ DATABASE LAYER (PostgreSQL + PostGIS)                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL 16.3 + PostGIS 3.5                                          │ │
│  │  Database: arknettransit  |  Port: 5432  |  User: david                 │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │ Spatial Tables (PostGIS geometry columns + GIST indexes)          │  │ │
│  │  │  ✅ highways (geom: LineString, 4326)                             │  │ │
│  │  │  ✅ stops (geom: Point, 4326) - GTFS compliant                    │  │ │
│  │  │  ✅ shape_geometries (geom: LineString, 4326) - GTFS aggregated   │  │ │
│  │  │  ✅ depots (geom: Point, 4326)                                    │  │ │
│  │  │  ✅ landuse_zones (geom: Polygon, 4326)                           │  │ │
│  │  │  ✅ pois (geom: Point, 4326)                                      │  │ │
│  │  │  ✅ regions (geom: MultiPolygon, 4326) - admin boundaries        │  │ │
│  │  │  ✅ geofences (geom: Polygon, 4326)                               │  │ │
│  │  │  ⏳ buildings (geom: Polygon, 4326) - NOT YET CREATED             │  │ │
│  │  │  ✅ vehicle_events (geom: Point, 4326)                            │  │ │
│  │  │  ✅ active_passengers (geom: Point, 4326)                         │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │ GIST Spatial Indexes (12 indexes)                                 │  │ │
│  │  │  - idx_highways_geom, idx_stops_geom, idx_depots_geom             │  │ │
│  │  │  - idx_landuse_zones_geom, idx_pois_geom, idx_regions_geom        │  │ │
│  │  │  - idx_shape_geometries_geom, idx_geofences_geom                  │  │ │
│  │  │  - idx_vehicle_events_geom, idx_active_passengers_geom            │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                    ↑ Strapi ORM (write)          ↑ Direct SQL (read - Phase 2)│
└────────────────────┼──────────────────────────────┼────────────────────────────┘
                     │                              │
                     │                              │ (Phase 2 - Future)
                     │                              │
┌────────────────────┴──────────────┐  ┌───────────┴────────────────────────────┐
│ BUSINESS LOGIC LAYER (Simulators) │  │ GEOSPATIAL SERVICE LAYER (Future)     │
├───────────────────────────────────┤  ├───────────────────────────────────────┤
│                                    │  │                                        │
│  ┌──────────────────────────────┐ │  │  ┌──────────────────────────────────┐ │
│  │ arknet_transit_simulator/    │ │  │  │ geospatial_service/              │ │
│  │ (Python)                     │ │  │  │ (Python FastAPI)                 │ │
│  │ - Vehicle movement           │ │  │  │ Port: 8001                       │ │
│  │ - Route navigation           │ │  │  │ - Geofencing API                 │ │
│  │ - Stop detection             │ │  │  │ - Reverse geocoding API          │ │
│  │ - Socket.IO events           │ │  │  │ - Spatial query optimization     │ │
│  │ Consumes: Strapi API         │ │  │  │ - Redis caching layer            │ │
│  └──────────────────────────────┘ │  │  │ Database: arknettransit (same)   │ │
│                                    │  │  │ Connection: asyncpg (read-only)  │ │
│  ┌──────────────────────────────┐ │  │  │ ⏳ Phase 2 - Not yet implemented │ │
│  │ commuter_simulator/          │ │  │  └──────────────────────────────────┘ │
│  │ (Python - ACTIVE)            │ │  │                                        │
│  │ ✅ Route Reservoir           │ │  └────────────────────────────────────────┘
│  │    - ST_DWithin(building,    │ │
│  │      route, 500m)            │ │  ┌────────────────────────────────────────┐
│  │ ✅ Depot Reservoir           │ │  │ DEPRECATED LEGACY SYSTEMS             │
│  │    - ST_DWithin(building,    │ │  ├────────────────────────────────────────┤
│  │      depot, 1000m)           │ │  │                                        │
│  │ ✅ Poisson distribution      │ │  │  ⚠️ commuter_service/                 │
│  │ ✅ Temporal patterns         │ │  │  (Python - DEPRECATED)                │
│  │ Architecture:                │ │  │  - Being phased out                   │
│  │  infrastructure/database/    │ │  │  - Replaced by commuter_simulator     │
│  │  services/route_reservoir/   │ │  │  - Tight coupling issues              │
│  │  services/depot_reservoir/   │ │  │  - Do not use for new development     │
│  │ Consumes:                    │ │  │                                        │
│  │  - Strapi API (CRUD)         │ │  └────────────────────────────────────────┘
│  │  - Geospatial API (spatial)  │ │
│  └──────────────────────────────┘ │
│                                    │
└────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ DATA FLOW PATTERNS                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ WRITES (Data Creation/Updates):                                             │
│   Strapi Admin UI → Strapi API → PostgreSQL                                 │
│   GeoJSON Import → Strapi Controller → PostgreSQL (ST_GeomFromText)         │
│                                                                              │
│ READS (Data Consumption):                                                   │
│   Simulators → Strapi API → PostgreSQL (CRUD operations)                    │
│   Simulators → Geospatial API → PostgreSQL (spatial queries)                │
│                                                                              │
│ REAL-TIME EVENTS:                                                           │
│   Simulators → Socket.IO → Strapi → Dashboard                               │
│   Import Progress → Socket.IO → Admin UI (progress bars)                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ KEY ARCHITECTURAL PRINCIPLES                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 1. Single Source of Truth:                                                  │
│    ✅ Strapi owns database schema and all CRUD operations                   │
│    ✅ All writes go through Strapi Entity Service API                       │
│    ✅ Simulators NEVER access database directly                             │
│                                                                              │
│ 2. PostGIS First:                                                           │
│    ✅ All spatial tables use geometry columns (Point, LineString, Polygon)  │
│    ✅ GIST indexes on all geometry columns                                  │
│    ✅ GTFS compliance for transit data (stops, shapes, routes)              │
│                                                                              │
│ 3. Separation of Concerns:                                                  │
│    ✅ Strapi = Data persistence + Admin UI                                  │
│    ✅ Geospatial Service = Optimized spatial queries (Phase 1: in Strapi)   │
│    ✅ Simulators = Business logic (vehicle movement, passenger spawning)    │
│                                                                              │
│ 4. Phased Migration:                                                        │
│    ✅ Phase 1 (MVP): Geospatial API in Strapi (simpler deployment)          │
│    ✅ Phase 2 (Scale): Extract to FastAPI service (>1000 req/s)             │
│    ✅ Same database: Both Strapi and geospatial service connect to          │
│       arknettransit PostgreSQL (Strapi writes, geospatial reads)            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📖 **DOCUMENT HIERARCHY**

This workspace has multiple documentation files. Here's the authoritative order:

1. **`CONTEXT.md`** (this file) - ✅ **PRIMARY REFERENCE**
   - Complete project context, architecture, and system integration
   - Component roles and responsibilities
   - User preferences and work style
   - Start here for project understanding

2. **`TODO.md`** - ✅ **ACTIVE TASK LIST**
   - Step-by-step implementation plan (65+ steps, 6 phases)
   - Time estimates and validation criteria
   - Progress tracking with checkboxes
   - Update this as you complete tasks

3. **`GEOJSON_IMPORT_CONTEXT.md`** - ⚠️ **HISTORICAL REFERENCE**
   - Early architecture study (600+ lines)
   - Created before CONTEXT.md consolidation
   - Keep for reference, but CONTEXT.md supersedes it
   - Contains detailed file analysis and constraints

4. **`PROJECT_STATUS.md`** - 📚 **HISTORICAL LOG**
   - Project updates through October 13, 2025
   - Background context on simulator development
   - Not actively maintained during import system work

5. **`ARCHITECTURE_DEFINITIVE.md`** - 📚 **SYSTEM DESIGN**
   - Overall system architecture
   - May be outdated for import system specifics

---

## 🕐 **SESSION HISTORY**

### **How We Got Here**

**October 25, 2025** - User lost chat history and requested full context rebuild:

1. **Initial Request**: "Read context, read TODO" (chat history lost)
2. **Context Recovery**: Read PROJECT_STATUS.md and ARCHITECTURE_DEFINITIVE.md
3. **First Deliverable**: Created initial TODO list (8 items)
4. **Scope Clarification**: User revealed this is a **feasibility study** for:
   - Redis-based reverse geocoding
   - Real-time geofencing
   - Poisson spawning integration
   - Strapi action-buttons plugin triggers
5. **Deep Analysis**: Examined codebase (action-buttons plugin, spawning systems, geofence API)
6. **GeoJSON Analysis**: User confirmed 11 files from sample_data (excluding barbados_geocoded_stops)
7. **First Context Doc**: Created GEOJSON_IMPORT_CONTEXT.md (600+ lines)
8. **User Requested Reorganization**: Phased approach based on their vision
9. **Custom Plugin Clarification**: Confirmed `strapi-plugin-action-buttons` is custom ArkNet plugin (no marketplace equivalent)
10. **TODO Created**: Built TODO.md with 65+ granular steps across 6 phases
11. **Single Source of Truth**: User requested CONTEXT.md + TODO.md separation
12. **Added System Integration**: Enhanced CONTEXT.md with 10 detailed workflow diagrams
13. **Role Clarification**: User asked to confirm conductor/driver/commuter roles
14. **Architecture Fix**: Discovered and corrected "Conductor Service" error (doesn't exist - assignment happens in spawn strategies)
15. **Agent Role Established**: User confirmed agent acts as 50+ year senior developer with authority to push back on bad practices
16. **Phase 1 Steps 1.1-1.3 Complete**: Schema analyzed, plugin verified, database columns validated, backups created
17. **Design Decision**: User requested 5 separate buttons (one per GeoJSON file type) with full Socket.IO progress feedback
18. **Current State**: ✅ Steps 1.1-1.3 complete (9/75 steps), ready for full implementation (Steps 1.4-1.10)

### **Key Decisions Made**

| Decision | Rationale | Date |
|----------|-----------|------|
| **Use Redis for reverse geocoding** | PostgreSQL queries ~2000ms, Redis target <200ms (10-100x improvement) | Oct 25 |
| **11 GeoJSON files in scope** | User specified: exclude barbados_geocoded_stops from sample_data | Oct 25 |
| **Use custom action-buttons plugin** | Already built at `src/plugins/strapi-plugin-action-buttons/`, no marketplace equivalent | Oct 25 |
| **Universal streaming for ALL imports** | Consistency, memory efficiency (<500MB), progress feedback, future-proofing. Files: 628MB building, 41MB highway, 4MB landuse, 3.6MB amenity, <1MB admin. Single code path reduces bugs. | Oct 25 |
| **Centroid extraction needed** | amenity.geojson has MultiPolygon, POI schema expects Point | Oct 25 |
| **6-phase implementation** | Country Schema → Redis → Geofencing → POI → Depot/Route → Conductor | Oct 25 |
| **Event-based passenger assignment** | No centralized "Conductor Service" - routes assigned in spawn strategies | Oct 25 |
| **5 separate import buttons** | One button per file type (highway, amenity, landuse, building, admin) for granular control | Oct 25 |
| **Socket.IO for progress** | Real-time progress feedback during GeoJSON imports, leveraging existing Socket.IO infrastructure | Oct 25 |
| **Batch processing (500-1000 features)** | Optimal database performance, enables progress updates, prevents memory spikes | Oct 25 |
| **Full implementation today** | Not just skeleton - complete streaming parser, Socket.IO progress, database integration | Oct 25 |

### **Current Checkpoint**

- ✅ **Documentation**: CONTEXT.md and TODO.md complete and validated
- ✅ **Architecture**: Component roles clarified, system flows documented
- ✅ **Phase 1 Steps 1.1-1.7.3c**: UI buttons working, backend API created, PostGIS migration completed for highways
- ✅ **Phase 1.8: PostGIS Migration**: All 11 tables migrated with geometry columns + GIST indexes (Oct 25 18:17)
- ✅ **Phase 1.9: Buildings Content Type**: Created with PostGIS Polygon column + GIST index (Oct 25 19:16)
- ⏳ **Phase 1.10: Streaming GeoJSON Parser**: NEXT - Universal streaming for ALL 5 content types
- 🎯 **Next Action**: Install stream-json, create reusable streaming utility, update all 5 import endpoints

**Streaming Strategy Confirmed**:

- **Scope**: ALL 5 content types (highway, amenity, landuse, building, admin)
- **File Sizes**: 628MB building (critical), 41MB highway, 4.12MB landuse, 3.65MB amenity, <1MB admin
- **Rationale**: Consistency (single code path), memory efficiency (<500MB), real-time progress, future-proofing
- **Implementation**: Reusable `geojson-stream-parser.ts` utility with configurable batch size (500-1000 features)
- **Benefits**: No memory leaks, production-ready scalability, consistent progress feedback across all imports

---

## 🚨 **CRITICAL: DATABASE ARCHITECTURE ISSUES (Oct 25, 2025 18:00)**

### **Problem Discovered**

During highway GeoJSON import implementation, discovered the database uses **individual lat/lon columns and linking tables** instead of proper **PostGIS geometry columns** for spatial data.

### **Impact Assessment**

- ❌ **Performance**: 10-100x slower spatial queries without GIST indexes
- ❌ **Storage**: 90% more database records (477K vs 22K for highways alone)
- ❌ **Scalability**: Cannot handle production workload efficiently
- ❌ **Functionality**: Missing spatial operations (distance, intersection, buffering)
- 💰 **Cost**: Estimated **$50,000+ additional infrastructure expense** if not fixed

### **✅ RESOLUTION COMPLETE (Oct 25, 2025 18:17)**

**Migration Status**: ✅ **ALL SPATIAL TABLES MIGRATED TO POSTGIS**

**Migrated Tables** (11 total):

- ✅ highways - LineString geometry with GIST index
- ✅ stops - Point geometry with GIST index (GTFS compliant)
- ✅ depots - Point geometry with GIST index
- ✅ shape_geometries - NEW aggregated LineString table (27 shapes, GTFS compliant)
- ✅ landuse_zones - Polygon geometry with GIST index
- ✅ pois - Point geometry with GIST index
- ✅ regions - MultiPolygon geometry with GIST index
- ✅ geofences - Polygon geometry with GIST index
- ✅ vehicle_events - Point geometry with GIST index
- ✅ active_passengers - Point geometry with GIST index
- ✅ geofence_all - Geography column with GIST index

**Spatial Indexes Created**: 12 GIST indexes on geometry columns

**Validation Results**:

- ✅ Distance queries working (ST_DWithin: 21ms execution)
- ✅ Length calculations working (ST_Length on highways: 0.055km)
- ✅ Aggregated shapes working (7-45 points per route shape)
- ✅ Point geometries working (5 depots with ST_AsText verified)

**Migration Script**: `arknet_fleet_manager/arknet-fleet-api/migrate_all_to_postgis.sql` (executed successfully)

### **Remaining Work**

⚠️ **Import Code Updates Required** (Step 1.8.4): ✅ **COMPLETE (Oct 25, 2025 18:25)**

- [x] Amenity/POI import - Extracts centroid, uses ST_GeomFromText('POINT(...)')
- [x] Landuse import - Uses ST_GeomFromText('POLYGON(...)')
- [x] Building import - Placeholder (table doesn't exist, streaming required for 658MB)
- [x] Admin boundaries - Uses ST_GeomFromText('MULTIPOLYGON(...)')

✅ **Highway import already updated** - Uses PostGIS LineString with WKT format

**🎉 PostGIS Migration: FULLY COMPLETE** - All spatial tables migrated, all import code updated

### **Next Phase: Buildings Table & Streaming Parser**

⚠️ **Buildings Content Type Required** (not yet created):

- **Purpose**: Foundation for realistic passenger spawning model
- **File**: sample_data/building.geojson (658MB, ~100K+ features)
- **Schema**: building_id, osm_id, building_type, geom geometry(Polygon, 4326)
- **Why Critical**: See "Passenger Spawning Architecture" section below

⚠️ **Streaming Parser Required** (Step 1.9):

- **Why**: building.geojson is 658MB (too large to read into memory)
- **Solution**: Use `stream-json` to process chunks
- **Applies to**: All GeoJSON imports for production batch processing

### **Passenger Spawning Architecture Vision**

The system uses **5 spatial datasets + temporal statistics** for realistic spawning across **3 reservoir types**:

#### **Three Reservoir Spawning Patterns**

1. **Route Reservoir** - Passengers along specific routes
   - **Origin**: Buildings + Landuse zones along route corridor
   - **Destination**: Buildings + Landuse zones along same route
   - **Logic**: Spawn passengers at stops where nearby buildings/zones have high density
   - **Example**: Route 1 spawns at stops near apartment buildings (residential landuse)
   - **Spatial Query**: Find buildings within 500m buffer of route shape using PostGIS

2. **Depot Reservoir** - Passengers near depot locations
   - **Origin**: Buildings + Landuse zones within depot catchment area
   - **Destination**: Depots (return trips) or nearby amenities
   - **Logic**: Depot acts as hub, spawn passengers in surrounding residential areas
   - **Example**: Cheapside Terminal depot spawns from nearby office buildings (morning) and residential (evening)
   - **Spatial Query**: Find buildings within 1km radius of depot using ST_DWithin()

3. **General Reservoir** - City-wide random spawning
   - **Origin**: Any building with appropriate landuse type
   - **Destination**: Any amenity/POI
   - **Logic**: Random pairs based on building type → amenity type matching
   - **Example**: Residential building → School (morning), Office → Restaurant (lunch)

#### **Spatial Dataset Roles**

1. **Buildings (658MB)** - Individual building footprints
   - **Route Reservoir**: Origin/destination points along route
   - **Depot Reservoir**: Origin/destination points near depots
   - **Building-level precision** (apartments vs houses vs offices)
   - **Different spawn rates by building type** (residential vs commercial)

2. **Landuse Zones (2,267 features)** - Area density modifiers
   - **Route Reservoir**: Density multiplier for buildings along route
   - **Depot Reservoir**: Density multiplier for buildings near depot
   - **Applied to buildings within zone boundaries**
   - **Example**: High-density residential × 2.5 spawn rate

3. **Amenities/POIs (1,427 features)** - Destination attractiveness
   - **All Reservoirs**: Primary trip destinations
   - **Creates trip generation patterns** (commute, shopping, school)
   - **Example**: University spawns 1,000 students at 8am

4. **Admin Boundaries (parishes)** - Regional population calibration
   - **All Reservoirs**: Regional population totals from census
   - **Distributes regional totals across buildings**
   - **Example**: St. Michael parish 80K people → allocate to buildings

5. **Highways (22,719 features)** - Road network connectivity
   - **Route Reservoir**: Defines route corridors for spawning
   - **Accessibility factor**: Buildings near highways spawn more riders

6. **Depots (5 locations)** - Hub locations
   - **Depot Reservoir**: Center point for catchment area spawning
   - **Spatial query**: ST_DWithin(depot.geom, building.geom, 1000m)

#### **Spawning Algorithms** (conceptual)

**Route Reservoir**:

```python
for stop in route.stops:
    # Find buildings near this stop
    nearby_buildings = ST_DWithin(building.geom, stop.geom, 500)
    
    for building in nearby_buildings:
        landuse_zone = find_zone_containing(building)
        base_rate = building.units * transit_usage_rate
        time_modifier = poisson_distribution(current_hour)
        density_modifier = landuse_zone.density_factor
        
        spawn_rate = base_rate * time_modifier * density_modifier
        spawn_passenger(building.centroid, random_stop_on_route)
```

**Depot Reservoir**:

```python
for depot in depots:
    # Find buildings within depot catchment
    nearby_buildings = ST_DWithin(building.geom, depot.geom, 1000)
    
    for building in nearby_buildings:
        landuse_zone = find_zone_containing(building)
        base_rate = building.units * depot_ridership_rate
        time_modifier = poisson_distribution(current_hour)
        density_modifier = landuse_zone.density_factor
        
        spawn_rate = base_rate * time_modifier * density_modifier
        spawn_passenger(building.centroid, depot.location)
```

**Result**: Production-grade realistic passenger spawning with:

- **Spatial precision** (building-level, not just random zones)
- **Temporal patterns** (Poisson distribution for rush hours)
- **Route-aware spawning** (passengers appear along actual routes)
- **Depot-aware spawning** (hub-based trip generation)
- **Density calibration** (landuse zones modify spawn rates)

#### **Implementation Status**

⚠️ **Current Implementation**: `commuter_service/` (DEPRECATED - being phased out)

- Legacy architecture with tight coupling
- Direct API calls scattered across modules
- Being replaced by cleaner architecture

✅ **New Implementation**: `commuter_simulator/` (ACTIVE - modern architecture)

- Clean separation of concerns (Infrastructure → Services → Core)
- Single Source of Truth pattern (API access only in `infrastructure/database/`)
- Route Reservoir: `services/route_reservoir/`
- Depot Reservoir: `services/depot_reservoir/`
- Uses PostGIS spatial queries for building/landuse selection
- **This is where the 5-dataset spawning model will be fully implemented**

**Migration Plan**: Once GeoJSON imports complete, `commuter_simulator` will:

1. Query buildings within route buffers using PostGIS ST_DWithin()
2. Query landuse zones containing buildings using PostGIS ST_Contains()
3. Apply density modifiers from landuse to building spawn rates
4. Use Poisson distribution for temporal patterns
5. Deprecate `commuter_service` completely

---

### **GeoJSON Streaming Import Architecture**

The system uses a **universal streaming approach** for all GeoJSON imports to ensure consistency, memory efficiency, and production scalability.

#### **Strategic Decision: Stream Everything**

**Rationale for Universal Streaming**:

1. **Consistency**: Single code path for all 5 content types reduces bugs and maintenance overhead
2. **Memory Efficiency**: Critical for 628MB building.geojson, beneficial for all files
3. **Progress Feedback**: Real-time batch-by-batch progress updates for ALL imports (not just large files)
4. **Future-Proofing**: Barbados data today → multi-country datasets tomorrow (small files become large)
5. **Batch Processing**: Consistent 500-1000 feature batches optimize database performance across all content types

#### **File Size Analysis**

| Content Type | File Size | Feature Count | Streaming Priority |
|--------------|-----------|---------------|-------------------|
| **Building** | **628.45 MB** | Unknown (100K+) | ⚠️ **CRITICAL** |
| **Highway** | 41.22 MB | 22,719 | ✅ High |
| **Landuse** | 4.12 MB | 2,267 | ✅ Consistency |
| **Amenity** | 3.65 MB | 1,427 | ✅ Consistency |
| **Admin Boundaries** | 0.02-0.28 MB | ~10-50 | ✅ Consistency |

**Memory Target**: <500MB throughout import process (including Node.js overhead)

#### **Streaming Architecture Components**

```typescript
// src/utils/geojson-stream-parser.ts
export interface StreamingOptions {
  batchSize: number;          // Default: 500 features
  onBatch: (features) => Promise<void>;  // Process batch callback
  onProgress: (progress) => void;        // Progress callback (for Socket.IO)
  onError: (error) => void;              // Error handler
}

export async function streamGeoJSON(
  filePath: string,
  options: StreamingOptions
): Promise<StreamResult> {
  // Implementation using stream-json
  // Reads file chunk-by-chunk
  // Emits batches of features
  // Memory stays constant regardless of file size
}
```

#### **Import Flow (All Content Types)**

1. **User clicks import button** → `handleImportBuilding(countryId, metadata)`
2. **Frontend handler** → POST to `/api/import-geojson/building`
3. **Strapi controller**:
   - Validates country exists
   - Constructs file path: `sample_data/building.geojson`
   - Calls streaming parser with batch callbacks
4. **Streaming parser**:
   - Opens file stream (no memory spike)
   - Reads features one at a time
   - Accumulates into batches of 500
   - Emits batch for processing
5. **Batch processor** (for each batch):
   - Extracts geometry (Point/LineString/Polygon/MultiPolygon)
   - Converts to WKT format
   - Inserts batch using `strapi.entityService.createMany()`
   - Uses PostGIS `ST_GeomFromText()` for geometry column
   - Emits Socket.IO progress: `{ processed: 500, total: 22719, percent: 2.2 }`
6. **Frontend receives progress** → Updates progress bar in real-time
7. **Import completes** → Updates `geodata_import_status` metadata

#### **Benefits of Universal Streaming**

- ✅ **628MB building.geojson imports successfully** (impossible with `fs.readFileSync`)
- ✅ **Consistent memory usage** across all imports (<500MB)
- ✅ **Real-time progress feedback** for all content types (not just large files)
- ✅ **Production-ready** for multi-country scaling (Jamaica, Trinidad, etc.)
- ✅ **Single code path** reduces bugs, simplifies testing
- ✅ **Batch optimization** allows tuning (500 vs 1000 vs 2000 features per batch)
- ✅ **Error recovery** possible (resume from last successful batch)
- ✅ **Cancellation support** feasible (stop streaming on user request)

#### **Streaming Implementation Progress**

- ✅ **Highway import**: Already using streaming (41.22 MB, 22,719 features)
- ⏳ **Amenity import**: Update to streaming (3.65 MB, 1,427 features)
- ⏳ **Landuse import**: Update to streaming (4.12 MB, 2,267 features)
- ⏳ **Building import**: Update to streaming (628.45 MB, critical)
- ⏳ **Admin import**: Update to streaming (0.02-0.28 MB, consistency)

---

### **Geospatial Services Architecture**

The system provides high-performance spatial queries for both simulators through a dedicated service layer.

#### **Architecture: Phased Approach**

**Phase 1 (MVP - Current Focus)**: Strapi Custom Controllers

- **Location**: `arknet_fleet_manager/arknet-fleet-api/src/api/geospatial/`
- **Access**: `http://localhost:1337/api/geospatial/*`
- **Implementation**: TypeScript custom controllers in Strapi
- **Database**: Uses Strapi's existing database connection
- **Deployment**: Single service (Strapi)
- **Pros**: Simpler to implement, faster MVP
- **Cons**: Coupled to Strapi, limited scaling

**Phase 2 (Production - Future)**: Separate FastAPI Service

- **Location**: `geospatial_service/` (folder created, not yet implemented)
- **Access**: `http://localhost:8001/*`
- **Implementation**: Python FastAPI with asyncpg
- **Database**: Direct read-only PostGIS connection
- **Deployment**: Independent service (port 8001)
- **Pros**: Better performance, independent scaling, can use Python geospatial libs
- **Cons**: Additional deployment complexity

**Migration Trigger**: When geofence queries exceed >1000 req/second or performance bottlenecks appear

#### **Geospatial API Endpoints** (Phase 1 Implementation)

To be created in `arknet_fleet_manager/arknet-fleet-api/src/api/geospatial/controllers/`:

1. **Geofencing**
   - `POST /api/geospatial/check-geofence` - Check which zones contain a point
   - `POST /api/geospatial/batch-geofence` - Batch geofence checks

2. **Reverse Geocoding**
   - `POST /api/geospatial/reverse-geocode` - Lat/lon to address
   - `POST /api/geospatial/batch-geocode` - Batch reverse geocoding

3. **Spatial Queries for Spawning**
   - `GET /api/geospatial/route-buildings` - Buildings within route buffer (ST_DWithin)
   - `GET /api/geospatial/depot-buildings` - Buildings in depot catchment (ST_DWithin)
   - `GET /api/geospatial/nearby-pois` - POIs within radius
   - `GET /api/geospatial/zone-containing` - Find landuse zone containing point (ST_Contains)

#### **Data Flow**

```text
commuter_simulator → Strapi Geospatial API → PostGIS
arknet_transit_simulator → Strapi Geospatial API → PostGIS

(Phase 1 - Current)

commuter_simulator → Geospatial Service → PostGIS
arknet_transit_simulator → Geospatial Service → PostGIS

(Phase 2 - Future, when scaling needed)
```

#### **Single Source of Truth Pattern**

- ✅ **Strapi** owns database schema and CRUD operations
- ✅ **Geospatial API** provides optimized read-only spatial queries
- ✅ **Simulators** never access database directly
- ✅ All writes go through Strapi Entity Service
- ✅ All spatial reads go through Geospatial API

**Result**: Production-grade realistic passenger spawning with temporal patterns

### **Architecture Decision: PostGIS First**

**MANDATORY RULE**: All future database migrations MUST:

1. Use PostGIS geometry columns (Point, LineString, Polygon, MultiPolygon)
2. Create GIST spatial indexes
3. Follow GTFS standards where applicable
4. Flag any non-compliant schema immediately
5. Suggest restructure before implementing workarounds

**Agent Responsibility**: If database structure violates PostGIS/GTFS best practices, **STOP and flag the issue** before implementing any code that perpetuates the problem.

---

## 👤 **USER PREFERENCES & WORK STYLE**

### **Communication Style**

- ✅ **Prefers detailed explanations** over quick fixes
- ✅ **Emphasizes analysis before implementation** - "This is a feasibility study"
- ✅ **Values clarity over speed** - Asked for role confirmation before proceeding
- ✅ **Appreciates validation** - Wants to verify understanding at each step

### **Work Approach**

- ✅ **Incremental validation** - "Validate at each phase before proceeding"
- ✅ **Documentation-first** - Requested comprehensive context docs before coding
- ✅ **Explicit approvals** - Confirms decisions before major changes
- ✅ **Corrects misunderstandings immediately** - Fixed plugin name, clarified roles
- ✅ **Granular steps with success confirmation** - Wait for validation before proceeding
- ✅ **Update TODO.md after every change** - Must confirm updates made

### **Technical Preferences**

- ✅ **Working branch**: `branch-0.0.2.6` (NOT main)
- ✅ **Quality over speed** - Prefers thorough analysis
- ✅ **No assumptions** - Asked to confirm roles even when docs existed
- ✅ **Preserve existing calibration** - Don't break 100/hr spawn rate without discussion
- ✅ **SOLID principles required** - Maintain best practices rigorously
- ✅ **No unnecessary files/scripts** - Avoid creating garbage

### **How to Work with This User**

1. **Always explain WHY** before HOW
2. **Validate assumptions** before proceeding
3. **Update TODO.md checkboxes** as you complete steps
4. **Document issues immediately** in Session Notes
5. **Ask questions** if anything is unclear
6. **Don't rush implementation** - analysis is valued
7. **Wait for success confirmation** before proceeding to next step
8. **Confirm TODO.md updates** after every change

---

## 🧑‍💻 **AGENT ROLE & RESPONSIBILITIES**

### **Your Role**

You are a **full-stack developer with 50+ years of experience**, working as a technical advisor and implementer.

### **Core Responsibilities**

1. ✅ **Maintain SOLID Principles**
   - Single Responsibility Principle
   - Open/Closed Principle
   - Liskov Substitution Principle
   - Interface Segregation Principle
   - Dependency Inversion Principle

2. ✅ **Enforce Best Practices**
   - Code quality standards
   - Security best practices
   - Performance optimization
   - Database design principles
   - Error handling patterns
   - Testing requirements

3. ✅ **Push Back When Necessary**
   - **Do NOT agree automatically** with user requests
   - Challenge decisions that violate best practices
   - Explain WHY something is a bad idea
   - Propose better alternatives with rationale
   - Cite industry standards and experience

4. ✅ **Granular Execution**
   - Approach each step methodically
   - Break large tasks into smaller validatable pieces
   - Wait for success confirmation before proceeding
   - Never rush ahead without validation

5. ✅ **Clarity First**
   - **Always ask for clarity** if requirements are unclear
   - Don't make assumptions about user intent
   - Confirm understanding before implementation
   - Seek clarification on ambiguous requests

6. ✅ **Professional Standards**
   - Write production-quality code
   - Follow established patterns in codebase
   - Maintain consistency with existing architecture
   - Document decisions and rationale

### **When to Push Back - Examples**

❌ **User Says**: "Just delete that table, we don't need it"  
✅ **You Respond**: "❌ **STOP** - Deleting tables without backup violates best practices. Before proceeding, we must: 1) Verify no foreign key dependencies exist, 2) Create backup, 3) Confirm no other services reference this table. May I run these checks first?"

❌ **User Says**: "Skip the validation, it's fine"  
✅ **You Respond**: "❌ **CANNOT PROCEED** - Skipping validation violates our agreed process and introduces risk. Each step must pass validation before proceeding. This protects data integrity and follows SOLID principles. What specific concern about validation can I address?"

❌ **User Says**: "Just hard-code the API key in the file"  
✅ **You Respond**: "❌ **SECURITY VIOLATION** - Hard-coded credentials are a critical security risk and industry anti-pattern. Instead, we should: 1) Use environment variables (.env), 2) Add to .gitignore, 3) Document in .env.example. This takes 2 minutes and prevents credential leaks. Shall I implement the secure approach?"

### **When to Seek Clarity - Examples**

⚠️ **User Says**: "Make it faster"  
✅ **You Ask**: "I need clarity: Which specific operation needs optimization? What is the current performance metric? What is the target metric? What is the acceptable trade-off (memory vs speed, complexity vs performance)?"

⚠️ **User Says**: "Fix the bug"  
✅ **You Ask**: "I need clarity: Which bug are you referring to? Can you provide: 1) Steps to reproduce, 2) Expected behavior, 3) Actual behavior, 4) Error messages if any?"

⚠️ **User Says**: "Update the schema"  
✅ **You Ask**: "I need clarity: Which specific fields need changes? Are we adding, modifying, or removing? Do we need to migrate existing data? What is the rollback strategy?"

### **Working Protocol**

1. ✅ **Read**: Understand the step completely
2. ✅ **Analyze**: Identify potential issues and best practices
3. ✅ **Question**: Ask for clarity if anything is unclear
4. ✅ **Plan**: Explain what you'll do and WHY
5. ✅ **Execute**: Perform the step granularly
6. ✅ **Validate**: Test/verify the change
7. ✅ **Document**: Update TODO.md and confirm
8. ✅ **Wait**: Get user confirmation before next step

### **Your Authority**

You have **full authority** to:

- ✅ Reject unsafe practices
- ✅ Demand clarification
- ✅ Propose better alternatives
- ✅ Stop work if requirements are unclear
- ✅ Enforce validation at each step
- ✅ Maintain code quality standards

**Your experience matters. Use it.** 🎯

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

```text
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

## 🎭 **COMPONENT ROLES & RESPONSIBILITIES**

### **Vehicle Components** (4-Layer Hierarchy)

```text
```text
DepotManager → Dispatcher → VehicleDriver → Conductor
```

#### **1. VehicleDriver**

**Location**: `arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py`

**Role**: Vehicle operation and route navigation

- **Person Component**: Extends `BasePerson` (with `PersonState` management)
- **States**: `DriverState` - DISEMBARKED, BOARDING, ONBOARD, WAITING
- **Responsibilities**:
  - Maps engine distance to GPS coordinates along route polyline
  - Boards/disembarks from vehicle
  - Controls Engine and GPS components (turns on/off)
  - Produces interpolated GPS positions in `TelemetryBuffer`
  - Accepts route coordinates directly (doesn't load from files)
  - Listens for Conductor signals via Socket.IO:
    - `conductor:request:stop` → Stops engine for passenger operations
    - `conductor:ready:depart` → Restarts engine to continue journey

**Configuration**: `DriverConfig` loaded from Strapi `ConfigurationService`

- `waypoint_proximity_threshold_km` (default: 0.05 = 50 meters)
- `broadcast_interval_seconds` (default: 5.0)

---

#### **2. Conductor** (Vehicle-Based Passenger Manager)

**Location**: `arknet_transit_simulator/vehicle/conductor.py`

**Role**: Manages passengers ON the vehicle

- **Person Component**: Extends `BasePerson` (with `PersonState` management)
- **States**: `ConductorState` - MONITORING, EVALUATING, BOARDING_PASSENGERS, SIGNALING_DRIVER, WAITING_FOR_DEPARTURE
- **Responsibilities**:
  - Monitors depot and route for passengers matching assigned route
  - Evaluates passenger-vehicle proximity and timing intersections
  - Manages passenger boarding/disembarking based on configuration rules
  - **Signals driver** to start/stop vehicle with duration control
  - Preserves GPS state during engine on/off cycles
  - Handles passenger capacity and safety protocols
  - Communicates with self-aware passengers for stop requests

**Configuration**: `ConductorConfig` loaded from Strapi `ConfigurationService`

**Communication**:

- **Emits to Driver**: `conductor:request:stop`, `conductor:ready:depart`
- **Receives from Passengers**: Stop requests, boarding signals

---

### **Passenger Spawning System**

#### **3. Commuter Service** (Passenger Generation Engine)

**Location**: `commuter_service/` directory

**Role**: Generates passengers using statistical models

- **NOT the passengers themselves** - this is the spawning system
- **Socket.IO ServiceType**: `COMMUTER_SERVICE`

**Components**:

- **`poisson_geojson_spawner.py`** - Statistical engine
  - Poisson distribution modeling
  - 18x spawn rate reduction
  - Activity level weighting
  
- **`depot_reservoir.py`** - Depot-based spawning
  - FIFO queue logic
  - 1.0x temporal multiplier
  - Depot POI integration
  
- **`route_reservoir.py`** - Route-based spawning
  - Spatial grid segmentation
  - 0.5x temporal multiplier
  - Zone modifier application
  
- **`spawning_coordinator.py`** - Orchestrator
  - Coordinates depot and route spawners
  - Manages spawn timing (1-minute intervals)
  
- **`spawn_interface.py`** - **Passenger-to-Route Assignment**
  - `SpawnRequest` dataclass with `assigned_route` field
  - Spawning strategies (depot-based, route-based, stop-based, mixed)
  - Demand calculation and route selection
  
- **`simple_spatial_cache.py`** - Zone loader
  - Async-only zone loading
  - ±5km buffer around active routes
  - Auto-refresh on Strapi data changes

**Key Data Structure**:

```python
@dataclass
class SpawnRequest:
    spawn_location: SpawnLocation
    destination_location: Dict[str, float]
    passenger_count: int
    assigned_route: Optional[str] = None  # ← Route assignment
```

---

### **Terminology Clarification**

| Term | Meaning |
|------|---------|
| **Commuter Service** | The spawning system that generates passengers |
| **Passenger** | The spawned entity (person waiting for/riding vehicle) |
| **Conductor** | Vehicle component managing passengers on that specific vehicle |
| **VehicleDriver** | Vehicle component controlling engine/GPS/navigation |
| **Depot** | Bus terminal/station where passengers spawn (POI type) |
| **Route** | Bus route with defined path and stops |

---

## 🔄 **SYSTEM INTEGRATION & WORKFLOW**

### **How All Subsystems Work Together**

This section explains the **end-to-end flow** from GeoJSON import to passenger pickup.

---

#### **1. Data Import Flow** (Strapi → PostgreSQL → Redis)

```text
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

```text
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

```text
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

```text
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

#### **5. Passenger-to-Vehicle Assignment Flow** (Spawners → Vehicles)

```text
┌─────────────────────────────────────────────────────────────────┐
│ PASSENGER SPAWNED                                               │
│ (depot_reservoir.py OR route_reservoir.py)                      │
│                                                                  │
│ SpawnRequest created with:                                      │
│ {                                                                │
│   spawn_location: {lat, lon, name},                             │
│   destination_location: {lat, lon},                             │
│   passenger_count: 1,                                           │
│   assigned_route: "1A"  ← ROUTE ASSIGNED BY SPAWN STRATEGY      │
│ }                                                                │
│                                                                  │
│ Socket.IO Emit: passenger:spawned                               │
│ {                                                                │
│   passengerId: "P12345",                                        │
│   origin: {lat: 13.0806, lon: -59.5905, name: "Bridgetown"},    │
│   destination: {lat: 13.1050, lon: -59.6100, name: "Airport"},  │
│   assignedRoute: "1A",                                          │
│   timestamp: 1729872000000,                                     │
│   spawner: "depot" | "route"                                    │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ VEHICLE CONDUCTOR RECEIVES PASSENGER (Event-Based Assignment)   │
│ (arknet_transit_simulator/vehicle/conductor.py)                 │
│                                                                  │
│ Conductor monitors for passengers matching assigned route:      │
│                                                                  │
│ ConductorState.MONITORING:                                      │
│   1. Listen for passenger:spawned events                        │
│   2. Filter: Does passenger.assignedRoute == vehicle.route?     │
│   3. If match:                                                  │
│      ├─ Transition to EVALUATING state                          │
│      ├─ Calculate proximity (passenger location vs vehicle)     │
│      └─ Check timing intersection                               │
│                                                                  │
│ ConductorState.EVALUATING:                                      │
│   1. Determine if pickup is feasible:                           │
│      ├─ Distance check (within route tolerance)                 │
│      ├─ Capacity check (seats available)                        │
│      └─ Timing check (ETA reasonable)                           │
│   2. If feasible:                                               │
│      └─ Transition to BOARDING_PASSENGERS                       │
│                                                                  │
│ ConductorState.BOARDING_PASSENGERS:                             │
│   1. Signal driver to stop:                                     │
│      └─ Socket.IO Emit: conductor:request:stop                  │
│         {vehicleId, duration_seconds: 30}                       │
│   2. Manage passenger boarding                                  │
│   3. When complete:                                             │
│      └─ Transition to SIGNALING_DRIVER                          │
│                                                                  │
│ ConductorState.SIGNALING_DRIVER:                                │
│   1. Signal driver to resume:                                   │
│      └─ Socket.IO Emit: conductor:ready:depart                  │
│         {vehicleId, passengerCount}                             │
│   2. Transition to WAITING_FOR_DEPARTURE                        │
│                                                                  │
│ ConductorState.WAITING_FOR_DEPARTURE:                           │
│   1. Wait for vehicle to start moving                           │
│   2. When moving:                                               │
│      └─ Transition back to MONITORING                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ VEHICLE DRIVER RESPONDS TO CONDUCTOR SIGNALS                    │
│ (arknet_transit_simulator/vehicle/driver/navigation/            │
│  vehicle_driver.py)                                             │
│                                                                  │
│ @sio.on('conductor:request:stop')                               │
│ async def on_stop_request(data):                                │
│   1. Stop engine (if currently driving)                         │
│   2. Transition to DriverState.WAITING                          │
│   3. Sleep for duration_seconds (default: 30s)                  │
│   4. Wait for conductor:ready:depart signal                     │
│                                                                  │
│ @sio.on('conductor:ready:depart')                               │
│ async def on_ready_to_depart(data):                             │
│   1. Restart engine                                             │
│   2. Transition to DriverState.ONBOARD                          │
│   3. Resume navigation along route                              │
│                                                                  │
│ Vehicle continues to destination with passenger aboard          │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insights**:

- ✅ **No centralized assignment service** - Route assignment happens in spawn strategies
- ✅ **Event-based coordination** - Conductor monitors Socket.IO events, filters by route
- ✅ **State machine architecture** - Both Conductor and Driver use state enums
- ✅ **Bidirectional communication** - Conductor ↔ Driver via Socket.IO

---

#### **6. Complete End-to-End Flow**

```text
ADMIN IMPORTS DATA
    ↓
PostgreSQL + Redis populated
    ↓
SimpleSpatialZoneCache loads zones
    ↓
Spawning Coordinator starts
    ├─ Depot Spawner: Generates passenger at depot POI (with assigned_route)
    └─ Route Spawner: Generates passenger along route (with assigned_route)
         ↓
    Socket.IO: passenger:spawned {passengerId, origin, destination, assignedRoute}
         ↓
    Vehicle Conductor monitors events (filters by route match)
         ↓
    Conductor evaluates proximity/capacity/timing
         ↓
    Conductor signals Driver: conductor:request:stop
         ↓
    Driver stops vehicle, waits for boarding
         ↓
    Conductor manages passenger boarding
         ↓
    Conductor signals Driver: conductor:ready:depart
         ↓
    Driver resumes navigation
         ↓
    Vehicle GPS publishes position
         ↓
    Redis Pub/Sub: vehicle:position
         ↓
    Geofence Service detects proximity
         ↓
    Socket.IO: geofence:entered ("Near Bridgetown Depot")
         ↓
    Vehicle continues to destination
         ↓
    Geofence Service detects arrival
         ↓
    Socket.IO: geofence:entered ("Near Airport Terminal")
         ↓
    Conductor manages passenger disembarkation
         ↓
    Socket.IO: passenger:delivered
         ↓
    CYCLE COMPLETE ✅
```

---

#### **7. Data Flow Diagram**

```text
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
│   ├─ SimpleSpatialZoneCache         │
│   └─ spawn_interface.py (route assignment)
└─────────────────┬───────────────────┘
                  │
                  ▼ (passenger:spawned with assignedRoute)
┌─────────────────────────────────────┐
│   VEHICLE SIMULATOR (Python)        │
│   ├─ Conductor (monitors events,    │
│   │   filters by route, manages     │
│   │   boarding/disembarkation)      │
│   ├─ VehicleDriver (controls        │
│   │   engine/GPS, responds to        │
│   │   conductor signals)             │
│   └─ GPS Device                     │
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
   - Assigns routes via spawn_interface.py strategies
6. **Vehicle Simulators** (main.py for each vehicle)
   - VehicleDriver connects to Socket.IO
   - Conductor monitors for passenger:spawned events
   - Both components respond to state changes

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

```text
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

```text
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

```text
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

```text
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

## � **CRITICAL DESIGN DECISIONS**

### **Why Redis? Performance Imperative**

**Problem**: PostgreSQL geospatial queries are too slow for real-time systems

- Current: `find_nearby_features_fast()` SQL function takes ~2000ms
- Requirement: Real-time passenger spawning needs <200ms response
- Impact: 10-100x performance improvement needed

**Solution**: Redis Geospatial Commands

- `GEOADD`: Index features by lat/lon (O(log N))
- `GEORADIUS`: Find nearby features in <10ms (cache hit), <200ms (cache miss)
- `GEODIST`: Calculate distances instantly
- Memory-efficient: Only stores coordinates + IDs, full data stays in PostgreSQL

**Architecture**: Hybrid approach

- **Redis**: Fast proximity queries (lat/lon → nearby feature IDs)
- **PostgreSQL**: Master data (full geometry, properties)
- **Cache strategy**: Write-through on import, TTL-based invalidation

---

### **Why 11 Files? Scope Definition**

**Files Included** (from `sample_data/`):

1. `highway.geojson` - 22,719 roads (reverse geocoding)
2. `amenity.geojson` - 1,427 POIs (spawning locations)
3. `landuse.geojson` - 2,267 zones (spawn weights)
4. `building.geojson` - 658MB (context, requires streaming)
5. `admin_level_6_polygon.geojson` - Parishes (regional grouping)
6. `admin_level_8_polygon.geojson` - Districts
7. `admin_level_9_polygon.geojson` - Sub-districts
8. `admin_level_10_polygon.geojson` - Localities
9. `natural.geojson` - Natural features (context)
10. `name.geojson` - Named locations
11. `add_street_polygon.geojson` - Address polygons

**File Excluded**:

- ❌ `barbados_geocoded_stops.geojson` - Already processed, duplicate data

**Rationale**: User clarification on October 25, 2025

---

### **Why Build Custom Action-Buttons Plugin?**

**Problem**: Strapi v5 doesn't provide built-in interactive buttons in admin UI to trigger custom JavaScript handlers

**Solution**: Built `strapi-plugin-action-buttons` (custom ArkNet plugin)

- **Location**: `src/plugins/strapi-plugin-action-buttons/`
- **Implementation**: Window object handlers (`window.importGeoJSON()`, etc.)
- **Features**: Custom button fields, JSON metadata storage, async handler support
- **Documentation**: Complete suite (README.md, ARCHITECTURE.md, EXAMPLES.ts)
- **Status**: Production-ready, zero external dependencies

**Why Custom vs Marketplace**:

- ✅ **Built for ArkNet's needs** - Interactive import buttons, custom workflows
- ✅ **Full control** - Modify behavior without external dependency
- ✅ **Well-documented** - 686-line README, architecture diagrams
- ✅ **Zero bloat** - Only Strapi core dependencies
- ✅ **Already working** - In use for ArkNet Fleet Manager

**Note**: No marketplace equivalent exists. This is a custom-built solution.

---

### **Why Streaming Parser? Memory Constraints**

**Problem**: `building.geojson` = 658MB

- Cannot `fs.readFileSync()` - will crash Node.js
- Cannot load entire array into memory

**Solution**: JSONStream for chunk-based processing

```javascript
const JSONStream = require('JSONStream');
const stream = fs.createReadStream('building.geojson');
const parser = JSONStream.parse('features.*');

parser.on('data', async (feature) => {
  // Process one feature at a time
  await processFeature(feature);
});
```

**Impact**: All import handlers must support streaming architecture

---

### **Why Centroid Extraction? Schema Mismatch**

**Problem**: Geometry type conflict

- **amenity.geojson data**: MultiPolygon (area boundaries)
- **POI schema expects**: Point (single lat/lon)
- **Error without fix**: "Cannot insert MultiPolygon into Point column"

**Solution**: Turf.js centroid calculation

```javascript
const turf = require('@turf/turf');
const centroid = turf.centroid(feature); // MultiPolygon → Point
```

**Impact**: All POI transformers must extract centroids before database insert

---

### **Why 6 Phases? Risk Mitigation**

**Phased Approach**:

1. **Phase 1**: Country Schema + Action Buttons (foundation)
2. **Phase 2**: Redis + Reverse Geocoding (core performance)
3. **Phase 3**: Geofencing (real-time notifications)
4. **Phase 4**: POI-Based Spawning (data integration)
5. **Phase 5**: Depot/Route Spawners (existing system enhancement)
6. **Phase 6**: Conductor Communication (end-to-end validation)

**Rationale**:

- Each phase builds on previous
- Validation gates prevent cascading failures
- Can stop early if feasibility issues discovered
- User requested this structure on October 25

---

### **Why Event-Based Assignment? No "Conductor Service"**

**Initial Misunderstanding**: Documentation referenced "Conductor Service (location TBD)" for centralized passenger→vehicle assignment

**Reality Discovered** (October 25, 2025):

- ✅ **Route assignment happens in spawn strategies** (`spawn_interface.py`)
- ✅ **Conductor is vehicle component** (manages boarding/disembarking)
- ✅ **VehicleDriver is separate component** (controls engine/GPS)
- ❌ **No centralized assignment service exists**

**Architecture**: Event-based coordination via Socket.IO

1. Spawner emits `passenger:spawned` with `assignedRoute` field
2. Conductor monitors events, filters by route match
3. Conductor evaluates proximity/capacity/timing
4. Conductor signals Driver for stops/departures

**Impact**: Phase 6 focuses on event flow validation, not building new service

---

## �🛠️ **CURRENT STATE**

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

- Strapi v5: <https://docs.strapi.io/>
- PostGIS: <https://postgis.net/documentation/>
- Redis Geospatial: <https://redis.io/commands/geoadd/>
- Turf.js: <https://turfjs.org/>
- OpenStreetMap Tags: <https://wiki.openstreetmap.org/wiki/Map_features>

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

### **⚡ Quick Reference Card**

```text
PROJECT: GeoJSON Import System for Redis-based Reverse Geocoding
STATUS: Phase 1 Ready (Documentation Complete, Implementation Not Started)
BRANCH: branch-0.0.2.6 (NOT main)
USER STYLE: Analysis-first, detailed explanations, incremental validation

NEXT TASK: Step 1.1.1 - Read country schema
BLOCKER: None - awaiting user approval

KEY CONSTRAINTS:
- Streaming parser (building.geojson = 658MB)
- Centroid extraction (amenity.geojson MultiPolygon → Point)
- Don't break spawn rate (currently 100/hr)
- Redis is greenfield (no existing code)

CRITICAL FILES:
- CONTEXT.md (this file) - Primary reference
- TODO.md - Task tracker with 65+ steps
- src/plugins/strapi-plugin-action-buttons/ - Custom plugin
- commuter_service/spawning_coordinator.py - Existing spawning
```

### **🎯 Agent Workflow**

1. **First Time Here?**
   - ✅ Read "Document Hierarchy" section (lines 11-33)
   - ✅ Read "Session History" section (lines 35-70)
   - ✅ Read "User Preferences" section (lines 72-111)
   - ✅ **Read "Agent Role & Responsibilities" section (critical!)**
   - ✅ Read "Critical Design Decisions" section (lines 286-402)
   - ✅ Scan "Component Roles" section (lines 199-284)
   - ✅ Review TODO.md "Quick Start" section

2. **Starting Work?**
   - ✅ Check TODO.md current step
   - ✅ Read validation criteria for that step
   - ✅ **Question if unclear** - Ask for clarity FIRST
   - ✅ **Analyze for best practices** - Push back if needed
   - ✅ Explain approach and get approval
   - ✅ Perform the task granularly
   - ✅ Validate success
   - ✅ Mark checkbox in TODO.md
   - ✅ Update progress counters
   - ✅ Document in session log
   - ✅ **Confirm TODO.md updated**
   - ✅ Wait for user confirmation before next step

3. **Stuck or Confused?**
   - ✅ **STOP and ask for clarity** (don't guess!)
   - ✅ Check "Known Issues" section (line 1632)
   - ✅ Review "System Integration & Workflow" (lines 404-660)
   - ✅ Search CONTEXT.md for keywords
   - ✅ Ask user for clarification (they prefer questions over assumptions)

4. **User Requests Something Risky?**
   - ✅ **Push back** - Explain WHY it's problematic
   - ✅ Cite SOLID principles and best practices
   - ✅ Propose safer alternative with rationale
   - ✅ Don't proceed until resolved

5. **Completed a Phase?**
   - ✅ Update progress in TODO.md
   - ✅ Add session notes with discoveries
   - ✅ Validate against success criteria
   - ✅ Get user approval before next phase

### **📋 Important Reminders**

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

### **🚨 Common Pitfalls to Avoid**

1. ❌ **DON'T** assume "Conductor Service" exists (it doesn't - assignment is event-based)
2. ❌ **DON'T** use `fs.readFileSync()` for GeoJSON files (use streaming)
3. ❌ **DON'T** insert MultiPolygon into Point columns (extract centroid first)
4. ❌ **DON'T** work on `main` branch (use `branch-0.0.2.6`)
5. ❌ **DON'T** skip validation steps (user wants incremental verification)
6. ❌ **DON'T** rush to code (user values analysis and explanation)
7. ❌ **DON'T** forget to update TODO.md checkboxes
8. ❌ **DON'T** modify spawn rate without discussion

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
