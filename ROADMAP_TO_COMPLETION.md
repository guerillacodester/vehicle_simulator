# 🗺️ Roadmap to Completion — ArkNet Transit System

**Status**: Architecture Design Phase Complete  
**Current Date**: October 10, 2025  
**Branch**: branch-0.0.2.2  
**Overall Progress**: 85% Complete (Implementation) + New Architecture Designed

---

## 📊 Executive Summary

### ✅ What's Already Built (85%)

1. **Infrastructure** (100%)
   - PostgreSQL 17 + PostGIS 3.5
   - Strapi 5.23.5 Enterprise
   - Socket.IO Foundation (4 namespaces)
   - Python Socket.IO Client

2. **Priority 1: API Integration** (100%)
   - Production API data source
   - Geographic data loading (9,702 features)
   - Depot integration (5 active depots)
   - Poisson spawning with real data
   - Plugin-compatible architecture

3. **Priority 2: Real-Time Coordination** (60%)
   - ✅ Phase 1: Socket.IO foundation
   - ✅ Depot reservoir (FIFO queue)
   - ✅ Route reservoir (grid-based)
   - ❌ **Passenger Socket.IO events** (not implemented)
   - ❌ **Location-aware passengers** (not implemented)
   - ❌ **Conductor-driver coordination** (basic, needs enhancement)

### 🎨 What's Been Designed (This Session)

4. **NEW: LocationService Architecture** (Design Complete, 0% Implementation)
   - Single source of truth for position awareness
   - Geofence containment (circles MVP → polygons Phase 2)
   - Nearest entity queries (stops, POIs, places)
   - Event-driven trigger system
   - Real-time Strapi sync
   - Multi-actor coordination (passengers, conductors, drivers)

---

## 🎯 Current Position & Critical Decision Point

### You're At a Fork in the Road

**Option A: Complete Priority 2 First (Original Plan)**
- Finish passenger Socket.IO events
- Build location-aware passenger intelligence
- Complete conductor-driver coordination
- **Then** implement LocationService

**Option B: Build LocationService First (New Architecture)**
- LocationService is a **prerequisite** for:
  - Location-aware passengers (Priority 2, Phase 2)
  - Depot queue management (conductor needs geofence awareness)
  - Next-stop announcements (passenger feature)
- **Then** complete Priority 2 with full location context

**Option C: Hybrid Approach**
- Complete simple Priority 2 items without LocationService
- Build LocationService
- Enhance Priority 2 with location intelligence

---

## 📋 Recommended Path: Option B (LocationService First)

**Rationale**: LocationService unlocks multiple Priority 2 features simultaneously.

---

## 🚀 Phase-by-Phase Roadmap

### **PHASE 0: Foundation Cleanup** (30 minutes)

**Goal**: Ensure current codebase is ready for new work

- [ ] Run all existing tests (Priority 1 validation scripts)
- [ ] Verify Socket.IO infrastructure still works
- [ ] Check Strapi API connectivity
- [ ] Document any broken functionality
- [ ] Create git checkpoint: `pre-locationservice-implementation`

**Deliverables**:
- Test results summary
- Known issues list
- Clean git state

---

### **PHASE 1: LocationService MVP — Circle Geofences** (Week 1: 3-4 days)

**Goal**: Single source of truth for position awareness with circle geofences

#### **Day 1: Core Data Models** (3-4 hours)

- [ ] Create `arknet_transit_simulator/geospatial/` package
- [ ] Implement `models.py`:
  - [ ] `Point` class
  - [ ] `BoundingBox` class
  - [ ] `Geofence` class (circle geometry only)
  - [ ] `GeofenceEvent` class
  - [ ] `NearestResult` class
  - [ ] `LocationContext` class
- [ ] Unit tests for data models
- [ ] Validation: Models serialize/deserialize correctly

**Files Created**:
```
arknet_transit_simulator/geospatial/
  __init__.py
  models.py
  tests/
    test_models.py
```

**Success Criteria**:
- All model classes work correctly
- Geofence.contains() works for circles
- LocationContext serializes to JSON

#### **Day 2: LocationService Core** (4-5 hours)

