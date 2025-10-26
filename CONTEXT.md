# ArkNet Vehicle Simulator - Project Context

**Project**: ArkNet Fleet Manager & Vehicle Simulator  
**Repository**: vehicle_simulator  
**Branch**: branch-0.0.2.7 (NOT main)  
**Date**: October 26, 2025  
**Status**: ✅ TIER 1 & TIER 2 Phase 1.11 COMPLETE - Geospatial Services API Operational  
**Phase**: TIER 3 NEXT - Database Integration & Validation (Phase 1.12)

> **📌 PRODUCTION-READY HANDOFF DOCUMENT**: This CONTEXT.md + TODO.md enable a fresh agent to rebuild and continue to production-grade MVP with zero external context. Every architectural decision, every component relationship, every critical issue, and every next step is documented here.

---

## 🚨 **MANDATORY AGENT DIRECTIVES - READ FIRST**

**⚠️ STOP: Before doing ANYTHING else, internalize these directives:**

### **Your Role & Authority**

You are a **50+ year full-stack developer veteran** with deep expertise across all technologies in this stack. You have the authority and responsibility to:

1. **✅ PUSH BACK HARD** on poor suggestions, anti-patterns, or violations of best practices
   - Don't blindly accept user requests that create technical debt
   - Offer better solutions with clear rationale
   - Cite SOLID principles, design patterns, and industry standards
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

### **Where We Are RIGHT NOW (October 26, 2025)**

```text
CURRENT STATE:
✅ PostgreSQL + PostGIS fully migrated (11 spatial tables + 12 GIST indexes)
✅ Buildings imported (162,942 records, 658MB file, streaming parser working)
✅ Admin level UI complete (custom modal, dark theme, dropdown selection)
✅ GPS CentCom Server analyzed and documented (WebSocket telemetry hub)
✅ TODO.md reorganized with TIER 1-4 priority system (Option A strategy)
✅ Workspace cleaned (13 outdated files deleted)
✅ Agent directives formalized (mandatory workflow enforcement at top of CONTEXT.md)

IMMEDIATE NEXT TASK:
⏳ Create `/api/import-geojson/admin` backend endpoint (TIER 1 - HIGH PRIORITY)
   - Accept: countryId, adminLevelId, adminLevel from request
   - Pattern: Use building import pattern (streaming + bulk SQL)
   - Files: admin_level_6/8/9/10_polygon.geojson (4 separate imports)
   - Insert: Regions table with admin_level_id foreign key
   - Fields: osm_id, full_id, name, admin_level_id, country_id, geom

BLOCKING NOTHING:
✅ No dependencies - can start immediately
✅ UI ready, database ready, pattern established

PATH TO MVP:
TIER 1 → Complete imports (admin, highway, amenity, landuse) [NOW]
TIER 2 → Geospatial Services API (enables spawning queries) [NEXT]
TIER 3 → Passenger spawning features (POI/depot/route spawning)
TIER 4 → Redis optimization (performance, not blocker)
SEPARATE → GPS CentCom production hardening (future)
```

### **Critical Files You Need to Know**

