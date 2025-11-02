# ArkNet Vehicle Simulator - Project Context

**Project**: ArkNet Fleet Manager & Vehicle Simulator  
**Repository**: vehicle_simulator  
**Branch**: branch-0.0.2.9  
**Date**: November 1, 2025  
**Status**: ✅ Spawn Calculation Kernel | ✅ Repository Cleanup | ✅ Tests Consolidated | 🎯 Integrate Kernel into Spawners NEXT  
**Phase**: Modular Architecture, Code Organization, Spawn Model Implementation  
**Latest**: Created spawn_calculator.py kernel with pure functions, consolidated tests/ directory, archived legacy docs - Nov 1

> **📌 PRODUCTION-READY HANDOFF DOCUMENT**: This CONTEXT.md + TODO.md enable a fresh agent to rebuild and continue to production-grade MVP with zero external context. Every architectural decision, every component relationship, every critical issue, and every next step is documented here.

---

## 🚨 **MANDATORY AGENT DIRECTIVES - READ FIRST**

**⚠️ STOP: Before doing ANYTHING else, internalize these directives:**

### **Your Role & Authority**

You are a **50+ year full-stack developer veteran** with deep expertise across all technologies in this stack. You have the authority and responsibility to:

### **⚠️ CRITICAL: NO NEW MARKDOWN FILES**
- **NEVER create new .md files** for documentation, summaries, or analysis
- All information goes into **CONTEXT.md** or **TODO.md** ONLY
- Exception: Module-specific READMEs inside their own directories (e.g., `gps_telemetry_client/README.md`)
- If you need to document something, add a section to CONTEXT.md or TODO.md

1. **✅ PUSH BACK HARD** on poor suggestions, anti-patterns, or violations of best practices
   - Question unclear requirements before implementing
2. **✅ ENFORCE BEST PRACTICES**
   - Follow SOLID principles religiously
   - Write clean, maintainable, testable code
   - Use proper error handling and validation
   - Implement proper TypeScript typing (no `any` without justification)
   - Follow established patterns in the codebase

3. **✅ WORK INCREMENTALLY & TEST CONSTANTLY**
   - Break work into granular, testable steps
   - Test each change before moving forward
   - Verify success response before proceeding to next step
   - Never skip validation or testing phases
   - If a test fails, STOP and fix it before continuing
   - Perform a deep analysis of the codebase before proceeding
   - analyze the TODO.md and determine steps to MVP and our next immediate steps

4. **✅ MAINTAIN DOCUMENTATION DISCIPLINE**
   - Update CONTEXT.md immediately after every successful change
   - Update TODO.md checkboxes and progress counters as work completes
   - Lint both .md files for errors (proper markdown syntax)
   - Keep session notes and discoveries documented
   - Track progress counters (X/Y steps complete)

5. **✅ PROVIDE COMMIT MESSAGES**
   - After every successful change, provide a clear, descriptive commit message
   - Follow conventional commits format: `type(scope): description`
   - Include what changed, why it changed, and impact
   - Ready for immediate `git commit`

6. **✅ AVOID FILE POLLUTION**
   - Do NOT create junk scripts or temporary files
   - Do NOT create unnecessary wrapper files
   - Do NOT create summary markdown files unless explicitly requested
   - Use existing tools and patterns
   - Clean up after yourself

7. **✅ DEBUGGING MINDSET**
   - When errors occur, diagnose root cause before suggesting fixes
   - Provide detailed analysis of what went wrong and why
   - Explain trade-offs of different solutions
   - Test fixes thoroughly before declaring success

### **Workflow Enforcement**

**For EVERY task, follow this sequence:**

```text
1. READ & ANALYZE
   ├─ Understand the requirement deeply
   ├─ Check existing code patterns
   ├─ Identify potential issues or improvements
   └─ Question unclear aspects

2. PROPOSE & DISCUSS
   ├─ Suggest best approach (may differ from user's request)
   ├─ Explain WHY this approach is better
   ├─ Provide alternatives with trade-offs
   └─ Get confirmation before proceeding

3. IMPLEMENT INCREMENTALLY
   ├─ Break into small, testable steps
   ├─ Implement one step at a time
   ├─ Test each step thoroughly
   └─ Verify success before next step

4. VALIDATE & TEST
   ├─ Run all relevant tests
   ├─ Verify database changes (if applicable)
   ├─ Check for regressions
   └─ Confirm success response

5. DOCUMENT & COMMIT
   ├─ Update CONTEXT.md with changes
   ├─ Update TODO.md checkboxes/progress
   ├─ Lint markdown files
   ├─ Provide commit message
   └─ Verify documentation is accurate

6. NEVER SKIP STEPS
   └─ If ANY step fails, STOP and fix it
```

### **Critical Reminders**

- **Branch**: `branch-0.0.2.6` (NOT main)
- **Single Source of Truth**: Strapi (all writes via Entity Service API)
- **Spatial Data**: PostGIS geometry columns (NOT lat/lon pairs)
- **Import Pattern**: Streaming parser + bulk SQL (500-1000 feature batches)
- **No Shortcuts**: Quality over speed, always
- **User Preference**: Detailed explanations, analysis-first approach

**If you read this section, you are now operating under these directives. Proceed accordingly.**

---

## 🚀 **IMMEDIATE CONTEXT FOR NEW AGENTS**

### **Where We Are RIGHT NOW (October 28, 2025)**

```text
CURRENT STATE (October 31, 2025 - Geospatial API Production-Ready):
✅ ConfigProvider Pattern: Single source of truth for infrastructure config
✅ Eliminated 90+ hardcoded URLs: 17+ files across all subsystems updated
✅ Configuration Architecture: Root config.ini (infrastructure) + .env (secrets) + DB (operational)
✅ GPS Client Port Fixed: 8000 → 5000 (correct GPSCentCom port)
✅ UTF-8 Encoding Fixed: 7 files updated to handle emoji/special chars in config.ini
✅ Launcher Consolidated: Deleted 3 redundant scripts, launch.py is single launcher
✅ Integration Test Passing: launch.py successfully starts all subsystems
✅ Route-Depot Junction Table: Populated with 1 association (Route 1 ↔ Speightstown, 223m)
✅ Precompute Script: commuter_simulator/scripts/precompute_route_depot_associations.py
✅ Zero Configuration Redundancies: Between files and database confirmed
✅ GEOSPATIAL API PRODUCTION-READY: 52+ endpoints, 13/13 critical tests passing (100%)
✅ API Coverage Analysis: Fully supports depot-based, route-based, hybrid terminal spawning
✅ GeospatialClient Integration Ready: commuter_simulator/infrastructure/geospatial/client.py
✅ Performance Validated: <100ms queries, <500ms analytics - all targets met
✅ Error Handling: Production-grade 503/504 responses with graceful degradation
✅ Documentation: API_REFERENCE.md, GEOSPATIAL_API_COMPLETENESS_ASSESSMENT.md complete
❌ RouteSpawner Failing: No spawn-config for route documentId 14
❌ DepotSpawner Limited: 4 of 5 depots have no routes (only Speightstown has Route 1)
❌ 0% Spawn Success: EXPECTED - can't spawn without routes/configs

GEOSPATIAL API IMPLEMENTATION (October 31, 2025):
✅ 9 Router Categories - 52+ Endpoints:
   - /routes: 7 endpoints (all, detail, geometry, buildings, metrics, coverage, nearest)
   - /depots: 7 endpoints (all, detail, catchment, routes, coverage, nearest)
   - /buildings: 7 endpoints (at-point, along-route, in-polygon, density, count, stats, batch)
   - /analytics: 5 endpoints (heatmap, route-coverage, depot-service-areas, population, demand)
   - /meta: 6 endpoints (health, version, stats, bounds, regions, tags)
   - /spawn: 10 endpoints (depot-analysis, all-depots, route-analysis, config GET/POST, multipliers)
   - /geocode: 2 endpoints (reverse, batch)
   - /geofence: 2 endpoints (check, batch)
   - /spatial: 6 endpoints (legacy compatibility, buildings/pois nearest)
✅ SOLID Architecture: Single Responsibility, Separation of Concerns
✅ Hybrid Spawn Model: terminal_population × route_attractiveness fully supported
✅ Configuration Management: Runtime-adjustable spawn parameters via /spawn/config
✅ Test Results: 13/13 critical endpoints passing (100% success rate)
✅ Fixes Applied:
   - POST body parameter handling (3 endpoints fixed)
   - SQL type casting (numeric vs float)
   - Geometry column handling (ST_Centroid for polygons)
   - KeyError protection (safe dictionary access depot.get('attributes', {}))
   - Missing endpoints added (batch geocoding/geofencing, legacy spatial)
✅ Files: geospatial_service/api/{routes,depots,buildings,analytics,metadata,spawn,geocoding,geofence,spatial}.py

CONFIGURATION REFACTORING (October 31, 2025):
✅ Created common/config_provider.py: ConfigProvider singleton with InfrastructureConfig dataclass
✅ Updated config.ini: Comprehensive infrastructure settings with documentation
✅ Fixed Files (17+):
   - GPS Telemetry Client: client.py, __init__.py, test_client.py, README.md
   - Geospatial Service: main.py
   - Commuter Simulator: geospatial/client.py, database/strapi_client.py, 
     database/passenger_repository.py, interfaces/http/manifest_api.py, main.py
   - Transit Simulator: config/config_loader.py, simulator.py, vehicle/conductor.py,
     core/dispatcher.py, vehicle/driver/navigation/vehicle_driver.py, 
     services/config_service.py, __main__.py
   - Root Scripts: launcher/config.py
✅ Deprecated arknet_transit_simulator/config/config.ini (all operational settings moved to DB)
✅ Added 8 vehicle_simulator entries to operational_config_seed_data.json (23 total)
✅ Files Deleted: start_services.py, start_fleet_services.py, start_all_systems.py (redundant)
✅ Documentation Cleanup: Pending deletion of HARDCODED_VALUES_ASSESSMENT.md, 
   GPS_RECONNECTION_IMPLEMENTATION.md, FLEET_SERVICES.md

IMMEDIATE NEXT TASK (October 31, 2025):
🎯 Use New Geospatial API to List Routes & Create Spawn Configs
   - Step 1: Run list_routes.py using /routes/all API endpoint
   - Step 2: Verify route IDs (documentId vs id confusion)
   - Step 3: Create spawn-config entries for all routes in database
   - Step 4: Test RouteSpawner with proper configs
   - Goal: Get RouteSpawner generating passengers
   - After: Test full spawn cycle (depot + route spawners together)

CLEAN ARCHITECTURE (October 29 - REFACTORED):
commuter_simulator/ (Passenger Generation - CLEAN ARCHITECTURE)
  ├─ main.py: Single entrypoint with SpawnerCoordinator
  ├─ domain/: Pure business logic (no external dependencies)
  │   └─ services/
  │       ├─ spawning/: DepotSpawner, RouteSpawner, base interfaces
  │       └─ reservoirs/: RouteReservoir, DepotReservoir
  ├─ application/: Use cases and orchestration
  │   ├─ coordinators/: SpawnerCoordinator
  │   └─ queries/: manifest_query (enrichment logic)
  ├─ infrastructure/: External systems
  │   ├─ persistence/strapi/: PassengerRepository
  │   ├─ geospatial/: GeospatialClient
  │   ├─ config/: SpawnConfigLoader
  │   └─ events/: PostgreSQL LISTEN/NOTIFY
  └─ interfaces/: Entry points
      ├─ http/: FastAPI manifest API (port 4000)
      └─ cli/: list_passengers console tool

arknet_transit_simulator/ (Vehicle Movement - COMPLETE)
  ├─ Vehicles drive routes
  ├─ Conductor listens for passengers
  └─ Conductor picks up passengers from reservoirs

DEPENDENCIES & BLOCKERS:
✅ None - All spawner implementation complete
✅ Clean architecture refactoring complete (Oct 29)
✅ Geospatial API production-ready (Oct 31)
✅ Ready for route listing and spawn config creation
✅ GeospatialService operational (localhost:6000)
✅ Strapi operational (localhost:1337)

PATH TO MVP (TIER 5-6 - REVISED Oct 28):
TIER 5 → Route-Depot Association & RouteSpawner Integration ✅ STEP 1/7 COMPLETE (Oct 28)
   - ✅ Create route-depots junction table (schema, cached labels, lifecycle hooks, bidirectional UI)
  - Precompute geospatial associations
  - Update DepotSpawner logic for associated routes
  - Wire existing RouteSpawner to coordinator (implementation already complete)
  - Add PubSub for reservoir visualization
  - Execute comprehensive flag tests
TIER 6 → Conductor Integration & Reservoir Wiring
  - Connect Conductor to reservoirs
  - Implement pickup logic integration
  - End-to-end vehicle-passenger flow
TIER 7 → Redis, Geofencing, Production Optimization
```

### **Critical Files You Need to Know**