- [ ] Implement `service.py`:
  - [ ] `LocationService.__init__()`
  - [ ] `get_location_context()`
  - [ ] `_get_containing_geofences()`
  - [ ] `_detect_transitions()`
  - [ ] Thread-safe add/remove/update geofences
- [ ] Implement `utils.py`:
  - [ ] `haversine_distance()`
  - [ ] Circle bbox computation
- [ ] Unit tests for LocationService
- [ ] Integration test: Add geofence, query position, detect enter/exit

**Files Created**:
```
arknet_transit_simulator/geospatial/
  service.py
  utils.py
  tests/
    test_service.py
    test_utils.py
```

**Success Criteria**:
- Can add/remove geofences at runtime
- Position queries return correct geofences
- Enter/exit events detected correctly
- Thread-safe concurrent queries

#### **Day 3: Strapi Integration** (3-4 hours)

- [ ] Create Strapi `geofence` content type (circle only)
- [ ] Add lifecycle hooks (auto-compute bbox)
- [ ] Implement `loaders.py`:
  - [ ] `load_from_strapi()`
  - [ ] `Geofence.from_strapi()`
- [ ] Create sample circle geofences in Strapi (3-5 depots)
- [ ] Test sync: Strapi → LocationService
- [ ] Test real-time updates (webhook or polling)

**Files Created**:
```
arknet_fleet_manager/arknet-fleet-api/src/api/geofence/
  content-types/geofence/schema.json
  content-types/geofence/lifecycles.js

arknet_transit_simulator/geospatial/
  loaders.py
  tests/
    test_loaders.py
```

**Success Criteria**:
- Strapi geofence content type works
- LocationService loads geofences from Strapi
- Updates propagate (webhook or 60s polling)
- Sample depot geofences defined

#### **Day 4: GPSDevice Integration** (3-4 hours)

- [ ] Modify `GPSDevice._data_worker()`:
  - [ ] Instantiate LocationService
  - [ ] Call `get_location_context()` every sample
  - [ ] Emit `geofence:event` via Socket.IO
  - [ ] Emit enriched `vehicle:location` with context
- [ ] Create example script: `examples/location_service_demo.py`
- [ ] Test with simulated GPS movement
- [ ] Verify enter/exit events fire correctly
- [ ] Update documentation

**Files Modified**:
```
arknet_transit_simulator/vehicle/gps_device/device.py
```

**Files Created**:
```
arknet_transit_simulator/geospatial/examples/
  location_service_demo.py
  README.md
```

**Success Criteria**:
- GPS device queries LocationService every sample
- Geofence events emitted via Socket.IO
- Simulated vehicle enters depot → event fires
- Documentation updated

**PHASE 1 MILESTONE**: LocationService MVP with circle geofences operational

---

### **PHASE 2: Nearest Entity Queries** (Week 2: 3-4 days)

**Goal**: Add spatial indexing and nearest stop/POI queries

#### **Day 1-2: Spatial Indexing** (6-8 hours)

- [ ] Install scipy (for KDTree)
- [ ] Implement `spatial_index.py`:
  - [ ] KDTree wrapper
  - [ ] Rebuild index on data changes
  - [ ] Query k-nearest neighbors
- [ ] Implement stop/POI data models
- [ ] Load stops from Strapi `route-stops`
- [ ] Build spatial index at startup
- [ ] Unit tests for spatial queries

**Files Created**:
```
arknet_transit_simulator/geospatial/
  spatial_index.py
  tests/
    test_spatial_index.py
```

**Success Criteria**:
- KDTree builds from stop/POI data
- Nearest stop query returns correct result
- Performance acceptable (< 1ms per query)

#### **Day 3: Complete LocationContext** (4-5 hours)

- [ ] Implement `get_nearest_stop()`
- [ ] Implement `get_nearest_poi()`
- [ ] Implement `get_nearest_place()`
- [ ] Add `nearby_*` queries (within radius)
- [ ] Update `get_location_context()` to populate all fields
- [ ] Integration tests with real Strapi data
- [ ] Performance test (1,200 concurrent queries)

