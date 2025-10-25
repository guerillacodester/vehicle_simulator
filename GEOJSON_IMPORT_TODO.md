# GeoJSON Import System - Implementation Plan (SINGLE SOURCE OF TRUTH)

**Date**: October 25, 2025  
**Project**: ArkNet Vehicle Simulator  
**Status**: ⚠️ CRITICAL - PostGIS Migration Required  
**Last Updated**: October 25, 2025 18:05

> **📌 COMPANION DOCUMENTS**:  
>
> - `GEOJSON_IMPORT_CONTEXT.md` for architecture details  
> - `DB_AUDIT_POSTGIS_GTFS.md` for database compliance audit  
> - **🚨 READ BEFORE CONTINUING**: PostGIS migration is MANDATORY

---

## 🚨 **CRITICAL BLOCKER: DATABASE RESTRUCTURE REQUIRED**

**Status**: Database structure does NOT comply with PostGIS/GTFS best practices  
**Impact**: System will have poor performance, high costs, limited spatial capabilities  
**Action Required**: Execute comprehensive PostGIS migration IMMEDIATELY

### Migration Files Created

1. `migrate_all_to_postgis.sql` - Comprehensive migration script
2. `DB_AUDIT_POSTGIS_GTFS.md` - Full compliance audit

### What Was Fixed

✅ **highways** - Migrated to PostGIS LineString (Oct 25, 2025)  
⏳ **stops** - NEEDS PostGIS Point migration  
⏳ **shapes** - NEEDS PostGIS LineString aggregation table  
⏳ **depots** - NEEDS PostGIS Point migration  
⏳ **landuse_zones, pois, regions** - Have PostGIS but need cleanup

**DO NOT PROCEED** with batch imports until migration is complete!

---

## 📋 **IMPLEMENTATION STRATEGY**

This plan follows a **validate-at-each-step** approach:

1. ✅ **Country Schema + Action Buttons** → Migrate schema & verify UI works
2. ✅ **Redis + Reverse Geocoding** → Get infrastructure running & benchmark <200ms
3. ✅ **Geofencing** → Test real-time notifications work
4. ✅ **POI-Based Spawning** → Integrate POIs with Poisson system
5. ✅ **Depot/Route Spawners** → Verify commuter generation meets specs
6. ✅ **Conductor Communication** → End-to-end validation with all systems

**Total Estimated Effort**: ~100-140 hours (2.5-3.5 weeks full-time)

---

## 🎨 **PHASE 1: COUNTRY SCHEMA + ACTION BUTTONS**

**Estimated**: 14-18 hours  
**Goal**: Update country content-type, add action buttons, successfully migrate schema, verify button functionality in Strapi admin.

---

### **Task 1.1: Analyze Current Country Schema** (2-3 hours)

- [ ] **1.1.1** Read current country schema
  - File: `arknet_fleet_manager/arknet-fleet-api/src/api/country/content-types/country/schema.json`
  - Document existing fields: name, iso_code, geometry, etc.
  - Check if action-buttons plugin is installed
  
- [ ] **1.1.2** Verify action-buttons plugin installation
  - Check `package.json` for `@artechventure/strapi-action-buttons`
  - If missing: `npm install @artechventure/strapi-action-buttons --save`
  - Restart Strapi: `npm run develop`
  
- [ ] **1.1.3** Review plugin documentation
  - Read plugin README: <https://github.com/artechventure/strapi-action-buttons>
  - Understand field configuration: `buttonLabel`, `onClick`, `metadata`
  - Identify required customType: `plugin::action-buttons.buttons`

---

### **Task 1.2: Design Action Buttons Schema** (3-4 hours)

- [ ] **1.2.1** Define button configuration
  - Create buttons for each GeoJSON file type:
    - Import Highways
    - Import Amenities/POIs
    - Import Landuse Zones
    - Import Buildings
    - Import Admin Boundaries
    - View Import Stats
    - Clear Redis Cache
  