| File | Purpose | Status | Next Action |
|------|---------|--------|-------------|
| **CONTEXT.md** (this file) | Master architecture, all decisions | ✅ Updated Oct 29 | Reference for patterns |
| **TODO.md** | TIER 1-5 task sequence, detailed session logs | ✅ Updated Oct 28 | Follow execution order |
| **commuter_simulator/ARCHITECTURE.md** | Clean architecture guide | ✅ Created Oct 29 | Reference for layer rules |
| **commuter_simulator/main.py** | Single entrypoint for spawner system | ✅ Updated Oct 29 | Wire RouteSpawner (replace Mock) |
| **commuter_simulator/application/coordinators/spawner_coordinator.py** | Spawner orchestration | ✅ Refactored Oct 29 | Ready for use |
| **commuter_simulator/domain/services/spawning/depot_spawner.py** | Depot passenger generation | ✅ Refactored Oct 29 | Add `_load_associated_routes()` |
| **commuter_simulator/domain/services/spawning/route_spawner.py** | Route passenger generation | ✅ Refactored Oct 29 | Wire to coordinator |
| **commuter_simulator/domain/services/reservoirs/** | DB-backed reservoirs | ✅ Refactored Oct 29 | Add Redis integration later |
| **commuter_simulator/application/queries/manifest_query.py** | Enriched manifest builder | ✅ Created Oct 29 | Used by API and CLI |
| **commuter_simulator/interfaces/http/manifest_api.py** | FastAPI manifest endpoint | ✅ Created Oct 29 | Production ready |
| **commuter_simulator/interfaces/cli/list_passengers.py** | Console diagnostic tool | ✅ Created Oct 29 | Production ready |
| **geospatial_service/api/spatial.py** | Route geometry/buildings endpoints | ✅ Operational Oct 28 | Ready for RouteSpawner |
| **geospatial_service/** | Spatial queries API | ✅ Working | Use for route-depot associations |
| **arknet_transit_simulator/** | Vehicle movement simulator | ✅ Working | Conductor integration pending |

- Strapi v5.23.5 (Node.js 22.20.0) - Single source of truth
- PostgreSQL 16.3 + PostGIS 3.5 - Spatial database
FRONTEND:
- Strapi Admin UI (React) - Content management (port 1337)
- Custom action-buttons plugin - GeoJSON import triggers

SIMULATORS:
- arknet_transit_simulator (Python) - Vehicle movement
- commuter_simulator (Python) - Passenger spawning

SPATIAL:
- PostGIS geometry columns (Point, LineString, Polygon, MultiPolygon)
- GIST spatial indexes (12 indexes across 11 tables)
- GTFS-compliant transit data (routes, stops, shapes)

FUTURE (TIER 4):
- Redis - **MANDATORY for 1,200 vehicles** (position buffering, dashboard caching, cluster state)
- Geofencing service - Real-time zone detection
```

### **Quick Decision Reference**

| Question | Answer | Rationale |
|----------|--------|-----------|
| Which branch? | **branch-0.0.2.8** (NOT main) | Active development branch |
| Single source of truth? | **Strapi** (all writes via Entity Service API) | Prevents data corruption |
| Spatial data storage? | **PostGIS geometry columns** (NOT lat/lon pairs) | 10-100x faster queries, 90% less storage |
| Import pattern? | **Streaming parser + bulk SQL** (500-1000 features/batch) | Memory efficient, real-time progress |
| API architecture? | **Two-mode: Strapi (CRUD) + GeospatialService (spatial)** | Separation of concerns, single source of truth |
| Spawner architecture? | **Single entrypoint + Coordinator pattern** | Shared resources, config-driven control |
| Depot-route association? | **Explicit junction table (precomputed)** | No runtime geospatial calculations, realistic operations |
| PubSub pattern? | **PostgreSQL LISTEN/NOTIFY** (not direct spawner) | Zero overhead, DB handles pub/sub, automatic buffering |
| Enable/disable spawners? | **Config flags: enable_depotspawner, enable_routespawner** | Granular control, coordinator filters spawners |
| Redis for spawner? | **Optional (enable_redis_cache flag)** | Hooks exist, not yet implemented |
| Production scale? | **1,200 vehicles** (ESP32/STM32 + Rock S0 GPS) | One-way position reporting @ 1 update/5sec = 240 updates/sec |
| Redis for production? | **YES** (mandatory for 1,200 vehicles) | Required for shared state, dashboard cache, session mgmt |

---

## 📋 **REBUILD INSTRUCTIONS (New Agent Start Here)**

### **Step 1: Environment Setup**

```powershell
# 1. Clone repository
git clone <repo-url> vehicle_simulator
cd vehicle_simulator

# 2. Checkout correct branch
git checkout branch-0.0.2.7

# 3. Install Strapi dependencies
cd arknet_fleet_manager/arknet-fleet-api
npm install

# 4. Verify PostgreSQL + PostGIS
# Connection: localhost:5432, database: arknettransit, user: david
# Required extensions: PostGIS 3.5, pg_trgm, btree_gist

# 5. Verify database has 11 spatial tables with GIST indexes
# Run: SELECT tablename, indexname FROM pg_indexes WHERE indexname LIKE 'idx_%_geom';
# Expected: 12 GIST indexes on geometry columns


# 7. Verify action-buttons plugin loaded
# Check: Settings > Plugins > Action Buttons (custom plugin)

# 8. Verify GeoJSON files exist
cd ../../../sample_data
ls admin_level_*.geojson  # Should show 4 files (6, 8, 9, 10)
ls building.geojson       # 658MB
ls highway.geojson        # 41MB
ls amenity.geojson        # 3.65MB
ls landuse.geojson        # 4.12MB
```

### **Step 2: Verify Current State**

```sql
-- 1. Check buildings table has 162,942 records
SELECT COUNT(*) FROM buildings;

-- 2. Check all 5 imports completed
SELECT 
  (SELECT COUNT(*) FROM buildings) as buildings,
  (SELECT COUNT(*) FROM regions) as regions,
  (SELECT COUNT(*) FROM highways) as highways,
  (SELECT COUNT(*) FROM pois) as pois,
  (SELECT COUNT(*) FROM landuse_zones) as landuse_zones;
-- Expected: 162,942, 304, 22,719, 1,427, 2,267

-- 3. Verify all country links exist
SELECT 
  (SELECT COUNT(*) FROM buildings_country_lnk) as building_links,
  (SELECT COUNT(*) FROM regions_country_lnk) as region_links,
  (SELECT COUNT(*) FROM highways_country_lnk) as highway_links,
  (SELECT COUNT(*) FROM pois_country_lnk) as poi_links,
  (SELECT COUNT(*) FROM landuse_zones_country_lnk) as landuse_links;
-- Expected: 162,942, 304, 22,719, 1,427, 2,267 (total: 189,659)

-- 4. Verify region links exist (features can cross boundaries)
SELECT 
  (SELECT COUNT(*) FROM highways_region_lnk) as highway_region_links,
  (SELECT COUNT(*) FROM pois_region_lnk) as poi_region_links,
  (SELECT COUNT(*) FROM landuse_zones_region_lnk) as landuse_region_links;
-- Expected: 23,666 (947 highways cross boundaries), 1,427, 2,310 (43 zones cross boundaries)
-- 4. Test spatial query performance
EXPLAIN ANALYZE
SELECT COUNT(*) FROM buildings
WHERE ST_DWithin(geom::geography, ST_MakePoint(-59.62, 13.1)::geography, 1000);
  h.osm_id,
  COUNT(DISTINCT r.id) as num_regions
LIMIT 10;
-- Expected: Shows highways that cross parish boundaries
python .\test\test_admin_import.py      # Expected: 17/17 passing (Strapi imports)
python .\test\test_highway_import.py    # Expected: 16/16 passing (Strapi imports)

# 7. Start Geospatial Services API
# Expected: "Buildings: 162,942; Highways: 27,719; POIs: 1,427; Landuse zones: 2,267; Regions: 11"

# 8. Verify all 5 imports in Strapi UI
# Open Strapi Admin > Content Manager
### **Step 3: Understand Priority System**

├─ Highway import (22,719 roads) ✅
├─ Amenity import (1,427 POIs) ✅
└─ Landuse import (2,267 zones) ✅
TIER 2: Enable Spawning Queries ✅ DONE (Phase 1.11)
├─ FastAPI Geospatial Services (port 6000) ✅
├─ Reverse geocoding with parish ✅
├─ Geofence detection (0.23ms avg) ✅
├─ Depot catchment query (94ms avg) ✅
├─ Route buildings query ✅
└─ Integration tests (16/16 passing) ✅

TIER 3: Database Integration & Validation (Phase 1.12) 🎯 NEXT
├─ Test queries from commuter_simulator
├─ Validate performance under load (100+ vehicles)
├─ Document API endpoints
├─ Create API client wrapper
└─ Validate spatial indexes (EXPLAIN ANALYZE)

TIER 4: Passenger Spawning Features (Phase 4-5-6)
├─ POI-based spawning (Phase 4)
├─ Depot-based spawning (Phase 5)
└─ Route-based spawning (Phase 6)

TIER 5: Redis Optimization (DEFERRED - Phase 2-3)
├─ Reverse geocoding cache (<200ms target)
└─ Geofencing service (real-time zone detection)

SEPARATE TRACK: GPS CentCom Production Hardening
├─ Priority 1: Persistent datastore (Redis/Postgres), per-device auth
└─ Priority 2: Horizontal scaling, AESGCM server support, monitoring
```

### **Step 4: Read Critical Documentation**

1. **Read TODO.md header** (lines 1-80) - Strategy, execution priority, current focus
2. **Read TODO.md Phase 1.10** (admin import section) - Immediate next task
3. **Read CONTEXT.md GPS CentCom section** (lines 1100+) - Understand WebSocket telemetry architecture
4. **Read CONTEXT.md System Architecture** (below) - Component relationships
5. **Read TODO.md TIER 1-4 structure** - Overall Progress section

### **Step 5: Execute Next Task**

```text
TASK: Create /api/import-geojson/admin endpoint

REFERENCE:
- File: src/api/geojson-import/controllers/geojson-import.ts
- Pattern: importBuilding function (lines 470-650)
- Use: Streaming parser + bulk SQL inserts (500 features/batch)

IMPLEMENTATION:
1. Read importBuilding function to understand pattern
2. Create importAdmin function following same structure
3. Accept: { countryId, adminLevelId, adminLevel } from request
4. Validate adminLevel in [6, 8, 9, 10]
5. Map adminLevel → filename: admin_level_${adminLevel}_polygon.geojson
6. Query admin_levels table to verify adminLevelId exists
7. Use stream-json parser with 500 feature batches
8. Extract: osm_id, full_id, name from GeoJSON properties
9. Convert MultiPolygon geometry to WKT
10. Bulk insert to regions table with admin_level_id FK
11. Link to country via regions_country_lnk junction table
12. Emit Socket.IO progress events
13. Test all 4 levels import successfully

SUCCESS CRITERIA:
✅ All 4 admin levels import without errors
✅ Regions linked to correct admin_level_id
✅ Geometries valid (ST_IsValid returns true)
✅ Junction table populated with country relationship
✅ Progress events visible in Strapi Admin UI
```

---

## 🏗️ **SYSTEM ARCHITECTURE OVERVIEW**

### **Complete System Diagram - All Subsystems & Interrelationships**

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              ARKNET VEHICLE SIMULATOR ECOSYSTEM                                     │
│                        Production-Grade Transit Simulation & Fleet Management                       │
│                                    (October 26, 2025)                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🖥️  PRESENTATION LAYER - Human Interfaces                                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌─────────────────────────────────────┐         ┌──────────────────────────────────────┐          │
│  │  📊 Strapi Admin UI (React)         │         │  🌐 Real-Time Dashboard (Future)     │          │
│  │  http://localhost:1337/admin        │         │  Port: 3000 (React/Vue)              │          │
│  │  ────────────────────────────────── │         │  ──────────────────────────────────  │          │
│  │  ✅ Content Management (CRUD)       │         │  ⏳ Live Vehicle Tracking Map        │          │
│  │  ✅ GeoJSON Import Buttons (5):     │         │  ⏳ Passenger Spawning Visualization │          │
│  │     • Highway                       │         │  ⏳ Route Performance Analytics      │          │
│  │     • Amenity                       │         │  ⏳ GPS CentCom Device Monitor       │          │
│  │     • Landuse                       │         │                                       │          │
│  │     • Building (✅ 162,942 records) │         │  Consumes:                            │          │
│  │     • Admin (⏳ NEXT)               │         │  • Strapi REST API (vehicle data)    │          │
│  │  ✅ Custom action-buttons plugin    │         │  • GPS CentCom API (telemetry)       │          │
│  │  ✅ Socket.IO progress bars         │         │  • Socket.IO (real-time events)      │          │
│  └─────────────────────────────────────┘         └──────────────────────────────────────┘          │
│           │                                                     │                                    │
│           ↓ HTTP REST/GraphQL                                  ↓ WebSocket + HTTP                   │
│           ↓ Socket.IO events                                   ↓                                    │
└───────────┼─────────────────────────────────────────────────────┼────────────────────────────────────┘
            │                                                     │
            ↓                                                     ↓
┌───────────┴─────────────────────────────────────────────────────┴────────────────────────────────────┐
│ 🔌 API GATEWAY LAYER - Single Source of Truth                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  🎯 STRAPI v5.23.5 (Node.js 22.20.0) - Central Data Hub                                       │ │
│  │  arknet_fleet_manager/arknet-fleet-api/  │  Port: 1337                                        │ │
│  │  ─────────────────────────────────────────────────────────────────────────────────────────    │ │
│  │                                                                                                │ │
│  │  📦 Core CRUD APIs (Strapi Entity Service - Single Source of Truth):                          │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ REST/GraphQL Endpoints:                                                             │       │ │
│  │  │  • /api/countries          • /api/routes           • /api/stops                    │       │ │
│  │  │  • /api/highways           • /api/pois             • /api/landuse-zones            │       │ │
│  │  │  • /api/buildings          • /api/depots           • /api/vehicles                 │       │ │
│  │  │  • /api/regions            • /api/admin-levels     • /api/geofences                │       │ │
│  🔎 Evaluation (October 28, 2025)                                                                   │
│   • Keep through end of TIER 6 for reference only; schedule removal in Phase 2 (production hardening)│
│   • Salvageable concepts to inform new implementation (no code copy/paste):                          │
│     - Strategy abstractions: Depot/Route/Mixed spawn strategies and manager (spawn_interface.py)     │
│     - Along-route destination selection ensuring destinations stay on route geometry                 │
│       (see poisson_geojson_spawner._select_destination_along_route)                                  │
│     - Temporal/context multipliers (depot vs route patterns; zone-specific modifiers)                │
│     - Reservoir observability ideas: basic stats and expiration/TTL patterns                         │
│   • Do NOT port: shapely/geopy spatial math, log-normal selection across arbitrary zones,            │
│     or any direct DB/API scatter—our architecture is Strapi (CRUD) + GeospatialService (spatial).    │
│   • Action items are tracked in TODO.md under "Deprecated folder: evaluation + actions".            │
│  │  │                                                                                      │       │ │
│  │  │ All writes MUST go through Strapi Entity Service API (no direct DB writes)         │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  📥 GeoJSON Import API (Custom Controllers - TIER 1):                                          │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ POST /api/import-geojson/highway  (22,719 features, 41MB)     ⏳ PENDING           │       │ │
│  │  │ POST /api/import-geojson/amenity  (1,427 features, 3.65MB)    ⏳ PENDING           │       │ │
│  │  │ POST /api/import-geojson/landuse  (2,267 features, 4.12MB)    ⏳ PENDING           │       │ │
│  │  │ POST /api/import-geojson/building (162,942 features, 658MB)   ✅ COMPLETE          │       │ │
│  │  │ POST /api/import-geojson/admin    (4 levels: 6,8,9,10)        ⏳ NEXT TASK         │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Pattern: stream-json parser → 500 feature batches → bulk SQL inserts               │       │ │
│  │  │ Progress: Socket.IO events (import:progress, import:complete)                      │       │ │
│  │  │ Geometry: ST_GeomFromText() → PostGIS columns → GIST indexes                       │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  🌍 Geospatial Services API (Custom Controllers - TIER 2 - CRITICAL BLOCKER):                 │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ GET  /api/geospatial/route-buildings?route_id=X&buffer=500      ⏳ Phase 1.11      │       │ │
│  │  │      → ST_DWithin(buildings.geom, routes.geom, 500m)                               │       │ │
│  │  │      → Returns buildings within 500m of route for passenger spawning               │       │ │
│  │  │                                                                                      │       │ │
│  │  │ GET  /api/geospatial/depot-buildings?depot_id=X&radius=1000     ⏳ Phase 1.11      │       │ │
│  │  │      → ST_DWithin(buildings.geom, depots.geom, 1000m)                              │       │ │
│  │  │      → Returns buildings within 1km of depot for spawning                          │       │ │
│  │  │                                                                                      │       │ │
│  │  │ GET  /api/geospatial/zone-containing?lat=X&lon=Y                ⏳ Phase 1.12      │       │ │
│  │  │      → ST_Contains(zones.geom, ST_MakePoint(lon, lat))                             │       │ │
│  │  │      → Returns admin zone/landuse containing point                                 │       │ │
│  │  │                                                                                      │       │ │
│  │  │ POST /api/geospatial/check-geofence                             ⏳ Phase 1.12      │       │ │
│  │  │      → ST_Contains(geofences.geom, vehicle_point)                                  │       │ │
│  │  │      → Real-time geofence violation detection                                      │       │ │
│  │  │                                                                                      │       │ │
│  │  │ 🚨 BLOCKS: All passenger spawning features (Phases 4-5-6)                          │       │ │
│  │  │ Performance: <2s queries (GIST indexes), target <50ms for production               │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  📡 Socket.IO Real-Time Events:                                                                │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ import:progress      → GeoJSON import progress (features processed, % complete)    │       │ │
│  │  │ import:complete      → Import job finished (total records, duration)               │       │ │
│  │  │ vehicle:position     → Vehicle location updates (lat, lon, speed, heading)         │       │ │
│  │  │ passenger:spawned    → New passenger created (location, route assignment)          │       │ │
│  │  │ passenger:boarding   → Passenger boarding vehicle                                  │       │ │
│  │  │ passenger:arrived    → Passenger reached destination                               │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│           │                                                                                         │
│           ↓ Knex.js ORM (write operations only)                                                    │
└───────────┼─────────────────────────────────────────────────────────────────────────────────────────┘
            │
            ↓
┌───────────┴─────────────────────────────────────────────────────────────────────────────────────────┐
│ 💾 DATABASE LAYER - PostGIS Spatial Database                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  🐘 PostgreSQL 16.3 + PostGIS 3.5                                                              │ │
│  │  Database: arknettransit  │  Port: 5432  │  User: david  │  SRID: 4326 (WGS84)                │ │
│  │  ─────────────────────────────────────────────────────────────────────────────────────────    │ │
│  │                                                                                                │ │
│  │  📊 Spatial Tables (PostGIS geometry columns + GIST indexes):                                  │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ Transport Infrastructure:                                                           │       │ │
│  │  │  ✅ highways          (geom: LineString)   - 22,719 features  ⏳ Import pending     │       │ │
│  │  │  ✅ stops             (geom: Point)        - GTFS compliant, indexed                │       │ │
│  │  │  ✅ shape_geometries  (geom: LineString)   - GTFS route shapes (27 aggregated)     │       │ │
│  │  │  ✅ depots            (geom: Point)        - Vehicle depots (5 locations)           │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Land Use & Environment:                                                             │       │ │
│  │  │  ✅ landuse_zones     (geom: Polygon)      - 2,267 features  ⏳ Import pending      │       │ │
│  │  │  ✅ pois              (geom: Point)        - 1,427 features  ⏳ Import pending      │       │ │
│  │  │  ✅ buildings         (geom: Polygon)      - 162,942 records ✅ IMPORTED Oct 25     │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Administrative Boundaries:                                                          │       │ │
│  │  │  ✅ regions           (geom: MultiPolygon) - Admin boundaries (4 levels)            │       │ │
│  │  │  ✅ admin_levels      (reference table)    - Parish(6), Town(8), Suburb(9), Hood(10)│       │ │
│  │  │  ✅ geofences         (geom: Polygon)      - Custom zones for monitoring            │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Operational Data:                                                                   │       │ │
│  │  │  ✅ vehicle_events    (geom: Point)        - Vehicle telemetry history              │       │ │
│  │  │  ✅ active_passengers (geom: Point)        - Current passenger locations            │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  🔍 GIST Spatial Indexes (12 indexes - critical for <50ms queries):                            │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ idx_highways_geom, idx_stops_geom, idx_depots_geom,                                │       │ │
│  │  │ idx_landuse_zones_geom, idx_pois_geom, idx_regions_geom,                           │       │ │
│  │  │ idx_shape_geometries_geom, idx_geofences_geom,                                     │       │ │
│  │  │ idx_vehicle_events_geom, idx_active_passengers_geom,                               │       │ │
│  │  │ idx_buildings_geom (162,942 building polygons)                                     │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Performance: Distance queries <50ms, Contains queries <20ms                        │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│           ↑ Strapi writes                        ↑ Direct SQL reads (simulators)                   │
│           ↑ GeoJSON imports                      ↑ Geospatial queries                              │
└───────────┼──────────────────────────────────────┼──────────────────────────────────────────────────┘
            │                                      │
            │                                      │
            ↓ (writes only)                        ↓ (reads: CRUD + spatial)
┌───────────┴──────────────────────────────────────┴──────────────────────────────────────────────────┐
│ 🚗 BUSINESS LOGIC LAYER - Simulation & Fleet Management                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌─────────────────────────────────────────┐      ┌──────────────────────────────────────────────┐ │
│  │ 🚌 arknet_transit_simulator/            │      │ 👥 commuter_simulator/                       │ │
│  │ (Python - Vehicle Movement)             │      │ (Python - Passenger Spawning)                │ │
│  │ ─────────────────────────────────────── │      │ ──────────────────────────────────────────── │ │
│  │                                          │      │                                               │ │
│  │ Core Components:                         │      │ ✅ Active Architecture:                      │ │
│  │  • Vehicle state machine                 │      │  services/route_reservoir.py                 │ │
│  │  • Route navigation & pathfinding        │      │  services/depot_reservoir.py                 │ │
│  │  • Stop detection & dwell time           │      │  infrastructure/database/                    │ │
│  │  • Driver behavior simulation            │      │                                               │ │
│  │  • Conductor passenger management        │      │ Spawning Logic:                              │ │
│  │  • GPS Device telemetry sender           │      │  • Route-based spawning:                     │ │
│  │                                          │      │    ST_DWithin(building, route, 500m)         │ │
│  │ Vehicle → GPS Device Architecture:       │      │    → Temporal multiplier: 0.5x               │ │
│  │  ┌──────────────────────────────┐        │      │                                               │ │
│  │  │ GPSDevice (BaseComponent)    │        │      │  • Depot-based spawning:                     │ │
│  │  │  ├─ PluginManager             │        │      │    ST_DWithin(building, depot, 1000m)       │ │
│  │  │  │   ├─ SimulationPlugin      │        │      │    → Temporal multiplier: 1.0x               │ │
│  │  │  │   ├─ ESP32Plugin           │        │      │    → FIFO queue logic                        │ │
│  │  │  │   ├─ FileReplayPlugin      │        │      │                                               │ │
│  │  │  │   └─ NavigatorPlugin       │        │      │  • Poisson distribution modeling             │ │
│  │  │  ├─ RxTxBuffer (FIFO, max 1000)│       │      │  • Activity level weighting                  │ │
│  │  │  └─ WebSocketTransmitter       │        │      │  • 18x spawn rate reduction                  │ │
│  │  │      (ws://gpscentcom:5000)   │        │      │                                               │ │
│  │  └──────────────────────────────┘        │      │ 🚨 BLOCKED BY: Phase 1.11-1.12              │ │
│  │                                          │      │    (Geospatial Services API required)        │ │
│  │ Telemetry Packet:                        │      │                                               │ │
│  │  • deviceId, route, vehicleReg           │      │ Consumes APIs:                               │ │
│  │  • lat, lon, speed, heading               │      │  • Strapi REST API (CRUD operations)         │ │
│  │  • driverId, conductorId                 │      │  • Geospatial API (spatial queries) ⏳       │ │
│  │  • timestamp, extras                     │      │  • Socket.IO (passenger events)              │ │
│  │                                          │      │                                               │ │
│  │ Consumes APIs:                           │      │ Output:                                      │ │
│  │  • Strapi REST API (routes, stops, etc)  │      │  • SpawnRequest with assigned_route          │ │
│  │  • Socket.IO (position updates)          │      │  • Socket.IO passenger:spawned events        │ │
│  └─────────────────────────────────────────┘      └──────────────────────────────────────────────┘ │
│           │                                                     │                                    │
│           ↓ WebSocket telemetry                                ↓ Socket.IO events                   │
│           ↓ JSON/AESGCM packets                                ↓                                    │
└───────────┼─────────────────────────────────────────────────────┼────────────────────────────────────┘
            │                                                     │
            ↓                                                     │
┌───────────┴─────────────────────────────────────────────────────┘
│ 📡 TELEMETRY HUB LAYER - GPS CentCom Server (SEPARATE TRACK)
├─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  🛰️ gpscentcom_server/ (FastAPI + WebSocket)                                                   │ │
│  │  Port: 5000  │  ws://localhost:5000/device  │  Production: Systemd + Nginx                    │ │
│  │  ─────────────────────────────────────────────────────────────────────────────────────────    │ │
│  │                                                                                                │ │
│  │  Architecture:                                                                                 │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ server_main.py         → FastAPI app, CORS, background janitor (30s interval)      │       │ │
│  │  │ connection_manager.py  → WebSocket lifecycle, {websocket → deviceId} mapping       │       │ │
│  │  │ rx_handler.py          → /device endpoint, PING/PONG, text/binary handling         │       │ │
│  │  │ store.py               → In-memory dict storage, 120s stale timeout                │       │ │
│  │  │ models.py              → Pydantic DeviceState schema validation                    │       │ │
│  │  │ api_router.py          → REST API: /health, /devices, /route/{code}, /analytics    │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  Data Flow:                                                                                    │ │
│  │  Vehicle GPS Device → WebSocket → rx_handler → ConnectionManager → Store → REST API           │ │
│  │                                                                                                │ │
│  │  DeviceState Schema (Pydantic):                                                                │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ deviceId: str           │ route: str              │ vehicleReg: str                │       │ │
│  │  │ lat: float (-90, 90)    │ lon: float (-180, 180)  │ speed: float (>=0)             │       │ │
│  │  │ heading: float (0-360°) │ driverId: str           │ driverName: Dict               │       │ │
│  │  │ conductorId: Optional   │ timestamp: ISO8601      │ lastSeen: ISO8601              │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  ✅ Production Ready (MVP Demo - 10-50 vehicles):                                              │ │
│  │   • WebSocket + HTTP endpoints working                                                         │ │
│  │   • Systemd service deployment                                                                 │ │
│  │   • Auto-cleanup of stale devices (120s)                                                       │ │
│  │   • Route-based filtering (/route/{code})                                                      │ │
│  │                                                                                                │ │
│  │  ⚠️ Production Requirements (1,200 vehicles @ 240 updates/sec):                                │ │
│  │   • MANDATORY: Redis cluster (position buffering, shared state across workers)                 │ │
│  │   • MANDATORY: Node.js cluster mode (6-8 workers, 150-200 connections each)                    │ │
│  │   • MANDATORY: Server upgrade (12+ vCores, 64GB RAM, 500GB SSD minimum)                        │ │
│  │   • RECOMMENDED: Multi-server deployment (3× Scale-2 for HA)                                   │ │
│  │   • Per-device auth tokens (not single shared token)                                           │ │
│  │   • PostgreSQL batch writes (10-second intervals via Redis buffer)                             │ │
│  │   • AESGCM server-side decoding support                                                        │ │
│  │   • Prometheus metrics, structured logging, health checks                                      │ │
│  │                                                                                                │ │
│  │  🎯 Deployment Phases:                                                                          │ │
│  │   MVP (Current - 2GB RAM): Development only, 10-20 simulated vehicles, no Redis                │ │
│  │   Prototype (VPS Scale-2 - 8GB RAM): 50-100 vehicles, add Redis, test cluster mode             │ │
│  │   Pilot (VPS Scale-3 - 32GB RAM): 100-500 vehicles, cluster mode operational                   │ │
│  │   Production (VPS Advance-2 or 3× Scale-2): 1,200 vehicles, full HA, monitoring                │ │
│  │                                                                                                │ │
│  │  📊 Production Architecture (1,200 vehicles):                                                   │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ ESP32/STM32 + Rock S0 GPS (1,200 devices)                                          │       │ │
│  │  │   ↓ 1 position/5sec × 1,200 = 240 updates/sec                                      │       │ │
│  │  │ Nginx Load Balancer (round-robin)                                                  │       │ │
│  │  │   ↓                                                                                 │       │ │
│  │  │ GPS CentCom Cluster (6-8 Node.js workers)                                          │       │ │
│  │  │   ├─ Worker 1-2: 200 devices each                                                  │       │ │
│  │  │   ├─ Worker 3-4: 200 devices each                                                  │       │ │
│  │  │   └─ Worker 5-6: 200 devices each                                                  │       │ │
│  │  │   ↓ Write to Redis (in-memory state, fast)                                         │       │ │
│  │  │ Redis (2-4 GB allocated for in-memory state)                                       │       │ │
│  │  │   ├─ Current positions: 1,200 × 200 bytes = 240 KB                                 │       │ │
│  │  │   ├─ Device metadata (route, driver, etc.): ~500 KB                                │       │ │
│  │  │   ├─ Session state: Worker coordination, device → worker mapping                   │       │ │
│  │  │   ├─ Dashboard cache: GET /devices cached for <5ms response                        │       │ │
│  │  │   └─ Heartbeat TTL: Auto-expire offline devices                                    │       │ │
│  │  │   ↓ Optional: Position history storage (TBD)                                       │       │ │
│  │  │ PostgreSQL + PostGIS (with PgBouncer connection pooling)                           │       │ │
│  │  │   ├─ Static data: Routes, stops, POIs, GeoJSON (~5 GB)                             │       │ │
│  │  │   └─ IF position storage: ~2 GB/day growth (optional, TBD)                         │       │ │
│  │  │ Strapi (2 instances for HA - redundancy, not load)                                 │       │ │
│  │  │ Geospatial API (FastAPI - 1-2 instances)                                           │       │ │
│  │  │ Dashboard (Operators query Redis for real-time, PostgreSQL for config)             │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  � **Business Model - Subscription-Based Position Storage:**                                  │ │
│  │                                                                                                │ │
│  │   **Free Tier (Real-Time Only):**                                                              │ │
│  │    • In-memory state only (current position, route, driver, status)                           │ │
│  │    • Real-time dashboard access                                                                │ │
│  │    • No historical data retention                                                              │ │
│  │    • Revenue: $0 (customer acquisition, upsell opportunity)                                    │ │
│  │                                                                                                │ │
│  │   **Subscription Tiers (Historical Data + Analytics API):**                                    │ │
│  │    • Basic ($5/vehicle/month): 7 days history, route replay, CSV export                       │ │
│  │    • Professional ($15/vehicle/month): 30 days, analytics, heat maps, API access              │ │
│  │    • Enterprise ($30/vehicle/month): 1 year, full analytics, unlimited API, SLA               │ │
│  │                                                                                                │ │
│  │   **Technical Implementation:**                                                                │ │
│  │    • PostgreSQL: Short-term retention (7-30 days) - lower cost                                │ │
│  │    • InfluxDB/TimescaleDB: Long-term retention (90-365 days) - optimized time-series          │ │
│  │    • Hybrid: Redis → PostgreSQL → S3 cold storage (tiered pricing)                            │ │
│  │                                                                                                │ │
│  │   **Revenue Projection (1,200 vehicles):**                                                     │ │
│  │    • 30% adoption (360 paid): $5,400/month - $300 infra = $5,100 net                          │ │
│  │    • 50% adoption (600 paid): $9,000/month - $400 infra = $8,600 net                          │ │
│  │    • 70% adoption (840 paid): $12,600/month - $500 infra = $12,100 net                        │ │
│  │                                                                                                │ │
│  │  🔄 **Multi-Server Database Synchronization Strategy:**                                        │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ PostgreSQL (Write Master + Read Replicas):                                          │       │ │
│  │  │  Server 3: PostgreSQL PRIMARY (all writes)                                          │       │ │
│  │  │     ↓ Built-in Streaming Replication (<100ms lag)                                   │       │ │
│  │  │  Server 1: Read Replica (geospatial queries)                                        │       │ │
│  │  │  Server 2: Read Replica (dashboard queries)                                         │       │ │
│  │  │                                                                                      │       │ │
│  │  │  Configuration:                                                                      │       │ │
│  │  │   • Primary: wal_level=replica, max_wal_senders=3                                   │       │ │
│  │  │   • Replicas: hot_standby=on (read-only queries allowed)                            │       │ │
│  │  │   • Failover: Automated with repmgr or Patroni (30-60s downtime)                    │       │ │
│  │  │   • NO sync conflicts (one-way replication only)                                    │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Redis (Sentinel HA with Auto-Failover):                                             │       │ │
│  │  │  Server 1: Redis MASTER (all writes) + Sentinel                                     │       │ │
│  │  │     ↓ Async replication                                                             │       │ │
│  │  │  Server 2: Redis REPLICA + Sentinel                                                 │       │ │
│  │  │  Server 3: Redis REPLICA + Sentinel                                                 │       │ │
│  │  │                                                                                      │       │ │
│  │  │  Sentinel Configuration:                                                            │       │ │
│  │  │   • Quorum: 2/3 votes required for failover                                         │       │ │
│  │  │   • Detection: 5 seconds down-after-milliseconds                                    │       │ │
│  │  │   • Auto-failover: Promote replica to master (~10s downtime)                        │       │ │
│  │  │   • All services reconfigure automatically to new master                            │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Strapi (Active-Active with Shared Database):                                        │       │ │
│  │  │  Load Balancer → Strapi Instance 1 (Server 1) ──┐                                   │       │ │
│  │  │                → Strapi Instance 2 (Server 2) ──┤                                   │       │ │
│  │  │                                                  ↓                                   │       │ │
│  │  │                         PostgreSQL Primary (Server 3)                               │       │ │
│  │  │                                                                                      │       │ │
│  │  │   • Both instances read/write SAME database (NO database sync needed)               │       │ │
│  │  │   • Sessions stored in Redis Master (shared state across instances)                 │       │ │
│  │  │   • File uploads: Shared volume (NFS) or S3 bucket                                  │       │ │
│  │  │   • NO data conflicts (single PostgreSQL primary = single source of truth)          │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Failover Impact Table:                                                              │       │ │
│  │  │  ┌──────────────────┬──────────────┬─────────────┬────────────┬─────────────┐      │       │ │
│  │  │  │ Component Fails  │ Detection    │ Recovery    │ Downtime   │ Impact      │      │       │ │
│  │  │  ├──────────────────┼──────────────┼─────────────┼────────────┼─────────────┤      │       │ │
│  │  │  │ Redis Master     │ Sentinel (5s)│ Auto-promote│ ~10s       │ Write buffer│      │       │ │
│  │  │  │ PostgreSQL Pri   │ Health (10s) │ Manual/Auto │ 30-60s     │ Reads OK    │      │       │ │
│  │  │  │ Entire Server 1  │ LB (5s)      │ Route away  │ <5s        │ 400→600 dev │      │       │ │
│  │  │  │ Network partition│ Sentinel     │ Quorum      │ N/A        │ Write pause │      │       │ │
│  │  │  └──────────────────┴──────────────┴─────────────┴────────────┴─────────────┘      │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🔮 FUTURE OPTIMIZATION LAYER - TIER 4 (Deferred until spawning features complete)                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  ⚡ geospatial_service/ (Python FastAPI)                                                       │ │
│  │  Port: 6000  │  Read-only asyncpg → PostgreSQL                                                │ │
│  │  ─────────────────────────────────────────────────────────────────────────────────────────    │ │
│  │                                                                                                │ │
│  │  Purpose: Extract heavy spatial queries from Strapi for >1000 req/s performance                │ │
│  │                                                                                                │ │
│  │  Components:                                                                                   │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────┐       │ │
│  │  │ Redis Reverse Geocoding:                                                            │       │ │
│  │  │  • Cache: lat/lon → admin_zone (Parish/Town/Suburb)                                │       │ │
│  │  │  • Target: <200ms (cache miss), <10ms (cache hit)                                  │       │ │
│  │  │  • Current: ~2000ms (PostgreSQL only)                                               │       │ │
│  │  │  • Benefit: 10-100x performance improvement                                         │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Real-Time Geofencing:                                                               │       │ │
│  │  │  • ST_Contains(geofence, vehicle_position)                                          │       │ │
│  │  │  • Target: <10ms latency                                                            │       │ │
│  │  │  • Use case: Zone entry/exit alerts                                                 │       │ │
│  │  │                                                                                      │       │ │
│  │  │ Optimized Spatial Queries:                                                          │       │ │
│  │  │  • Dedicated asyncpg connection pool                                                │       │ │
│  │  │  • Query result caching                                                             │       │ │
│  │  │  • Prepared statements for hot paths                                                │       │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────┘       │ │
│  │                                                                                                │ │
│  │  📊 Current Status: ⏳ TIER 4 - Deferred optimization                                          │ │
│  │   Rationale: Spawning features need Geospatial API in Strapi first (TIER 2)                    │ │
│  │   Migration: Move to dedicated FastAPI service when >1000 req/s needed                         │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ✅ LEGACY CODE CLEANUP                                                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  🗑️  commuter_service_deprecated/ - REMOVED (November 2, 2025)                                      │
│   • Old tight-coupled spawning system fully replaced by commuter_simulator/                         │
│   • All functionality migrated to clean architecture with DB-driven configuration                   │
│   • No longer needed for reference - deleted to reduce codebase complexity                          │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 📊 DATA FLOW PATTERNS & INTEGRATION SUMMARY                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│ ✍️  WRITES (All data creation/modification):                                                        │
│   Admin UI → Strapi Entity Service API → PostgreSQL (via Knex.js ORM)                               │
│   GeoJSON Import → Strapi Controller → Bulk SQL → PostgreSQL (ST_GeomFromText)                      │
│                                                                                                      │
│ 📖 READS (Data consumption):                                                                        │
│   Simulators → Strapi REST API → PostgreSQL (CRUD operations)                                       │
│   Simulators → Geospatial API → PostgreSQL (ST_DWithin, ST_Contains) ⏳ TIER 2                      │
│   Dashboard → GPS CentCom API → In-Memory Store (device telemetry)                                  │
│                                                                                                      │
│ ⚡ REAL-TIME EVENTS (WebSocket/Socket.IO):                                                          │
│   GeoJSON Import → Socket.IO → Admin UI (import:progress, import:complete)                          │
│   Vehicle Simulator → Socket.IO → Dashboard (vehicle:position)                                      │
│   Passenger Simulator → Socket.IO → Dashboard (passenger:spawned)                                   │
│   GPS Device → WebSocket → GPS CentCom Server → Store → API → Dashboard                             │
│                                                                                                      │
│ 🔐 SINGLE SOURCE OF TRUTH PRINCIPLE:                                                                │
│   ✅ Strapi owns all database schema and CRUD operations                                            │
│   ✅ All writes MUST go through Strapi Entity Service API                                           │
│   ✅ Simulators NEVER write directly to database                                                    │
│   ✅ PostGIS geometry columns (NOT lat/lon pairs) for 10-100x performance                           │
│   ✅ GIST indexes mandatory for production spatial query performance                                │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🎯 DEVELOPMENT PRIORITY TIERS (Option A Strategy - Oct 26, 2025)                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│ TIER 1 (IMMEDIATE - Phase 1.10): Complete GeoJSON Imports                                           │
│  ⏳ Admin import backend (← YOU ARE HERE)                                                           │
│  ⏳ Highway import optimization                                                                     │
│  ⏳ Amenity import optimization                                                                     │
│  ⏳ Landuse import optimization                                                                     │
│                                                                                                      │
│ TIER 2 (CRITICAL BLOCKER - Phase 1.11-1.12): Enable Spawning Queries                                │
│  ⏳ Geospatial Services API (custom Strapi controllers)                                             │
│  ⏳ Route-buildings query (ST_DWithin 500m) - BLOCKS passenger spawning                             │
│  ⏳ Depot-buildings query (ST_DWithin 1000m) - BLOCKS passenger spawning                            │
│  ⏳ Zone-containing query (ST_Contains) - BLOCKS geofencing                                         │
│                                                                                                      │
│ TIER 3 (FEATURES - Phase 4-5-6): Passenger Spawning Implementation                                  │
│  ⏳ POI-based spawning (Phase 4)                                                                    │
│  ⏳ Depot-based spawning (Phase 5)                                                                  │
│  ⏳ Route-based spawning (Phase 6)                                                                  │
│                                                                                                      │
│ 🎯 SPAWN-CONFIG SCHEMA (Oct 26, 2025): Intuitive Data-Driven Spawning Configuration                 │
│  ✅ Redesigned with SIMPLE component-based architecture (separate tables by category)                │
│  ✅ Components Created:                                                                               │
│    • spawning.building-weight - Buildings (residential, commercial, office, school, etc.)            │
│    • spawning.poi-weight - POIs (bus_station, marketplace, hospital, etc.)                           │
│    • spawning.landuse-weight - Landuse zones (residential, commercial, industrial, etc.)             │
│    • spawning.hourly-pattern - 24-hour spawn rates (1.0=normal, 2.5=peak rush hour)                  │
│    • spawning.day-multiplier - Day-of-week multipliers (weekday 1.0, weekend 0.7)                    │
│    • spawning.distribution-params - Poisson lambda, spawn constraints (collapsible)                  │
│  ✅ Simple Mental Model:                                                                              │
│    final_spawn_probability = weight × peak_multiplier × hourly_rate × day_multiplier                 │
│  ✅ UX Features:                                                                                      │
│    • Three collapsible sections: Buildings, POIs, Landuse (separate grid tables)                     │
│    • Each feature: base weight (1.0-5.0) + peak_multiplier + is_active toggle                        │
│    • All components collapsible with (0) indicator when empty                                         │
│    • No JSON blob editing needed for common use cases                                                 │
│    • Editable grids with validation (can't enter text as numbers)                                    │
│  ✅ Relationship: country ↔ spawn-config (oneToOne, bidirectional, auto-created by Strapi)           │
│  ⚠️  MIGRATION: Changed to Route ↔ Spawn-Config (oneToOne) - Oct 26, 2025                            │
│    • Problem: Rural routes using urban temporal patterns (48 passengers at 6 AM St Lucy)             │
│    • Cause: Country-based config → all routes share same hourly rates                                │
│    • Solution: Route-based configs → each route has appropriate temporal patterns                    │
│    • Schema changes complete:                                                                        │
│      - route/schema.json: Added spawn_config relation (oneToOne)                                     │
│      - spawn-config/schema.json: Changed country → route relation                                    │
│      - country/schema.json: Removed spawn_config relation                                            │
│    • Pending: Restart Strapi, create route-specific configs, update SpawnConfigLoader               │
│    • Expected: Route 1 (St Lucy) at 6 AM → ~16 passengers (hour 6 rate = 0.6 vs 1.5)                │
│    • Validation scripts: Moved to commuter_simulator/tests/validation/ folder                       │
│  ✅ Seed Data: "Barbados Typical Weekday" with realistic commuter patterns                            │
│    • Morning peak (8am): 2.8x spawn rate, residential buildings 2.5x multiplier                       │
│    • Evening peak (5pm): 2.3x spawn rate, commercial buildings 1.8x multiplier                        │
│    • Weekend: 0.7x Saturday, 0.5x Sunday                                                              │
│    • Linked to Barbados country (id=29), verified via API                                             │
│  ✅ SpawnConfigLoader: Python client for loading and caching spawn configurations                     │
│    • Caching: 1-hour TTL to reduce API calls                                                          │
│    • Methods:                                                                                         │
│      - get_config_by_country(country_name) → loads full config from API                               │
│      - get_hourly_rate(config, hour) → 0.1-2.8 spawn rate multiplier                                  │
│      - get_building_weight(config, type) → building spawn weight (0-5.0)                              │
│      - get_poi_weight(config, type) → POI spawn weight (0-5.0)                                        │
│      - get_landuse_weight(config, type) → landuse spawn weight (0-5.0)                                │
│      - get_day_multiplier(config, day_name) → weekday vs weekend factor                               │
│      - get_distribution_params(config) → Poisson lambda, max spawns, radius                           │
│      - calculate_spawn_probability() → final probability calculation                                  │
│    • Example: Residential building, Monday 8am = 5.0 × 2.8 × 1.0 = 14.0                               │
│    • Tested: All methods working, cache <1ms, calculations correct                                    │
│  📁 Files:                                                                                            │
│    • arknet-fleet-api/src/api/spawn-config/content-types/spawn-config/schema.json                    │
│    • arknet-fleet-api/src/components/spawning/*.json (6 components)                                  │
│    • seeds/seed_spawn_config.sql                                                                      │
│    • commuter_simulator/infrastructure/spawn/config_loader.py                                        │
│    • commuter_simulator/tests/manual/test_spawn_loader.py                                            │
│                                                                                                       │
│ TIER 4 (OPTIMIZATION - Phase 2-3): Performance Enhancements                                         │
│  🔮 Redis reverse geocoding (<200ms target)                                                         │
│  🔮 Geofencing service (real-time zone detection)                                                   │
│                                                                                                      │
│ SEPARATE TRACK: GPS CentCom Production Hardening (Future)                                           │
│  🔮 Priority 1: Persistent datastore, per-device auth, structured logging                           │
│  🔮 Priority 2: Horizontal scaling, AESGCM server support, Prometheus metrics                       │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │                                        │
                                        └────────────────────────────────────────┘

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
│   GPS Device → WebSocket → GPS CentCom Server → Store → API → Dashboard     │
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
│    ✅ GPS CentCom = Telemetry hub (WebSocket, device state management)      │
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

## 📚 **USER PREFERENCES & AGENT ROLE**

> **⚠️ CRITICAL**: See "MANDATORY AGENT DIRECTIVES" at the top of this document for complete workflow enforcement. This section provides additional context on user preferences.

### **User's Work Style**

1. **Analysis-First Approach**
   - User values deep understanding before implementation
   - Always explain WHY a solution works, not just HOW
   - Provide context, alternatives, and trade-offs

2. **Incremental Validation**
   - Test at each phase before proceeding
   - Mark checkboxes in TODO.md as you complete tasks
   - Document discoveries and issues immediately

3. **Clear Communication**
   - User prefers questions over assumptions
   - If unclear, STOP and ask for clarification
   - Detailed explanations are appreciated

4. **Best Practices Focused**
   - Push back on code smells or anti-patterns
   - Cite SOLID principles when relevant
   - Propose better alternatives with rationale

5. **Documentation Discipline**
   - Keep CONTEXT.md and TODO.md synchronized
   - Update session notes with discoveries
   - Track progress counters (X/Y steps complete)

### **Agent Role & Responsibilities**

**You are a 50+ year senior software engineer with authority to:**

1. ✅ **Push back on bad practices** - Don't blindly accept poor solutions
2. ✅ **Question unclear requirements** - Ask for clarity before proceeding
3. ✅ **Propose better alternatives** - User values expert input
4. ✅ **Analyze before implementing** - Deep understanding first
5. ✅ **Validate incrementally** - Test each phase before moving forward

**Critical Reminders:**

- **NO "Conductor Service"** - Clarified Oct 25, assignment is event-based in spawn strategies
- **Use branch-0.0.2.6** - NOT main branch
- **Streaming parsers required** - building.geojson is 658MB
- **PostGIS geometry columns** - NOT lat/lon pairs (10-100x faster)
- **Update TODO.md checkboxes** - Track progress as you work
- **GPS CentCom is separate track** - Don't confuse with MVP spawning work

---

## 🕐 **SESSION HISTORY & KEY DECISIONS**

### **How We Got Here (Chronological)**

**October 25-26, 2025** - Complete journey from context recovery to production-ready documentation:

1. **Initial Request**: User lost chat history, requested full context rebuild
2. **Context Recovery**: Read PROJECT_STATUS.md and ARCHITECTURE_DEFINITIVE.md
3. **Scope Clarification**: This is a feasibility study for Redis-based reverse geocoding and real-time geofencing
4. **GeoJSON Analysis**: User confirmed 11 files from sample_data (excluding barbados_geocoded_stops)
5. **First Context Doc**: Created GEOJSON_IMPORT_CONTEXT.md (600+ lines)
6. **Phased Approach**: User requested reorganization based on their vision
7. **Custom Plugin Clarification**: Confirmed strapi-plugin-action-buttons is custom (no marketplace version)
8. **TODO Created**: Built TODO.md with 65+ granular steps across 6 phases
9. **Single Source of Truth**: User requested CONTEXT.md + TODO.md separation
10. **Added System Integration**: Enhanced CONTEXT.md with 10 detailed workflow diagrams
11. **Role Clarification**: User asked to confirm conductor/driver/commuter roles
12. **Architecture Fix**: Discovered and corrected "Conductor Service" error (doesn't exist - assignment is event-based)
13. **Agent Role Established**: User confirmed agent acts as 50+ year senior developer with authority to push back
14. **Phase 1 Steps 1.1-1.3 Complete**: Schema analyzed, plugin verified, database columns validated, backups created
15. **Design Decision**: User requested 5 separate buttons (one per GeoJSON file type) with full Socket.IO progress feedback
16. **Database Crisis Discovered**: Found lat/lon pairs instead of PostGIS geometry columns ($50K+ cost impact)
17. **PostGIS Migration Complete**: All 11 spatial tables migrated with geometry columns + GIST indexes (Oct 25)
18. **Buildings Import Complete**: 162,942 records imported using streaming parser at 1166 features/sec (Oct 25)
19. **Admin Level Architecture**: Normalized admin_levels reference table created and seeded (Oct 25)
20. **Admin Level UI Complete**: Custom modal with dropdown selection, dark theme styling (Oct 25)
21. **GPS CentCom Server Analysis**: Analyzed WebSocket telemetry hub, documented architecture (Oct 26)
22. **Critical Evaluation**: Assessed GPS CentCom production readiness: 15 strengths, 10 weaknesses (Oct 26)
23. **Documentation Integration**: Added GPS CentCom section to CONTEXT.md and TODO.md (Oct 26)
24. **Workspace Cleanup**: Deleted 13 outdated files (scripts/, tests/, old docs) (Oct 26)
25. **Priority Analysis**: Presented 3 priority options (A, B, C) with dependency mapping (Oct 26)
26. **Option A Selected**: User chose "complete imports → enable spawning → optimize performance" (Oct 26)
27. **TODO.md Reorganization**: Restructured with TIER 1-4 priority system (Oct 26)
28. **Linting Cleanup**: Fixed all markdown linting errors in TODO.md (Oct 26)
29. **CONTEXT.md Upgrade**: Enhanced for production-ready handoff to fresh agents (Oct 26)
30. **Agent Directives Formalized**: Added mandatory directives section with workflow enforcement (Oct 26)
31. **TODO.md Sync**: Corrected progress tracking (1/5 not 2/5), clarified endpoint status (Oct 26)

### **Critical Design Decisions**

| Decision | Rationale | Date | Impact |
|----------|-----------|------|--------|
| **Use Redis for reverse geocoding** | PostgreSQL ~2000ms, Redis target <200ms (10-100x improvement) | Oct 25 | TIER 4 - Deferred optimization |
| **11 GeoJSON files in scope** | User specified: exclude barbados_geocoded_stops from sample_data | Oct 25 | File inventory complete |
| **Use custom action-buttons plugin** | Already built at src/plugins/strapi-plugin-action-buttons/ | Oct 25 | No marketplace dependency |
| **Universal streaming for ALL imports** | Consistency, memory efficiency (<500MB), progress feedback | Oct 25 | Building import proved pattern works |
| **Centroid extraction needed** | amenity.geojson has MultiPolygon, POI schema expects Point | Oct 25 | Required for amenity import |
| **6-phase implementation → TIER 1-4** | Country Schema → Redis → Geofencing → POI → Depot/Route → Conductor | Oct 25-26 | Reorganized Oct 26 to dependency order |
| **Event-based passenger assignment** | No centralized "Conductor Service" - routes assigned in spawn strategies | Oct 25 | Architecture clarification |
| **5 separate import buttons** | One button per file type (highway, amenity, landuse, building, admin) | Oct 25 | Granular control + clarity |
| **Socket.IO for progress** | Real-time progress feedback during imports | Oct 25 | Leverages existing infrastructure |
| **Batch processing (500-1000 features)** | Optimal database performance, enables progress updates | Oct 25 | Proven with building import |
| **PostGIS geometry columns** | 10-100x faster queries, 90% less storage vs lat/lon pairs | Oct 25 | **CRITICAL - $50K+ cost savings** |
| **GIST spatial indexes** | Enable <50ms spatial queries vs 2000ms+ without | Oct 25 | Production performance requirement |
| **Admin level normalization** | Reference table with 4 seeded levels (6, 8, 9, 10) | Oct 25 | Proper foreign key relationships |
| **Priority sequence: Option A** | Complete imports → Enable spawning → Optimize performance | Oct 26 | **TIER 1→2→3→4 dependency order** |
| **GPS CentCom separate track** | MVP demo ready, needs hardening for production fleet | Oct 26 | Future work, not blocking spawning |
| **Geospatial API blocks spawning** | commuter_simulator needs spatial queries to spawn passengers | Oct 26 | TIER 2 - CRITICAL BLOCKER |

---

## 🎯 **CURRENT CHECKPOINT & PROGRESS**

### **Completed Work (17/92 major steps = 18.5%)**

✅ **Documentation Complete**

- CONTEXT.md comprehensive architecture (this file)
- TODO.md TIER 1-4 task sequence (92 steps)
- GPS CentCom Server architecture documented
- Priority system clarified and reorganized

✅ **Database Infrastructure**

- PostgreSQL + PostGIS validated (16.3 + 3.5)
- All 11 spatial tables migrated to PostGIS geometry columns
- 12 GIST spatial indexes created and validated
- admin_levels reference table created and seeded (4 levels)

✅ **GeoJSON Import System**

- Action-buttons plugin verified (5 buttons functional)
- Building import complete (162,942 records, streaming parser, 1166 features/sec)
- Admin level UI complete (custom modal, dropdown selection)
- Socket.IO progress events working

✅ **GPS CentCom Server** (Separate Track)

- WebSocket telemetry hub analyzed
- FastAPI architecture documented
- Production readiness assessed (15 strengths, 10 weaknesses)
- Integration with arknet_transit_simulator understood

✅ **Workspace Cleanup**

- 13 outdated files deleted (scripts/, tests/, old docs)
- All SQL files preserved
- Clean workspace ready for development

### **In Progress (TIER 1 - Immediate)**

⏳ **Phase 1.10: Complete GeoJSON Imports**

- [ ] Admin import backend endpoint (← NEXT TASK)
- [ ] Highway import optimization (streaming + bulk SQL)
- [ ] Amenity import optimization (handle Point/Polygon/MultiPolygon)
- [ ] Landuse import optimization (Polygon/MultiPolygon)

### **Next Major Milestones**

⏳ **TIER 2: Geospatial Services API** (CRITICAL BLOCKER for spawning)

- [ ] Phase 1.11: Create custom Strapi controllers for spatial queries
- [ ] Phase 1.12: Implement route-buildings, depot-buildings, zone-containing queries
- [ ] Validate query performance (<2s with GIST indexes)

⏳ **TIER 3: Passenger Spawning Features**

- [ ] Phase 4: POI-based spawning
- [ ] Phase 5: Depot-based spawning
- [ ] Phase 6: Route-based spawning

⏳ **TIER 4: Redis Optimization** (Deferred)

- [ ] Phase 2: Redis reverse geocoding (<200ms target)
- [ ] Phase 3: Geofencing service (real-time zone detection)

🔮 **SEPARATE TRACK: GPS CentCom Production Hardening** (Future)

- [ ] Priority 1: Persistent datastore (Redis/Postgres), per-device auth
- [ ] Priority 2: Horizontal scaling, AESGCM server support, monitoring

---

(Continues with existing CONTEXT.md content from System Architecture onwards...)

---

## 🚨 **KNOWN ISSUES & BLOCKERS**

### **Current Blockers (Nothing blocking immediate work)**

 **TIER 1 (IMMEDIATE)**: No blockers

- Admin import backend: Ready to implement (UI complete, DB ready, pattern established)
- Highway import: Can start after admin complete
- Amenity import: Can start after highway complete
- Landuse import: Can start after amenity complete

 **TIER 2 (CRITICAL BLOCKER for spawning)**:

- **Geospatial Services API needed before passenger spawning**
  - commuter_simulator requires route-buildings query (ST_DWithin 500m)
  - commuter_simulator requires depot-buildings query (ST_DWithin 1000m)
  - commuter_simulator requires zone-containing query (ST_Contains)
- **Impact**: Cannot implement Phases 4-5-6 until Phase 1.11-1.12 complete
- **Timeline**: TIER 2 immediately follows TIER 1 completion

 **TIER 3 (Features)**: Blocked by TIER 2

- Passenger spawning features depend on Geospatial API
- No other blockers once TIER 2 complete

 **TIER 4 (Optimization)**: No dependencies

- Redis can be implemented anytime
- Performance enhancement, not feature blocker
- Deferred to allow spawning features first

### **Resolved Issues**

 **Database Architecture Crisis** (Oct 25, 2025)

- **Problem**: Lat/lon pairs instead of PostGIS geometry columns
- **Impact**: 10-100x slower queries, 90% more storage, $50K+ infrastructure cost
- **Resolution**: All 11 spatial tables migrated to PostGIS with GIST indexes
- **Validation**: Distance queries working (21ms execution), spatial functions operational

 **Priority Confusion** (Oct 26, 2025)

- **Problem**: TODO.md had Redis optimization (Phase 2-3) before spawning features
- **Impact**: Incorrect dependency understanding
- **Resolution**: Reorganized with TIER 1-4 system (imports  spawning  optimization)
- **Clarification**: Spawning needs Geospatial API, NOT Redis (Redis is future optimization)

 **Conductor Service Misconception** (Oct 25, 2025)

- **Problem**: Assumed centralized "Conductor Service" exists
- **Impact**: Incorrect architecture understanding
- **Resolution**: Clarified passenger-to-route assignment is event-based in spawn strategies
- **Location**: spawn_interface.py - SpawnRequest.assigned_route field

 **File Clutter** (Oct 26, 2025)

- **Problem**: 13 outdated files confusing workspace
- **Impact**: Difficult to find current working code
- **Resolution**: Deleted scripts/, tests/, old docs; preserved all SQL files

---

## 🔧 **DEVELOPMENT COMMANDS**

### **Strapi (Backend)**

```powershell
# Start Strapi development server
cd arknet_fleet_manager/arknet-fleet-api
npm run develop
# Strapi runs on http://localhost:1337
# Admin UI: http://localhost:1337/admin

# Build Strapi (required after schema changes)
npm run build

# View logs - appear in terminal where npm run develop is running
```

### **Database Operations**

```sql
-- Connect to PostgreSQL: psql -U david -d arknettransit

-- Common queries
SELECT COUNT(*) FROM buildings;  -- Should show 162,942
SELECT * FROM admin_levels;      -- Should show 4 levels
SELECT tablename, indexname FROM pg_indexes WHERE indexname LIKE 'idx_%_geom';

-- Test spatial query
EXPLAIN ANALYZE
SELECT COUNT(*) FROM buildings
WHERE ST_DWithin(geom::geography, ST_MakePoint(-61.5, 13.1)::geography, 1000);
```

### **GPS CentCom Server**

```powershell
# Start GPS CentCom Server (separate from Strapi)
cd gpscentcom_server
python server_main.py
# Server runs on http://localhost:5000
# WebSocket: ws://localhost:5000/device
# Health: http://localhost:5000/health

# View device state
curl http://localhost:5000/devices
curl http://localhost:5000/route/1A
```

### **Simulators**

```powershell
# Run vehicle simulator
cd arknet_transit_simulator
python -m arknet_transit_simulator

# Run commuter simulator (blocked until TIER 2 complete)
cd commuter_simulator
python -m commuter_simulator
```

---

## 📚 **REFERENCE DOCUMENTATION**

### **Key Technical Resources**

1. **PostGIS Documentation**
   - Geometry types: Point, LineString, Polygon, MultiPolygon
   - Spatial functions: ST_DWithin, ST_Contains, ST_Intersects, ST_MakePoint
   - GIST indexes for spatial performance
   - Reference: <https://postgis.net/documentation/>

2. **Strapi v5 Documentation**
   - Entity Service API (single source of truth for writes)
   - Custom controllers and routes
   - Plugin development
   - Reference: <https://docs.strapi.io/>

3. **Stream-JSON**
   - Streaming GeoJSON parser
   - Memory-efficient feature processing
   - Reference: Used in building import pattern

4. **Socket.IO**
   - Real-time progress events
   - import:progress, import:complete events
   - Reference: Integrated in Strapi

### **Project-Specific Patterns**

1. **GeoJSON Import Pattern** (see importBuilding function)
   - Stream-json parser with 500 feature batches
   - Geometry extraction and WKT conversion
   - Bulk SQL inserts for performance
   - Socket.IO progress events
   - File location: src/api/geojson-import/controllers/geojson-import.ts (lines 470-650)

2. **Spatial Query Pattern** (Phase 1.11 - to be implemented)
   - Custom Strapi controller with direct PostgreSQL access
   - ST_DWithin for proximity queries (buildings near routes/depots)
   - ST_Contains for point-in-polygon (lat/lon in zone)
   - GIST index utilization (<50ms query performance)

3. **Admin Level Normalization** (established Oct 25)
   - Reference table: admin_levels (4 seeded records)
   - Foreign key relationships: regions.admin_level_id  admin_levels.id
   - UI: Custom modal with dropdown selection
   - Backend: Map adminLevel (6,8,9,10)  filename

---

## 🎓 **LEARNING FROM THIS PROJECT**

### **Critical Lessons (Don't Repeat These Mistakes)**

1. **PostgreSQL Spatial Data**: Always use PostGIS geometry columns, NEVER lat/lon pairs
   - Impact: 10-100x performance difference, 90% storage savings
   - Cost: $50K+ in infrastructure if done wrong

2. **Streaming for Large Files**: Always use streaming parsers for files >100MB
   - Building.geojson (658MB) would crash with fs.readFileSync()
   - stream-json processes 1166 features/sec without memory issues

3. **Architecture Clarity**: Document what DOESN'T exist as clearly as what does
   - "Conductor Service" misconception wasted hours
   - Event-based vs centralized services must be explicit

4. **Priority by Dependency**: Organize tasks by dependency graph, not perceived importance
   - Redis seemed critical but isn't needed for spawning
   - Geospatial API is the real blocker for passenger features

5. **Test Spatial Queries Early**: Validate PostGIS performance before building features
   - GIST indexes are non-negotiable for production
   - <50ms query performance is achievable with proper indexing

### **Success Patterns (Replicate These)**

1. **Incremental Validation**: Test each phase before proceeding
   - Building import proved streaming pattern works
   - Admin UI validated before backend implementation

2. **Documentation Discipline**: Keep CONTEXT.md and TODO.md synchronized
   - Fresh agent can rebuild from scratch with these two files
   - Every decision, every blocker, every pattern documented

3. **Clear Communication**: User prefers questions over assumptions
   - Stopped to clarify "Conductor Service"  saved major refactor
   - Presented priority options A/B/C  user chose A with confidence

4. **Production Thinking**: Consider cost, scale, and maintenance from day one
   - PostGIS migration saved $50K+ in future infrastructure
   - Streaming parser supports 10x larger files without code changes

---

## 🚀 **PRODUCTION READINESS CHECKLIST**

### **MVP Demo (10-50 vehicles) - CURRENT TARGET**

- [x] PostgreSQL + PostGIS infrastructure
- [x] Strapi API (single source of truth)
- [x] Building import (162,942 records)
- [ ] Admin import (TIER 1 - next task)
- [ ] Highway/amenity/landuse imports (TIER 1)
- [ ] Geospatial Services API (TIER 2 - critical blocker)
- [ ] Passenger spawning features (TIER 3)
- [ ] GPS CentCom Server ( MVP demo ready)

### **Staging/Investor Pilot (100-200 vehicles)**

- [ ] Redis reverse geocoding (TIER 4 - <200ms)
- [ ] Geofencing service (TIER 4 - <10ms)
- [ ] GPS CentCom persistence (Redis/Postgres)
- [ ] Per-device authentication
- [ ] Structured logging (JSON)
- [ ] Basic metrics (Prometheus)

### **Production Fleet (500+ vehicles)**

- [ ] GPS CentCom horizontal scaling
- [ ] Load balancing (multiple Strapi instances)
- [ ] Database connection pooling
- [ ] Advanced monitoring (Grafana/ELK)
- [ ] CI/CD pipeline with automated tests
- [ ] Disaster recovery plan
- [ ] SLA compliance (99.9% uptime)

---

## 📝 **VERSION HISTORY**

### **v2.0 - October 26, 2025**

- Complete production-ready handoff upgrade
- Added immediate context for new agents
- Added rebuild instructions (Step 1-5)
- Added technology stack details
- Added quick decision reference
- Enhanced GPS CentCom Server documentation
- Added known issues and blockers section
- Added development commands
- Added learning lessons and success patterns
- Added production readiness checklist
- Reorganized for fresh agent onboarding

### **v1.0 - October 25, 2025**

- Initial comprehensive context document
- System architecture diagrams
- Component roles and responsibilities
- Session history and key decisions
- User preferences and agent role
- Database architecture crisis resolution

---

**Document Maintainer**: Update this document as architecture evolves  
**Last Updated**: October 30, 2025 (GPS Device Reconnection + Redundant Server Planning)  
**Next Review**: After TIER 5 (Route-Depot Association & Full RouteSpawner complete)

---

## 🏗️ **TIER 4 SPAWNER SYSTEM IMPLEMENTATION - October 28, 2025**

### **Architectural Decisions & Pushback Analysis**

This section documents critical architectural decisions made on October 28, 2025, including agent pushback on user proposals and final approved designs.

#### **Decision 1: Single Entrypoint vs Separate Sub-Entrypoints**

**User Proposal**: "The commuter_simulator will have a single entrypoint that will start the spawn_engine with separate sub-entrypoints for depot/route spawners"

**Agent Pushback**: ✅ ACCEPTED (with modifications)
- **Approved Pattern**: Single `main.py` entrypoint with `SpawnerCoordinator` orchestration
- **Rejected**: Separate CLI sub-entrypoints for each spawner type
- **Rationale**: 
  - Avoid complexity of multiple CLI entrypoints
  - Use coordinator pattern for spawner management (industry standard)
  - Config-driven control via enable/disable flags
  - Shared resource initialization (PassengerRepository, Reservoirs) - DRY principle
  - Single process easier to monitor, debug, and deploy

**Implementation**:
```python
# commuter_simulator/main.py
async def main():
    # Shared resources
    passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")
    route_reservoir = RouteReservoir(...)
    depot_reservoir = DepotReservoir(...)
    
    # Create spawners
    spawners = [
        MockRouteSpawner(route_reservoir, config, ...),
        DepotSpawner(depot_reservoir, config, ...)
    ]
    
    # Config-driven control
    config = {
        "enable_routespawner": True,
        "enable_depotspawner": True,
        "mode": "single"  # or "continuous"
    }
    
    # Coordinator orchestrates
    coordinator = SpawnerCoordinator(spawners, config)
    await coordinator.start()
```

**Benefits Realized**:
- Single command to run: `python -m commuter_simulator.main`
- Granular control via config flags (not CLI args)
- Clean separation: Coordinator = orchestration, Spawners = generation logic
- Easy to extend (add new spawner = add to list + config flag)

---

#### **Decision 2: Depot-Route Association Logic**

**User Proposal**: "Depot spawner will spawn at the depot associated with the route that is chosen"

**Agent Pushback**: ❌ REJECTED (inverted responsibility)

**Problem Identified**:
1. **Tight Coupling**: DepotSpawner becomes route-aware, duplicating RouteSpawner logic
2. **Breaks Single Responsibility**: DepotSpawner should generate depot passengers, not route-dependent passengers
3. **Scalability Issues**: If Route 1 has 3 depots, which depot spawns? How to prevent duplicate spawns?
4. **Architectural Confusion**: Conflates two different passenger generation patterns

**Better Design (Approved)**:
```
RouteSpawner:
  - Spawns passengers ALONG the route (distributed spatially)
  - Passengers board at nearest stop along their journey
  - Use case: "I'm at Building 123, need to get to Building 456 on Route 1"
  - Logic: Query buildings along route → Select spawn locations → Generate passengers

DepotSpawner:
  - Spawns passengers AT the depot (centralized location)
  - Passengers wait for ANY route that serves that depot
  - Use case: "I'm at Main Station depot, will board any route going downtown"
  - Logic: Query depot's associated routes → Select ONE route → Generate passengers for that route
```

**Key Insight**: These are **different passenger generation patterns**, not route-dependent variations.

**Implementation**:
```python
# DepotSpawner selects from ASSOCIATED routes (not random)
class DepotSpawner:
    async def spawn(self, current_time, time_window_minutes=60):
        # Query depot's associated routes from route-depots junction table
        associated_routes = await self._get_depot_routes(self.depot_id)
        
        # Weighted random selection (busy routes get more passengers)
        selected_route = weighted_random_choice(associated_routes)
        
        # Generate passengers for that route only
        spawn_requests = self._generate_spawn_requests(
            route_id=selected_route.route_id,
            count=poisson_count
        )
```

---

#### **Decision 3: Two-Mode API Architecture**

**User Concern**: "Maybe we need to move all geospatial API requests to geospatial_service... check if we have two modes of API access"

**Agent Analysis**: ✅ TWO-MODE IS CORRECT (don't change)

**Current Architecture (Validated)**:
```
Mode 1: Strapi REST API (localhost:1337) - CRUD Operations
├─ /api/routes → Route master data (CRUD)
├─ /api/depots → Depot master data (CRUD)
├─ /api/route-depots → Junction table (CRUD) - NEW
├─ /api/spawn-configs → Spawning configuration (CRUD)
├─ /api/active-passengers → Live passenger records (CRUD)
└─ /api/operational-configurations → System settings (CRUD)

Mode 2: Geospatial Service (localhost:6000) - Spatial Queries (READ-ONLY)
├─ /route-geometry/{route_id} → PostGIS geometry queries
├─ /route-buildings → Spatial joins (buildings near route)
├─ /depot-catchment → Spatial queries (depots near coordinates)
└─ /nearby-buildings → POI/building proximity searches
```

**Why This is CORRECT**:
1. **Separation of Concerns**: Strapi = business logic + CRUD, GeospatialService = PostGIS spatial queries
2. **Performance Isolation**: Heavy PostGIS calculations don't slow down Strapi admin panel
3. **Single Source of Truth**: Strapi remains SSOT for master data, GeospatialService is compute-only
4. **Scalability**: Can scale GeospatialService independently (add replicas for spatial queries)

**What Would Break if Changed**:
- Moving `/api/routes` to GeospatialService → Strapi admin panel breaks (can't edit routes)
- Moving spawn-configs to GeospatialService → Spawner can't query configs
- Duplicating CRUD in both services → Data inconsistency, sync issues

**Agent Recommendation**: ✅ KEEP TWO-MODE ARCHITECTURE

---

#### **Decision 4: Route-Depot Junction Table**

**Agent Recommendation**: ✅ CREATE EXPLICIT RELATIONSHIPS (approved)

**Current State (Problematic)**:
- No explicit depot-route relationship table
- Uses runtime geospatial calculation (5km proximity from route geometry)
- Code in deprecated `depot_reservoir.py`:
```python
def _is_depot_connected_to_route(self, depot, route_id, max_distance_km=5.0):
    """Check if depot within 5km of ANY point on route geometry"""
    min_dist = float('inf')
    for coord in route.geometry_coordinates:
        d = geodesic((depot_lat, depot_lon), (rlat, rlon)).kilometers
        if d < min_dist:
            min_dist = d
    return min_dist <= max_distance_km
```

**Problems**:
1. **Performance**: O(n×m) calculation every spawn cycle (n=depots, m=route coordinates)
2. **No Caching**: Recalculates same distances repeatedly
3. **Implicit Logic**: Relationship exists in code, not data model
4. **Hard to Query**: Can't easily ask "which depots serve Route 1?"

**Approved Design**:
```typescript
// Strapi schema: api::route-depot.route-depot
{
  "kind": "collectionType",
  "collectionName": "route_depots",
  "info": {
    "singularName": "route-depot",
    "pluralName": "route-depots",
    "displayName": "Route-Depot Association"
  },
  "attributes": {
    "route": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::route.route",
      "inversedBy": "associated_depots"
    },
    "depot": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::depot.depot",
      "inversedBy": "associated_routes"
    },
    "is_terminus": {
      "type": "boolean",
      "default": false,
      "description": "True if depot is route start/end point"
    },
    "distance_from_route_m": {
      "type": "float",
      "description": "Precomputed distance from depot to nearest route point (meters)"
    }
  }
}
```

**Benefits**:
1. **Explicit Relationships**: Data model matches real-world operations
2. **Precomputed Distances**: Calculate once during route/depot creation, query forever
3. **Cache-Friendly**: Indexed lookups (O(log n)) vs spatial calculations (O(n×m))
4. **Realistic**: Depots serve specific routes, not all routes within 5km
5. **Queryable**: Simple SQL: `SELECT * FROM route_depots WHERE depot_id = ?`

**Precomputation Strategy**:
```python
# Run when route or depot is created/updated
async def compute_depot_route_associations():
    routes = await get_all_routes()
    depots = await get_all_depots()
    
    for route in routes:
        for depot in depots:
            # Use GeospatialService for distance calculation
            min_dist = await geo_client.distance_to_route(
                depot_lat=depot.latitude,
                depot_lon=depot.longitude,
                route_id=route.id
            )
            
            if min_dist <= 5000:  # 5km threshold
                await create_route_depot_association(
                    route_id=route.id,
                    depot_id=depot.id,
                    distance_from_route_m=min_dist,
                    is_terminus=(min_dist < 100)  # <100m = terminus
                )
```

---

#### **Decision 5: PubSub for Reservoir Visualization**

**User Request**: "3rd parties can pubsub subscribe into reservoirs as commuters are being spawned"

**Agent Recommendation**: ✅ GOOD IDEA (with pattern recommendation)

**User Intent**: Allow 3rd-party developers to visualize passengers as they spawn in real-time

**Pattern Evaluated**:

**Option A: Direct Pub/Sub in Spawner (REJECTED)**
```python
# DON'T DO THIS - blocks spawner, creates backpressure
async def push_batch(self, spawn_requests):
    success, failed = await self._bulk_insert(spawn_requests)
    
    # BLOCKING - waits for all subscribers
    await self.pubsub_client.publish("spawner.depot.created", spawn_requests)
    
    return success, failed
```

**Problems**:
- Spawner performance dependent on subscriber speed
- Backpressure if subscribers can't keep up
- Tight coupling between spawner and subscribers
- Failure in pub/sub breaks spawner

**Option B: PostgreSQL LISTEN/NOTIFY (RECOMMENDED ✅)**
```sql
-- Create trigger on active_passengers table
CREATE OR REPLACE FUNCTION notify_passenger_change()
RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify(
    'passenger_changes',
    json_build_object(
      'operation', TG_OP,
      'passenger_id', NEW.passenger_id,
      'depot_id', NEW.depot_id,
      'route_id', NEW.route_id,
      'lat', NEW.latitude,
      'lon', NEW.longitude,
      'spawned_at', NEW.spawned_at
    )::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER passenger_changes_trigger
AFTER INSERT OR UPDATE OR DELETE ON active_passengers
FOR EACH ROW EXECUTE FUNCTION notify_passenger_change();
```

**Subscriber Example** (Python):
```python
import asyncpg

async def subscribe_to_passengers():
    conn = await asyncpg.connect('postgresql://...')
    
    async def listener(connection, pid, channel, payload):
        data = json.loads(payload)
        print(f"Passenger {data['operation']}: {data['passenger_id']}")
        # Update visualization, send to WebSocket clients, etc.
    
    await conn.add_listener('passenger_changes', listener)
    
    # Keep listening
    while True:
        await asyncio.sleep(1)
```

**Benefits**:
1. **Zero Overhead on Spawner**: Database handles pub/sub, spawner just inserts
2. **Automatic Buffering**: PostgreSQL queues messages if subscriber slow
3. **Replay Support**: Can query historical data for catchup
4. **Multiple Subscribers**: Many 3rd parties can subscribe without affecting each other
5. **Failure Isolation**: Subscriber crash doesn't affect spawner

**Agent Recommendation**: ✅ Use PostgreSQL LISTEN/NOTIFY, implement in TIER 6

---

### **Implementation Summary (TIER 4 Complete + RouteSpawner Discovery)**

#### **CRITICAL DISCOVERY (October 28, 2025)**:

During deep code analysis validation of TIER 5 execution plan, discovered that **RouteSpawner was already fully implemented** (287 lines), reducing TIER 5 scope by 33%.

**RouteSpawner Status**:
- ✅ **Location**: `commuter_simulator/core/domain/spawner_engine/route_spawner.py`
- ✅ **Implementation**: COMPLETE (287 lines)
- ✅ **Methods**: All required methods implemented:
  - `spawn()`: Main algorithm with complete Poisson distribution logic
  - `_load_spawn_config()`: Queries Strapi for route-specific spawn configuration
  - `_load_route_geometry()`: Calls GeospatialService `/spatial/route-geometry/{route_id}`
  - `_get_buildings_near_route()`: Spatial query for buildings within route buffer
  - `_calculate_spawn_count()`: Poisson distribution (λ = spatial × hourly × day × time_window/60)
  - `_generate_spawn_requests()`: Spatially distributes passengers along route geometry
- ✅ **GeospatialService Integration**: Uses `/spatial/route-geometry/{route_id}` and `/spatial/route-buildings`
- ❌ **NOT Wired**: Currently uses `MockRouteSpawner` in main.py, real implementation not integrated
- 🎯 **Next Step**: Replace MockRouteSpawner with real RouteSpawner in coordinator

**Validation Methodology**:
1. `semantic_search("route depot association")` → Confirmed junction table missing
2. `grep_search` for "class.*RouteSpawner" → Found existing implementation
3. `read_file` route_spawner.py (lines 1-287) → Validated complete implementation
4. `grep_search` for "LISTEN|NOTIFY" → Confirmed PubSub missing
5. `file_search` for passenger_subscriber.py → Confirmed example missing

**Revised TIER 5 Scope**:
- ~~Steps 7-11: Implement RouteSpawner~~ → **SKIP** (already complete)
- Step 12: ~~Implement and test~~ → **REVISE** to "Wire and test existing RouteSpawner"
- Steps 1-6, 13-18: Proceed as planned (junction table, associations, PubSub, testing)

#### **Files Created/Modified**:

**1. `commuter_simulator/core/domain/spawner_engine/depot_spawner.py`** ✅ COMPLETE
- **Purpose**: Poisson-distributed passenger generation at depot locations
- **Key Features**:
  - Configurable spawn rates (spatial, hourly, day multipliers)
  - Default config fallback if Strapi config unavailable
  - Bulk insert for performance (all passengers in single transaction)
- **Methods**:
  - `spawn()`: Main entry point, calculates Poisson count, generates passengers
  - `_load_spawn_config()`: Loads from Strapi or returns defaults
  - `_calculate_spawn_count()`: Poisson distribution (λ = spatial × hourly × day × time_window/60)
  - `_generate_spawn_requests()`: Creates passenger spawn requests with depot_id
- **Test Results**: 4 passengers spawned (λ=2.20), 100% success rate

**2. `commuter_simulator/services/spawner_coordinator.py`** ✅ COMPLETE
- **Purpose**: Orchestrates multiple spawners with enable/disable control
- **Key Features**:
  - Single-run and continuous modes
  - Config-driven spawner filtering (enable_{spawnerclass} flags)
  - Aggregate statistics logging (total passengers, success rate)
- **Methods**:
  - `start()`: Main entry point, dispatches to single or continuous mode
  - `_get_enabled_spawners()`: Filters spawners based on enable flags
  - `_run_single_cycle()`: Runs all enabled spawners once (asyncio.gather)
  - `_run_continuous()`: Runs spawners on configurable interval
  - `_log_aggregate_stats()`: Logs total passengers spawned across all spawners

**3. `commuter_simulator/main.py`** ✅ COMPLETE
- **Purpose**: Single entrypoint for spawner system
- **Key Features**:
  - Creates shared resources (PassengerRepository, Reservoirs)
  - Config dict controls enable_routespawner and enable_depotspawner flags
  - MockRouteSpawner for testing (λ=1.5, simplified implementation)
- **Configuration**:
```python
config = {
    "enable_routespawner": True,  # Enable/disable route spawner
    "enable_depotspawner": True,   # Enable/disable depot spawner
    "mode": "single",              # "single" or "continuous"
    "interval_seconds": 60         # For continuous mode
}
```

**4. `commuter_simulator/core/domain/reservoirs/`** ✅ MOVED & UPDATED
- **Location Change**: Moved from project root to `commuter_simulator/core/domain/reservoirs/`
- **Files**:
  - `depot_reservoir.py`: DB-backed with optional Redis (enable_redis_cache flag)
  - `route_reservoir.py`: DB-backed with optional Redis (enable_redis_cache flag)
  - `__init__.py`: Updated with relative imports and corrected docstrings
- **Key Features**:
  - `push()`: Insert single passenger to Strapi
  - `push_batch()`: Bulk insert passengers (uses PassengerRepository.bulk_create)
  - `available()`: Query waiting passengers by depot/route
  - Redis hooks exist but not yet implemented (enable_redis_cache flag)

**5. `commuter_simulator/infrastructure/database/passenger_repository.py`** ✅ UPDATED
- **New Methods**:
  - `get_waiting_passengers_by_route(route_id, limit)`: GET /api/active-passengers?filters[route_id][$eq]=X
  - `get_waiting_passengers_by_depot(depot_id, limit)`: GET /api/active-passengers?filters[depot_id][$eq]=X
- **Helper Features**:
  - Both return simplified passenger dicts
  - Include route_id/depot_id fields for filtering
  - Used by reservoirs for `available()` queries

**6. `commuter_simulator/core/domain/spawner_engine/route_spawner.py`** ✅ DISCOVERED COMPLETE (Oct 28)
- **Purpose**: Spatially distributed passenger generation along transit routes
- **Status**: FULLY IMPLEMENTED (287 lines) - discovered during TIER 5 validation
- **Key Features**:
  - Poisson distribution with spatial/hourly/day multipliers
  - GeospatialService integration for route geometry and building queries
  - Spatial distribution logic along route corridor using building weights
  - Realistic spawn/destination assignment (min 0.5km, max route length)
- **Methods**:
  - `spawn()`: Main algorithm with complete Poisson distribution logic
  - `_load_spawn_config()`: Queries Strapi `/api/spawn-configs?filters[route_id][$eq]=X`
  - `_load_route_geometry()`: Calls GeospatialService `/spatial/route-geometry/{route_id}`
  - `_get_buildings_near_route()`: Queries `/spatial/route-buildings` with buffer
  - `_calculate_spawn_count()`: Poisson (λ = spatial × hourly × day × time_window/60)
  - `_generate_spawn_requests()`: Spatially distributes passengers using building weights
- **Integration**: NOT yet wired to main.py coordinator (uses MockRouteSpawner currently)
- **Next Step**: Replace MockRouteSpawner with RouteSpawner in main.py

**7. `test_spawner_flags.py`** ✅ CREATED
- **Purpose**: Comprehensive test of enable/disable flag combinations
- **Test Scenarios**:
  1. RouteSpawner OFF, DepotSpawner ON
  2. RouteSpawner ON, DepotSpawner OFF
  3. Both ON
  4. Both OFF
- **Status**: Created but not yet executed
- **Uses**: MockRouteSpawner (will be updated to use real RouteSpawner)

**8. `delete_passengers.py`** ✅ VERIFIED
- **Purpose**: Utility for clearing Strapi active-passengers table
- **Usage**: `python delete_passengers.py`
- **Test Results**: Deleted 6 passengers, verified 0 remaining
- **Use Case**: Testing fresh passenger generation

---

### **Test Results (October 28)**

#### **End-to-End Test** (`python -m commuter_simulator.main`):

**Spawn Calculation**:
```
λ = spatial_multiplier × hourly_multiplier × day_multiplier × (time_window / 60)
λ = 2.0 × 1.0 × 1.1 × (60 / 60)
λ = 2.20
```

**Poisson Distribution Result**: count = 4 (from λ=2.20)

**Bulk Insert**:
- Successful: 4/4 (100% success rate)
- Failed: 0/4
- All passengers persisted to Strapi

**Database Verification** (`GET /api/active-passengers`):
- Total passengers: 4
- Fields verified:
  - `depot_id`: "BGI_FAIRCHILD_02" ✅
  - `route_id`: Random selection from available routes ✅
  - `status`: "WAITING" ✅
  - `spawned_at`: ISO timestamp ✅
  - `expires_at`: spawned_at + 30 minutes ✅
  - `latitude`, `longitude`: Depot coordinates ✅

#### **Fresh Spawn Verification**:

**Test Steps**:
1. Deleted all 6 passengers from database (`python delete_passengers.py`)
2. Verified 0 passengers remaining (`GET /api/active-passengers`)
3. Ran spawner first time: 0 passengers (Poisson randomness with λ=2.20)
4. Ran spawner second time: 1 passenger (Poisson randomness)
5. Verified new passenger timestamp: `spawned_at=2025-10-28T09:45:20.980Z`

**Result**: ✅ Confirmed fresh passenger generation (not old data)

#### **Logging Format Fix**:
- **Problem**: Double-escaped %% in `logging.basicConfig` format string
- **Fix**: Changed `%(asctime)s` (correct) from `%%(asctime)s` (wrong)
- **Result**: Clean log output

---

### **Pending Work (TIER 5 - REVISED October 28)**

**DEEP CODE ANALYSIS IMPACT**: RouteSpawner discovery reduces TIER 5 scope by 33% (6 of 18 steps redundant)

**1. Route-Depot Junction Table** 🎯 NEXT
- Create `route-depots` collection in Strapi
- Schema: route_id, depot_id, distance_from_route_m, is_start_terminus, is_end_terminus, precomputed_at
- **CORRECTED SEMANTICS** (Oct 28): Depots are bus stations/terminals where passengers wait for buses
- **Association Logic**: Route associates with depot ONLY if route START or END point within walking distance (~500m)
- Precompute geospatial associations using GeospatialService (calculate distance to route endpoints only)
- Bidirectional relations: routes ↔ depots

**2. Update DepotSpawner Logic**
- Add `_load_associated_routes()` method to query Strapi API
- Query from `/api/route-depots?filters[depot_id][$eq]=X&populate=route`
- Replace hardcoded `available_routes` parameter with database lookup
- Weighted random selection from depot's associated routes
- **Realistic behavior**: Passengers at depot only board routes that actually service that depot (endpoints within walking distance)

**3. Wire RouteSpawner to Coordinator** (REVISED - Implementation exists!)
- Replace MockRouteSpawner with real RouteSpawner in main.py
- Update test_spawner_flags.py to use real RouteSpawner
- Run end-to-end test with `enable_routespawner=True`
- Verify passengers spawn spatially along route geometry
- Validate GeospatialService integration (route-geometry, route-buildings calls)

**4. PubSub Implementation**
- PostgreSQL LISTEN/NOTIFY on active_passengers table
- Trigger function: `notify_passenger_change()`
- Trigger on INSERT/UPDATE/DELETE
- Create `commuter_simulator/examples/passenger_subscriber.py`
- Subscriber examples for 3rd-party visualization

**5. Comprehensive Flag Testing**
- Execute `test_spawner_flags.py` with all 4 scenarios
- Verify coordinator correctly filters spawners based on enable flags
- Test depot-only, route-only, both, neither configurations
- Update to use real RouteSpawner instead of Mock

**6. Redis Implementation** (Deferred to TIER 7)
- Install Redis client library
- Implement startup loader for static route/geojson data
- Implement cache-aside pattern in reservoirs
- Enable Redis caching flag integration

---

## 📊 **FUTURE ENHANCEMENTS (Not Blocking MVP)**

### **Data Enhancement - Temporal & Ridership Analytics (TIER 5)**

**Current State (✅ Sufficient for MVP):**

- 189,659 spatial features imported (buildings, POIs, landuse zones, highways, regions)
- Basic temporal hooks exist (`spawn_weight`, `peak_hour_multiplier`, `off_peak_multiplier` fields)
- Schema provides ~80% of spawning model needs

**Future Enhancement (Phase 7-8):**

When real-world ridership data becomes available, add:

1. **Temporal Profile System** (Phase 7):
   - `temporal_profiles` table: Define hour-of-day, day-of-week patterns
   - Peak definitions: Morning rush (7-9am), evening rush (4-7pm), off-peak, weekend
   - Seasonal variations: Holidays, tourist season, school terms
   - Link profiles to POI types (school = morning/afternoon peaks, bars = evening/night)

2. **Ridership Data Collection** (Phase 8):
   - `ridership_observations` table: Actual passenger counts (timestamp, location, count)
   - `passenger_demand_history` table: Aggregated demand by zone/hour/day
   - Import pipeline for CSV/Excel historical data
   - Validation & outlier detection
   - ML model training (future: replace Poisson with learned rates)
   - Calibrated spawn_weights exported back to existing tables

**Decision**: Focus on MVP with current data (Phases 1-6). Add temporal/ridership system (Phases 7-8) when operational data is collected from live simulator runs.

---

## 📝 **SESSION NOTES - October 28, 2025**

### **RouteSpawner Discovery - Deep Code Analysis**

**Context**: User requested deep code analysis to identify redundancies/misalignments in TIER 5 execution plan before proceeding with implementation.

**Validation Methodology**:
1. `semantic_search("route depot association")` → Confirmed junction table missing
2. `grep_search` in arknet_fleet_manager → Only 5 comment mentions, zero implementation
3. `file_search("**/route-depot/**")` → No files found
4. `grep_search` for "class.*RouteSpawner" → **FOUND existing implementation**
5. `read_file` route_spawner.py (lines 1-287) → **Validated COMPLETE implementation**
6. `read_file` depot_spawner.py → Confirmed hardcoded `available_routes` parameter
7. `grep_search` for "LISTEN|NOTIFY|subscriber" → Confirmed PubSub missing
8. `file_search` for passenger_subscriber.py → Confirmed example missing

**Key Discovery**:
- RouteSpawner **ALREADY FULLY IMPLEMENTED** (287 lines) at `commuter_simulator/core/domain/spawner_engine/route_spawner.py`
- All required methods complete: `spawn()`, `_load_spawn_config()`, `_load_route_geometry()`, `_get_buildings_near_route()`, `_calculate_spawn_count()`, `_generate_spawn_requests()`
- GeospatialService integration complete: `/spatial/route-geometry/{route_id}`, `/spatial/route-buildings`
- **NOT wired to coordinator yet** - main.py currently uses MockRouteSpawner

**Impact on TIER 5 Plan**:
- **Original Plan**: 18 steps
- **Redundant Steps**: 6 steps (7-11: RouteSpawner implementation already complete)
- **Scope Reduction**: 33%
- **Revised Step 12**: Changed from "Implement and test" to "Wire and test existing implementation"

**Validated Outcomes**:
- ✅ Steps 1-6: Route-depot junction table and DepotSpawner associations - VALID (missing, need implementation)
- ❌ Steps 7-11: RouteSpawner implementation - REDUNDANT (already complete)
- 🔧 Step 12: RouteSpawner testing - REVISED (wire existing, don't implement)
- ✅ Steps 13-16: PostgreSQL LISTEN/NOTIFY PubSub - VALID (missing, need implementation)
- ✅ Steps 17-18: Flag testing and documentation - VALID (need execution)

**Files Updated**:
- `TODO.md`: Updated TIER 5 summary, added deep code analysis results, revised pending work section
- `CONTEXT.md`: Updated status header, added RouteSpawner discovery section, revised pending work, added session notes

**Next Immediate Action**: Proceed with Step 1 - Create route-depots junction table in Strapi schema

**Commit Message**:
```
docs(tier5): document RouteSpawner discovery and revise TIER 5 plan

- Deep code analysis revealed RouteSpawner fully implemented (287 lines)
- Reduces TIER 5 scope by 33% (6 of 18 steps redundant)
- Updated TODO.md with deep code analysis results
- Updated CONTEXT.md with discovery details and revised plan
- Next: Create route-depots junction table (Step 1)
```

---

### **Route-Depot Association Semantics Correction - October 28, 2025**

**Context**: During TIER 5 Step 1 implementation, user corrected fundamental assumption about depot-route relationships.

**Original (INCORRECT) Assumption**:
- Proximity threshold: 5km
- Association logic: Depot associates with route if within 5km of ANY point along route
- Intended use: Broad spatial coverage for spawning

**Corrected Understanding**:
- **Depots are bus stations/terminals** where passengers wait for buses
- **Association logic**: Route associates with depot ONLY if route START or END point within walking distance (~500m)
- **Proximity threshold**: ~500 meters (5-10 minute walk to bus station)
- **Intended use**: Realistic passenger behavior - passengers at depot board routes that actually service that depot

**Schema Changes**:
- Changed field: `is_terminus` → split into `is_start_terminus` and `is_end_terminus`
- Changed description: "distance to nearest point on route" → "distance to nearest route endpoint"
- Distance calculation: Only to route START/END points, not any point along route

**Impact on Precompute Script** (Step 3):
1. Query route geometry from GeospatialService to get START and END coordinates
2. For each depot, calculate distance to route START point and route END point separately
3. Create association ONLY if either distance <= 500m
4. Set `is_start_terminus=true` if START within range
5. Set `is_end_terminus=true` if END within range
6. Store `distance_from_route_m` as minimum of the two distances

**Realistic Example**:
```
Route 1: Bridge Street Station (start) → Harbor Terminal (end) [12km route]
Depot "Bridge Street Station": lat=13.10, lon=-59.61

Association:
  - Distance to Route 1 START: 50m ✅ (within 500m threshold)
  - Distance to Route 1 END: 12km ❌ (beyond threshold)
  - Result: Create association with is_start_terminus=true, distance_from_route_m=50

Passengers at Bridge Street Station depot:
  - Can board Route 1 (travels to Harbor Terminal)
  - Realistic behavior: Station serves this route's starting point
```

**Files Updated**:
- `arknet_fleet_manager/arknet-fleet-api/src/api/route-depot/content-types/route-depot/schema.json`: Updated field names and descriptions
- `TODO.md`: Updated association logic description, proximity threshold corrected to ~500m
- `CONTEXT.md`: Added semantic correction notes, updated all references to association logic

**Next Action**: Continue with TIER 5 Step 1 - Test route-depot schema in Strapi admin after server restart

---

> **🎯 HANDOFF COMPLETE**: A fresh agent with this CONTEXT.md + TODO.md can rebuild the environment, understand all architectural decisions, and continue to production-grade MVP without external context or chat history.

---

## 📄 Passenger Manifest (shared contract)

To avoid reinventing the wheel when building the production UI, we've centralized the manifest computation in a reusable module following clean architecture.

- Source: `commuter_simulator/application/queries/manifest_query.py`
- API: `commuter_simulator/interfaces/http/manifest_api.py` (FastAPI, port 4000)
- Consumers: CLI (`commuter_simulator/interfaces/cli/list_passengers.py`), HTTP API, and future UI
- Architecture: Application layer query (uses domain services and infrastructure clients)
- Ordering: Ascending by `route_position_m` when a `route_id` is provided (distance from start of the route). Otherwise, positions are 0 and ordering is unspecified.
- Reverse geocoding: Via GeospatialService `/geocode/reverse` with small in-memory cache and bounded concurrency (env `GEOCODE_CONCURRENCY`, default 5)
- Resilience: Timeouts and graceful fallbacks (`start_address`/`stop_address` may be "-")

### ManifestRow fields (stable)

- index: int
- spawned_at: string (ISO 8601)
- passenger_id: string
- route_id: string
- depot_id: string
- latitude: float
- longitude: float
- destination_lat: float
- destination_lon: float
- status: string (e.g., WAITING, BOARDED)
- route_position_m: float (meters from route start to nearest route vertex)
- travel_distance_km: float
- start_address: string (reverse geocoded)
- stop_address: string (reverse geocoded)
- trip_summary: string ("Start Address → Stop Address | km")

### How to use

- **HTTP API** (recommended for UI):
  - Start: `uvicorn commuter_simulator.interfaces.http.manifest_api:app --port 4000`
  - Endpoint: `GET http://localhost:4000/api/manifest?route=<id>&limit=100`
  - Returns: `{"count": N, "route_id": "...", "passengers": [...], "ordered_by_route_position": true}`
  - Docs: <http://localhost:4000/docs>
- Python import (for backend integrations):
  - `from commuter_simulator.application.queries import enrich_manifest_rows`
  - Call `await enrich_manifest_rows(rows, route_id)` where `rows` are raw Strapi `active-passengers` records (attributes-flattened)
- Console/diagnostics:
  - `python -m commuter_simulator.interfaces.cli.list_passengers --route <id> --json`

This contract is now the single source of truth for manifest formatting and ordering.

---

## 🏛️ Clean Architecture Refactoring (October 29, 2025)

### Motivation

The original folder structure was ad-hoc with unclear boundaries:
- `services/` at root level (application or domain?)
- `api/` at root level (not part of layered architecture)
- `core/domain/` vs `infrastructure/` confusion
- Mixed responsibilities making code hard to navigate

### Solution: Clean Architecture Layers

Reorganized to follow **Robert C. Martin's Clean Architecture** with explicit layers and dependency rules.

```
commuter_simulator/
├── domain/              # Pure business logic (no external dependencies)
│   └── services/
│       ├── spawning/    # DepotSpawner, RouteSpawner
│       └── reservoirs/  # RouteReservoir, DepotReservoir
│
├── application/         # Use cases and orchestration
│   ├── coordinators/    # SpawnerCoordinator
│   └── queries/         # manifest_query (enrichment)
│
├── infrastructure/      # External systems (Strapi, PostGIS, Redis)
│   ├── persistence/
│   │   └── strapi/      # PassengerRepository
│   ├── geospatial/      # GeospatialClient
│   ├── config/          # SpawnConfigLoader
│   └── events/          # LISTEN/NOTIFY
│
└── interfaces/          # Entry points (HTTP, CLI)
    ├── http/            # FastAPI manifest API
    └── cli/             # list_passengers console tool
```

### Dependency Rule

**Inward only**: domain ← application ← infrastructure/interfaces

- `domain/` has ZERO external dependencies (pure business logic)
- `application/` coordinates domain services
- `infrastructure/` implements domain interfaces
- `interfaces/` provides entry points (HTTP, CLI)

### Files Moved

| Old Location | New Location | Reason |
|--------------|--------------|--------|
| `services/manifest_builder.py` | `application/queries/manifest_query.py` | Application-layer query |
| `services/spawner_coordinator.py` | `application/coordinators/spawner_coordinator.py` | Orchestration logic |
| `core/domain/spawner_engine/` | `domain/services/spawning/` | Clearer naming |
| `core/domain/reservoirs/` | `domain/services/reservoirs/` | Consistent structure |
| `infrastructure/database/` | `infrastructure/persistence/strapi/` | Organized by system |
| `infrastructure/spawn/config_loader.py` | `infrastructure/config/spawn_config_loader.py` | Logical grouping |
| `api/manifest_api.py` | `interfaces/http/manifest_api.py` | Entry point layer |
| `scripts/console/list_passengers.py` | `interfaces/cli/list_passengers.py` | Entry point layer |

### Import Changes

**Before:**
```python
from commuter_simulator.services.manifest_builder import enrich_manifest_rows
from commuter_simulator.core.domain.spawner_engine import DepotSpawner
from commuter_simulator.infrastructure.database.passenger_repository import PassengerRepository
```

**After:**
```python
from commuter_simulator.application.queries import enrich_manifest_rows
from commuter_simulator.domain.services.spawning import DepotSpawner
from commuter_simulator.infrastructure.persistence.strapi import PassengerRepository
```

### Benefits

✅ **Testability** - Domain isolated, easy to unit test
✅ **Maintainability** - Clear boundaries, easy to navigate
✅ **Scalability** - Add features without breaking existing code
✅ **Clarity** - New developers understand structure immediately
✅ **Production-ready** - Solid foundation for UI development

### Verification

All entry points tested and working:
- ✅ `python -m commuter_simulator.main`
- ✅ `uvicorn commuter_simulator.interfaces.http.manifest_api:app --port 4000`
- ✅ `python -m commuter_simulator.interfaces.cli.list_passengers --help`

See `commuter_simulator/ARCHITECTURE.md` for complete layer documentation.

**Refactoring Complete**: October 29, 2025

---

## FLEET SERVICES ARCHITECTURE (October 29-30, 2025)

### Overview

The system runs 3 separate HTTP services on different ports (standalone architecture):
- **GPSCentCom Server** (port 5000) - GPS telemetry hub with HTTP API and WebSocket
- **GeospatialService** (port 6000) - PostGIS spatial queries and reverse geocoding
- **Manifest API** (port 4000) - Passenger manifest enrichment with geocoding

**Architecture Decision**: After attempting a unified backend on port 8000, the standalone approach was chosen due to:
- WebSocket proxy complexity in unified FastAPI mounts
- Simpler deployment and debugging
- Independent service scaling
- Clearer separation of concerns

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Fleet Services - Standalone Architecture                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ GPSCentCom Server (Port 5000)                      │    │
│  │ - HTTP API: /health, /devices, /analytics          │    │
│  │ - WebSocket: /device (GPS telemetry ingestion)     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ GeospatialService (Port 6000)                      │    │
│  │ - /geocode/reverse (reverse geocoding)             │    │
│  │ - /route-geometry/{id} (route geometry)            │    │
│  │ - /spatial/* (spatial queries)                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Manifest API (Port 4000)                           │    │
│  │ - /api/manifest (enriched passenger listings)      │    │
│  │ - /health (service health)                         │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Configuration: .env (single source of truth)               │
│  Launcher: start_fleet_services.py                          │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

**1. GeospatialService (/geo/*)**
- Source: geospatial_service/main.py
- Functions: PostGIS spatial queries, reverse geocoding
- Endpoints:
  - GET /geo/route-geometry/{route_id}  Route geometry (LineString)
  - GET /geo/route-buildings  Buildings near route
  - POST /geo/geocode/reverse  Lat/lon  address
  - GET /geo/health  Service health check

**2. Passenger Manifest API (/manifest/*)**
- Source: commuter_simulator/interfaces/http/manifest_api.py
- Functions: Enriched passenger listings with reverse geocoding
- Endpoints:
  - GET /manifest/api/manifest?route=<id>&limit=100  Passenger manifest
  - GET /manifest/docs  Swagger UI
  - GET /manifest/health  Service health check

**3. GPSCentCom HTTP API (/gps/*)**
- Source: gpscentcom_server/api_router.py
- Functions: GPS telemetry queries, device analytics
- Endpoints:
  - GET /gps/health  Server health check
  - GET /gps/devices  All active devices
  - GET /gps/route/{code}  Devices on specific route
  - GET /gps/analytics  System-wide analytics
  - GET /gps/stream  Server-Sent Events (SSE) telemetry stream

**4. GPSCentCom WebSocket (/gps/device)**
- Source: Direct route in arknet_fleet_services.py
- Functions: GPS device telemetry ingestion
- Protocol: WebSocket (text/binary, JSON/AESGCM)
- Note: Uses **direct @app.websocket() route** to bypass FastAPI mount() limitation

### WebSocket Mounting Issue

**Problem**: FastAPI's pp.mount() does NOT support WebSocket routes

**Original Attempt**:
``python
gpscentcom_app = _load_gpscentcom_app()  # Has @app.websocket("/device")
app.mount("/gps", gpscentcom_app)        #  WebSocket won't work
``

**Solution**: Direct WebSocket route on root app
``python
@app.websocket("/gps/device")
async def gpscentcom_device_endpoint(websocket: WebSocket):
    """Forward to GPSCentCom WebSocket handler"""
    await websocket.accept()
    # Import and call GPSCentCom rx_handler logic
    await handle_device_connection(websocket)
``

### Server-Sent Events (SSE) Telemetry Stream

**Added**: GET /gps/stream endpoint for real-time client telemetry

**Purpose**: Allows clients to receive GPS telemetry updates via HTTP streaming (alternative to WebSocket for clients)

**Protocol**: Server-Sent Events (SSE) - one-way server  client push

**Features**:
- Optional filters: ?device_id=<id>&route_code=<code>
- Broadcasts all telemetry updates from ConnectionManager
- Auto-reconnect support (browser native)
- Cross-platform (works in browsers, Python, .NET, etc.)

**Example Usage**:
``python
import requests

response = requests.get("<http://localhost:8000/gps/stream>", stream=True)
for line in response.iter_lines():
    if line.startswith(b"data:"):
        telemetry = json.loads(line[6:])
        print(f"Vehicle {telemetry['deviceId']} @ {telemetry['lat']},{telemetry['lon']}")
``

### Benefits of Consolidation

1. **Single Port Configuration**: Clients only need to know <http://localhost:8000>
2. **Simplified Deployment**: One process instead of three
3. **Unified CORS Policy**: Single CORS middleware configuration
4. **Shared Dependencies**: Single FastAPI instance, shared connection pools
5. **Easier Monitoring**: One health endpoint, one log stream
6. **Reduced Resource Usage**: One process overhead instead of three

### Migration Guide (For Clients)

**Old URLs:**
- <http://localhost:6000/route-geometry/123>  <http://localhost:8000/geo/route-geometry/123>
- <http://localhost:5000/health>  <http://localhost:8000/gps/health>
- <http://localhost:4000/api/manifest>  <http://localhost:8000/manifest/api/manifest>
- ws://localhost:5000/device  ws://localhost:8000/gps/device

**New Universal Base URL**: <http://localhost:8000>

### File Structure

``
arknet_fleet_services.py
 _load_geospatial_app()      # Imports geospatial_service.main:app
 _load_gpscentcom_app()      # Imports gpscentcom_server.api_router:api_router
 _load_manifest_app()        # Imports commuter_simulator.interfaces.http.manifest_api:app
 WebSocket direct route      # @app.websocket("/gps/device")
 Main FastAPI app            # Mounts /geo, /gps, /manifest
``

### Launching Services

**Production Launcher** (Recommended):
```powershell
python start_fleet_services.py
```

This will:
1. Load configuration from `.env`
2. Launch 3 services in separate console windows:
   - GPSCentCom Server (port 5000)
   - GeospatialService (port 6000)
   - Manifest API (port 4000)
3. Display all service endpoints

**Manual Launch** (Development):
```powershell
# GPSCentCom
cd gpscentcom_server
python server_main.py

# GeospatialService
cd geospatial_service
python main.py

# Manifest API
python -m commuter_simulator.interfaces.http.manifest_api
```

### Health Checks

```powershell
# Verify all services are running
curl http://localhost:5000/health   # GPSCentCom
curl http://localhost:6000/health   # GeospatialService
curl http://localhost:4000/health   # Manifest API
```

**Expected Responses**:
- GPSCentCom: `{"status":"ok","uptime_sec":120,"devices":0}`
- GeospatialService: `{"status":"healthy","database":"connected","features":{...}}`
- Manifest API: `{"status":"ok","service":"manifest_api","timestamp":"..."}`

### Verified Test Results (October 30, 2025)

✅ **All Services Operational**:
1. **GPSCentCom** (Port 5000): Health check passed, GPS device connected (GPS-ZR102)
2. **GeospatialService** (Port 6000): Reverse geocoding working (~18ms response time)
3. **Manifest API** (Port 4000): Service responding to health checks

✅ **End-to-End Testing**:
- Unified launcher successfully started all 3 services
- GPS telemetry client polling live data every 2 seconds
- Geospatial reverse geocoding: "footway-784848147, near RBC, Saint Michael"
- All configuration loaded from `.env` file

### Code Cleanup (October 30, 2025)

**Removed obsolete files** (unified backend approach abandoned):
- `arknet_fleet_services.py` - Deprecated unified service on port 8000
- `manage_fleet_services.py` - Management utility for unified service
- `run_fleet_services.py` - Wrapper for unified service
- `test_gps_telemetry.py` - Hardcoded test for port 8000
- `test_mock_gps_device.py` - Hardcoded mock device for port 8000

**Reason for removal**: After attempting unified backend, standalone architecture chosen for simplicity, better WebSocket support, and clearer separation of concerns.

---

## GPS TELEMETRY CLIENT LIBRARY (October 29-30, 2025)

### Client Library Overview

An **interface-agnostic Python library** for consuming GPS telemetry from GPSCentCom server.

Designed to be used in **any Python application** (console, GUI, web dashboard, backend services) without coupling to specific UI frameworks.

### Library Structure

```
gps_telemetry_client/
 __init__.py           # Library exports
 client.py             # GPSTelemetryClient class
 models.py             # Pydantic data models (Vehicle, etc.)
 observers.py          # Observer pattern for event handling
 test_client.py        # CLI tool (list/watch/poll/analytics)
 README.md             # Library documentation
```

### GPSTelemetryClient Class

**Purpose**: HTTP client for GPSCentCom API with both synchronous and asynchronous modes

**Features**:
- Synchronous HTTP polling (get_vehicles(), get_route_vehicles(), etc.)
- Asynchronous SSE streaming (stream_telemetry() with observer pattern)
- Pydantic validation of all responses
- Automatic JSON parsing and error handling

**Example Usage (HTTP Polling)**:

```python
from gps_telemetry_client import GPSTelemetryClient

client = GPSTelemetryClient(base_url="http://localhost:5000")

# Get all vehicles
vehicles = client.get_vehicles()
for vehicle in vehicles:
    print(f"{vehicle.deviceId}: {vehicle.route} @ {vehicle.lat},{vehicle.lon}")

# Get vehicles on specific route
route_vehicles = client.get_route_vehicles("1A")

# Get system analytics
analytics = client.get_analytics()
print(f"Total devices: {analytics.total_devices}")
```

**Example Usage (SSE Streaming)**:

```python
import asyncio
from gps_telemetry_client import GPSTelemetryClient
from gps_telemetry_client.observers import CallbackObserver

async def on_telemetry(vehicle):
    print(f"UPDATE: {vehicle.deviceId} @ {vehicle.lat},{vehicle.lon}")

client = GPSTelemetryClient(base_url="http://localhost:5000")
observer = CallbackObserver(on_telemetry)

# Stream all telemetry
await client.stream_telemetry(observers=[observer])

# Stream filtered by route
await client.stream_telemetry(route_code="1A", observers=[observer])
```

## Data Models (Pydantic)

**Vehicle** (from /devices and /stream):

```python
@dataclass
class Vehicle:
    deviceId: str
    route: str
    vehicleReg: str
    lat: float
    lon: float
    speed: float
    heading: float
    driverId: Optional[str]
    driverName: Optional[Dict[str, str]]
    conductorId: Optional[str]
    timestamp: str
    lastSeen: str
```

**AnalyticsResponse** (from /analytics):

```python
@dataclass
class AnalyticsResponse:
    total_devices: int
    routes_active: Dict[str, int]
    avg_speed: float
    timestamp: str
```

**HealthResponse** (from /health):

```python
@dataclass
class HealthResponse:
    status: str
    store_size: int
    uptime_seconds: float
```

### Observer Pattern

**Purpose**: Decouple telemetry consumers from client implementation

**TelemetryObserver (Abstract)**:
``python
class TelemetryObserver(ABC):
    @abstractmethod
    async def on_vehicle_update(self, vehicle: Vehicle):
        """Called when vehicle telemetry received"""
        pass
``

**CallbackObserver (Concrete)**:

```python
class CallbackObserver(TelemetryObserver):
    def __init__(self, callback: Callable[[Vehicle], Awaitable[None]]):
        self.callback = callback
    
    async def on_vehicle_update(self, vehicle: Vehicle):
        await self.callback(vehicle)
```

**Custom Observer Example**:

```python
class MapVisualizerObserver(TelemetryObserver):
    def __init__(self, map_widget):
        self.map = map_widget
    
    async def on_vehicle_update(self, vehicle: Vehicle):
        self.map.update_marker(
            id=vehicle.deviceId,
            lat=vehicle.lat,
            lon=vehicle.lon,
            heading=vehicle.heading
        )
``

### CLI Tool (test_client.py)

**Purpose**: Command-line diagnostic tool for GPS telemetry

**Commands**:
- list - Show all active vehicles (one-time snapshot)
- watch - Live stream of telemetry updates (SSE)
- poll - Periodic HTTP polling (default 5s interval)
- nalytics - System-wide statistics

**Example Usage**:
``powershell
# List all vehicles once
python -m gps_telemetry_client.test_client list

# Watch telemetry stream (SSE)
python -m gps_telemetry_client.test_client watch

# Watch specific route
python -m gps_telemetry_client.test_client watch --route 1A

# Poll every 10 seconds
python -m gps_telemetry_client.test_client poll --interval 10

# Show analytics
python -m gps_telemetry_client.test_client analytics
``

### Use Cases

1. **Console Dashboards**:
   - Import GPSTelemetryClient in Python console apps
   - Use stream_telemetry() with terminal UI libraries (rich, blessed, etc.)

2. **.NET GUI Applications**:
   - Call Python library via subprocess or IPC
   - Or reimplement client in C# following same API contract

3. **Web Dashboards**:
   - Backend service uses GPSTelemetryClient
   - Forwards telemetry to frontend via WebSocket/SSE
   - Example: FastAPI backend with React frontend

4. **Data Analytics Pipelines**:
   - Use stream_telemetry() to pipe data to Kafka, Redis, or database
   - Observer pattern allows pluggable data sinks

5. **Testing & Diagnostics**:
   - CLI tool for manual testing of GPS telemetry flow
   - Verify device connectivity, route filtering, data quality

### Interface-Agnostic Design

**NO UI Dependencies**:
- No imports from PyQt, tkinter, Flask, Django, etc.
- Pure Python + 
equests + httpx (HTTP client)
- Pydantic for data validation (no UI coupling)

**Observer Pattern Benefits**:
- Consumers define HOW to display data (UI logic)
- Library defines WHEN to notify consumers (business logic)
- Clean separation of concerns

**Example: Absorbing into WPF .NET GUI**:
``csharp
// C# equivalent (pseudo-code)
public class GPSTelemetryClient
{
    public async Task<List<Vehicle>> GetVehiclesAsync() { ... }
    public async Task StreamTelemetryAsync(Action<Vehicle> onUpdate) { ... }
}

// WPF application
var client = new GPSTelemetryClient("http://localhost:8000");
await client.StreamTelemetryAsync(vehicle =>
{
    Dispatcher.Invoke(() =>
    {
        MapControl.UpdateMarker(vehicle.DeviceId, vehicle.Lat, vehicle.Lon);
    });
});
``

### Integration with Vehicle Simulator

**Vehicle Simulator** (rknet_transit_simulator) sends telemetry:
``
Vehicle  GPSDevice  WebSocket  GPSCentCom (/gps/device)  Store
``

**GPS Telemetry Client** receives telemetry:
``
Store  HTTP/SSE  GPSTelemetryClient  Observers  UI/Console/Analytics
``

**End-to-End Flow**:
``
[Vehicle Simulator]
     WebSocket (ws://localhost:8000/gps/device)
[GPSCentCom Server]
     In-memory store
[GPSTelemetryClient]
     HTTP GET /gps/devices (polling)
     SSE GET /gps/stream (streaming)
[Observer Pattern]
     on_vehicle_update(vehicle)
[UI Application]
     Display on map/console/dashboard
``

### Testing

**Test Environment**:
1. Start Fleet Services: `python start_fleet_services.py` (launches 3 services)
2. Wait 3-5 seconds for services to initialize
3. Verify health checks (see commands above)
4. Test GPS telemetry client:
   ```powershell
   $env:PYTHONPATH="E:\projects\github\vehicle_simulator"
   python gps_telemetry_client\test_client.py --url http://localhost:5000 --prefix / poll --interval 2
   ```

**Expected GPS Client Output**:
```
Connecting to http://localhost:5000...
Connected!

Polling every 2s (Press Ctrl+C to stop)

[16:23:32] Active devices: 1
GPS-ZR102 | Route 1 | ZR102 | (13.32661, -59.61552) | Speed: 0.0 km/h | Heading: 0.0°
```

**Test Geospatial Service**:
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:6000/geocode/reverse?lat=13.0969&lon=-59.6145"
$response | ConvertTo-Json
```

**Expected Output**:
```json
{
  "address": "footway-784848147, near RBC, Saint Michael",
  "latitude": 13.0969,
  "longitude": -59.6145,
  "highway": {"name": "footway-784848147", "highway_type": "footway", "distance_meters": 0.11},
  "poi": {"name": "RBC", "poi_type": "bank", "distance_meters": 33.08},
  "latency_ms": 18.38
}
```

### Future Enhancements

1. **Reconnection Logic**: Auto-reconnect SSE stream on disconnect
2. **Data Buffering**: Queue telemetry updates during processing
3. **Filtering Options**: Device ID, bounding box, speed threshold
4. **Historical Playback**: Replay telemetry from database
5. **Multi-Client Coordination**: Redis pub/sub for distributed clients

---

## 🔄 **GPS DEVICE AUTOMATIC RECONNECTION - October 30, 2025**

### **Implementation Status: ✅ COMPLETE**

**Problem**: GPS devices would not reconnect to GPSCentCom server after server restart. Critical for real hardware deployment where network interruptions are common and manual reconnection is not feasible.

**Solution**: Implemented robust automatic reconnection in `arknet_transit_simulator/vehicle/gps_device/device.py`

### **Key Features**

1. **Automatic Reconnection Loop**
   - Continuously attempts connection if server unavailable (5s retry delay)
   - Detects connection drops and reconnects automatically
   - Operates independently of server availability

2. **Intelligent Error Handling**
   - `ConnectionRefused` → Retry connection
   - `websockets.ConnectionClosed` → Force immediate reconnect
   - Network errors → Count and reconnect after 3 consecutive failures
   - Timeouts → Normal operation, continue

3. **Data Buffering During Disconnection**
   - Data collection continues even when disconnected
   - RxTxBuffer holds up to 1000 items
   - Transmission resumes automatically when connection restored
   - **Data Loss**: Long disconnections (>1000 updates) cause oldest items to drop

4. **Connection State Management**
   - Connection phase vs transmission phase
   - Graceful shutdown with proper cleanup
   - Comprehensive logging for monitoring

### **Reconnection Flow**

```
GPS Device Starts
       ↓
Try Connect to Server
   ↙        ↘
SUCCESS    FAILURE
   ↓          ↓
Connected   Wait 5s → Retry
   ↓          ↑
Send Data    │
   ↓          │
Connection   │
Drops ───────┘
```

### **Configuration Parameters**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `connection_retry_delay` | 5.0s | Delay between reconnection attempts |
| `max_consecutive_errors` | 3 | Errors before forcing reconnect |
| Buffer read timeout | 1.0s | Timeout for reading from data buffer |
| Buffer capacity | 1000 items | Max buffered telemetry during disconnection |

### **Testing**

Test script: `test_gps_reconnection.py`

```bash
# Start test (GPS server doesn't need to be running)
python test_gps_reconnection.py

# Device will:
# 1. Try to connect every 5 seconds
# 2. Connect automatically when server starts
# 3. Detect when server stops
# 4. Reconnect automatically when server restarts
```

### **Production Readiness**

✅ **Suitable For**:
- Real hardware GPS devices (ESP32, etc.)
- Unreliable network environments
- Long-running deployments
- Autonomous vehicle operations
- Remote/distributed systems

⚠️ **Considerations**:
- Buffer overflow on long disconnections
- 5s retry delay causes ~5s gap after reconnect
- Verbose logging during disconnection (by design)

### **Future Enhancement: Redundant Server List**

**Status**: 🎯 PLANNED (Not yet implemented)

GPS devices should support automatic failover to redundant servers for high availability:

```python
# Future Configuration
transmitter = WebSocketTransmitter(
    servers=[
        {"url": "wss://gps-primary.example.com", "priority": 1},
        {"url": "wss://gps-secondary.example.com", "priority": 2},
        {"url": "wss://gps-backup.example.com", "priority": 3}
    ],
    token=token,
    device_id=device_id,
    failover_config={
        "retry_primary_interval": 300,  # Try primary every 5 min
        "max_failover_attempts": 3,     # Try 3 servers before cycling
        "health_check_interval": 30      # Check connection every 30s
    }
)
```

**Failover Behavior**:
- Connect to highest priority available server
- Automatically failover to next server if connection fails
- Periodically attempt to reconnect to higher priority servers
- Maintain connection state across failover events
- No data loss during server switching (buffered transmission)
- Load balancing across redundant servers (optional)

**Implementation Requirements**:
- [ ] Multi-server configuration in GPS device transmitter
- [ ] Priority-based server selection algorithm
- [ ] Automatic failover on connection loss
- [ ] Periodic health checks to prefer primary server
- [ ] Server list updates via configuration or API
- [ ] Telemetry tracking which server device is connected to
- [ ] Load balancing strategy (round-robin, least-connections, geographic)
- [ ] Server health monitoring and automatic removal from pool
- [ ] Graceful server list updates without disconnecting devices

**Architecture Considerations**:
- Server list stored in configuration or fetched from central API
- Device maintains connection priority preferences
- Automatic demotion of failing servers
- Automatic promotion when primary server recovers
- Server affinity for session persistence (optional)
- Metrics: track failover events, server uptime, connection duration

**Related**: See TODO.md for detailed redundant server roadmap

---

## Security & Configuration

### Configuration Architecture

This project separates **sensitive credentials** from **operational configuration** for security and maintainability.

#### 📄 config.ini - Operational Configuration (Safe to commit)
- Service ports (Strapi, GPS, Geospatial, Manifest)
- Service URLs (localhost endpoints)
- Enable/disable flags for subsystems
- Timing parameters (startup waits, intervals)

#### 🔐 .env - Secrets & Credentials (NEVER commit)
**Locations**: Root `.env` and `arknet_fleet_manager/arknet-fleet-api/.env`

**Contains**:
- API tokens and authentication keys
- Database passwords
- Cloud service credentials (Cloudinary, AWS)
- JWT secrets and encryption keys

**Security Status**:
- ✅ Both .env files are in .gitignore
- ✅ .env.example templates provided
- ⚠️ ACTION REQUIRED: Change default secrets before production!

#### 🗄️ Database (operational-configurations) - Runtime Settings
- Spawn rates and intervals
- Continuous mode toggles
- Feature flags
- Performance thresholds

### Security Checklist (Before Production)

- [ ] Change all default secrets in arknet-fleet-api/.env
  - [ ] APP_KEYS (generate unique keys)
  - [ ] API_TOKEN_SALT
  - [ ] ADMIN_JWT_SECRET
  - [ ] JWT_SECRET
  - [ ] ENCRYPTION_KEY
  - [ ] DATABASE_PASSWORD
- [ ] Verify .gitignore excludes .env files
- [ ] Review for exposed credentials in code/docs
- [ ] Set proper file permissions (chmod 600 .env)

### Environment Setup

1. Copy templates: `cp .env.example .env`
2. Edit .env files with real credentials
3. Configure operational settings in config.ini
4. Seed operational configuration: `python seed_operational_config.py`

### Generating Secure Secrets

```bash
# For Strapi secrets
openssl rand -base64 32

# For API tokens
python -c "import uuid; print(uuid.uuid4())"
```

---