**Success Criteria**:
- `LocationContext` returns all fields populated
- Nearest queries accurate
- Performance target: < 5ms per full context query
- Works with 9,702 real geographic features

#### **Day 4: Passenger Integration** (3-4 hours)

- [ ] Create `LocationAwarePassenger` class
- [ ] Implement continuous location queries
- [ ] Subscribe to `vehicle:location` events
- [ ] Calculate ETA to passenger
- [ ] Emit `passenger:stop_request` when ready
- [ ] Test passenger → conductor flow

**Files Created**:
```
commuter_service/location_aware_passenger.py
examples/passenger_location_demo.py
```

**Success Criteria**:
- Passenger queries location every 2 seconds
- Knows nearest stop name and distance
- Can request stop when vehicle nearby
- Events flow: passenger → conductor → driver

**PHASE 2 MILESTONE**: Full location intelligence operational

---

### **PHASE 3: Event-Driven Triggers** (Week 3: 3-4 days)

**Goal**: Declarative location-based automation

#### **Day 1-2: Trigger System** (6-8 hours)

- [ ] Create `triggers/` package
- [ ] Implement trigger models:
  - [ ] `LocationTrigger`
  - [ ] `TriggerCondition` (geofence, proximity, distance)
  - [ ] `TriggerAction` (callback, GPIO, Socket.IO, log)
  - [ ] `TriggerEvent`
- [ ] Implement `evaluator.py`:
  - [ ] `evaluate_triggers()`
  - [ ] Debouncing logic
  - [ ] Rate limiting
- [ ] Implement `executor.py`:
  - [ ] Action execution
  - [ ] Error handling
  - [ ] GPIO support (optional)
- [ ] Unit tests

**Files Created**:
```
arknet_transit_simulator/geospatial/triggers/
  __init__.py
  models.py
  conditions.py
  actions.py
  evaluator.py
  executor.py
  tests/
    test_triggers.py
```

**Success Criteria**:
- Can define triggers programmatically
- Triggers evaluate correctly
- Actions execute (callbacks tested)
- Thread-safe trigger updates

#### **Day 3: Strapi Trigger Storage** (3-4 hours)

- [ ] Create Strapi `location-trigger` content type
- [ ] Implement trigger JSON schema
- [ ] Load triggers from Strapi
- [ ] Test CRUD operations
- [ ] Create sample triggers (depot entry, stop proximity)

**Files Created**:
```
arknet_fleet_manager/arknet-fleet-api/src/api/location-trigger/
  content-types/location-trigger/schema.json
```

**Success Criteria**:
- Triggers stored in Strapi
- LocationService loads triggers at startup
- Can add/remove triggers via admin UI

#### **Day 4: Conductor/Driver Coordination** (4-5 hours)

- [ ] Define depot entry trigger
- [ ] Define depot stop position trigger (10m from center)
- [ ] Update `Conductor`:
  - [ ] Subscribe to `trigger:depot_entry`
  - [ ] Monitor distance to depot center
  - [ ] Emit `driver:stop_command` at 10m
- [ ] Update `Driver`:
  - [ ] Subscribe to `driver:stop_command`
  - [ ] Execute stop maneuver
  - [ ] Emit `vehicle:stopped`
- [ ] Test complete flow: GPS → trigger → conductor → driver

**Success Criteria**:
- Vehicle enters depot geofence → trigger fires
- Conductor detects 10m position → commands stop
- Driver stops at precise location
- Events logged correctly

**PHASE 3 MILESTONE**: Event-driven coordination operational

---

### **PHASE 4: Polygon Geofences** (Week 4: 2-3 days)

**Goal**: Add polygon support for precise boundaries

#### **Day 1: Polygon Geometry** (4-5 hours)

- [ ] Add polygon support to `Geofence` class
- [ ] Implement `point_in_polygon()` (ray casting)
- [ ] Add polygon bbox computation
- [ ] Add polygon validation (closed ring)
- [ ] Unit tests (complex polygons, holes, edge cases)

**Success Criteria**:
- Polygon containment works correctly
- Bbox optimization effective
- Performance acceptable

#### **Day 2: Strapi Polygon Support** (3-4 hours)