- [ ] **1.2.2** Design import status tracking field
  - Add `geodata_import_status` field (JSON)
  - Track status for: highway, amenity, landuse, building, admin
  - Fields: status, lastImportDate, featureCount, lastJobId
  
- [ ] **1.2.3** Plan schema migration strategy
  - Decide: Manual edit or use Strapi admin?
  - Create backup of current schema
  - Document rollback procedure

---

### **Task 1.3: Update Country Schema** (2-3 hours)

- [ ] **1.3.1** Add action buttons field to schema
  - File: `arknet_fleet_manager/arknet-fleet-api/src/api/country/content-types/country/schema.json`
  - Add `geodata_import_buttons` with customField type
  - Configure all button definitions
  
- [ ] **1.3.2** Add import status field to schema
  - Add `geodata_import_status` as JSON type
  - Set default values for all file types

---

### **Task 1.4: Run Migration & Verify** (3-4 hours)

- [ ] **1.4.1** Backup database
  - Export current database: `pg_dump arknet_fleet > backup_pre_migration.sql`
  - Save schema.json backup: `cp schema.json schema.json.backup`
  
- [ ] **1.4.2** Restart Strapi to trigger migration
  - Stop Strapi
  - Start Strapi: `npm run develop`
  - Watch logs for migration success/errors
  
- [ ] **1.4.3** Verify schema in database
  - Check PostgreSQL columns for new fields
  - Verify `geodata_import_buttons` and `geodata_import_status` exist
  
- [ ] **1.4.4** Test in Strapi admin UI
  - Navigate to Content Manager → Country → Barbados
  - Verify action buttons render correctly
  - Click each button (expect console errors - handlers not implemented yet)
  - Verify `geodata_import_status` shows default JSON

---

### **Task 1.5: Implement Window Handlers** (4-5 hours)

- [ ] **1.5.1** Create global handlers file
  - File: `arknet_fleet_manager/arknet-fleet-api/admin-extensions/geojson-handlers.js`
  - Implement `window.importGeoJSON(entityId, metadata)`
  - Implement `window.viewImportStats(entityId, metadata)`
  - Implement `window.clearRedisCache(entityId, metadata)`
  
- [ ] **1.5.2** Inject handlers into Strapi admin
  - Choose injection method (script tag, plugin hooks, webpack)
  - Test handlers are globally available
  
- [ ] **1.5.3** Test handlers in browser console
  - Open Strapi admin → Country → Barbados
  - Open browser DevTools console
  - Test: `window.importGeoJSON(1, { fileType: 'highway' })`
  - Verify: Console logs appear, fetch request sent

---

### **Task 1.6: Phase 1 Validation** (1 hour)

**✅ Phase 1 Complete When:**