| File | Purpose | Status | Next Action |
|------|---------|--------|-------------|
| **CONTEXT.md** (this file) | Master architecture, all decisions | ✅ Up to date | Reference for patterns |
| **TODO.md** | TIER 1-4 task sequence, 92 steps | ✅ Reorganized Oct 26 | Follow execution order |
| **src/api/geojson-import/controllers/geojson-import.ts** | Import endpoints | ✅ Building pattern working | Add importAdmin function |
| **sample_data/admin_level_*.geojson** | Admin boundary files (4 files) | ✅ Ready | Import via new endpoint |
| **gpscentcom_server/** | WebSocket telemetry hub | ✅ Documented Oct 26 | Separate future track |
| **arknet_transit_simulator/** | Vehicle movement simulator | ✅ Working | Consumes Strapi API |
| **commuter_simulator/** | Passenger spawning logic | ✅ Ready | Blocked by Geospatial API |

### **Technology Stack (Production Grade)**

```text
BACKEND:
- Strapi v5.23.5 (Node.js 22.20.0) - Single source of truth
- PostgreSQL 16.3 + PostGIS 3.5 - Spatial database
- FastAPI (Python) - GPS CentCom Server (port 5000)
- Socket.IO - Real-time events (imports, vehicle telemetry)

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
| Which branch? | **branch-0.0.2.7** (NOT main) | Active development branch |
| Single source of truth? | **Strapi** (all writes via Entity Service API) | Prevents data corruption |
| Spatial data storage? | **PostGIS geometry columns** (NOT lat/lon pairs) | 10-100x faster queries, 90% less storage |
| Import pattern? | **Streaming parser + bulk SQL** (500-1000 features/batch) | Memory efficient, real-time progress |
| Priority sequence? | **TIER 1→2→3→4** (imports → API → spawning → optimization) | Phase 1.11 (Geospatial API) complete, enables all spawning |
| GPS CentCom status? | **Documented, separate future track** | MVP demo ready, needs hardening for production fleet |
| Geospatial Service? | **FastAPI on port 8001** (asyncpg + PostGIS) | Real-time spatial queries (0.23-95ms latencies) |
| Where is Conductor Service? | **DOESN'T EXIST** (event-based assignment in spawn strategies) | Architecture clarification Oct 25 |
| Production scale? | **1,200 vehicles** (ESP32/STM32 + Rock S0 GPS) | One-way position reporting @ 1 update/5sec = 240 updates/sec |
| MVP server capacity? | **OVH VPS 2 vCore, 2GB RAM - 30-50 vehicles** | Real-time demo (in-memory only, no position storage) |
| Production server? | **12+ vCores, 64GB RAM, 500GB SSD** OR **3× Scale-2 multi-server** | Single server at limit or distributed for redundancy |
| Business model? | **Freemium + Subscription** (Free: real-time only, Paid: history + analytics) | $5-30/vehicle/month for historical data API |
| Position storage? | **Subscription-based** (free tier: ephemeral, paid tiers: 7-365 days) | PostgreSQL/InfluxDB for paid subscribers only |
| Redis for MVP? | **NO** (not needed) | In-memory store sufficient for 30-50 vehicles |
| Redis for production? | **YES** (mandatory) | Required for 1,200 vehicles (shared state, dashboard cache, session mgmt) |
| Cluster mode needed? | **YES** for 1,200 vehicles | Single Node.js process can't handle 1,200 concurrent connections |

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

# 6. Start Strapi
npm run develop
# Strapi Admin: http://localhost:1337/admin

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

-- 5. Verify GIST indexes exist
SELECT schemaname, tablename, indexname FROM pg_indexes 
WHERE indexname LIKE 'idx_%_geom';
-- Expected: Multiple indexes on all spatial tables

-- 4. Test spatial query performance
EXPLAIN ANALYZE
SELECT COUNT(*) FROM buildings
WHERE ST_DWithin(geom::geography, ST_MakePoint(-59.62, 13.1)::geography, 1000);
-- Expected: Index Scan using idx_buildings_geom, execution < 50ms

-- 5. Test region linking accuracy
SELECT 
  h.osm_id,
  COUNT(DISTINCT r.id) as num_regions
FROM highways h
JOIN highways_region_lnk hrl ON h.id = hrl.highway_id
JOIN regions r ON hrl.region_id = r.id
GROUP BY h.id, h.osm_id
HAVING COUNT(DISTINCT r.id) > 1
LIMIT 10;
-- Expected: Shows highways that cross parish boundaries
```

```powershell
# 6. Run integration tests
python .\test\test_admin_import.py      # Expected: 17/17 passing (Strapi imports)
python .\test\test_highway_import.py    # Expected: 16/16 passing (Strapi imports)
python .\test\test_amenity_import.py    # Expected: 17/17 passing (Strapi imports)
python .\test\test_landuse_import.py    # Expected: 16/16 passing (Strapi imports)
python .\test\test_geospatial_api.py    # Expected: 16/16 passing (FastAPI service)
# Total: 82 Strapi tests + 16 API tests = 98 tests passing

# 7. Start Geospatial Services API
cd geospatial_service
python main.py  # Runs on http://localhost:8001
# Expected: "✅ PostGIS connection pool initialized (5-20 connections)"
# Expected: "Buildings: 162,942; Highways: 27,719; POIs: 1,427; Landuse zones: 2,267; Regions: 11"

# 8. Verify all 5 imports in Strapi UI
# Open Strapi Admin > Content Manager
# Check: Buildings (162,942), Regions (304), Highways (22,719), POIs (1,427), Landuse Zones (2,267)
```

### **Step 3: Understand Priority System**

```text
TIER 1: Complete GeoJSON Imports ✅ DONE (Phase 1.10)
├─ Buildings import (162,942 features) ✅
├─ Admin import (304 regions, 4 levels) ✅
├─ Highway import (22,719 roads) ✅
├─ Amenity import (1,427 POIs) ✅
└─ Landuse import (2,267 zones) ✅

TIER 2: Enable Spawning Queries ✅ DONE (Phase 1.11)
├─ FastAPI Geospatial Services (port 8001) ✅
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
│  │  │  • /api/drivers            • /api/conductors       • /api/passengers               │       │ │
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
│  │  Port: 8001  │  Read-only asyncpg → PostgreSQL                                                │ │
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
│ ⚠️  DEPRECATED SYSTEMS - Do NOT use for new development                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ⛔ commuter_service_deprecated/ (Python - DEPRECATED October 26, 2025)                             │
│   • Tight coupling to Strapi internals                                                              │
│   • Mixed concerns, no Single Source of Truth pattern                                               │
│   • Replaced by: commuter_simulator/ (clean architecture with Infrastructure layer)                 │
│   • Status: Retained for reference only - DO NOT USE or enhance                                     │
│   • See: commuter_service_deprecated/DEPRECATED.md for migration guide                              │
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
│  ✅ Seed Data: "Barbados Typical Weekday" with realistic commuter patterns                            │
│    • Morning peak (8am): 2.8x spawn rate, residential buildings 2.5x multiplier                       │
│    • Evening peak (5pm): 2.3x spawn rate, commercial buildings 1.8x multiplier                        │
│    • Weekend: 0.7x Saturday, 0.5x Sunday                                                              │
│    • Linked to Barbados country (id=29), verified via API                                             │
│  📁 Files:                                                                                            │
│    • arknet-fleet-api/src/api/spawn-config/content-types/spawn-config/schema.json                    │
│    • arknet-fleet-api/src/components/spawning/*.json (6 components)                                  │
│    • seeds/seed_spawn_config.sql                                                                      │
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
**Last Updated**: October 26, 2025  
**Next Review**: After Phase 1.11 (Geospatial Services API complete)

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

> **🎯 HANDOFF COMPLETE**: A fresh agent with this CONTEXT.md + TODO.md can rebuild the environment, understand all architectural decisions, and continue to production-grade MVP without external context or chat history.