- [ ] Update geofence schema (add polygon field)
- [ ] Update lifecycle hooks (polygon bbox)
- [ ] Test polygon CRUD
- [ ] Create sample polygon geofences
- [ ] Import polygon from GeoJSON file

**Success Criteria**:
- Can create polygon geofences in Strapi
- LocationService loads polygons correctly
- Hybrid (circles + polygons) works

#### **Day 3: Map Drawing Tool (Optional)** (4-6 hours)

- [ ] Research Strapi map plugins
- [ ] Install strapi-plugin-mapbox or similar
- [ ] Configure map-based polygon drawing
- [ ] Test polygon creation via map UI

**Success Criteria**:
- Can draw polygons on map
- GeoJSON auto-generated
- Saves to Strapi correctly

**PHASE 4 MILESTONE**: Full geometry support complete

---

### **PHASE 5: Priority 2 Completion** (Week 5: 2-3 days)

**Goal**: Finish remaining Priority 2 items with LocationService

#### **Items to Complete**:

1. **Passenger Socket.IO Events** (2-3 hours)
   - [ ] Implement missing passenger events (boarding, alighting, journey)
   - [ ] Update TypeScript event definitions
   - [ ] Test passenger lifecycle

2. **Multi-Passenger Capacity Management** (3-4 hours)
   - [ ] Real-time seat tracking
   - [ ] Boarding queue with capacity limits
   - [ ] Dynamic passenger flow
   - [ ] Test with 50+ passengers per vehicle

3. **Route-Based Pickup Continuation** (3-4 hours)
   - [ ] Monitor route stops after depot departure
   - [ ] Integrate route reservoir
   - [ ] Dynamic pickup optimization
   - [ ] Test depot → route transition

4. **Fleet Coordination** (2-3 hours)
   - [ ] Multi-vehicle coordination logic
   - [ ] Performance metrics (pickup efficiency)
   - [ ] Load balancing
   - [ ] Test with 100+ vehicles

5. **Complete Vehicle Cycle** (2-3 hours)
   - [ ] End-to-end journey: spawn → pickup → transport → dropoff
   - [ ] Conductor decision logic
   - [ ] Driver route optimization
   - [ ] Integration test (full cycle)

**PHASE 5 MILESTONE**: Priority 2 100% complete

---

### **PHASE 6: Testing & Documentation** (Week 6: 2-3 days)

#### **Day 1: Comprehensive Testing** (6-8 hours)

- [ ] Unit tests (all modules > 80% coverage)
- [ ] Integration tests (end-to-end flows)
- [ ] Performance tests (1,200 vehicles)
- [ ] Load tests (concurrent queries)
- [ ] Stress tests (edge cases)
- [ ] Fix all failing tests

#### **Day 2: Documentation** (4-6 hours)

- [ ] Update `README.md` (quick start)
- [ ] Update `TODO.md` (mark complete)
- [ ] Create `DEPLOYMENT_GUIDE.md`
- [ ] Create `API_REFERENCE.md` (LocationService)
- [ ] Create video tutorial (optional)
- [ ] Update architecture diagrams

#### **Day 3: Cleanup & Release** (3-4 hours)

- [ ] Code review (self-review all changes)
- [ ] Remove commented code
- [ ] Format all files
- [ ] Run linters (TypeScript, Python)
- [ ] Git cleanup (squash commits if needed)
- [ ] Create release tag: `v1.0.0`
- [ ] Merge to main branch

**PHASE 6 MILESTONE**: Production-ready release

---

## 📊 Time Estimates

### By Phase

| Phase | Description | Duration | Cumulative |
|-------|-------------|----------|------------|
| 0 | Foundation cleanup | 0.5 days | 0.5 days |
| 1 | LocationService MVP (circles) | 4 days | 4.5 days |
| 2 | Nearest entity queries | 4 days | 8.5 days |
| 3 | Event-driven triggers | 4 days | 12.5 days |
| 4 | Polygon geofences | 3 days | 15.5 days |
| 5 | Priority 2 completion | 3 days | 18.5 days |
| 6 | Testing & documentation | 3 days | 21.5 days |