- [x] Country schema migration successful
- [x] Action buttons render in Strapi admin
- [x] Window handlers trigger (even if API doesn't exist yet)
- [x] Changes committed to Git

**📝 Document Issues:**

- Record migration errors (if any)
- Note UI rendering issues
- Plan fixes for next iteration

**💾 Commit:**

```bash
git add schema.json geojson-handlers.js
git commit -m "feat: Add GeoJSON import action buttons to country schema"
git push origin branch-0.0.2.6
```

---

## 🔴 **PHASE 2: REDIS + REVERSE GEOCODING**

**Estimated**: 18-24 hours  
**Goal**: Install Redis, implement geospatial indexing, build reverse geocoding service, benchmark <200ms performance.

---

### **Task 2.1: Redis Infrastructure Setup** (4-6 hours)

- [ ] **2.1.1** Install Redis on Windows
  - Download Redis for Windows (or use WSL)
  - Start Redis server: `redis-server`
  - Test connection: `redis-cli ping` → PONG
  
- [ ] **2.1.2** Configure Redis for production
  - Set password in `redis.conf`
  - Enable persistence (appendonly)
  - Set max memory and eviction policy
  
- [ ] **2.1.3** Install Redis client for Node.js
  - Navigate to: `arknet_fleet_manager/arknet-fleet-api/`
  - Install: `npm install ioredis --save`
  
- [ ] **2.1.4** Create Redis client utility
  - File: `src/utils/redis-client.js`
  - Configure connection with retry strategy
  - Add error handling and logging
  
- [ ] **2.1.5** Add Redis config to environment
  - File: `.env`
  - Add: REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
  
- [ ] **2.1.6** Test Redis connection
  - Create test script: `scripts/test-redis.js`
  - Test SET/GET operations
  - Verify connection works

---

### **Task 2.2: Redis Geospatial Service** (6-8 hours)

- [ ] **2.2.1** Create Redis geospatial service
  - File: `src/services/redis-geo.service.js`
  - Implement: `addHighway(countryCode, lon, lat, highwayId, metadata)`
  - Implement: `addPOI(countryCode, lon, lat, poiId, metadata)`
  - Implement: `findNearbyHighways(countryCode, lon, lat, radiusMeters)`
  - Implement: `findNearbyPOIs(countryCode, lon, lat, radiusMeters)`
  - Implement: `getReverseGeocode(lat, lon)` (cache lookup)
  - Implement: `setReverseGeocode(lat, lon, address, ttl)`
  - Implement: `clearCountryCache(countryCode)`
  
- [ ] **2.2.2** Write unit tests
  - Test GEOADD operations
  - Test GEORADIUS queries
  - Test cache operations
  - Test error handling
  
- [ ] **2.2.3** Manual testing with sample data
  - Add test highway: Tom Adams Highway
  - Add test POI: Bridgetown Mall
  - Query nearby features
  - Verify results accuracy

---

### **Task 2.3: Reverse Geocoding API** (4-5 hours)

- [ ] **2.3.1** Create reverse geocoding controller
  - File: `src/api/reverse-geocode/controllers/reverse-geocode.js`
  - Endpoint: `GET /api/reverse-geocode?lat={lat}&lon={lon}`
  - Logic: Check cache → Query Redis → Format address → Cache result
  
- [ ] **2.3.2** Register routes
  - File: `src/api/reverse-geocode/routes/reverse-geocode.js`
  - Register GET endpoint
  - Configure auth (public for testing)
  
- [ ] **2.3.3** Test API endpoint
  - Test with sample coordinates
  - Verify cache hit/miss behavior
  - Test address formatting

---

### **Task 2.4: Performance Benchmarking** (4-5 hours)

- [ ] **2.4.1** Create benchmark script
  - File: `scripts/benchmark-reverse-geocode.js`
  - Generate 100 test coordinates
  - Measure cache hit/miss latency
  - Calculate avg, p95, p99
  
- [ ] **2.4.2** Run benchmark
  - Execute benchmark script
  - Record results
  - Verify targets met
  
- [ ] **2.4.3** Compare with PostgreSQL baseline
  - Test existing `/api/geofence/find-nearby-features-fast`
  - Measure same 100 queries
  - Compare Redis vs PostgreSQL
  - Target: 10x+ improvement
  
- [ ] **2.4.4** Document performance
  - Create: `docs/redis-performance-benchmark.md`
  - Record comparison results
  - Note optimization opportunities

---

### **Task 2.5: Phase 2 Validation** (1 hour)

**✅ Phase 2 Complete When:**

- [x] Redis server running and accessible
- [x] Reverse geocoding API responding
- [x] Cache hit latency <10ms
- [x] Cache miss latency <200ms
- [x] 10x+ faster than PostgreSQL baseline

**💾 Commit:**

```bash
git add redis-client.js redis-geo.service.js reverse-geocode/
git commit -m "feat: Implement Redis geospatial service for reverse geocoding"
git push origin branch-0.0.2.6
```

---

## 🔔 **PHASE 3: GEOFENCING**

**Estimated**: 12-16 hours  
**Goal**: Implement Redis Pub/Sub for vehicle positions, detect geofence enter/exit events, emit real-time Socket.IO notifications.

---

### **Task 3.1: Redis Pub/Sub Infrastructure** (4-5 hours)

- [ ] **3.1.1** Create geofence service
  - File: `src/services/geofence-notifier.service.js`
  - Subscribe to `vehicle:position` channel
  - On message: Check nearby features using Redis GEORADIUS
  - Emit Socket.IO event if features found
  
- [ ] **3.1.2** Update GPS device to publish positions
  - File: `arknet_transit_simulator/vehicle/gps_device.py`
  - Add Redis client: `pip install redis`
  - On position update: `redis.publish('vehicle:position', json.dumps(data))`
  
- [ ] **3.1.3** Test Pub/Sub latency
  - Publish 100 position updates
  - Measure publish → Socket.IO emission time
  - Target: <10ms average latency

---

### **Task 3.2: Geofence Detection Logic** (4-5 hours)

- [ ] **3.2.1** Implement proximity detection
  - Method: `detectProximity(vehicleId, lat, lon, countryCode)`
  - Query Redis for nearby highways (50m)
  - Query Redis for nearby POIs (100m)
  - Compare with vehicle's last known location
  
- [ ] **3.2.2** Implement geofence enter/exit logic
  - Track vehicle state in Redis: `vehicle:{id}:current_highway`
  - Detect transitions: entered vs exited
  - Avoid duplicate notifications
  
- [ ] **3.2.3** Add reverse geocode enrichment
  - When geofence entered, fetch full address
  - Try cache first
  - Format: "{highway name}, near {poi name}"
  - Cache result

---

### **Task 3.3: Socket.IO Event Integration** (3-4 hours)

- [ ] **3.3.1** Define Socket.IO event schema
  - Event: `geofence:entered`
  - Event: `geofence:exited`
  - Include: vehicleId, location, highway, poi, address
  
- [ ] **3.3.2** Update vehicle client to listen for events
  - File: `arknet_transit_simulator/vehicle/socketio_client.py`
  - Add handlers for geofence events
  - Log events or trigger actions
  
- [ ] **3.3.3** Test with multiple vehicles
  - Start 10 vehicles on different routes
  - Monitor geofence events in real-time
  - Verify no duplicate notifications
  - Verify correct enter/exit sequences

---

### **Task 3.4: Phase 3 Validation** (1 hour)

**✅ Phase 3 Complete When:**

- [x] Geofence events emit via Socket.IO
- [x] Vehicle enter/exit detection working
- [x] Latency <10ms for notifications
- [x] No duplicate notifications
- [x] Multiple vehicles tested successfully

**💾 Commit:**

```bash
git add geofence-notifier.service.js gps_device.py
git commit -m "feat: Implement Redis Pub/Sub geofencing with Socket.IO"
git push origin branch-0.0.2.6
```

---

## 🎯 **PHASE 4: POI-BASED SPAWNING**

**Estimated**: 20-26 hours  
**Goal**: Import GeoJSON data (highway, amenity, landuse), integrate POIs with Poisson spawning system, calibrate activity levels.

---

### **Task 4.1: GeoJSON Import Service - Core** (6-8 hours)

- [ ] **4.1.1** Install dependencies
  - `npm install JSONStream turf --save`
  - JSONStream: Streaming parser for large files
  - Turf: Geospatial calculations (centroid)
  
- [ ] **4.1.2** Create import service file
  - File: `src/services/geojson-import.service.js`
  - Class: `GeoJSONImportService`
  
- [ ] **4.1.3** Implement file validation
  - Method: `validateImportRequest(countryId, fileType)`
  - Check country exists
  - Check file exists in `sample_data/`
  - Check file type supported
  
- [ ] **4.1.4** Implement streaming JSON parser
  - Method: `streamParseGeoJSON(filePath, onFeature)`
  - Use JSONStream for memory efficiency
  - Emit progress events every 100 features
  
- [ ] **4.1.5** Create import job tracking
  - Add `import_job` table to database
  - Track: status, progress, errors
  - Update every 100 features

---

### **Task 4.2: Property Transformers** (6-8 hours)

- [ ] **4.2.1** Create transformer for Highway
  - File: `src/transformers/highway.transformer.js`
  - Extract: osm_id, highway_type, name, ref, lanes, maxspeed
  - Calculate midpoint of LineString for center coordinates
  - Return object matching highway schema
  
- [ ] **4.2.2** Create transformer for Amenity/POI
  - File: `src/transformers/amenity.transformer.js`
  - Extract: osm_id, amenity (→ poi_type), name
  - Handle MultiPolygon: Calculate centroid using Turf
  - Assign activity_level by amenity type
  - Store other properties in metadata JSON
  
- [ ] **4.2.3** Create transformer for Landuse
  - File: `src/transformers/landuse.transformer.js`
  - Extract: osm_id, landuse_type, name
  - Calculate centroid of MultiPolygon
  - Assign spawn_weight by landuse type
  - Assign population_density defaults
  
- [ ] **4.2.4** Write unit tests
  - Test each transformer with sample features
  - Test centroid calculation accuracy
  - Test edge cases (null properties, missing geometry)

---

### **Task 4.3: Import Implementation** (5-6 hours)

- [ ] **4.3.1** Create import API endpoint
  - File: `src/api/geojson-import/controllers/geojson-import.js`
  - Endpoint: `POST /api/geojson-import`
  - Body: `{ countryId, fileType }`
  - Start async import, return job ID
  
- [ ] **4.3.2** Implement highway import workflow
  - Stream parse `sample_data/highway.geojson`
  - Transform each feature
  - Batch insert to database (100 at a time)
  - Update Redis geospatial index
  - Update job progress
  
- [ ] **4.3.3** Implement amenity import workflow
  - Stream parse `sample_data/amenity.geojson`
  - Transform features (handle MultiPolygon)
  - Batch insert to `poi` table
  - Update Redis geospatial index
  
- [ ] **4.3.4** Implement landuse import workflow
  - Stream parse `sample_data/landuse.geojson`
  - Transform features
  - Batch insert to `landuse_zone` table

---

### **Task 4.4: Poisson Integration** (3-4 hours)

- [ ] **4.4.1** Update activity levels
  - File: `commuter_service/poisson_geojson_spawner.py`
  - Expand `activity_levels` dictionary with all OSM amenity types
  - Add time-of-day modifiers for context-sensitive types
  
- [ ] **4.4.2** Test SimpleSpatialZoneCache
  - Restart commuter service
  - Verify cache loads new POIs from Strapi
  - Check memory usage with 3,694 zones
  
- [ ] **4.4.3** Initial spawn rate test
  - Run spawner for 1 hour
  - Log spawn counts by zone and amenity
  - Calculate actual spawn rate
  - Note if calibration needed

---

### **Task 4.5: Phase 4 Validation** (1 hour)

**✅ Phase 4 Complete When:**

- [x] Highway, Amenity, Landuse imported successfully
- [x] POIs visible in Strapi admin
- [x] Redis geospatial indexes populated
- [x] SimpleSpatialZoneCache loading new POIs
- [x] Spawn rate roughly maintains target (fine-tuning in Phase 5)

**💾 Commit:**

```bash
git add geojson-import.service.js transformers/ poisson_geojson_spawner.py
git commit -m "feat: Implement GeoJSON import with POI-based spawning"
git push origin branch-0.0.2.6
```

---

## 🚌 **PHASE 5: DEPOT/ROUTE SPAWNERS**

**Estimated**: 18-24 hours  
**Goal**: Verify depot and route spawning systems generate commuters according to specs, integrate with POI data, calibrate spawn rates.

---

### **Task 5.1: Depot Spawner Analysis** (4-5 hours)

- [ ] **5.1.1** Review depot_reservoir.py architecture
  - Understand FIFO queue mechanism
  - Identify spawn rate calculation
  - Check proximity-based spawn logic
  
- [ ] **5.1.2** Analyze depot spawn requirements
  - Target: Journey start spawns (1.0x temporal multiplier)
  - Requirement: Spawn near depot locations
  - Integration: Use depot POIs from imported data
  
- [ ] **5.1.3** Test current depot spawner
  - Run depot spawner for 1 hour
  - Log spawn counts
  - Log spawn locations (near depots?)
  - Identify gaps

---

### **Task 5.2: Route Spawner Analysis** (4-5 hours)

- [ ] **5.2.1** Review route_reservoir.py architecture
  - Understand grid-based spatial indexing
  - Identify spawn rate calculation
  - Check route segment logic
  
- [ ] **5.2.2** Analyze route spawn requirements
  - Target: Already traveling spawns (0.5x temporal multiplier)
  - Requirement: Spawn along active routes
  - Integration: Use route segment + nearby POIs
  
- [ ] **5.2.3** Test current route spawner
  - Run route spawner for 1 hour
  - Log spawn counts by route segment
  - Log spawn distribution
  - Identify gaps

---

### **Task 5.3: Spawn Rate Calibration** (6-8 hours)

- [ ] **5.3.1** Analyze spawn distribution
  - Run both spawners for 2 hours
  - Log detailed spawn metrics:
    - Total spawns/hour (target: 90-180)
    - Depot vs route split
    - Spawns by amenity type
    - Spawns by landuse zone
  
- [ ] **5.3.2** Identify over/under-represented zones
  - Find zones with >20% of total spawns
  - Find zones with <1% of total spawns
  - Adjust spawn_weight in database
  
- [ ] **5.3.3** Re-calibrate temporal multipliers
  - Current reduction: 18x
  - With new data, may need adjustment
  - Test different multipliers: 15x, 18x, 20x, 25x
  - Select multiplier maintaining 100/hr average
  
- [ ] **5.3.4** Fine-tune activity levels
  - Adjust POI activity_level based on actual usage
  - Test time-of-day modifiers
  - Verify realistic spawn patterns

---

### **Task 5.4: Integration Testing** (3-4 hours)

- [ ] **5.4.1** Test depot + route spawners together
  - Run both systems simultaneously
  - Monitor total spawn rate
  - Verify depot/route split reasonable
  
- [ ] **5.4.2** Test with vehicle operations
  - Start 5 vehicles on different routes
  - Verify spawns occur near vehicle paths
  - Verify depot spawns occur at depot locations
  
- [ ] **5.4.3** Load testing
  - Simulate 10 concurrent vehicles
  - Monitor spawn rate stability
  - Check for performance degradation

---

### **Task 5.5: Phase 5 Validation** (1 hour)

**✅ Phase 5 Complete When:**

- [x] Depot spawner generates commuters per specs
- [x] Route spawner generates commuters per specs
- [x] Combined spawn rate: 90-180/hr
- [x] Spawn distribution realistic (not clustered)
- [x] POI activity levels integrated
- [x] Temporal multipliers calibrated

**💾 Commit:**

```bash
git add depot_reservoir.py route_reservoir.py poisson_geojson_spawner.py
git commit -m "feat: Calibrate depot/route spawners with POI integration"
git push origin branch-0.0.2.6
```

---

## 🔗 **PHASE 6: CONDUCTOR COMMUNICATION**

**Estimated**: 14-18 hours  
**Goal**: Ensure conductor service communicates with depot/route spawners, validate end-to-end passenger flow.

---

### **Task 6.1: Conductor Architecture Analysis** (3-4 hours)

- [ ] **6.1.1** Locate conductor service
  - Search for conductor-related files
  - Understand conductor's role in system
  - Identify communication mechanism
  
- [ ] **6.1.2** Review spawner → conductor flow
  - How do spawners notify conductor?
  - Socket.IO events? Direct API calls?
  - What data is passed?
  
- [ ] **6.1.3** Document current state
  - Is communication already working?
  - What needs to be added/fixed?
  - What are the requirements?

---

### **Task 6.2: Communication Implementation** (5-7 hours)

- [ ] **6.2.1** Implement spawner → conductor events
  - Emit Socket.IO event when passenger spawned
  - Include: passengerId, location, destination, timestamp
  
- [ ] **6.2.2** Implement conductor listener
  - Subscribe to passenger spawn events
  - Process new passenger requests
  - Assign to appropriate vehicle/route
  
- [ ] **6.2.3** Test event flow
  - Trigger depot spawn
  - Verify conductor receives event
  - Verify event contains correct data

---

### **Task 6.3: End-to-End Testing** (4-5 hours)

- [ ] **6.3.1** Full system integration test
  - Start all services:
    - Strapi API
    - Redis
    - Depot spawner
    - Route spawner
    - Conductor service
    - Vehicle simulators (5 vehicles)
  
- [ ] **6.3.2** Validate passenger flow
  - Passenger spawns at depot → conductor notified
  - Passenger spawns on route → conductor notified
  - Conductor assigns passenger to vehicle
  - Vehicle picks up passenger
  - Passenger delivered to destination
  
- [ ] **6.3.3** Monitor for issues
  - Check for dropped events
  - Check for duplicate passengers
  - Check for orphaned passengers
  - Verify timing is realistic

---

### **Task 6.4: Phase 6 Validation** (2 hours)

**✅ Phase 6 Complete When:**

- [x] Conductor receives depot spawn events
- [x] Conductor receives route spawn events
- [x] Passengers assigned to vehicles correctly
- [x] End-to-end flow validated (spawn → assign → pickup → deliver)
- [x] No dropped/duplicate events
- [x] All systems communicating correctly

**💾 Final Commit:**

```bash
git add conductor_service/ spawning_coordinator.py
git commit -m "feat: Complete conductor communication with spawners"
git push origin branch-0.0.2.6
```

---

## ✅ **PROJECT COMPLETION CRITERIA**

### **All Phases Complete When:**

**✅ Infrastructure:**

- [x] Country schema migrated with action buttons
- [x] Redis server running and indexed
- [x] All GeoJSON data imported (highway, amenity, landuse)

**✅ Performance:**

- [x] Reverse geocoding <200ms (cache miss)
- [x] Reverse geocoding <10ms (cache hit)
- [x] Geofence notifications <10ms
- [x] Spawn rate: 90-180 commuters/hour

**✅ Integration:**

- [x] POI-based spawning operational
- [x] Depot spawner using imported data
- [x] Route spawner using imported data
- [x] Conductor receiving spawn events
- [x] End-to-end passenger flow validated

**✅ Quality:**

- [x] All unit tests passing
- [x] Performance benchmarks documented
- [x] No critical bugs
- [x] System stable under load

---

## 📊 **PROGRESS TRACKING**

**Current Phase**: Not Started  
**Status**: Planning Complete  
**Last Updated**: October 25, 2025

### **Phase Completion Status**

- [ ] Phase 1: Country Schema + Action Buttons (0%)
- [ ] Phase 2: Redis + Reverse Geocoding (0%)
- [ ] Phase 3: Geofencing (0%)
- [ ] Phase 4: POI-Based Spawning (0%)
- [ ] Phase 5: Depot/Route Spawners (0%)
- [ ] Phase 6: Conductor Communication (0%)

### **Overall Progress**: 0% (0/6 phases)

---

## 📝 **NOTES**

- Each task designed to be atomic (1-4 hours)
- Validate at end of each phase before proceeding
- Document issues immediately
- Commit frequently with clear messages
- Update progress tracking in real-time

---

**Document Version**: 2.0  
**Last Updated**: October 25, 2025  
**Next Review**: After Phase 1 completion