**Total**: ~22 working days (4-5 weeks)

### By Week

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | LocationService MVP | Circle geofences, GPS integration |
| 2 | Nearest queries | Spatial indexing, passenger integration |
| 3 | Triggers | Declarative automation, conductor coordination |
| 4 | Polygons | Precise boundaries, map tools |
| 5 | Priority 2 | Complete remaining features |
| 6 | Polish | Testing, docs, release |

---

## 🎯 Critical Path

**Blockers** (must complete in order):

1. **LocationService Core** → Required for all location-aware features
2. **Spatial Indexing** → Required for nearest queries
3. **Triggers** → Required for conductor automation
4. **Priority 2 Items** → Depends on 1-3

**Parallel Work** (can do simultaneously):

- Strapi content types (can create while building LocationService)
- Documentation (can write alongside code)
- Testing (can write tests before/during implementation)

---

## ⚠️ Risk & Mitigation

### Risk 1: Complexity Overwhelm

**Symptom**: Too many new concepts at once  
**Mitigation**: 
- Start with simplest version (circles, no triggers)
- Add one feature at a time
- Test thoroughly before moving on

### Risk 2: Strapi Integration Issues

**Symptom**: Content types don't work as expected  
**Mitigation**:
- Test Strapi schemas manually first
- Use Strapi admin UI to verify
- Fallback: Load from JSON files

### Risk 3: Performance Problems

**Symptom**: Queries too slow for 1,200 vehicles  
**Mitigation**:
- Profile early (Day 2 of each phase)
- Optimize bbox filtering
- Add spatial index (R-tree) if needed

### Risk 4: Scope Creep

**Symptom**: Adding too many features  
**Mitigation**:
- Stick to MVP for Phase 1-2
- Defer "nice to have" to Phase 4+
- Review roadmap weekly

---

## 📝 Success Criteria (Final)

### LocationService

- [ ] Single source of truth for all position queries
- [ ] Supports circles and polygons
- [ ] Real-time add/remove/update (Strapi-synced)
- [ ] Thread-safe concurrent queries
- [ ] < 5ms per location context query
- [ ] Works with 1,200 concurrent vehicles

### Priority 2

- [ ] Passenger Socket.IO events complete
- [ ] Location-aware passengers operational
- [ ] Conductor-driver coordination automated
- [ ] Multi-passenger capacity management
- [ ] Route-based pickup continuation
- [ ] Fleet coordination and analytics
- [ ] Complete vehicle cycle (spawn → dropoff)

### Overall System

- [ ] All tests passing (unit + integration)
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Clean, maintainable codebase
- [ ] Production-ready

---

## 🚦 Next Immediate Action

**CHOOSE YOUR PATH:**

### Option A: Start LocationService MVP Now (Recommended)

```bash
# Create package
mkdir -p arknet_transit_simulator/geospatial/tests
mkdir -p arknet_transit_simulator/geospatial/triggers
mkdir -p arknet_transit_simulator/geospatial/examples

# Create initial files
touch arknet_transit_simulator/geospatial/__init__.py
touch arknet_transit_simulator/geospatial/models.py
touch arknet_transit_simulator/geospatial/service.py
touch arknet_transit_simulator/geospatial/utils.py
touch arknet_transit_simulator/geospatial/loaders.py

# Start with models
code arknet_transit_simulator/geospatial/models.py
```

**What I'll implement**: Complete Day 1 (Core Data Models) in 3-4 hours

### Option B: Finish Priority 2 Without LocationService First

- Complete passenger events (2-3 hours)
- Simple conductor-driver coordination (1-2 hours)
- Basic capacity management (2-3 hours)
- **Then** build LocationService

### Option C: Foundation Cleanup First

- Run all validation scripts
- Check Socket.IO still works
- Verify Strapi connectivity
- Document current state
- **Then** proceed to Option A or B

---

## 📞 Decision Point

**Which path do you want to take?**

1. **Start LocationService MVP now** (my recommendation)
2. **Finish Priority 2 first, LocationService later**
3. **Foundation cleanup, then decide**
4. **Something else** (tell me your preference)

Let me know and I'll start implementing immediately.
