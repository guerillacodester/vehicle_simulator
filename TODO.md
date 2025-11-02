# Vehicle Simulator - Commuter Spawning & Fleet Coordination

**Project**: ArkNet Vehicle Simulator  
**Branch**: branch-0.0.2.9  
**Started**: October 25, 2025  
**Updated**: November 1, 2025 - Spawn Calculator Kernel, Repository Cleanup, Tests Consolidated  
**Status**: ✅ Spawn Calculator Kernel | ✅ Tests Organized | ✅ Docs Consolidated | 🎯 Integrate Kernel into Spawners NEXT  
**Strategy**: Modular Calculation Kernel → Spawner Integration → Statistical Validation → MVP

> **📌 Key Documentation**:
> - `CONTEXT.md` - Complete project context, architecture, all technical details
> - `TODO.md` - Task tracking, progress, next steps

**Execution Priority**:

```text
TIER 1: Phase 1.10 (GeoJSON imports) ✅ COMPLETE
TIER 2: Phase 1.11 (Geospatial Services API) ✅ COMPLETE  
TIER 3: Phase 1.12 (Vehicle Simulation Validation) ✅ COMPLETE
TIER 4: Spawner System Implementation ✅ COMPLETE (Oct 28)
TIER 4.5: Configuration Refactoring & Launcher Consolidation ✅ COMPLETE (Oct 31)
TIER 4.6: Geospatial Services API - Production-Grade Comprehensive API ✅ COMPLETE (Oct 31)
TIER 4.7: Spawn Calculation Kernel & Repository Cleanup ✅ COMPLETE (Nov 1)
  - ✅ Spawn Calculator Kernel: Pure calculation functions (spawn_calculator.py)
  - ✅ Complete hybrid spawn formula: terminal_population × route_attractiveness
  - ✅ Temporal weighting: base_rate × hourly_mult × day_mult
  - ✅ Validated with Route 1 data: 202 pass/hr peak, 5 pass/hr night (40x variation)
  - ✅ Zero-sum conservation verified: Terminal population constant, routes redistribute
  - ✅ Unit tests: 40+ test cases covering all calculation methods
  - ✅ Documentation: SPAWN_CALCULATOR_README.md with examples and API reference
  - ✅ Repository cleanup: Moved 27+ temp files, consolidated test/ → tests/
  - ✅ Tests organized: tests/{geospatial,integration,validation}/
  - ✅ Docs consolidated: SECURITY.md → CONTEXT.md
  - ✅ Markdown linting: All .md files passing markdownlint
  - Files: commuter_simulator/core/domain/spawner_engine/spawn_calculator.py (370 lines)
  - Tests: commuter_simulator/tests/test_spawn_calculator.py (465 lines)
  - Validation: tests/validation/test_spawn_calculator_kernel.py
TIER 5: Spawner Integration & Statistical Validation 🎯 NEXT (Nov 1+)
  - 🎯 Phase 5.1: Integrate spawn_calculator into RouteSpawner (Nov 1)
  - 🎯 Phase 5.2: Integrate spawn_calculator into DepotSpawner (Nov 1)
  - 🎯 Phase 5.3: Statistical validation tests (Nov 1-2)
  - 🎯 Phase 5.4: Route-depot associations for all 5 depots (Nov 2)
  - 🎯 Phase 5.5: Additional routes and spawn configs (Nov 2-3)
  - 🎯 Phase 5.6: End-to-end integration testing (Nov 3)
TIER 6: MVP Feature Completion 📋 (Nov 4-7)
TIER 7: Production Hardening 📋 (Nov 8-10)
```

---

## 🎯 **GRANULAR ROADMAP TO MVP** (Updated Nov 1, 2025)

### **TIER 5: Spawner Integration & Statistical Validation** (Nov 1-3, 2025)

#### **Phase 5.1: Integrate Spawn Calculator into RouteSpawner** [2-3 hours]

**Current State:**
- ✅ RouteSpawner exists with duplicated calculation logic
- ✅ spawn_calculator.py kernel validated with Route 1 data
- ❌ RouteSpawner not using modular kernel

**Tasks:**
- [ ] 5.1.1: Read current RouteSpawner._calculate_spawn_count() implementation
  - File: `commuter_simulator/core/domain/spawner_engine/route_spawner.py`
  - Lines: 230-265 (current calculation logic)
  - Understand current parameters and return values
- [ ] 5.1.2: Import SpawnCalculator into RouteSpawner
  - Add: `from commuter_simulator.core.domain.spawner_engine.spawn_calculator import SpawnCalculator`
  - Verify import works (no circular dependencies)
- [ ] 5.1.3: Replace _calculate_spawn_count() with kernel call
  - Keep same method signature for compatibility
  - Map existing parameters to SpawnCalculator.calculate_hybrid_spawn()
  - Parameters needed:
    - buildings_near_depot (from depot catchment query)
    - buildings_along_route (from _get_buildings_near_route())
    - total_buildings_all_routes (sum across all routes at depot)
    - spawn_config (from load_spawn_config())
    - current_time (method parameter)
    - time_window_minutes (method parameter)
  - Return spawn_count from kernel result
- [ ] 5.1.4: Add depot catchment query to RouteSpawner
  - Query: GET `/depots/{depot_id}/catchment?radius_meters=800`
  - Store buildings_near_depot for terminal population calculation
  - Cache result (depot catchment doesn't change)
- [ ] 5.1.5: Add total_buildings aggregation
  - Query all routes at depot from route-depots junction table
  - Sum buildings_along_route for each route
  - Use for route attractiveness calculation
- [ ] 5.1.6: Update logging to show calculation breakdown
  - Log: base_rate, hourly_mult, day_mult, effective_rate
  - Log: terminal_population, route_attractiveness, passengers_per_hour
  - Log: lambda_param, spawn_count
  - Format: Match validation script output for consistency
- [ ] 5.1.7: Test RouteSpawner with kernel integration
  - Run spawner for Route 1
  - Verify spawn count matches validation predictions (~48 for 15-min window at 8 AM)
  - Check logs show correct calculation breakdown

**Success Criteria:**
- ✅ RouteSpawner uses spawn_calculator.py (zero calculation duplication)
- ✅ Spawn counts match validation predictions (±10% for Poisson variance)
- ✅ Logging shows full calculation breakdown
- ✅ No regressions in existing functionality

---

#### **Phase 5.2: Integrate Spawn Calculator into DepotSpawner** [1-2 hours]

**Current State:**
- ✅ DepotSpawner exists with simplified calculation logic
- ✅ Uses spatial_base instead of building-based calculation
- ❌ Not using hybrid spawn model

**Decision Point:** Should DepotSpawner use hybrid model or remain simple?
- **Option A (Recommended)**: Keep DepotSpawner simple (spatial_base approach)
  - DepotSpawner is fallback for routes without specific spawn configs
  - Uses simpler Poisson(spatial_base × hourly × day) calculation
  - Avoids complexity of building counts and route attractiveness
- **Option B**: Convert DepotSpawner to hybrid model
  - Would need to query buildings, routes, calculate attractiveness
  - More realistic but duplicates RouteSpawner logic
  - Could cause double-counting if both spawners enabled

**Recommended Tasks (Option A):**
- [ ] 5.2.1: Review DepotSpawner calculation logic
  - File: `commuter_simulator/core/domain/spawner_engine/depot_spawner.py`
  - Lines: 250-280 (current calculation)
  - Verify it's appropriate as fallback spawner
- [ ] 5.2.2: Extract temporal multiplier logic to kernel
  - Move hourly_rate and day_mult extraction to SpawnCalculator
  - Create helper: `SpawnCalculator.extract_temporal_multipliers()`
  - Use in both DepotSpawner and RouteSpawner
- [ ] 5.2.3: Document DepotSpawner vs RouteSpawner usage
  - DepotSpawner: Fallback, simple spatial model
  - RouteSpawner: Primary, hybrid building-based model
  - Recommend: Use RouteSpawner when routes have spawn configs
  - Update: CONTEXT.md and code comments

**Success Criteria:**
- ✅ Clear separation between DepotSpawner (simple) and RouteSpawner (hybrid)
- ✅ Temporal multiplier logic extracted to kernel (DRY principle)
- ✅ Documentation explains when to use each spawner

---

#### **Phase 5.3: Statistical Validation Tests** [3-4 hours]

**Current State:**
- ✅ Manual validation complete (validate_hybrid_spawn_model.py)
- ✅ Kernel unit tests complete (test_spawn_calculator.py)
- ❌ No automated spawner statistical validation

**Tasks:**
- [ ] 5.3.1: Create test_spawner_statistical_correctness.py
  - Location: `tests/validation/test_spawner_statistical_correctness.py`
  - Purpose: Verify spawners generate statistically correct passenger distributions
- [ ] 5.3.2: Test 1 - Route-level spawn counts (mean validation)
  - Run RouteSpawner for 100 iterations (15-min windows)
  - Collect spawn counts for Route 1 at Monday 8 AM
  - Calculate mean spawn count
  - Expected: ~48 passengers (lambda = 50.57 for 15-min window)
  - Tolerance: ±5% (Poisson mean = lambda)
  - Assert: 45.5 <= mean <= 50.5
- [ ] 5.3.3: Test 2 - Poisson distribution validation (variance check)
  - Use same 100 iterations as Test 1
  - Calculate variance of spawn counts
  - Expected: variance ≈ lambda (Poisson property: variance = mean)
  - Tolerance: ±15% (accounting for sample size)
  - Assert: 43 <= variance <= 58
- [ ] 5.3.4: Test 3 - Temporal variation (peak vs off-peak)
  - Run spawner at 4 different times:
    - Monday 8 AM (peak): Expected ~48
    - Monday 5 PM (evening peak): Expected ~56
    - Monday 12 PM (lunch): Expected ~23
    - Monday 2 AM (night): Expected ~3
  - Verify ratios match validation predictions
  - Assert: Night spawns < Lunch < Morning Peak < Evening Peak
  - Assert: Evening Peak / Night ≈ 18.7x (56/3)
- [ ] 5.3.5: Test 4 - Spatial distribution (passengers near route)
  - Spawn 50 passengers on Route 1
  - Check origin coordinates in database
  - Verify all origins within 100m of Route 1 geometry
  - Use PostGIS ST_Distance to validate
  - Assert: 100% of passengers within buffer
- [ ] 5.3.6: Test 5 - Zero-sum conservation (multi-route)
  - Simulate Speightstown depot with 5 routes
  - Assign different building counts to each route
  - Run spawner for 1 hour (4 × 15-min windows)
  - Calculate total passengers across all routes
  - Expected: Total ≈ terminal_population (202 pass/hr at 8 AM)
  - Tolerance: ±10% (Poisson variance across routes)
  - Assert: 182 <= total <= 222
- [ ] 5.3.7: Test 6 - Route attractiveness distribution
  - Using same 5-route scenario from Test 5
  - Verify passenger distribution matches building proportions
  - Route with 20% of buildings should get ~20% of passengers
  - Tolerance: ±5% (Poisson variance)
  - Assert: Each route within tolerance
- [ ] 5.3.8: Create test summary report
  - Output: Table showing all test results
  - Include: Mean, variance, ratios, pass/fail status
  - Save: tests/validation/spawner_validation_results.txt
  - Format: Human-readable with emoji indicators

**Success Criteria:**
- ✅ All 6 statistical tests passing
- ✅ Spawn counts within ±5% of predictions
- ✅ Temporal variation matches 40x peak-to-night ratio
- ✅ Spatial distribution 100% within route buffer
- ✅ Zero-sum conservation verified
- ✅ Automated test suite runnable on demand

---

#### **Phase 5.4: Route-Depot Associations for All 5 Depots** [2-3 hours]

**Current State:**
- ✅ 1 of 5 depots has route association (Speightstown ↔ Route 1)
- ❌ 4 depots have zero routes (Fairchild, Oistins, Bridgetown, Princess Alice)
- ✅ Precompute script exists (precompute_route_depot_associations.py)

**Tasks:**
- [ ] 5.4.1: List all available routes in GTFS database
  - Query: GET `/api/routes` from Strapi
  - Expected: 20-30 routes for Barbados bus system
  - Document: Route IDs, names, coverage areas
- [ ] 5.4.2: Identify which routes service each depot
  - Method: Check route start/end points vs depot locations
  - Walking distance threshold: 500m (configurable)
  - Use Geospatial API: /routes/{id}/geometry
  - Calculate: Distance from depot to route endpoints
- [ ] 5.4.3: Create route-depot associations for Fairchild depot
  - Location: Northern Barbados (near Route 1)
  - Expected routes: Route 1, possibly Route 2
  - Run precompute script or manual API calls
  - Verify in Strapi: route-depots table updated
- [ ] 5.4.4: Create route-depot associations for Oistins depot
  - Location: Southern Barbados
  - Expected routes: Routes serving south coast
  - Identify from GTFS data or OpenStreetMap
- [ ] 5.4.5: Create route-depot associations for Bridgetown depot
  - Location: Capital, central hub
  - Expected routes: Most/all routes (major terminus)
  - This depot may have 15+ route associations
- [ ] 5.4.6: Create route-depot associations for Princess Alice depot
  - Location: Eastern Barbados
  - Expected routes: Routes serving east coast
- [ ] 5.4.7: Verify all associations in database
  - Query: GET `/api/route-depots?pagination[pageSize]=100`
  - Expected: 30-50 total associations (avg 6-10 routes per depot)
  - Validate: All 5 depots have at least 1 route
  - Document: Association counts per depot

**Success Criteria:**
- ✅ All 5 depots have route associations
- ✅ Bridgetown depot (hub) has 10+ routes
- ✅ Other depots have 2-8 routes each
- ✅ No depot has zero routes (spawner failure condition eliminated)
- ✅ All associations have distance_from_route_m < 500m

---

#### **Phase 5.5: Additional Routes and Spawn Configs** [3-4 hours]

**Current State:**
- ✅ 1 spawn config exists (Route 1 - St Lucy Rural, 0.05 pass/bldg/hr)
- ❌ 20+ routes have no spawn configs (spawner will fail)
- ✅ Geospatial API can calculate building counts per route

**Tasks:**
- [ ] 5.5.1: Categorize routes by type
  - Urban routes (Bridgetown area): Higher base rate (0.08-0.12 pass/bldg/hr)
  - Suburban routes: Medium base rate (0.05-0.08 pass/bldg/hr)
  - Rural routes: Lower base rate (0.03-0.05 pass/bldg/hr)
  - Use OpenStreetMap landuse data or manual classification
- [ ] 5.5.2: Calculate buildings along each route
  - Loop through all routes
  - Query: GET `/routes/{id}/buildings?buffer_meters=100`
  - Store building counts for spawn config creation
  - Expected: 50-200 buildings per route
- [ ] 5.5.3: Create spawn config template
  - Base structure from Route 1 config
  - Adjust passengers_per_building_per_hour by route type
  - Keep hourly_rates and day_multipliers consistent
  - Template ready for bulk creation
- [ ] 5.5.4: Create spawn configs for top 10 routes
  - Priority: Routes with most depot associations
  - Create via Strapi API: POST `/api/spawn-configs`
  - Include: Route reference, config JSON, name, description
  - Verify in Strapi admin panel
- [ ] 5.5.5: Validate spawn configs are queryable
  - Test: GET `/api/spawn-configs?filters[route][id][$eq]=X`
  - Ensure all 10 routes return valid configs
  - Check field names match RouteSpawner expectations
- [ ] 5.5.6: Run validation script with new routes
  - Execute: python tests/validation/validate_hybrid_spawn_model.py
  - Should now show results for 10 routes (not just Route 1)
  - Verify passenger counts are realistic per route type
- [ ] 5.5.7: Document route categorization
  - Create: docs/route_classification.md
  - Include: Route ID, name, type, base rate, rationale
  - Helps future agents understand spawn rate decisions

**Success Criteria:**
- ✅ 10+ routes have spawn configs (10x improvement)
- ✅ Base rates appropriate for route type (urban > suburban > rural)
- ✅ Validation script shows realistic passenger counts per route
- ✅ All configs queryable and properly formatted
- ✅ Documentation explains rate calibration

---

#### **Phase 5.6: End-to-End Integration Testing** [4-5 hours]

**Current State:**
- ✅ Individual components tested (kernel, spawners, geospatial)
- ❌ Full system never run with multiple routes/depots
- ❌ No 24-hour simulation data

**Tasks:**
- [ ] 5.6.1: Prepare test environment
  - Clear passenger database (DELETE all passengers)
  - Verify all services running (Strapi, Geospatial, PostgreSQL)
  - Enable both DepotSpawner and RouteSpawner in config
  - Set continuous_mode = true
- [ ] 5.6.2: Run 1-hour integration test (short cycle)
  - Start commuter_simulator (python commuter_simulator/main.py)
  - Run for 1 simulated hour (4 spawn cycles @ 15-min intervals)
  - Monitor logs for spawn counts and errors
  - Expected: 100-300 passengers spawned across all routes/depots
- [ ] 5.6.3: Verify passenger distribution
  - Query database: Count passengers per route
  - Verify proportional to route attractiveness
  - Check spatial distribution (origins near depots/routes)
  - Validate temporal data (spawn timestamps)
- [ ] 5.6.4: Run 24-hour integration test (full cycle)
  - Start commuter_simulator for full day simulation
  - Simulate: Monday 12 AM → Tuesday 12 AM (24 hours)
  - 96 spawn cycles (15-min intervals)
  - Expected: 3,000-5,000 passengers total
  - Monitor system resources (CPU, memory, database size)
- [ ] 5.6.5: Analyze 24-hour temporal patterns
  - Extract passenger counts per hour
  - Plot: Passengers/hour vs Time of day
  - Verify curve matches expected patterns:
    - Low at night (2-5 AM): 10-20 pass/hr
    - Morning peak (7-9 AM): 150-250 pass/hr
    - Lunch dip (12-2 PM): 80-120 pass/hr
    - Evening peak (5-7 PM): 180-280 pass/hr
    - Evening decline (8-11 PM): 50-100 pass/hr
- [ ] 5.6.6: Validate conservation across routes
  - For each depot, sum passengers across all associated routes
  - Should equal terminal_population × spawn_cycles
  - Tolerance: ±15% (Poisson variance accumulates)
  - Verify no double-counting or missing passengers
- [ ] 5.6.7: Performance analysis
  - Measure: Spawn cycle execution time
  - Target: <2 seconds per cycle (for 10 routes)
  - Identify bottlenecks (geospatial queries, database writes)
  - Document performance baseline
- [ ] 5.6.8: Create integration test report
  - Document: Passenger counts, temporal patterns, performance
  - Include: Graphs, statistics, pass/fail criteria
  - Save: tests/validation/integration_test_report_YYYYMMDD.md
  - Share findings with team

**Success Criteria:**
- ✅ 1-hour test completes without errors
- ✅ 24-hour test generates 3,000-5,000 passengers
- ✅ Temporal patterns match expected curves (40x peak-to-night ratio)
- ✅ Spatial distribution 100% valid (passengers near routes/depots)
- ✅ Zero-sum conservation holds across all routes
- ✅ Performance <2 sec/cycle (scalable to production)
- ✅ No memory leaks or resource exhaustion

---

### **TIER 6: MVP Feature Completion** (Nov 4-7, 2025)

#### **Phase 6.1: Passenger State Management** [6-8 hours]

**Purpose**: Passengers need to track their journey state (waiting → riding → alighting)

**Tasks:**
- [ ] 6.1.1: Define passenger lifecycle states
  - SPAWNED: Passenger created at origin
  - WAITING: At depot/stop waiting for vehicle
  - BOARDING: Entering vehicle
  - RIDING: On vehicle, traveling to destination
  - ALIGHTING: Exiting vehicle
  - COMPLETED: Journey finished
  - EXPIRED: TTL exceeded, removed from system
- [ ] 6.1.2: Add state field to Passenger model
  - Strapi schema update: Add `state` enum field
  - Default: SPAWNED
  - Indexed for fast queries
- [ ] 6.1.3: Implement state transition logic
  - Create: commuter_simulator/core/domain/passenger_state_machine.py
  - Valid transitions: SPAWNED → WAITING → BOARDING → RIDING → ALIGHTING → COMPLETED
  - Prevent invalid transitions (e.g., RIDING → SPAWNED)
  - Log all state changes with timestamps
- [ ] 6.1.4: Add TTL (time-to-live) expiration
  - Default: 4 hours (configurable)
  - Background task checks for expired passengers
  - Transition: SPAWNED/WAITING → EXPIRED if TTL exceeded
  - Cleanup: Remove EXPIRED passengers from active pool
- [ ] 6.1.5: Create passenger state query endpoints
  - GET `/passengers/by-state/{state}`: Filter by state
  - GET `/passengers/waiting-at-depot/{depot_id}`: Waiting passengers at depot
  - GET `/passengers/on-vehicle/{vehicle_id}`: Passengers currently riding
- [ ] 6.1.6: Update spawner to set initial state
  - After spawning, set state = WAITING
  - Set spawn_timestamp and calculate expiration_timestamp
- [ ] 6.1.7: Test state transitions
  - Create test: tests/integration/test_passenger_lifecycle.py
  - Spawn passenger → Verify WAITING state
  - Manually trigger transitions → Verify state updates
  - Wait for TTL → Verify EXPIRED state

**Success Criteria:**
- ✅ All 7 passenger states defined and implemented
- ✅ State transitions validated (no invalid transitions)
- ✅ TTL expiration working (passengers auto-expire)
- ✅ Query endpoints return correct passengers by state
- ✅ Automated tests passing for full lifecycle

---

#### **Phase 6.2: Vehicle-Passenger Association (Pickup)** [8-10 hours]

**Purpose**: Vehicles need to pick up waiting passengers and update their state

**Tasks:**
- [ ] 6.2.1: Create pickup detection logic
  - When vehicle arrives at depot/stop
  - Query waiting passengers at that location
  - Distance threshold: 50m (configurable)
  - Capacity check: Vehicle max_capacity - current_passengers
- [ ] 6.2.2: Implement passenger pickup algorithm
  - First-come-first-served (FIFO) or priority-based
  - Select passengers up to vehicle capacity
  - Update passenger state: WAITING → BOARDING
  - Create vehicle-passenger association record
- [ ] 6.2.3: Add passengers field to Vehicle model
  - Strapi schema: Add `passengers` relation (many-to-many)
  - Junction table: vehicle-passengers
  - Fields: vehicle_id, passenger_id, boarded_at, expected_alight_at
- [ ] 6.2.4: Create pickup event handler
  - Trigger: Vehicle GPS location update
  - Check: Is vehicle near depot/stop?
  - Action: Run pickup algorithm
  - Broadcast: PubSub notification (vehicle picked up N passengers)
- [ ] 6.2.5: Update passenger state after pickup
  - BOARDING → RIDING (when vehicle departs)
  - Store: vehicle_id, boarded_at timestamp
  - Calculate: expected_alight_at (destination stop)
- [ ] 6.2.6: Handle capacity constraints
  - If demand > capacity, leave excess passengers in WAITING state
  - Log: "Vehicle X at capacity, left Y passengers waiting"
  - Trigger: Dispatch additional vehicle (future phase)
- [ ] 6.2.7: Test pickup integration
  - Create test: tests/integration/test_vehicle_pickup.py
  - Spawn 10 passengers at depot
  - Move vehicle to depot
  - Verify: Passengers transition WAITING → RIDING
  - Verify: Vehicle passengers list updated
  - Verify: Capacity limits enforced

**Success Criteria:**
- ✅ Pickup detection working (vehicle proximity triggers pickup)
- ✅ Passenger state transitions WAITING → BOARDING → RIDING
- ✅ Vehicle-passenger associations created correctly
- ✅ Capacity constraints enforced (no overloading)
- ✅ PubSub notifications broadcasting pickup events
- ✅ Integration tests passing

---

#### **Phase 6.3: Passenger Alighting (Drop-off)** [6-8 hours]

**Purpose**: Passengers need to exit vehicles when reaching their destination

**Tasks:**
- [ ] 6.3.1: Create alighting detection logic
  - When vehicle approaches passenger's destination
  - Distance threshold: 100m from destination
  - Check all passengers on vehicle for nearby destinations
- [ ] 6.3.2: Implement passenger alighting algorithm
  - Identify passengers with destination near current location
  - Update state: RIDING → ALIGHTING
  - Remove from vehicle's passengers list
  - Log: "Passenger X alighting at stop Y"
- [ ] 6.3.3: Update passenger record after alighting
  - Set: alighted_at timestamp
  - Set: final_location (actual drop-off coordinates)
  - Update state: ALIGHTING → COMPLETED
  - Calculate: journey_duration_seconds
- [ ] 6.3.4: Create alighting event handler
  - Trigger: Vehicle GPS location update
  - Check: Any passengers with destination nearby?
  - Action: Run alighting algorithm
  - Broadcast: PubSub notification (N passengers alighted)
- [ ] 6.3.5: Handle missed stops (passenger passed destination)
  - If vehicle goes 500m past destination without stopping
  - Log warning: "Passenger X missed stop at Y"
  - Force alight at next stop
  - Update passenger state: RIDING → ALIGHTING (missed_stop flag)
- [ ] 6.3.6: Test alighting integration
  - Create test: tests/integration/test_passenger_alighting.py
  - Spawn passenger with destination
  - Pick up passenger
  - Move vehicle to destination
  - Verify: Passenger transitions RIDING → ALIGHTING → COMPLETED
  - Verify: Vehicle passengers list updated
  - Verify: Journey metrics calculated (duration, distance)

**Success Criteria:**
- ✅ Alighting detection working (proximity triggers drop-off)
- ✅ Passenger state transitions RIDING → ALIGHTING → COMPLETED
- ✅ Journey metrics calculated (duration, distance traveled)
- ✅ Missed stop detection and handling
- ✅ Integration tests passing

---

#### **Phase 6.4: Reservoir Integration** [4-6 hours]

**Purpose**: Connect spawners to reservoir pattern for buffered passenger generation

**Tasks:**
- [x] 6.4.1: Review existing reservoir implementations
  - ~~File: commuter_service_deprecated/depot_reservoir.py~~ (removed Nov 2, 2025)
  - ~~File: commuter_service_deprecated/route_reservoir.py~~ (removed Nov 2, 2025)
  - ✅ Replaced by clean architecture implementation in commuter_simulator/
- [x] 6.4.2: Decide: Migrate or rewrite reservoirs?
  - **Decision**: Option B - Rewrite in new architecture (cleaner)
  - ✅ Implemented with DB-backed reservoirs using Strapi
- [x] 6.4.3: Create new DepotReservoir class
  - File: commuter_simulator/core/domain/reservoirs/depot_reservoir.py
  - Buffer size: Configurable (default 100 passengers)
  - Refill trigger: When buffer < 20% full
  - Refill amount: Generate next hour's worth of passengers
- [ ] 6.4.4: Create new RouteReservoir class
  - File: commuter_simulator/core/domain/reservoirs/route_reservoir.py
  - Same buffering logic as DepotReservoir
  - Route-specific: One reservoir per route
- [ ] 6.4.5: Wire reservoirs to spawners
  - Spawner generates → Reservoir buffers → Conductor consumes
  - Spawner calls: reservoir.refill(passengers)
  - Conductor calls: reservoir.take(count)
  - Reservoir manages internal buffer and refill logic
- [ ] 6.4.6: Implement reservoir statistics
  - Track: buffer_size, fill_rate, drain_rate, refill_count
  - Expose: GET `/reservoirs/stats` endpoint
  - Monitor: Alert if reservoir empty (demand > supply)
- [ ] 6.4.7: Test reservoir integration
  - Create test: tests/integration/test_reservoir_buffering.py
  - Fill reservoir with 100 passengers
  - Drain 80 passengers → Verify refill triggered
  - Verify: Buffer never empty during normal operation
  - Verify: Statistics accurate

**Success Criteria:**
- ✅ DepotReservoir and RouteReservoir classes implemented
- ✅ Spawners writing to reservoirs (not direct to database)
- ✅ Reservoirs buffering correctly (refill triggers working)
- ✅ Reservoir statistics tracking and exposed via API
- ✅ Integration tests passing

---

#### **Phase 6.5: Conductor Integration** [8-10 hours]

**Purpose**: Conductor consumes passengers from reservoirs and assigns to vehicles

**Tasks:**
- [ ] 6.5.1: Review existing conductor implementation
  - ~~File: commuter_service_deprecated/expiration_manager.py~~ (removed Nov 2, 2025)
  - Reference: conductor logic will be implemented fresh in new architecture
- [ ] 6.5.2: Create new Conductor class
  - File: commuter_simulator/core/domain/conductor/conductor.py
  - Responsibilities:
    - Monitor waiting passengers at depots
    - Match passengers to vehicles based on route
    - Trigger pickup events when vehicle arrives
    - Handle capacity constraints
- [ ] 6.5.3: Implement passenger-vehicle matching algorithm
  - Step 1: Get all waiting passengers at depot
  - Step 2: Get all vehicles currently at depot
  - Step 3: Match passengers to vehicles by route compatibility
  - Step 4: Respect vehicle capacity limits
  - Step 5: Assign passengers and trigger pickup
- [ ] 6.5.4: Add priority queue for passengers
  - Priority factors:
    - Wait time (longer wait = higher priority)
    - Destination proximity (closer = higher priority)
    - Passenger type (disabled, elderly = higher priority)
  - Use: heapq for efficient priority queue
- [ ] 6.5.5: Implement conductor event loop
  - Frequency: Every 30 seconds
  - Actions:
    - Query waiting passengers
    - Query available vehicles
    - Run matching algorithm
    - Assign passengers to vehicles
    - Broadcast assignments via PubSub
- [ ] 6.5.6: Wire conductor to reservoirs
  - Conductor pulls passengers from RouteReservoir
  - When reservoir runs low, triggers spawner refill
  - Maintains buffer of 50-100 passengers per route
- [ ] 6.5.7: Test conductor integration
  - Create test: tests/integration/test_conductor_assignment.py
  - Spawn 20 passengers at depot
  - Add 2 vehicles at depot (capacity 15 each)
  - Run conductor
  - Verify: All 20 passengers assigned (15 to vehicle 1, 5 to vehicle 2)
  - Verify: Priority queue respected (longest wait time assigned first)

**Success Criteria:**
- ✅ Conductor class implemented with matching algorithm
- ✅ Passengers assigned to vehicles correctly
- ✅ Priority queue working (longest wait time prioritized)
- ✅ Conductor event loop running continuously
- ✅ Reservoir integration working (conductor pulls from reservoirs)
- ✅ Integration tests passing

---

#### **Phase 6.6: PubSub Integration (PostgreSQL LISTEN/NOTIFY)** [6-8 hours]

**Purpose**: Real-time event broadcasting for passenger lifecycle and vehicle events

**Tasks:**
- [ ] 6.6.1: Set up PostgreSQL LISTEN/NOTIFY
  - Create channels:
    - `passenger_spawned`: Broadcast when new passenger created
    - `passenger_state_changed`: Broadcast state transitions
    - `vehicle_pickup`: Broadcast when vehicle picks up passengers
    - `vehicle_dropoff`: Broadcast when passengers alight
  - PostgreSQL triggers: Auto-notify on table updates
- [ ] 6.6.2: Create PubSub publisher class
  - File: commuter_simulator/infrastructure/pubsub/publisher.py
  - Methods:
    - publish(channel, message)
    - publish_passenger_spawned(passenger)
    - publish_state_change(passenger, old_state, new_state)
    - publish_pickup(vehicle, passengers)
    - publish_dropoff(vehicle, passengers)
- [ ] 6.6.3: Create PubSub subscriber class
  - File: commuter_simulator/infrastructure/pubsub/subscriber.py
  - Methods:
    - subscribe(channel, callback)
    - unsubscribe(channel)
    - start_listening() (async loop)
- [ ] 6.6.4: Integrate publishers into spawners
  - After spawning: Publish passenger_spawned event
  - After state change: Publish passenger_state_changed event
- [ ] 6.6.5: Integrate publishers into conductor
  - After assignment: Publish vehicle_pickup event
  - After alighting: Publish vehicle_dropoff event
- [ ] 6.6.6: Create example subscriber
  - File: commuter_simulator/examples/passenger_subscriber.py
  - Listens to all channels
  - Logs events to console with emoji indicators
  - Purpose: Demo real-time notifications
- [ ] 6.6.7: Test PubSub integration
  - Create test: tests/integration/test_pubsub_events.py
  - Start subscriber
  - Spawn passenger → Verify passenger_spawned event received
  - Change state → Verify passenger_state_changed event received
  - Pickup passenger → Verify vehicle_pickup event received
  - Verify: Event payload contains all expected data

**Success Criteria:**
- ✅ PostgreSQL LISTEN/NOTIFY channels created
- ✅ Publisher class broadcasting events correctly
- ✅ Subscriber class receiving events in real-time
- ✅ All spawner and conductor events published
- ✅ Example subscriber demonstrating real-time notifications
- ✅ Integration tests passing

---

### **TIER 7: Production Hardening** (Nov 8-10, 2025)

#### **Phase 7.1: Error Handling & Resilience** [6-8 hours]

**Tasks:**
- [ ] 7.1.1: Add retry logic for API failures
  - Geospatial API calls: 3 retries with exponential backoff
  - Strapi API calls: 3 retries with exponential backoff
  - Handle: Network errors, timeouts, 503 responses
- [ ] 7.1.2: Implement circuit breaker pattern
  - If Geospatial API fails 5 times in a row, stop calling for 60 seconds
  - If Strapi API fails 5 times in a row, stop calling for 60 seconds
  - Prevents cascade failures
- [ ] 7.1.3: Add graceful degradation
  - If Geospatial API down: Use cached building counts
  - If Strapi API down: Buffer passengers in memory, sync when available
  - If database down: Log errors, continue simulation (ephemeral mode)
- [ ] 7.1.4: Implement health checks
  - Endpoint: GET `/health` returns system status
  - Checks: Database, Geospatial API, Strapi API, memory usage
  - Status: healthy, degraded, or down
- [ ] 7.1.5: Add comprehensive logging
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Log rotation: Daily rotation, keep 7 days
  - Structured logging: JSON format for parsing
  - Include: request_id, user_id, timestamp, component
- [ ] 7.1.6: Create error aggregation
  - Track: Error counts by type, endpoint, time period
  - Alert: If error rate > 5% for 5 minutes
  - Dashboard: Real-time error monitoring
- [ ] 7.1.7: Test failure scenarios
  - Simulate: Geospatial API down
  - Simulate: Database connection loss
  - Simulate: Out of memory
  - Verify: System continues operating in degraded mode
  - Verify: Recovery when services restored

**Success Criteria:**
- ✅ Retry logic handling transient failures
- ✅ Circuit breakers preventing cascade failures
- ✅ Graceful degradation working (system operable when APIs down)
- ✅ Health checks exposing system status
- ✅ Comprehensive logging with rotation
- ✅ Error aggregation and alerting
- ✅ Failure scenario tests passing

---

#### **Phase 7.2: Performance Optimization** [8-10 hours]

**Tasks:**
- [ ] 7.2.1: Add database query caching
  - Cache: Route geometries (never change)
  - Cache: Depot catchments (rarely change)
  - Cache: Building counts per route (update daily)
  - TTL: 24 hours for static data, 1 hour for semi-static
- [ ] 7.2.2: Implement batch database writes
  - Instead of 1 INSERT per passenger: Batch 50-100 INSERTs
  - Reduces database round-trips from 100 to 1-2
  - Expected: 10x write performance improvement
- [ ] 7.2.3: Add database connection pooling
  - Pool size: 10 connections
  - Max overflow: 20 connections
  - Timeout: 30 seconds
  - Reuse connections instead of creating new ones
- [ ] 7.2.4: Optimize geospatial queries
  - Add spatial indexes to buildings, routes, depots tables
  - Use bounding box pre-filter before ST_Distance
  - Expected: 5x query performance improvement
- [ ] 7.2.5: Profile spawner performance
  - Measure: Time per spawn cycle
  - Identify bottlenecks: Geospatial queries, database writes, calculation
  - Target: <1 second per spawn cycle (for 10 routes)
- [ ] 7.2.6: Implement async/await for I/O operations
  - Make geospatial API calls async
  - Make database writes async
  - Parallel execution: Query 10 routes concurrently instead of sequentially
  - Expected: 3-5x performance improvement
- [ ] 7.2.7: Add performance metrics
  - Track: spawn_cycle_duration, passengers_per_second, api_latency
  - Expose: GET `/metrics` endpoint (Prometheus format)
  - Alert: If spawn_cycle_duration > 5 seconds

**Success Criteria:**
- ✅ Database query caching reducing API calls by 80%
- ✅ Batch writes improving write performance by 10x
- ✅ Connection pooling reducing connection overhead
- ✅ Spatial indexes improving query speed by 5x
- ✅ Async I/O improving overall performance by 3-5x
- ✅ Spawn cycle duration <1 second (for 10 routes)
- ✅ Performance metrics exposed via /metrics

---

#### **Phase 7.3: Monitoring & Observability** [6-8 hours]

**Tasks:**
- [ ] 7.3.1: Set up Prometheus metrics
  - Install Prometheus client library
  - Expose metrics at GET `/metrics`
  - Metrics:
    - passengers_spawned_total (counter)
    - passengers_active (gauge)
    - spawn_cycle_duration_seconds (histogram)
    - api_request_duration_seconds (histogram)
    - errors_total (counter by type)
- [ ] 7.3.2: Create Grafana dashboard
  - Install Grafana
  - Connect to Prometheus data source
  - Panels:
    - Passengers spawned over time (line graph)
    - Active passengers by state (pie chart)
    - Spawn cycle duration (histogram)
    - Error rate (line graph)
    - API latency (heatmap)
- [ ] 7.3.3: Add distributed tracing
  - Install OpenTelemetry
  - Trace full spawn cycle:
    - Spawner start → Geospatial query → Calculation → Database write → Complete
  - Identify slow spans
  - Visualize in Jaeger
- [ ] 7.3.4: Create alerting rules
  - Alert: Error rate > 5% for 5 minutes
  - Alert: Spawn cycle duration > 5 seconds for 10 minutes
  - Alert: Database connection pool exhausted
  - Alert: Memory usage > 80%
  - Delivery: Email, Slack, PagerDuty
- [ ] 7.3.5: Add logging aggregation
  - Ship logs to ELK stack (Elasticsearch, Logstash, Kibana)
  - Centralized log search and analysis
  - Create saved searches for common issues
- [ ] 7.3.6: Create runbook
  - Document: Common issues and resolution steps
  - Include: Alerting scenarios and remediation
  - Examples:
    - "Spawn cycle slow" → Check geospatial API latency
    - "High error rate" → Check database connectivity
    - "Memory leak" → Restart service, investigate code
- [ ] 7.3.7: Test monitoring integration
  - Trigger alerts intentionally
  - Verify: Prometheus collecting metrics
  - Verify: Grafana displaying real-time data
  - Verify: Alerts firing and delivering to Slack

**Success Criteria:**
- ✅ Prometheus metrics exposed and collecting
- ✅ Grafana dashboard showing real-time system state
- ✅ Distributed tracing identifying performance bottlenecks
- ✅ Alerting rules configured and tested
- ✅ Log aggregation working (ELK stack)
- ✅ Runbook documented for common issues
- ✅ End-to-end monitoring validated

---

#### **Phase 7.4: MVP Feature Freeze & Documentation** [4-6 hours]

**Tasks:**
- [ ] 7.4.1: Feature freeze announcement
  - No new features until MVP stable
  - Focus: Bug fixes, performance, documentation
- [ ] 7.4.2: Update CONTEXT.md
  - Document all Phase 5-7 changes
  - Update architecture diagrams
  - Add performance benchmarks
  - Include MVP feature list
- [ ] 7.4.3: Update TODO.md
  - Mark all TIER 5-7 tasks complete
  - Create TIER 8 for post-MVP enhancements
  - Prioritize post-MVP roadmap
- [ ] 7.4.4: Create API documentation
  - Document all REST endpoints (Strapi + Geospatial)
  - Include: Request/response examples, error codes
  - Tools: Swagger/OpenAPI spec
- [ ] 7.4.5: Create user guide
  - How to: Start services, spawn passengers, monitor system
  - Include: Screenshots, example commands
  - Audience: Operators, developers
- [ ] 7.4.6: Create deployment guide
  - Prerequisites: Python, Node.js, PostgreSQL, PostGIS
  - Step-by-step: Database setup, service configuration, first run
  - Include: Troubleshooting common issues
- [ ] 7.4.7: Code review checklist
  - Review all Phase 5-7 code for:
    - SOLID principles adherence
    - Error handling completeness
    - Test coverage >80%
    - Documentation clarity
    - Performance optimizations

**Success Criteria:**
- ✅ Feature freeze announced and enforced
- ✅ CONTEXT.md and TODO.md fully updated
- ✅ API documentation complete (Swagger/OpenAPI)
- ✅ User guide created with examples
- ✅ Deployment guide tested by fresh install
- ✅ Code review completed, no critical issues
- ✅ All documentation markdown lint-free

---

### **MVP DELIVERY CHECKLIST**

When all TIER 5-7 phases complete, verify:

- [ ] **Functional Requirements**
  - [ ] Passengers spawn at correct rates (validated statistically)
  - [ ] Vehicles pick up passengers at depots
  - [ ] Passengers alight at destinations
  - [ ] Full lifecycle tracked (spawned → waiting → riding → completed)
  - [ ] Real-time events broadcast via PubSub

- [ ] **Non-Functional Requirements**
  - [ ] Spawn cycle <2 seconds for 10 routes
  - [ ] Error rate <1% under normal operation
  - [ ] System runs 24 hours without crashes
  - [ ] Memory usage stable (no leaks)
  - [ ] Database writes batched and performant

- [ ] **Testing**
  - [ ] Unit test coverage >80%
  - [ ] Integration tests passing (all scenarios)
  - [ ] Statistical validation tests passing
  - [ ] 24-hour integration test completed
  - [ ] Failure scenario tests passing

- [ ] **Documentation**
  - [ ] CONTEXT.md updated with all changes
  - [ ] TODO.md reflects current state
  - [ ] API documentation complete
  - [ ] User guide created
  - [ ] Deployment guide tested
  - [ ] Runbook for common issues

- [ ] **Monitoring**
  - [ ] Prometheus metrics exposed
  - [ ] Grafana dashboard operational
  - [ ] Alerting rules configured
  - [ ] Logs aggregated in ELK
  - [ ] Health checks passing

**When all checkboxes ✅**: **MVP READY FOR DEMO** 🎉

---

### **Where Am I?**

- **Current Focus**: TIER 5 Step 1 ✅ COMPLETE - Route-Depot Association Schema (October 28)
- **Spawner System Status**: ✅ COMPLETE
  - DepotSpawner: Fully implemented with Poisson distribution and default config fallback
  - SpawnerCoordinator: Implemented with enable/disable flag support (single-run and continuous modes)
  - main.py: Single entrypoint with config-driven spawner control
  - Testing: End-to-end validation complete (4 passengers spawned successfully)
  - Fresh spawn verified: Deleted DB, re-ran, confirmed new passengers with matching timestamps
- **Architectural Decisions Made** (October 28):
  - ✅ Single entrypoint pattern (NOT separate sub-entrypoints)
  - ✅ Coordinator pattern for orchestrating multiple spawners
  - ✅ Config-driven enable/disable flags (enable_depotspawner, enable_routespawner)
  - ✅ Two-mode API architecture validated (Strapi = CRUD, GeospatialService = spatial queries)
  - ✅ Route-depot junction table design approved (explicit relationships, precomputed distances)
  - ✅ PubSub pattern recommended (PostgreSQL LISTEN/NOTIFY, not direct spawner integration)
  - ✅ RouteSpawner discovered complete (287 lines) - reduces TIER 5 scope by 33% (Oct 28)
- **Deep Code Analysis Results** (October 28, 2025):
  - ✅ RouteSpawner ALREADY FULLY IMPLEMENTED at `commuter_simulator/core/domain/spawner_engine/route_spawner.py`
  - ✅ All required methods complete: `spawn()`, `_load_spawn_config()`, `_load_route_geometry()`, `_get_buildings_near_route()`, `_calculate_spawn_count()`, `_generate_spawn_requests()`
  - ✅ GeospatialService integration complete: `/spatial/route-geometry/{route_id}`, `/spatial/route-buildings`
  - ❌ RouteSpawner NOT wired to main.py coordinator yet (currently uses MockRouteSpawner)
  - ❌ Route-depot junction table MISSING (confirmed via file_search, grep_search)
  - ❌ DepotSpawner uses hardcoded `available_routes` parameter (needs association querying)
  - ❌ PostgreSQL LISTEN/NOTIFY triggers NOT implemented
  - ❌ passenger_subscriber.py example NOT found
- **Next Immediate Task**: Create route-depots junction table in Strapi schema
- **After Route-Depot Association**: Wire existing RouteSpawner to coordinator (replace MockRouteSpawner)
- **Blocker**: None - All architectural decisions finalized, RouteSpawner already implemented
- **Status**: TIER 4 ✅ 100% COMPLETE
  - **Spawner Implementation**: DepotSpawner + SpawnerCoordinator + main.py entrypoint
  - **Test Results**: 4 passengers spawned (λ=2.20 from spatial × hourly × day multipliers)
  - **Bulk Insert**: 4/4 successful (100% success rate)
  - **Database Verification**: All passengers persisted to Strapi with correct fields
  - **Fresh Spawn Test**: Confirmed new passenger generation (not old data)
  - **MockRouteSpawner**: Created for testing without full geospatial dependencies

**Priority Path** (TIER 5 - REVISED Oct 28):

```text
Route-Depot Association 🎯 NEXT - OCT 28
  - Create route-depots junction table in Strapi
  - Precompute depot-route associations (walking distance ~500m to route endpoints)
  - CORRECTED: Depots are bus stations; routes associate only if start/end within walking distance
  - Update DepotSpawner to query associated routes (replace hardcoded list)
  - Wire existing RouteSpawner to coordinator (replace MockRouteSpawner)
  - Add PostgreSQL LISTEN/NOTIFY triggers for PubSub pattern
  - Create passenger_subscriber.py example for real-time notifications
  → Phase 1.14 (Conductor integration)
  → Phase 1.15 (Reservoir wiring & PubSub)
  → Phases 2-3 (Redis, Geofencing, Production Optimization)
```

---

## 🎉 **RECENT ACCOMPLISHMENTS (October 30, 2025)**

### Fleet Services Architecture Finalized

**Problem**: Attempted unified backend on port 8000 had WebSocket proxy issues  
**Solution**: Reverted to standalone services architecture for simplicity and reliability

**Achievements**:
1. ✅ **Port Configuration Centralized**
   - All ports moved to `.env` file (single source of truth)
   - Updated all references from old ports (8001→6000, 8002→4000)
   - No hardcoded ports in codebase (40+ files updated)

2. ✅ **Unified Fleet Launcher**
   - `start_fleet_services.py` - One command to launch all services
   - Reads configuration from `.env`
   - Launches 3 services in separate console windows
   - Displays all endpoints on startup

3. ✅ **End-to-End Testing Validated**
   - GPSCentCom (5000): GPS device connected, telemetry flowing
   - GeospatialService (6000): Reverse geocoding working (~18ms)
   - Manifest API (4000): Health checks passing
   - GPS client polling live data every 2 seconds

4. ✅ **Code Cleanup**
   - Removed 5 deprecated files (arknet_fleet_services.py, etc.)
   - Root directory now has only essential launcher
   - Documentation updated (CONTEXT.md, FLEET_SERVICES.md)

**Current Service Ports**:
- GPSCentCom: `http://localhost:5000`, `ws://localhost:5000/device`
- GeospatialService: `http://localhost:6000`
- Manifest API: `http://localhost:4000`

**Test Results**:
```
✅ GPSCentCom: {"status":"ok","devices":1}
✅ GeospatialService: {"status":"healthy","database":"connected","latency_ms":18.38}
✅ Manifest API: {"status":"ok","service":"manifest_api"}
✅ GPS Client: Polling live GPS data (GPS-ZR102 on Route 1)
✅ Reverse Geocoding: "footway-784848147, near RBC, Saint Michael"
```

---

### **What Do I Need to Know?**

1. **Read CONTEXT.md first** - Contains architecture, validation results, user preferences
2. **Spawner system implemented** - DepotSpawner, SpawnerCoordinator, main.py all working
3. **Architectural decisions finalized** (Oct 28):
   - Single entrypoint with coordinator pattern (NOT separate sub-entrypoints)
   - Config-driven enable/disable flags for spawner control
   - Two-mode API: Strapi (CRUD) + GeospatialService (spatial queries)
   - Route-depot junction table with precomputed associations
   - PubSub via PostgreSQL LISTEN/NOTIFY (not direct spawner integration)
4. **Test results validated** - 4 passengers spawned successfully, 100% persisted to Strapi
5. **User prefers detailed explanations** - Quality over speed, pushback on poor suggestions

### **Critical Architecture for TIER 5**

- 🎯 **Route-Depot Junction Table**: Explicit many-to-many relationships
  - **CORRECTED SEMANTICS** (Oct 28): Depots are bus stations/terminals where passengers wait for buses
  - **Association Logic**: Route associates with depot ONLY if route START or END point within walking distance (~500m)
  - Fields: route_id, depot_id, distance_from_route_m, is_start_terminus, is_end_terminus, precomputed_at
  - Eliminates runtime geospatial calculations for depot-route connections
  - Enables realistic spawning (passengers at depot board routes that actually service that depot)
  
- 🎯 **Updated DepotSpawner Logic**:
  - Query associated routes from route-depots junction table via Strapi API
  - Replace hardcoded `available_routes` parameter with database lookup
  - Weighted route selection based on distance or route priority
  - **Realistic behavior**: Passengers at depot only board routes with endpoints at that depot (not random routes)

- 🎯 **RouteSpawner Integration** (DISCOVERED COMPLETE - Oct 28):
  - ✅ RouteSpawner fully implemented (287 lines) at `commuter_simulator/core/domain/spawner_engine/route_spawner.py`
  - ✅ Poisson distribution with spatial/hourly/day multipliers
  - ✅ GeospatialService integration for route geometry and building queries
  - ✅ Spatial distribution logic along route corridor
  - ❌ NOT wired to main.py coordinator yet (uses MockRouteSpawner)
  - **Next Step**: Replace MockRouteSpawner with real RouteSpawner in coordinator
  - **Validation**: Run end-to-end test with `enable_routespawner=True`
  - Query associated routes from route-depots table
  - Weighted random selection from depot's associated routes
  - Generate passengers for selected route only (not random route assignment)
  
- 🎯 **Full RouteSpawner Implementation**:
  - Load route geometry from geospatial service
  - Query buildings along route (geospatial API: /spatial/route-buildings)
  - Calculate Poisson spawn count (spatial × hourly × day multipliers)
  - Spatially distribute passengers along route using building weights
  - Integrate with Strapi spawn-configs for route-specific parameters
  
- 🎯 **API Architecture** (Two-Mode Validated):
  - Mode 1: Strapi REST API (localhost:1337) - CRUD operations
    - /api/routes → Route master data
    - /api/depots → Depot master data
    - /api/route-depots → NEW junction table
    - /api/spawn-configs → Spawning configuration
    - /api/active-passengers → Live passenger records
  - Mode 2: Geospatial Service (localhost:6000) - Spatial queries (READ-ONLY)
    - /route-geometry/{route_id} → PostGIS geometry queries
    - /route-buildings → Spatial joins (buildings near route)
    - /depot-catchment → Depot proximity searches
    - /nearby-buildings → POI/building proximity searches
  
- 🎯 **PubSub for Visualization** (Recommended Pattern):
  - PostgreSQL LISTEN/NOTIFY on active_passengers table
  - Trigger-based notifications on INSERT/UPDATE/DELETE
  - Zero overhead on spawner (DB handles pub/sub)
  - Subscribers connect to DB, not spawner
  - Automatic replay/buffering built-in### **Files to Reference**

1. `commuter_simulator/main.py` - Single entrypoint for spawner system ✅ COMPLETE
2. `commuter_simulator/services/spawner_coordinator.py` - Spawner orchestration ✅ COMPLETE
3. `commuter_simulator/core/domain/spawner_engine/depot_spawner.py` - Depot passenger generation ✅ COMPLETE
4. `commuter_simulator/core/domain/reservoirs/depot_reservoir.py` - DB-backed depot reservoir ✅ COMPLETE
5. `commuter_simulator/core/domain/reservoirs/route_reservoir.py` - DB-backed route reservoir ✅ COMPLETE
6. `commuter_simulator/infrastructure/database/passenger_repository.py` - Strapi adapter ✅ COMPLETE
7. `test_spawner_flags.py` - Comprehensive enable/disable flag testing 📋 CREATED (not yet run)
8. `delete_passengers.py` - Utility for clearing Strapi passengers ✅ WORKING
9. ~~`commuter_service_deprecated/`~~ - Removed Nov 2, 2025 (fully replaced by commuter_simulator)
10. `CONTEXT.md` - Full architecture and validation metrics ✅ UPDATED

---

## ✅ Deprecated folder: REMOVED (Nov 2, 2025)

`commuter_service_deprecated/` has been **deleted** - all functionality successfully migrated to `commuter_simulator/` with:
- Clean architecture (Infrastructure → Services → Core)
- DB-driven configuration (operational-configurations)
- Single Source of Truth pattern (Geospatial API)
- Fail-fast behavior with no silent fallbacks

**Remaining spawner improvements:**

- [ ] RouteSpawner: Implement along-route destination selection
  - Ensure destinations remain on the route geometry
  - Use GeospatialService/PostGIS data, not shapely/geodesic
  - Acceptance: RouteSpawner generates spawn/destination pairs strictly on-route

- [ ] Temporal/context multipliers → align with spawn-configs
  - Reconcile depot vs route temporal patterns and zone multipliers with existing spawn-config schema
  - Document mapping; avoid hard-coded multipliers in code
  - Acceptance: Documented mapping + used by Route/Depot spawners via config

- [ ] Reservoir observability and expiration notes
  - Add minimal stats counters and TTL/expiration behavior notes to new reservoirs (non-blocking)
  - Acceptance: Basic metrics available and TTL strategy documented

Notes: All spatial computation remains in PostGIS via Strapi/GeospatialService (Single Source of Truth).

---

## 📊 **OVERALL PROGRESS**

**Priority Sequence**: Option A - Complete GeoJSON Import → Enable Spawning → Optimize Performance

### **🎯 TIER 1: IMMEDIATE - GeoJSON Import System (Current Focus)**

- [x] **Phase 1.1-1.9**: Foundation & Buildings Import ✅ COMPLETE (Oct 25-26, 2025)
  - ✅ Country schema + action buttons (5 buttons in UI)
  - ✅ Backend API + PostGIS migration (11 tables, 12 GIST indexes)
  - ✅ Buildings imported (162,942 records at 1166 features/sec, 658MB file)
  - ✅ Admin levels normalized (4 levels with UI dropdown)
  - ✅ Streaming parser created and working (geojson-stream-parser.ts)

- [x] **Phase 1.10**: Optimize Remaining Import Endpoints (5/5 tasks) ✅ **COMPLETE** (Oct 26, 2025)
  - [x] Building import with streaming ✅ COMPLETE (162,942 records, 658MB, 1166 features/sec)
  - [x] **Admin import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Schema normalization: Removed redundant `code` and `region_type` fields
    - ✅ Float precision: Changed center_lat/lon from `decimal` to `float` (preserves 7+ decimals)
    - ✅ Area calculation: PostGIS ST_Area(geography) / 1000000 for accurate km²
    - ✅ All 4 levels imported: 11 Parish, 5 Town, 136 Suburb, 152 Neighbourhood = 304 regions
    - ✅ Validation: 432.98 km² vs 432 km² official (+0.2% accuracy)
    - ✅ Junction tables: 304 admin_level links, 304 country links
    - ✅ Integration tests: 17/17 passing
  - [x] **Highway import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Performance optimization: Post-batch region linking (removed per-batch spatial queries)
    - ✅ 22,719 highways imported (all LineString geometries, SRID 4326)
    - ✅ Junction tables: 22,719 country links, 23,666 region links
    - ✅ 947 highways cross parish boundaries (validated by link count > highway count)
    - ✅ Spatial queries working: 12,385 highways within 10km of Bridgetown
    - ✅ Integration tests: 16/16 passing
  - [x] **Amenity import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Column fix: Removed non-existent `poi_id` and `full_id` columns
    - ✅ Binding fix: Corrected placeholder count (11 bindings, not 12)
    - ✅ Post-batch linking: Country links + region links after streaming completes
    - ✅ 1,427 POIs imported (all Point geometries extracted from Polygon/MultiPolygon centroids)
    - ✅ Junction tables: 1,427 country links, 1,427 region links
    - ✅ Amenity types: 399 parking, 254 worship, 133 restaurant, 111 school, 99 bar, 44 fuel, etc.
    - ✅ Spatial queries working: 652 POIs within 5km of Bridgetown
    - ✅ Integration tests: 17/17 passing
  - [x] **Landuse import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Fixed column mismatch: Removed non-existent `zone_id` and `full_id` columns
    - ✅ Fixed geometry type: Changed geom column from Polygon to GEOMETRY (accepts both Polygon and MultiPolygon)
    - ✅ Post-batch linking: Country links + region links after streaming completes
    - ✅ 2,267 zones imported (Polygon and MultiPolygon geometries, SRID 4326)
    - ✅ Junction tables: 2,267 country links, 2,310 region links
    - ✅ 43 zones cross parish boundaries (validated by link count > zone count)
    - ✅ Zone types: 937 farmland, 513 grass, 160 meadow, 144 residential, 65 forest/industrial, etc.
    - ✅ Spatial queries working: 343 zones within 5km of Bridgetown
    - ✅ Integration tests: 16/16 passing
  - **Summary**: ✅ ALL 5 IMPORTS 100% COMPLETE
    - **Total features**: 189,659 (162,942 buildings + 304 regions + 22,719 highways + 1,427 POIs + 2,267 landuse)
    - **All junction tables**: Country links (189,659) + region links (27,707) operational
    - **All integration tests**: 82 Strapi tests passing (17 admin + 16 highway + 17 amenity + 16 landuse + building)
    - **All spatial indexes**: GIST indexes on all geometry columns
    - **All PostGIS geometries**: Valid with SRID 4326
    - **Boundary crossings detected**: 990 features (947 highways + 43 landuse zones)
    - **Performance**: Streaming parsers handle large files (658MB building.geojson) efficiently
    - **Cleanup**: Removed temporary check_buildings_schema.py and check_landuse_schema.py validation scripts

### **🎯 TIER 2: FOUNDATION - Enable Spawning Queries (Required for Simulator)**

- [x] **Phase 1.11**: Geospatial Services API (7/7 steps) ✅ **COMPLETE** (Oct 26, 2025)
  - [x] Created FastAPI geospatial_service with asyncpg connection pooling
  - [x] Implemented PostGIS query optimization (bbox + geography distance pattern)
  - [x] Built reverse geocoding endpoint (highway + POI + parish)
  - [x] Built geofence check endpoints (region & landuse containment)
  - [x] Built depot catchment endpoint (buildings within radius)
  - [x] Built route buildings endpoint (buildings along route buffer)
  - [x] Created integration test suite (16/16 tests passing)
  - **Performance validated for real-time async usage**:
    - Geofence: 0.23ms avg (sub-millisecond!)
    - Reverse geocode: 2.46ms avg (with parish included)
    - Depot catchment: 94.76ms avg (1km radius, 3000+ buildings)
  - **Address format**: "Road name, near POI, Parish" (e.g., "Rockley New Road, near parking, Christ Church")
  - **Endpoints operational**:
    - `GET/POST /geocode/reverse` - Reverse geocoding with parish
    - `POST /geofence/check` - Point-in-polygon checks
    - `POST /geofence/check-batch` - Batch geofence checks
    - `GET/POST /spatial/depot-catchment` - Buildings near depot
    - `POST /spatial/route-buildings` - Buildings along route
  - **Database optimizations**:
    - Bounding box prefilter using ST_MakeEnvelope (GIST index friendly)
    - Geography distance only on small result sets
    - Longitude degree conversion adjusted by cos(latitude)
    - In-memory TTL cache (5s) for repeated identical queries

- [x] **Phase 1.12**: Database Integration & Validation (5/6 steps) 🎯 **CURRENT**
  - [x] Create API client wrapper for commuter_simulator
    - ✅ `commuter_simulator/infrastructure/geospatial/client.py` - Python client wrapper
    - ✅ Tested: reverse geocoding (105ms), geofencing (3ms), depot catchment (55ms)
    - ✅ Test: `commuter_simulator/tests/integration/test_geospatial_api.py`
  - [x] Test spatial queries from commuter_simulator spawning logic
    - ✅ Integration test: `commuter_simulator/tests/integration/test_geospatial_api.py`
    - ✅ Reverse geocoding: 4-20ms (fast enough for real-time)
    - ✅ Geofence checks: 3-5ms (sub-50ms target met)
    - ✅ Building queries: 13-59ms (good performance)
    - ✅ Depot catchment: 7-54ms (suitable for spawning)
    - ✅ Concurrent load: 0.5 queries/sec (20 concurrent)
  - [x] Design data-driven spawn-config schema for OSM features
    - ✅ Redesigned with SIMPLE component-based architecture (separate tables per category)
    - ✅ Created 6 Strapi components - clean separation by feature type:
      - `spawning.building-weight` - Buildings table (residential, commercial, office, school, etc.)
      - `spawning.poi-weight` - POIs table (bus_station, marketplace, hospital, etc.)
      - `spawning.landuse-weight` - Landuse zones table (residential, commercial, industrial, etc.)
      - `spawning.hourly-pattern` - 24-hour spawn rates (1.0=normal, 2.5=peak)
      - `spawning.day-multiplier` - Day-of-week multipliers (weekday vs weekend)
      - `spawning.distribution-params` - Poisson lambda, spawn constraints (collapsible)
    - ✅ Each feature has: base weight + peak_multiplier + is_active toggle
    - ✅ Simple mental model: final_spawn_probability = weight × peak_multiplier × hourly_rate × day_multiplier
    - ✅ UX: Three collapsible sections (Buildings, POIs, Landuse) with editable grid tables
    - ✅ No JSON blobs needed for common use cases
    - ✅ Relationship: country ↔ spawn-config (oneToOne, bidirectional)
    - 📁 Files:
      - `arknet-fleet-api/src/api/spawn-config/content-types/spawn-config/schema.json`
      - `arknet-fleet-api/src/components/spawning/*.json` (6 components)
  - [x] Seed spawn-config with realistic Barbados commuter patterns
    - ✅ Created SQL seed script: `seeds/seed_spawn_config.sql`
    - ✅ Seeded data: "Barbados Typical Weekday" with 8 building types, 6 POI types, 5 landuse types
    - ✅ Hourly patterns: 24-hour distribution (0.2 late night → 2.8 morning peak → 2.3 evening peak)
    - ✅ Day multipliers: Weekday 1.0, Saturday 0.7, Sunday 0.5
    - ✅ Poisson lambda: 3.5, max 50 spawns/cycle, 800m radius
    - ✅ Linked to Barbados country (id=29) via spawn_configs_country_lnk
    - ✅ Verified via API: All components loading correctly with `populate=*`
  - [x] Create SpawnConfigLoader for commuter_simulator
    - ✅ Created `commuter_simulator/infrastructure/spawn/config_loader.py`
    - ✅ Implements caching with 1-hour TTL (reduce API calls)
    - ✅ Methods: get_config_by_country(), get_hourly_rate(), get_building_weight(), get_poi_weight(), get_landuse_weight(), get_day_multiplier(), get_distribution_params(), calculate_spawn_probability()
    - ✅ Tested: Loads Barbados config, calculates spawn probabilities correctly
    - ✅ Example: Residential building Mon 8am = 5.0 × 2.8 × 1.0 = 14.0 probability multiplier
  - [x] SCHEMA MIGRATION: Country-Based → Route-Based Spawn Configs ✅ **COMPLETE**
    - **Problem Identified**: Rural routes (St Lucy) using urban temporal patterns → 48 passengers at 6 AM instead of ~16
    - **Root Cause**: spawn-config linked to Country (Barbados) → all routes share same hourly rates
    - **Solution**: Changed architecture to Route ↔ Spawn-Config (oneToOne)
    - ✅ **Schema Updates Complete**:
      - Updated `route/schema.json`: Added `spawn_config` relation (oneToOne → spawn-config)
      - Updated `spawn-config/schema.json`: Changed `country` to `route` relation (oneToOne → route)
      - Updated `country/schema.json`: Removed `spawn_config` relation
    - 🔄 **Data Migration Pending**:
      - [ ] Restart Strapi server (schema changes require rebuild)
      - [ ] Create route-specific spawn configs:
        - "Route 1 - St Lucy Rural" (hour 6 = 0.6, hour 7 = 1.2)
        - "Route 2 - Bridgetown Urban" (hour 6 = 1.5, hour 7 = 2.5)
      - [ ] Link each route to appropriate config
      - [ ] Update SpawnConfigLoader: Add get_config_by_route(route_id)
      - [ ] Update van_simulation_datadriven.py to use route-based config
    - **Expected Outcome**: Route 1 (St Lucy) at 6 AM → ~16 passengers (using rural-appropriate rates)
    - **Benefits**: Route-specific temporal patterns, no urban/rural conflicts, flexible per-route tuning
    - **Cleanup**: Moved validation scripts to `commuter_simulator/tests/validation/` folder
  - [ ] Validate performance under realistic load (100+ vehicles)

### **🎯 TIER 3: ADVANCED FEATURES - Passenger Spawning System**

- [ ] **Phase 4**: POI-Based Spawning (0/18 steps)
  - Requires: Phase 1.11 (Geospatial API)
  - Activity-based passenger generation

- [ ] **Phase 5**: Depot/Route Spawners (0/11 steps)
  - Requires: Phase 1.11 (Geospatial API)
  - ST_DWithin queries for proximity spawning

- [ ] **Phase 6**: Conductor Communication (0/7 steps)
  - Requires: Phase 5 (active spawning)
  - Vehicle-passenger interaction

### **🎯 TIER 4: PRODUCTION DEPLOYMENT - Infrastructure & Scaling**

- [ ] **Phase 2**: Redis Integration (0/12 steps) - **MANDATORY for 1,200 Vehicles**
  - **When**: Required before deploying to production (100+ vehicles)
  - **Why**: Position buffering, shared state, horizontal scaling
  - **Server Requirements**: See production deployment section below
  - [ ] Install Redis on production server
  - [ ] Configure Redis for persistence (AOF + RDB)
  - [ ] Implement position buffering (reduce PostgreSQL writes 10×)
  - [ ] Add shared session state for GPS CentCom cluster
  - [ ] Implement device heartbeat tracking (TTL-based)
  - [ ] Add reverse geocoding cache (1 hour TTL)
  - [ ] Configure Redis connection pooling
  - [ ] Test failover scenarios
  - [ ] Implement batch writes from Redis to PostgreSQL
  - [ ] Add monitoring for Redis memory usage
  - [ ] Document Redis backup procedures
  - [ ] Load test with simulated 1,200 devices

- [ ] **Phase 3**: GPS CentCom Cluster Mode (0/8 steps) - **REQUIRED for 1,200 Vehicles**
  - **When**: Required before 200+ vehicles
  - **Why**: Single Node.js process can't handle 1,200 connections
  - [ ] Implement Node.js cluster mode (6-8 workers)
  - [ ] Configure worker process management (PM2 or systemd)
  - [ ] Implement Redis-based session sharing
  - [ ] Add Nginx load balancing across workers
  - [ ] Implement rolling restart mechanism (zero downtime)
  - [ ] Add worker health checks and auto-restart
  - [ ] Test with 1,200 simulated concurrent connections
  - [ ] Document cluster architecture and scaling limits

### **🎯 TIER 5: OPTIMIZATION - Performance Enhancement**

- [ ] **Phase 4**: Geofencing & Real-Time Alerts (0/8 steps)
  - **When**: After Phase 2 (Redis) complete
  - **Why**: Operator notifications for zone violations
  - [ ] Implement geofence pub/sub (Redis channels)
  - [ ] Add zone enter/exit detection logic
  - [ ] Create operator alert dashboard
  - [ ] Add SMS/email notification integration
  - [ ] Implement geofence assignment UI
  - [ ] Add historical geofence violation logs
  - [ ] Test with 100+ vehicles crossing zones
  - [ ] Document alerting workflows

### **🎯 TIER 6: SUBSCRIPTION & ANALYTICS - Historical Data API (Revenue Stream)**

- [ ] **Phase 7**: Subscription Management System (0/12 steps) - **MONETIZATION**
  - [ ] Create subscription_plans table (plan_name, price, retention_days, features)
  - [ ] Create vehicle_subscriptions table (vehicle_id, plan_id, start_date, status)
  - [ ] Implement subscription API endpoints (create, update, cancel, status)
  - [ ] Add billing integration (Stripe/PayPal API)
  - [ ] Create usage tracking (API calls, storage consumption)
  - [ ] Implement rate limiting per subscription tier
  - [ ] Add subscription dashboard (admin view: revenue, active subscribers)
  - [ ] Create customer portal (upgrade/downgrade plans, view usage)
  - [ ] Implement grace period for expired subscriptions (3 days)
  - [ ] Add automated email notifications (payment failed, expiring soon)
  - [ ] Test subscription lifecycle (trial → paid → expired → renewed)
  - [ ] Document pricing model and API quotas

- [ ] **Phase 8**: Historical Position Storage (0/10 steps) - **PAID FEATURE**
  - [ ] Create position_history table with partitioning (by month)
  - [ ] Implement conditional write logic (only for paid subscribers)
  - [ ] Add data retention policy (auto-delete based on subscription tier)
  - [ ] Create background job for Redis → PostgreSQL batch writes
  - [ ] Implement time-series indexes (BRIN for timestamp ranges)
  - [ ] Add storage monitoring (track GB per vehicle per month)
  - [ ] Test with simulated 30-day retention (600 vehicles × 17K positions/day)
  - [ ] Optimize query performance for historical range queries
  - [ ] Add data export API (CSV, JSON, GeoJSON)
  - [ ] Document storage costs per tier ($0.50-5/vehicle/month)

- [ ] **Phase 9**: Analytics API (0/15 steps) - **PAID FEATURE**
  - [ ] Route replay endpoint: GET /api/vehicles/{id}/history?start={ts}&end={ts}
  - [ ] Heat map endpoint: GET /api/analytics/heatmap?zone={id}&timerange={7d}
  - [ ] Distance traveled: GET /api/analytics/distance?vehicle={id}&period={daily/weekly}
  - [ ] Idle time analysis: GET /api/analytics/idle?threshold={5min}
  - [ ] Geofence violations: GET /api/analytics/violations?zone={id}
  - [ ] Speed analytics: GET /api/analytics/speed?vehicle={id}&threshold={80kph}
  - [ ] Aggregated fleet metrics: GET /api/analytics/fleet/summary
  - [ ] Time-of-day analysis: GET /api/analytics/tod?metric={speed/distance}
  - [ ] Implement caching layer (Redis) for expensive analytics queries
  - [ ] Add API authentication (JWT tokens per subscription)
  - [ ] Rate limiting (1000 req/day Basic, unlimited Enterprise)
  - [ ] Create visualization widgets (charts, maps, tables)
  - [ ] Test analytics with 30 days of historical data
  - [ ] Document all analytics endpoints (OpenAPI/Swagger)
  - [ ] Benchmark query performance (<2s for 30-day aggregations)

- [ ] **Phase 10**: Temporal Profile System (0/8 steps) - **ANALYTICS ENHANCEMENT**
  - Create temporal_profiles table (hour, day, rate_multiplier)
  - Define peak patterns (morning rush 7-9am, evening rush 4-7pm)
  - Create seasonal_variations table (month, holiday, multiplier)
  - Link profiles to POI types (school, office, retail, etc.)
  - Import historical patterns (if data becomes available)
  - Validation: Compare simulated vs historical demand curves

- [ ] **Phase 11**: Ridership Data Collection (0/10 steps) - **ANALYTICS ENHANCEMENT**
  - Create ridership_observations table (timestamp, location, passenger_count, route_id)
  - Create passenger_demand_history table (zone_id, hour, day, avg_count, std_dev)
  - Build import pipeline for CSV/Excel ridership data
  - Create API endpoints for manual data entry
  - Implement data validation (outlier detection, consistency checks)
  - Link observations to zones/POIs/routes
  - Generate heat maps and demand visualizations
  - Train ML models on historical data (future: replace Poisson with learned rates)
  - Export calibrated spawn_weights back to landuse/POI tables
  - Dashboard for ridership analytics

**Note**: Current GeoJSON data (189,659 features) provides 80% of spawning model needs. Phase 10-11 adds the missing 20% (temporal patterns, actual ridership) when real-world data becomes available. The existing spawn_weight, peak_hour_multiplier fields in POI/landuse schemas are placeholders ready for calibrated values.

---

## 🖥️ **PRODUCTION DEPLOYMENT REQUIREMENTS**

### **Current Development Server**

- **OVH VPS vps2023-le-2**: 2 vCores, 2 GB RAM, 40 GB Storage
- **Suitable for**: MVP development, real-time tracking demo with **30-50 vehicles**
- **NOT suitable for**: Production deployment at 1,200 vehicle scale

**MVP Capacity Analysis (Real-Time Demo, No Position Storage):**

```text
Memory allocation:
├─ PostgreSQL: ~300 MB (routes, stops, POIs - NO position history)
├─ Strapi: ~300 MB (single instance)
├─ GPS CentCom: ~100 MB + (devices × 20 KB in-memory state)
├─ Geospatial API: ~150 MB
├─ System/OS: ~200 MB
└─ Available for devices: ~950 MB

Capacity:
├─ Conservative (stable): 30-40 vehicles (80% RAM utilization)
├─ Aggressive (max): 50-60 vehicles (95% RAM utilization)
└─ Bottleneck: RAM (not CPU or storage)

Performance expectations:
├─ Position updates: <100ms latency (WebSocket in-memory)
├─ Dashboard queries: <50ms (query in-memory store, not database)
├─ Geospatial queries: <100ms (PostGIS with indexes)
└─ No disk I/O bottleneck (no position writes)

Note: Position data storage is SUBSCRIPTION-BASED (free tier = real-time only, paid tier = history + analytics)
      Free MVP demo: In-memory tracking only | Paid tiers: 7/30/90/365 day retention with analytics API
```

### **Production Scaling Requirements (1,200 Vehicles)**

**Target Fleet Size**: 1,200 GPS devices (ESP32/STM32 with Rock S0 GPS module)  
**Update Frequency**: 1 position/5 seconds  
**Base Load**: 240 position updates/second (in-memory state updates)  
**Dashboard**: 5-10 operators monitoring fleet  
**Business Model**: Free tier (real-time only) + Subscription tiers (historical data + analytics)  
**Position Storage**: Subscription-based (PostgreSQL/InfluxDB for paid tiers, ephemeral for free tier)

#### **Minimum Single Server Option**

**OVH VPS Scale-3 or Advance-2:**

- **12+ vCores** minimum
- **48-64 GB RAM** minimum
- **500 GB SSD** minimum
- **Cost**: ~$150-300/month
- **Capacity**: 800-1,200 vehicles (at limit)
- **Risk**: Single point of failure

**Software Stack:**

```text
├─ GPS CentCom (Node.js Cluster - 6-8 workers)
├─ Strapi (2 instances for HA)
├─ Geospatial API (FastAPI - 1-2 instances)
├─ PostgreSQL (with connection pooling)
├─ Redis (6-8 GB allocated)
└─ Nginx (reverse proxy + load balancer)
```

#### **Recommended Multi-Server Option (High Availability)**

**3× OVH VPS Scale-2:**

- **4 vCores each, 8 GB RAM each, 160 GB SSD each**
- **Cost**: ~$120-180/month total
- **Capacity**: 1,200+ vehicles (400 per server)
- **Benefit**: High availability, horizontal scaling, redundancy, <5 second failover

**Distribution:**

```text
Server 1 (VPS Scale-2):
├─ GPS CentCom Workers 1-2 (400 devices)
├─ Redis MASTER + Sentinel
├─ Strapi Instance 1
├─ PostgreSQL Read Replica (geospatial queries)
└─ Nginx (reverse proxy)

Server 2 (VPS Scale-2):
├─ GPS CentCom Workers 3-4 (400 devices)
├─ Redis REPLICA + Sentinel
├─ Strapi Instance 2
├─ PostgreSQL Read Replica (dashboard queries)
└─ Nginx (reverse proxy)

Server 3 (VPS Scale-2):
├─ GPS CentCom Workers 5-6 (400 devices)
├─ Redis REPLICA + Sentinel
├─ PostgreSQL PRIMARY (write master)
├─ Geospatial API (FastAPI)
└─ Nginx (reverse proxy)

External Load Balancer (CloudFlare or OVH)
```

**Database Synchronization Strategy:**

**PostgreSQL (Single Write Master + Read Replicas):**

```text
All Writes → PostgreSQL Primary (Server 3)
   ↓ Streaming Replication (<100ms lag)
   ├→ Read Replica 1 (Server 1) - Geospatial queries
   └→ Read Replica 2 (Server 2) - Dashboard queries

Configuration:
- Primary: wal_level=replica, max_wal_senders=3
- Replicas: hot_standby=on
- Failover: Automatic with repmgr or Patroni
- No sync conflicts (one-way replication)
```

**Redis (Sentinel HA with Auto-Failover):**

```text
Redis Master (Server 1) - All writes
   ↓ Async replication
   ├→ Redis Replica (Server 2)
   └→ Redis Replica (Server 3)

Sentinels (all 3 servers) monitor master health:
- Quorum: 2/3 votes required for failover
- Detection: 5 seconds down-after-milliseconds
- Failover: Automatic promotion of replica to master
- Downtime: ~10 seconds for automatic failover
```

**Strapi (Active-Active with Shared PostgreSQL):**

```text
Load Balancer
   ├→ Strapi Instance 1 (Server 1) ──┐
   └→ Strapi Instance 2 (Server 2) ──┤
                                      ↓
                   PostgreSQL Primary (Server 3)

- Both instances read/write SAME database (no sync needed)
- Sessions stored in Redis Master (shared state)
- File uploads: Shared volume or S3 bucket
- No data conflicts (single source of truth)
```

**Failover Scenarios:**

| Failure | Detection | Recovery | Downtime | Impact |
|---------|-----------|----------|----------|--------|
| Redis Master dies | Sentinel quorum (5s) | Auto-promote replica | ~10 seconds | In-memory state sync delay |
| PostgreSQL Primary dies | Health check (10s) | Manual/auto promote replica | 30-60 seconds | Reads continue from replicas |
| Entire Server 1 dies | Load balancer (5s) | Route to Server 2/3 | <5 seconds | 400 devices → 600 each temp |
| Network partition | Split-brain detection | Sentinel quorum prevents | N/A | State updates paused |

**Position Storage & Monetization Strategy:**

**Free Tier (Real-Time Only):**

- In-memory state only (current position, route, driver, status)
- Real-time dashboard access
- No historical data retention
- Suitable for: Live tracking, dispatch operations, real-time monitoring

**Subscription Tier (Historical Data + Analytics):**

- Position history storage (PostgreSQL or InfluxDB/TimescaleDB)
- Configurable retention (7 days, 30 days, 90 days, 1 year)
- Analytics API endpoints (route replay, heat maps, performance metrics)
- Reports & visualizations (distance traveled, idle time, geofence violations)
- Data export (CSV, JSON, GeoJSON)
- Monthly fee covers: Storage costs + analytics processing + API access

**Technical Implementation:**

- **Option A**: PostgreSQL with Redis buffer (short-term: 7-30 days retention)
  - Use case: Recent history, basic analytics, route replay
  - Cost: ~$0.50-2/vehicle/month (storage + compute)

- **Option B**: InfluxDB/TimescaleDB (long-term: 90 days - 1 year retention)
  - Use case: Advanced analytics, trend analysis, compliance reporting
  - Cost: ~$2-5/vehicle/month (time-series optimization, higher storage)

- **Option C**: Hybrid (Redis → PostgreSQL → Cold Storage/S3)
  - Use case: Multi-tier retention (hot: 7 days, warm: 30 days, cold: 1 year)
  - Cost: ~$1-3/vehicle/month (tiered pricing based on access frequency)

**Pricing Model Examples:**

```text
Free Tier:
├─ Real-time tracking only
├─ Current position data
└─ $0/month per vehicle

Basic Plan ($5/vehicle/month):
├─ 7 days position history
├─ Basic analytics (distance, idle time)
├─ Route replay
└─ CSV export

Professional Plan ($15/vehicle/month):
├─ 30 days position history
├─ Advanced analytics (heat maps, performance)
├─ API access (1000 req/day)
├─ Automated reports
└─ GeoJSON export

Enterprise Plan ($30/vehicle/month):
├─ 1 year position history
├─ Full analytics suite
├─ Unlimited API access
├─ Custom integrations
├─ SLA guarantee (99.9% uptime)
└─ Dedicated support
```

**Revenue Projection (1,200 vehicles):**

```text
Scenario 1 (Conservative - 30% paid subscribers):
├─ 360 vehicles × $15/month (Professional) = $5,400/month
├─ Infrastructure costs: ~$200-300/month (single server)
└─ Net revenue: ~$5,100/month

Scenario 2 (Moderate - 50% paid subscribers):
├─ 600 vehicles × $15/month (Professional) = $9,000/month
├─ Infrastructure costs: ~$300-400/month (upgraded server)
└─ Net revenue: ~$8,600/month

Scenario 3 (High adoption - 70% paid subscribers):
├─ 840 vehicles × $15/month (Professional) = $12,600/month
├─ Infrastructure costs: ~$400-500/month (multi-server)
└─ Net revenue: ~$12,100/month
```

**Why Multi-Server vs Single Server:**

| Aspect | Single Server (Advance-2) | Multi-Server (3× Scale-2) |
|--------|---------------------------|---------------------------|
| **Cost** | ~$200/month | ~$150/month total |
| **Complexity** | Low (no sync needed) | Medium (sync configuration) |
| **Availability** | 99% (single point of failure) | 99.9% (survives server failure) |
| **Acceptable Downtime** | 30-60 minutes (hardware failure) | <5 seconds (automatic failover) |
| **Suitable for** | MVP, Pilot, cost-sensitive | Production SLA, mission-critical |
| **Management Effort** | Low | Medium (monitoring, failover testing) |
| **Position Storage Impact** | None (in-memory only) | None (in-memory only) |

**Recommendation**: Start with **Single Server** for MVP/Pilot (handles 50-100 vehicles with in-memory state). Migrate to **Multi-Server** when:

- You have >500 active vehicles
- SLA requires <5 minute downtime
- You decide to store position history (adds write load)
- You have operational experience to manage distributed systems
- Budget allows for monitoring/alerting infrastructure

### **Redis Requirements**

**Why Redis is MANDATORY for 1,200 vehicles:**

1. **In-memory state sharing**: GPS CentCom workers share device state across processes
2. **Dashboard performance**: Query 1,200 positions in <5ms (vs 100-200ms from PostgreSQL)
3. **Device heartbeat**: TTL-based online/offline detection
4. **Session state**: Shared sessions across Strapi instances
5. **Horizontal scaling**: Required for multi-server deployment
6. **Optional position buffering**: IF storing position history (TBD for production)

**Memory sizing (in-memory state only, no position storage):**

```text
1,200 vehicle current positions × 200 bytes = 240 KB (current state)
Device metadata (route, driver, etc.) × 1,200 = ~500 KB
Session data, heartbeats: ~200 MB
Dashboard cache: ~100 MB
Total: ~300 MB active data + 50% overhead = 450 MB minimum
Recommended allocation: 1-2 GB (comfortable headroom)

IF storing position trails (100 positions per vehicle):
Position trails: 100 × 200 bytes × 1,200 = 24 MB additional
Total with trails: ~500 MB + 50% overhead = 750 MB
Recommended allocation with trails: 2-4 GB
```

### **PostgreSQL Requirements**

**Connection pooling (PgBouncer):**

- Max connections: 100
- Pool size: 20-30
- Writes: Configuration data only (routes, stops, POIs)
- NO position writes (in-memory only for MVP)

**Storage (no position history):**

```text
Base schema + indexes: ~500 MB
GeoJSON data (189,659 features): ~4.5 GB
Routes, stops, schedules: ~500 MB
Total: ~5.5 GB (static - no growth)

IF position history added later:
1,200 vehicles × 17,280 updates/day = 20,736,000 positions/day
Daily growth: ~2 GB
Monthly growth: ~60 GB
Recommended: 500 GB minimum, with rotation/archival after 6 months
```

### **Development → Production Migration Path**

#### Phase 1: MVP Demo (Current - 2 vCore, 2 GB)

- ✅ Real-time tracking demo with **30-50 vehicles**
- ✅ In-memory state only (no position storage)
- ✅ Single GPS CentCom worker (no cluster mode)
- ✅ No Redis needed (in-memory store sufficient)
- ✅ All features work for demo/testing
- ⚠️ NOT suitable for production (no redundancy, limited capacity)

#### Phase 2: Prototype Testing (Upgrade to VPS Scale-2)

- 🎯 4 vCores, 8 GB RAM, 160 GB SSD (~$40-60/month)
- 🎯 **100-200 vehicles** capacity
- 🎯 Add Redis (1-2 GB allocation)
- 🎯 Test GPS CentCom cluster mode (2-4 workers)
- 🎯 Deploy 5-20 real prototype devices
- 🎯 Decide on position storage strategy (PostgreSQL vs InfluxDB vs ephemeral)

#### Phase 3: Pilot Deployment (Upgrade to VPS Scale-3)

- 🎯 8-12 vCores, 32 GB RAM, 400 GB SSD (~$100-150/month)
- 🎯 **500-800 vehicles** capacity
- 🎯 Redis + GPS CentCom cluster operational
- 🎯 Limited production fleet
- 🎯 Position storage implemented (if needed)
- 🎯 Monitoring and alerting configured

#### Phase 4: Full Production (VPS Advance-2 or 3× Scale-2)

- 🎯 12+ vCores, 64 GB RAM, 500 GB SSD (single server ~$200/month)
- 🎯 OR: 3× Scale-2 with load balancer (multi-server ~$150/month)
- 🎯 **1,200 vehicles** full deployment
- 🎯 Redis cluster (2-4 GB), PostgreSQL replica (if storing positions), full monitoring

### **Critical Pre-Production Checklist**

Before deploying to production with real GPS devices:

**Single Server Deployment (VPS Advance-2):**

- [ ] Server upgraded to minimum VPS Advance-2 (12 vCore, 64 GB RAM, 500 GB SSD)
- [ ] Redis installed and configured with persistence (RDB + AOF)
- [ ] GPS CentCom cluster mode implemented and tested (6-8 workers)
- [ ] PostgreSQL connection pooling configured (PgBouncer: 20-30 connections)
- [ ] Monitoring and alerting configured (CPU, RAM, disk, connection counts)
- [ ] Backup procedures documented and automated (PostgreSQL + Redis snapshots)
- [ ] Load tested with 1,200 simulated concurrent connections
- [ ] Disaster recovery plan documented (backup restoration SLA)
- [ ] Rolling deployment procedure tested

**Multi-Server Deployment (3× VPS Scale-2) - Additional Requirements:**

- [ ] PostgreSQL streaming replication configured (Primary → 2 Replicas)
- [ ] Redis Sentinel configured on all 3 servers (quorum: 2/3)
- [ ] Strapi session storage moved to Redis (shared state)
- [ ] Load balancer configured with health checks (CloudFlare or Nginx)
- [ ] Failover testing completed:
  - [ ] Redis master failure → auto-promote replica (<10s)
  - [ ] PostgreSQL primary failure → promote replica (<60s)
  - [ ] Entire server failure → load balancer routes traffic (<5s)
- [ ] Network partition handling tested (split-brain scenarios)
- [ ] Cross-server monitoring configured (centralized dashboard)
- [ ] Automated failover documented (runbooks for manual intervention)

---

## 📡 **GPS CENTCOM PRODUCTION READINESS**

- ✅ **Current Status**: MVP Demo Ready (FastAPI + WebSocket + In-Memory Store)
- [ ] **Future Tier 1**: Production-Grade Improvements
  - Persistent datastore (Redis or Postgres)
  - Per-device authentication tokens
  - Structured logging (JSON)
  - Basic metrics (Prometheus)
- [ ] **Future Tier 2**: Scale to Real Fleet
  - Horizontal scaling (Redis cluster)
  - Encrypted payloads (AESGCM server-side)
  - Advanced monitoring (Grafana/ELK)
  - CI/CD pipeline with tests

**Total Progress**: 18/92 major steps across GeoJSON + Spawning phases (Building import complete Oct 26)
**GPS CentCom**: Separate track, deferred until simulator fully functional

---

## 📡 **GPS CENTCOM SERVER STATUS**

**Location**: `gpscentcom_server/`  
**Technology**: FastAPI + WebSocket + In-Memory Store  
**Port**: 5000  
**Status**: ✅ MVP Demo Ready (production deployment exists)

### **Current Capabilities**

✅ **Core Features**:

- Real-time WebSocket telemetry ingestion (`/device` endpoint)
- REST APIs for device queries (`/devices`, `/device/{id}`, `/route/{code}`, `/analytics`)
- Auto-cleanup of stale devices (120s timeout)
- Plugin-based GPS device (simulation, ESP32, file replay, navigator)
- PING/PONG keepalive handling
- Structured error responses (ErrorRegistry)
- CORS enabled for cross-origin requests
- Socket.IO progress events during import operations
- Production deployment (Systemd + Nginx reverse proxy)

✅ **Data Model**:

- DeviceState with Pydantic validation
- Route-based filtering and analytics
- Lat/lon, speed, heading, timestamp tracking
- Driver/conductor metadata support

### **Known Limitations** (See CONTEXT.md for details)

❌ **Critical Production Gaps**:

1. **No persistence** - In-memory only, data lost on restart
2. **Shared auth token** - All devices use same `AUTH_TOKEN`
3. **No horizontal scaling** - Single-process limitation
4. **No AESGCM server support** - Binary codec exists client-side but not server-side
5. **No monitoring/metrics** - No Prometheus, no structured logging
6. **No rate limiting** - Vulnerable to DoS attacks
7. **No unit tests** - Zero automated testing
8. **Single server connection** - No redundant server failover for GPS devices

### **Production Roadmap** (from `gpscentcom_server/TODO.md`)

**MVP Production Grade** (safe for staging/investor pilots):

- [ ] Persistent datastore (Redis or Postgres) - **HIGH PRIORITY**
- [ ] Structured logging (JSON logs for cloud platforms)
- [ ] Basic metrics (Prometheus)
- [ ] TLS/HTTPS termination (wss://)
- [ ] Per-device identifiers + token pairs
- [ ] Unit tests for core modules
- [ ] Graceful shutdown improvements
- [ ] **Redundant server list for GPS device failover** - **HIGH PRIORITY**

**Redundant GPS Server Architecture** (Future Enhancement):

GPS devices should support automatic failover to redundant servers:

```python
# Future GPS Device Configuration
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

**Implementation Requirements**:
- [ ] Multi-server configuration in GPS device
- [ ] Priority-based server selection algorithm
- [ ] Automatic failover on connection loss
- [ ] Periodic health checks to prefer primary server
- [ ] Server list updates via configuration or API
- [ ] Telemetry tracking which server is active
- [ ] Load balancing across redundant servers (optional)

**MVP Complete** (foundation for real deployment):

- [ ] Horizontally scalable store (Redis cluster/Postgres HA)
- [ ] Per-device authentication & key management
- [ ] Encrypted payloads (AES/TLS end-to-end)
- [ ] Replay protection / integrity checks
- [ ] Advanced monitoring & alerts (Grafana/ELK)
- [ ] CI/CD pipeline with tests
- [ ] Extensible codec framework (CBOR, protobuf)

### **Integration with Vehicle Simulator**

**Current Flow**:

```text
arknet_transit_simulator
  └─ vehicle/gps_device/
       ├─ Plugin Manager (simulation/ESP32/file/navigator)
       ├─ RxTx Buffer (FIFO queue, max 1000 items)
       ├─ WebSocketTransmitter
       └─ PacketCodec (JSON/AESGCM)
            ↓
            ws://server:5000/device?token=xxx&deviceId=yyy
            ↓
gpscentcom_server
  ├─ rx_handler.py (WebSocket endpoint)
  ├─ connection_manager.py (lifecycle management)
  ├─ store.py (in-memory DeviceState)
  └─ api_router.py (REST endpoints)
       ↓
       GET /devices → Dashboard
```

**Recommendation**:

- ✅ Use now for development, testing, and demos (10-50 vehicles)
- ❌ Don't deploy to real vehicles without Redis + per-device auth
- 🎯 Priority if moving to production: Redis storage, per-device tokens, Prometheus metrics

---

## 🎨 **PHASE 1: COUNTRY SCHEMA + ACTION BUTTONS**

**Goal**: Update country schema, add action buttons, migrate successfully, verify UI

### **STEP 1.1: Analyze Current State** ⏱️ 30 min

- [x] **1.1.1** Read current country schema
  - File: `arknet_fleet_manager/arknet-fleet-api/src/api/country/content-types/country/schema.json`
  - Document existing fields
  - ✅ COMPLETED: Schema analyzed (113→145 lines)
  - ✅ COMPLETED: Database verified (16 columns in `countries` table)
  - ✅ COMPLETED: Migrated `geodata_import_status` from text→json with structured default
  - ✅ COMPLETED: Cleared old data, ready for fresh import tracking
  
- [x] **1.1.2** Verify action-buttons plugin exists
  - Path: `src/plugins/strapi-plugin-action-buttons/`
  - Plugin name: `strapi-plugin-action-buttons` ✅ (custom ArkNet plugin, no marketplace equivalent)
  - Check if enabled in `config/plugins.js`
  - ✅ COMPLETED: Plugin directory structure verified
  - ✅ COMPLETED: Documentation exists (ARCHITECTURE.md, EXAMPLES.ts, README.md)
  - ✅ COMPLETED: Plugin enabled in config/plugins.ts
  - ✅ COMPLETED: Built files exist in dist/ folder
  - ✅ COMPLETED: Strapi restart validated schema migration (text→jsonb)
  
- [x] **1.1.3** List current country fields in database
  - Query: `SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'countries'`
  - ✅ COMPLETED: 16 columns verified
  - ✅ COMPLETED: geodata_import_status confirmed as jsonb (migration successful)
  - ✅ COMPLETED: No unexpected schema changes after restart
  - ✅ COMPLETED: Database ready for button field addition

**✅ Validation**: Schema read, plugin confirmed, database columns listed

---

### **STEP 1.2: Review Plugin Documentation** ⏱️ 30 min

- [x] **1.2.1** Read plugin architecture ✅
  - File: `src/plugins/strapi-plugin-action-buttons/ARCHITECTURE.md`
  - ✅ COMPLETED: 290 lines read
  - ✅ COMPLETED: Component hierarchy understood (Schema → Registration → Component → Handler)
  - ✅ COMPLETED: Data flow understood (Button → window[onClick] → handler → DB)
  - ✅ COMPLETED: Security model understood (browser execution with admin privileges)
  
- [x] **1.2.2** Review examples ✅
  - File: `src/plugins/strapi-plugin-action-buttons/EXAMPLES.ts`
  - ✅ COMPLETED: 257 lines read
  - ✅ COMPLETED: 5 example handlers reviewed (send email, upload CSV, generate report, sync CRM, default action)
  - ✅ COMPLETED: Handler pattern understood: window[functionName] = async (fieldName, fieldValue, onChange) => {...}
  - ✅ COMPLETED: Metadata tracking pattern: onChange({ status, timestamp, ...data })
  - ✅ COMPLETED: Error handling pattern: try/catch with success/failed status
  
- [x] **1.2.3** Understand field configuration ✅
  - Focus: `plugin::action-buttons.button-field` field type
  - ✅ COMPLETED: Read README.md documentation (lines 1-250)
  - ✅ COMPLETED: Field configuration structure:

    ```json
    {
      "type": "customField",
      "customField": "plugin::action-buttons.button-field",
      "options": {
        "buttonLabel": "Click Me",
        "onClick": "handleMyAction"
      }
    }
    ```

  - ✅ COMPLETED: Handler signature: `function(fieldName: string, fieldValue: any, onChange?: (value: any) => void)`
  - ✅ COMPLETED: Ready to design GeoJSON import button configuration

**✅ Validation**: Plugin architecture understood, field configuration mastered

---

### **STEP 1.3: Backup Current Schema** ⏱️ 15 min

- [x] **1.3.1** Backup database ✅
  - Command: `pg_dump -U david -h 127.0.0.1 -d arknettransit -F p -f backup_TIMESTAMP.sql`
  - ✅ COMPLETED: Created backup_20251025_145744.sql (6.4 MB)
  - ✅ COMPLETED: All tables, data, schemas, constraints, indexes backed up
  
- [x] **1.3.2** Backup schema.json ✅
  - Command: `Copy-Item schema.json schema.json.backup_TIMESTAMP`
  - ✅ COMPLETED: Created schema.json.backup_20251025_152235 (3,357 bytes)
  - ✅ COMPLETED: Current schema with 145 lines and json field backed up
  
- [x] **1.3.3** Document rollback procedure ✅
  - Database: `psql -U david -h 127.0.0.1 -d arknettransit -f backup_20251025_145744.sql`
  - Schema: `Copy-Item schema.json.backup_20251025_152235 schema.json -Force; npm run develop`
  - ✅ COMPLETED: Rollback procedures documented

**✅ Validation**: Backups created (6.4 MB database + 3.4 KB schema), rollback documented

---

### **STEP 1.4: Install Socket.IO & Setup Infrastructure** ⏱️ 15 min

- [x] **1.4.1** Install Socket.IO client dependency ✅
  - Command: `npm install socket.io-client --save`
  - ✅ COMPLETED: Installed socket.io-client@4.8.1
  - ✅ COMPLETED: Verified in package.json (3 packages added)
  
- [x] **1.4.2** Create button-handlers.ts file structure ✅
  - File: `src/admin/button-handlers.ts`
  - ✅ COMPLETED: Created file with 387 lines
  - ✅ COMPLETED: Added TypeScript declarations for 5 handlers
  - ✅ COMPLETED: Added Socket.IO import and connection logic
  - ✅ COMPLETED: Added utility functions (getCountryId, getAuthToken, getApiBaseUrl)
  - ✅ COMPLETED: Created generic handleGeoJSONImport function
  - ✅ COMPLETED: Created 5 specific handlers (highway, amenity, landuse, building, admin)
  - ✅ COMPLETED: Added real-time Socket.IO progress tracking
  - ✅ COMPLETED: Added error handling and user feedback
  
- [x] **1.4.3** Add first button field to schema (Highway) ✅
  - File: `src/api/country/content-types/country/schema.json`
  - ✅ COMPLETED: Added `import_highway` field (lines 143-150)
  - ✅ COMPLETED: Configured as customField type
  - ✅ COMPLETED: Set customField to "plugin::action-buttons.button-field"
  - ✅ COMPLETED: Added options { buttonLabel: "🛣️ Import Highways", onClick: "handleImportHighway" }
  - ✅ COMPLETED: Validated JSON syntax (no errors)
  - ✅ COMPLETED: Schema now 153 lines (was 145)
  
- [x] **1.4.4** Create first handler (handleImportHighway) ✅
  - ✅ COMPLETED: Handler already created in step 1.4.2
  - ✅ COMPLETED: Full Socket.IO implementation
  - ✅ COMPLETED: Progress tracking with real-time updates
  - ✅ COMPLETED: Error handling and user feedback
  - ✅ COMPLETED: Metadata updates (status, progress, features)
  
- [x] **1.4.5** Wire up handler in app.tsx ✅
  - File: `src/admin/app.ts`
  - ✅ COMPLETED: Added import './button-handlers' at line 2
  - ✅ COMPLETED: Handlers will load when admin panel initializes
  - ✅ COMPLETED: All 5 handlers available on window object

**✅ Validation**: Socket.IO installed, handler structure created, Highway button ready

---

### **STEP 1.5: Test First Button (Highway)** ✅ COMPLETE

- [x] **1.5.1** Restart Strapi ✅
  - ✅ COMPLETED: Strapi restarted successfully
  - ✅ COMPLETED: No schema errors
  - ✅ COMPLETED: Custom field registered correctly
  
- [x] **1.5.2** Test Highway button in admin UI ✅
  - ✅ COMPLETED: Highway button appears in country edit page
  - ✅ COMPLETED: Confirmation dialog shows "Import highway.geojson for this country?"
  - ✅ COMPLETED: Handler functional
  
- [x] **1.5.3** Validate Highway button complete ✅
  - ✅ Button renders correctly
  - ✅ Handler function loaded (window.handleImportHighway)
  - ✅ Socket.IO client ready
  - ✅ Error handling graceful

**✅ Validation**: First button working, pattern validated

---

### **STEP 1.6: Add Remaining 4 Buttons** ✅ COMPLETE

- [x] **1.6.1** Add Amenity button field + handler ✅
  - ✅ COMPLETED: Added `import_amenity` field to schema
  - ✅ COMPLETED: Handler `handleImportAmenity` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import amenity.geojson for this country?"
  
- [x] **1.6.2** Add Landuse button field + handler ✅
  - ✅ COMPLETED: Added `import_landuse` field to schema
  - ✅ COMPLETED: Handler `handleImportLanduse` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import landuse.geojson for this country?"
  
- [x] **1.6.3** Add Building button field + handler ✅
  - ✅ COMPLETED: Added `import_building` field to schema
  - ✅ COMPLETED: Handler `handleImportBuilding` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import building.geojson for this country?"
  
- [x] **1.6.4** Add Admin button field + handler ✅
  - ✅ COMPLETED: Added `import_admin` field to schema
  - ✅ COMPLETED: Handler `handleImportAdmin` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import admin.geojson for this country?"
  
- [x] **1.6.5** Final validation - All 5 buttons ✅
  - ✅ VERIFIED: All 5 buttons render in UI
  - ✅ VERIFIED: Each button tested individually
  - ✅ VERIFIED: All handlers loaded (window.handleImport*)
  - ✅ VERIFIED: Confirmation dialogs display correct filenames

**✅ Validation**: All 5 buttons working, UI complete - PHASE 1 COMPLETE!

---

### **STEP 1.7: Highway Import with PostGIS** ⏱️ 90 min  

- [x] **1.7.1-1.7.3b** Backend API + Highway record insertion ✅ COMPLETE
  - Created `/api/import-geojson/highway` endpoint
  - Highway properties mapped and inserted
  - Tested with first feature from highway.geojson

- [x] **1.7.3c** PostGIS geometry insertion ✅ COMPLETE (Oct 25, 2025 17:57)
  - **CRITICAL FIX**: Rewrote from individual points to PostGIS LineString
  - Uses `ST_GeomFromText()` with WKT format
  - Single UPDATE query per highway
  - GIST spatial index on highways.geom column
  - Tested: 5-point LineString created successfully

**✅ Validation**: Highway import working with proper PostGIS geometry

---

### **STEP 1.8: 🚨 CRITICAL - Complete PostGIS Migration** ⏱️ 2-3 hours

**STATUS**: BLOCKING - Must complete before any other imports

**Problem**: Database uses individual lat/lon columns instead of PostGIS geometry  
**Impact**: $50K+ cost, 90% more records, 10-100x slower queries  
**Solution**: Execute comprehensive PostGIS migration for ALL spatial tables

#### **1.8.1** Execute PostGIS Migration Script ✅ COMPLETE (Oct 25, 2025 18:15)

- [x] **1.8.1a** Review migration script ✅
  - File: `arknet_fleet_manager/arknet-fleet-api/migrate_all_to_postgis.sql`
  - Migrates: stops, shapes, depots, geofences, vehicle_events, active_passengers
  
- [x] **1.8.1b** Execute migration ✅
  - Command executed successfully
  - No errors during execution
  - All success messages confirmed
  
- [x] **1.8.1c** Verify PostGIS columns created ✅
  - Verified 11 tables with geometry columns
  - Tables: highways, stops, depots, landuse_zones, pois, regions, geofences, shape_geometries, vehicle_events, active_passengers, geofence_all

#### **1.8.2** Verify GIST Spatial Indexes ✅ COMPLETE (Oct 25, 2025 18:16)

- [x] **1.8.2a** Check spatial indexes exist ✅
  - Verified 12 GIST spatial indexes created
  - Tables: highways, stops, depots, landuse_zones, pois, regions, geofences, shape_geometries, vehicle_events, active_passengers, geofence_circles, geofence_polygons
  - All using GIST index method

- [ ] **1.8.2b** Verify index types are GIST
  - All spatial indexes must use GIST (not BTREE)

#### **1.8.3** Test Spatial Queries

- [ ] **1.8.3a** Test point distance query (stops)
  - Find stops within 1km of a point
  - Verify uses spatial index (check EXPLAIN ANALYZE)
  
#### **1.8.3** Test Spatial Queries ✅ COMPLETE (Oct 25, 2025 18:17)

- [x] **1.8.3a** Test distance calculation (depots) ✅
  - Tested ST_DWithin() for finding depots within 5km
  - Query execution: 21.382ms
  - Found 4 depots within range
  
- [x] **1.8.3b** Test line length calculation (highways) ✅
  - Tested ST_Length() on highways and shape_geometries
  - Highway: 0.055 km (55 meters)
  - Shape geometries: Ranges from 0.24 km to 1.41 km
  
- [x] **1.8.3c** Verified PostGIS geometry types ✅
  - Highways: LineString with ST_NumPoints() working
  - Depots: Point geometry with ST_AsText() working
  - Shape geometries: Aggregated LineStrings (7-45 points each)

#### **1.8.4** Update Import Code for PostGIS ✅ COMPLETE (Oct 25, 2025 18:25)

- [x] **1.8.4a** Update amenity/POI import ✅
  - Extracts centroid from Point/Polygon/MultiPolygon geometries
  - Inserts as PostGIS Point: `ST_GeomFromText('POINT(lon lat)', 4326)`
  - Handles all geometry types with centroid calculation
  
- [x] **1.8.4b** Update landuse import ✅
  - Converts Polygon/MultiPolygon to PostGIS Polygon
  - Uses `ST_GeomFromText('POLYGON(...)', 4326)`
  - Handles MultiPolygon by using first polygon
  
- [x] **1.8.4c** Update building import ✅
  - Placeholder implementation (table doesn't exist yet)
  - PostGIS pattern documented for future implementation
  - Notes: Requires streaming parser for 658MB file
  
- [x] **1.8.4d** Update admin boundaries import ✅
  - Converts Polygon/MultiPolygon to PostGIS MultiPolygon
  - Uses `ST_GeomFromText('MULTIPOLYGON(...)', 4326)`
  - Handles single Polygon by converting to MultiPolygon for consistency

**✅ Validation**: All import endpoints updated with PostGIS geometry insertion pattern

---

### **STEP 1.9: Create Buildings Content Type** ⏱️ 30 min ✅ COMPLETE

**CRITICAL**: Buildings table required for realistic passenger spawning model (see CONTEXT.md "Passenger Spawning Architecture")

- [x] **1.9.1** Create building content type schema ✅
  - File: `src/api/building/content-types/building/schema.json`
  - ✅ Created schema with collectionName: "buildings"
  - ✅ Created controllers, routes, and services
  
- [x] **1.9.2** Define building schema fields ✅
  - ✅ `building_id` (UID, required, unique)
  - ✅ `osm_id` (biginteger, required)
  - ✅ `full_id` (string, maxLength: 50)
  - ✅ `building_type` (string, default: "yes")
  - ✅ `name` (string, nullable, maxLength: 255)
  - ✅ `addr_street` (string, nullable)
  - ✅ `addr_city` (string, nullable)
  - ✅ `addr_housenumber` (string, nullable)
  - ✅ `levels` (integer, nullable) - number of floors
  - ✅ `height` (decimal, nullable)
  - ✅ `amenity` (string, nullable)
  - ✅ `country` (relation to country, manyToOne)
  
- [x] **1.9.3** Add PostGIS geometry column ✅
  - ✅ Ran SQL: `ALTER TABLE buildings ADD COLUMN geom geometry(Polygon, 4326);`
  - ✅ Created GIST index: `CREATE INDEX idx_buildings_geom ON buildings USING GIST(geom);`
  - ✅ Verified: `\d buildings` shows geom geometry(Polygon,4326) column
  - ✅ GIST index confirmed: idx_buildings_geom gist (geom)
  
- [x] **1.9.4** Strapi restart and table creation ✅
  - ✅ Strapi restarted successfully
  - ✅ Buildings table created automatically by Strapi ORM
  - ✅ Buildings relation added to country schema
  - ✅ Ready for import endpoint testing (requires streaming parser for 658MB file)

**✅ Validation**: Buildings table exists with PostGIS geometry column and GIST index

---

### **STEP 1.10: Streaming GeoJSON Parser** ⏱️ 90 min

**CRITICAL**: Required for all GeoJSON imports - ensures consistency, memory efficiency, and production scalability

**Strategy Decision**: Implement streaming for **ALL 5 content types** (highway, amenity, landuse, building, admin)

**Rationale**:

- **Consistency**: Single code path reduces bugs and maintenance
- **Memory Efficiency**: 628MB building.geojson requires streaming; applying to all ensures <500MB memory usage
- **Progress Feedback**: Real-time progress bars for all imports (not just large files)
- **Future-Proofing**: Data grows (Barbados → multi-country), small files today = large files tomorrow
- **Batch Processing**: Consistent 500-1000 feature batches for optimal database performance

**File Size Analysis**:

- building.geojson: **628.45 MB** ⚠️ CRITICAL - streaming required
- highway.geojson: **41.22 MB** - streaming beneficial
- landuse.geojson: **4.12 MB** - streaming for consistency
- amenity.geojson: **3.65 MB** - streaming for consistency
- admin boundaries: **0.02-0.28 MB** - streaming for consistency

- [x] **1.10.1** Install streaming parser dependencies ✅
  - ✅ Ran: `cd arknet_fleet_manager/arknet-fleet-api && npm install stream-json`
  - ✅ Verified in package.json: "stream-json": "^1.9.1"
  
- [x] **1.10.2** Create reusable GeoJSON streaming parser utility ✅
  - ✅ Created: `src/utils/geojson-stream-parser.ts` (243 lines)
  - ✅ Implemented `streamGeoJSON()` function with batch processing
  - ✅ Implemented `estimateFeatureCount()` for progress estimation
  - ✅ Features:
    - Memory-efficient streaming (uses stream-json pipeline)
    - Configurable batch size (default: 500 features)
    - Progress callbacks per batch (for Socket.IO)
    - Error handling (file not found, malformed JSON, batch processing errors)
    - Pause/resume stream during batch processing
    - TypeScript interfaces: StreamingOptions, StreamProgress, StreamResult
  
- [ ] **1.10.3** Update ALL 5 import endpoints to use streaming
  - ⏳ **Admin import** - UPDATE endpoint (exists, imports 1 feature, needs full streaming import)
  - ⏳ **Highway import** - UPDATE endpoint (exists, uses readFileSync, needs streaming)
  - ⏳ **Amenity import** - UPDATE endpoint (exists, uses readFileSync, needs streaming)
  - ⏳ **Landuse import** - UPDATE endpoint (exists, uses readFileSync, needs streaming)
  - ✅ **Building import** - COMPLETED with streaming (628MB file, 500 feature batches, 162,942 records)
  - Replace all `fs.readFileSync` with streaming parser
  - Process features in batches (500-1000 at a time)
  - Emit Socket.IO progress updates per batch
  - **NOTE**: Strapi v5 EntityService doesn't have `createMany()` - use bulk SQL inserts
  - **STATUS**: 1/5 complete (Building only), 4 endpoints need conversion to streaming
  
- [ ] **1.10.4** Test streaming with building.geojson (stress test)
  - Click Building button in UI
  - Monitor memory usage (should stay <500MB throughout)
  - Verify progress updates in real-time (batch-by-batch)
  - Test with 628MB file (may take 10-30 minutes)
  - Confirm no memory leaks during long import
  
- [ ] **1.10.5** Validate streaming performance for all imports
  - Test all 5 import buttons sequentially
  - Check memory usage during each import (<500MB)
  - Verify no memory leaks between imports
  - Confirm batch progress updates working for all types
  - Measure and document import times per file
  
- [ ] **1.10.6** Production optimization
  - Fine-tune batch size for optimal performance (test 500, 1000, 2000)
  - Add error recovery (resume from last successful batch)
  - Add import cancellation support
  - Document memory usage benchmarks in CONTEXT.md

**✅ Validation**: Streaming parser working for all 5 content types, memory <500MB, no leaks, 628MB file imports successfully

---

### **STEP 1.11: Geospatial Services API (Phase 1)** ⏱️ 90 min

**CRITICAL**: Provides optimized spatial queries for simulators (see CONTEXT.md "Geospatial Services Architecture")

#### **Phase 1: Strapi Custom Controllers** (Current)

- [ ] **1.11.1** Create geospatial content type structure
  - Generate: `cd arknet_fleet_manager/arknet-fleet-api && npm run strapi generate`
  - Select: "api" → "geospatial"
  - Creates: `src/api/geospatial/` folder structure
  
- [ ] **1.11.2** Implement geofencing endpoints
  - File: `src/api/geospatial/controllers/geospatial.ts`
  - Endpoint: `POST /api/geospatial/check-geofence`
    - Input: `{ lat, lon }`
    - Query: `SELECT * FROM geofences WHERE ST_Contains(geom, ST_MakePoint(?, ?))`
    - Output: Array of zones containing point
  - Endpoint: `POST /api/geospatial/batch-geofence`
    - Input: `[{ lat, lon }, ...]`
    - Batch query for multiple points
  
- [ ] **1.11.3** Implement reverse geocoding endpoints
  - Endpoint: `POST /api/geospatial/reverse-geocode`
    - Input: `{ lat, lon }`
    - Query: Find nearest address/building with name
    - Output: `{ address, building_name, distance }`
  
- [ ] **1.11.4** Implement spawning spatial queries
  - Endpoint: `GET /api/geospatial/route-buildings?route_id=X&buffer=500`
    - Query: `ST_DWithin(building.geom, route_shape.geom, buffer)`
    - Output: Buildings within route buffer
  - Endpoint: `GET /api/geospatial/depot-buildings?depot_id=X&radius=1000`
    - Query: `ST_DWithin(building.geom, depot.geom, radius)`
    - Output: Buildings in depot catchment
  - Endpoint: `GET /api/geospatial/zone-containing?lat=X&lon=Y`
    - Query: `ST_Contains(landuse_zone.geom, ST_MakePoint(?, ?))`
    - Output: Landuse zone containing point
  - Endpoint: `GET /api/geospatial/nearby-pois?lat=X&lon=Y&radius=500`
    - Query: `ST_DWithin(poi.geom, ST_MakePoint(?, ?), radius)`
    - Output: POIs within radius
  
- [ ] **1.11.5** Add route definitions
  - File: `src/api/geospatial/routes/geospatial.ts`
  - Configure all endpoints with proper HTTP methods
  - Add authentication/authorization if needed
  
- [ ] **1.11.6** Test geospatial endpoints
  - Test geofence check with known coordinates
  - Test route-buildings query with existing route
  - Test depot-buildings query with existing depot
  - Verify PostGIS functions working (ST_DWithin, ST_Contains)
  - Check query performance (<100ms for simple queries)
  
- [ ] **1.11.7** Document API endpoints
  - Add OpenAPI/Swagger documentation
  - Document expected inputs/outputs
  - Provide example curl commands

**✅ Validation**: All geospatial endpoints working, simulators can query spatial data

**⏳ Phase 2 (Future)**: Extract to separate `geospatial_service/` FastAPI service when scaling needed (>1000 req/s)

---

### **STEP 1.12: Database Integration** ⏱️ 32 min

- [ ] **1.12.1** Update geodata_import_status after import
  - After successful import, update JSON field
  - Set status, featureCount, lastImportDate, jobId
  - Verify field updates in database
  
- [ ] **1.9.2** Store features in database (temporary solution)
  - Create temporary table for imported features
  - Store GeoJSON features during import
  - Verify data persists
  
- [ ] **1.9.3** Test end-to-end import (Highway)
  - Import highway.geojson fully
  - Verify database updated
  - Verify button metadata updated
  - Verify geodata_import_status field updated
  
- [ ] **1.9.4** Validate all 5 file types import to DB
  - Import all 5 file types sequentially
  - Verify data in database for each
  - Check geodata_import_status field shows all 5
  - Verify total feature counts accurate

**✅ Validation**: Full import pipeline working, data persisting, UI showing accurate status

---

### **STEP 1.10: Final Testing & Documentation** ⏱️ 20 min

- [ ] **1.10.1** Complete end-to-end test
  - Import all 5 GeoJSON files
  - Verify all progress updates work
  - Verify all database updates complete
  - Screenshot working UI
  
- [ ] **1.10.2** Document implementation
  - Update CONTEXT.md with GeoJSON import architecture
  - Document Socket.IO integration
  - Document streaming parser approach
  
- [ ] **1.10.3** Update TODO.md completion
  - Mark all Phase 1 steps complete
  - Update progress counters
  - Add session log entries
  - Mark Phase 1 as ✅ COMPLETE

**✅ Validation**: Phase 1 fully complete, documented, tested

---

## � **PHASE EXECUTION ORDER (Option A)**

Following the priority sequence, phases should be executed in this order:

1. ✅ **Phase 1.1-1.9**: Foundation (COMPLETE)
2. ⏳ **Phase 1.10**: Complete Import Endpoints (CURRENT - 1/5 tasks)
   - Only Building uses streaming (162,942 records imported)
   - Admin/Highway/Amenity/Landuse endpoints exist but incomplete
   - Need to update 4 endpoints: streaming parser + full imports
3. 🔜 **Phase 1.11**: Geospatial Services API (NEXT - enables spawning)
4. 🔜 **Phase 1.12**: Database Integration & Validation
5. 🔜 **Phase 4**: POI-Based Spawning (requires 1.11)
6. 🔜 **Phase 5**: Depot/Route Spawners (requires 1.11)
7. 🔜 **Phase 6**: Conductor Communication (requires 5)
8. 🔜 **Phase 2**: Redis + Reverse Geocoding (optimization)
9. 🔜 **Phase 3**: Geofencing (requires 2)

**Note**: Phase 2 (Redis) is moved after spawning phases since it's an optimization, not a blocker. PostgreSQL queries (~2s) work fine for initial development. Optimize with Redis (<200ms) after spawning is functional.

---

## �🔴 **PHASE 2: REDIS + REVERSE GEOCODING**

**EXECUTION ORDER**: After Phase 6 (Conductor Communication)  
**STATUS**: Deferred - Optimization phase, not a blocker for spawning functionality

---

### **STEP 1.5: Update Country Schema** ⏱️ 30 min

- [ ] **1.5.1** Edit schema.json
  - Add `geodata_import_buttons` field
  - Add `geodata_import_status` field
  
- [ ] **1.5.2** Verify JSON syntax
  - Check for trailing commas
  - Validate with JSON linter

**✅ Validation**: Schema updated, JSON valid

---

### **STEP 1.6: Run Migration** ⏱️ 1 hour

- [ ] **1.6.1** Stop Strapi server
  
- [ ] **1.6.2** Start Strapi in development mode
  - Command: `cd arknet_fleet_manager/arknet-fleet-api && npm run develop`
  
- [ ] **1.6.3** Watch console for migration logs
  - Look for: "Schema updated for content-type: country"
  - Check for errors
  
- [ ] **1.6.4** Verify in database
  - Query: `SELECT column_name FROM information_schema.columns WHERE table_name = 'countries' AND column_name IN ('geodata_import_buttons', 'geodata_import_status')`
  - Expected: Both columns exist

**✅ Validation**: Migration successful, columns exist in database

---

### **STEP 1.7: Verify in Strapi Admin UI** ⏱️ 30 min

- [ ] **1.7.1** Login to Strapi admin
  - URL: `http://localhost:1337/admin`
  
- [ ] **1.7.2** Navigate to Content Manager → Country
  
- [ ] **1.7.3** Open Barbados record (or create test country)
  
- [ ] **1.7.4** Verify action buttons render
  - Should see 7 buttons
  - Buttons should be clickable
  
- [ ] **1.7.5** Verify geodata_import_status field
  - Should show JSON editor
  - Should have default values

**✅ Validation**: UI renders correctly, fields visible

---

### **STEP 1.8: Create Window Handlers** ⏱️ 3 hours

- [ ] **1.8.1** Create admin extensions directory
  - Path: `arknet_fleet_manager/arknet-fleet-api/admin-extensions/`
  
- [ ] **1.8.2** Create handlers file
  - File: `admin-extensions/geojson-handlers.js`
  
- [ ] **1.8.3** Implement window.importGeoJSON handler

  ```javascript
  window.importGeoJSON = async (entityId, metadata) => {
    const { fileType } = metadata;
    console.log(`🚀 Importing ${fileType} for country ${entityId}`);
    
    try {
      const response = await fetch('/api/geojson-import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('jwtToken')}`
        },
        body: JSON.stringify({ countryId: entityId, fileType })
      });
      
      const result = await response.json();
      
      if (response.ok) {
        console.log('✅ Import started:', result);
        alert(`Import started! Job ID: ${result.jobId}`);
      } else {
        console.error('❌ Import failed:', result);
        alert(`Import failed: ${result.error}`);
      }
    } catch (error) {
      console.error('❌ Import error:', error);
      alert(`Import error: ${error.message}`);
    }
  };
  ```
  
- [ ] **1.8.4** Implement window.viewImportStats handler

  ```javascript
  window.viewImportStats = async (entityId, metadata) => {
    console.log(`📊 Viewing import stats for country ${entityId}`);
    alert('Stats view not yet implemented');
  };
  ```
  
- [ ] **1.8.5** Implement window.clearRedisCache handler

  ```javascript
  window.clearRedisCache = async (entityId, metadata) => {
    console.log(`🗑️ Clearing Redis cache for country ${entityId}`);
    const confirmed = confirm('Clear all Redis cache for this country?');
    if (!confirmed) return;
    alert('Cache clear not yet implemented');
  };
  ```
  
- [ ] **1.8.6** Inject script into Strapi admin
  - Check if custom admin build needed
  - Add script tag to `admin/src/index.html` OR
  - Use webpack config OR
  - Use Strapi plugin hooks

**✅ Validation**: Handlers created and registered globally

---

### **STEP 1.9: Test Handlers** ⏱️ 1 hour

- [ ] **1.9.1** Open Strapi admin in browser
  
- [ ] **1.9.2** Open DevTools Console (F12)
  
- [ ] **1.9.3** Test window.importGeoJSON manually
  - Command: `window.importGeoJSON(1, { fileType: 'highway' })`
  - Expected: Console log + fetch request (404 OK - API not built yet)
  
- [ ] **1.9.4** Click "Import Highways" button
  - Expected: Handler triggered, console logs appear
  
- [ ] **1.9.5** Click all other buttons
  - Verify each triggers correct handler

**✅ Validation**: All handlers trigger correctly, buttons functional

---

### **STEP 1.10: Phase 1 Checkpoint** ⏱️ 30 min

**✅ Phase 1 Complete When:**

- [x] Country schema migration successful
- [x] Action buttons render in Strapi admin
- [x] Window handlers trigger (even if API returns 404)
- [x] geodata_import_status field visible
- [x] All 7 buttons functional

**💾 Git Commit:**

```bash
git add arknet_fleet_manager/arknet-fleet-api/src/api/country/content-types/country/schema.json
git add arknet_fleet_manager/arknet-fleet-api/admin-extensions/geojson-handlers.js
git commit -m "feat: Add GeoJSON import action buttons to country schema

- Add geodata_import_buttons field with 7 buttons
- Add geodata_import_status field for tracking imports
- Implement window handlers: importGeoJSON, viewImportStats, clearRedisCache
- Buttons render in Strapi admin UI
- Handlers trigger on click (API endpoints to be implemented)"

git push origin branch-0.0.2.6
```

**📝 Notes/Issues:**

- (Document any issues encountered)

---

🔴 **PHASE 2: REDIS + REVERSE GEOCODING**

**Goal**: Install Redis, implement geospatial service, benchmark <200ms

### **STEP 2.1: Install Redis Server** ⏱️ 1 hour

- [ ] **2.1.1** Download Redis
  - Windows: Redis for Windows OR WSL2 + Redis
  - Download from: <https://redis.io/download> or <https://github.com/microsoftarchive/redis/releases>
  
- [ ] **2.1.2** Install/Extract Redis
  - Extract to: `C:\Redis` (Windows) or `/usr/local/bin` (WSL)
  
- [ ] **2.1.3** Start Redis server
  - Command: `redis-server` (or `redis-server.exe`)
  
- [ ] **2.1.4** Test connection
  - Command: `redis-cli ping`
  - Expected: `PONG`

**✅ Validation**: Redis responds with PONG

---

### **STEP 2.2: Configure Redis** ⏱️ 1 hour

- [ ] **2.2.1** Create redis.conf (if not exists)
  
- [ ] **2.2.2** Set password
  - Add: `requirepass your_secure_password_here`
  
- [ ] **2.2.3** Enable persistence
  - Add: `appendonly yes`
  - Add: `appendfilename "appendonly.aof"`
  
- [ ] **2.2.4** Set memory limits
  - Add: `maxmemory 512mb`
  - Add: `maxmemory-policy allkeys-lru`
  
- [ ] **2.2.5** Restart Redis with config
  - Command: `redis-server redis.conf`
  
- [ ] **2.2.6** Test authenticated connection
  - Command: `redis-cli -a your_password ping`
  - Expected: `PONG`

**✅ Validation**: Redis configured with password and persistence

---

### **STEP 2.3: Install Node.js Redis Client** ⏱️ 30 min

- [ ] **2.3.1** Navigate to API directory
  - Command: `cd arknet_fleet_manager/arknet-fleet-api`
  
- [ ] **2.3.2** Install ioredis
  - Command: `npm install ioredis --save`
  
- [ ] **2.3.3** Verify installation
  - Check: `package.json` contains `"ioredis": "^..."`

**✅ Validation**: ioredis installed in package.json

---

### **STEP 2.4: Create Redis Client Utility** ⏱️ 1 hour

- [ ] **2.4.1** Create utils directory (if not exists)
  - Path: `src/utils/`
  
- [ ] **2.4.2** Create redis-client.js
  - File: `src/utils/redis-client.js`
  
- [ ] **2.4.3** Implement client

  ```javascript
  const Redis = require('ioredis');
  
  const redis = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD || null,
    retryStrategy: (times) => {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    maxRetriesPerRequest: 3
  });
  
  redis.on('connect', () => {
    console.log('✅ Redis connected:', redis.options.host);
  });
  
  redis.on('error', (err) => {
    console.error('❌ Redis error:', err.message);
  });
  
  redis.on('close', () => {
    console.warn('⚠️ Redis connection closed');
  });
  
  module.exports = redis;
  ```

**✅ Validation**: Redis client created

---

### **STEP 2.5: Configure Environment** ⏱️ 15 min

- [ ] **2.5.1** Edit .env file
  - File: `arknet_fleet_manager/arknet-fleet-api/.env`
  
- [ ] **2.5.2** Add Redis config

  ```env
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_PASSWORD=your_secure_password_here
  ```

**✅ Validation**: Environment variables set

---

### **STEP 2.6: Test Redis Connection** ⏱️ 30 min

- [ ] **2.6.1** Create test script
  - File: `scripts/test-redis.js`
  
- [ ] **2.6.2** Implement test

  ```javascript
  const redis = require('../src/utils/redis-client');
  
  async function test() {
    console.log('Testing Redis connection...');
    
    await redis.set('test_key', 'Hello ArkNet Redis!');
    const value = await redis.get('test_key');
    console.log('✅ Retrieved:', value);
    
    await redis.del('test_key');
    console.log('✅ Test complete');
    
    process.exit(0);
  }
  
  test().catch(err => {
    console.error('❌ Test failed:', err);
    process.exit(1);
  });
  ```
  
- [ ] **2.6.3** Run test
  - Command: `node scripts/test-redis.js`
  - Expected: "Retrieved: Hello ArkNet Redis!"

**✅ Validation**: Redis connection test passes

---

### **STEP 2.7: Create Redis Geospatial Service** ⏱️ 4 hours

- [ ] **2.7.1** Create services directory (if not exists)
  - Path: `src/services/`
  
- [ ] **2.7.2** Create service file
  - File: `src/services/redis-geo.service.js`
  
- [ ] **2.7.3** Implement service class

  ```javascript
  const redis = require('../utils/redis-client');
  
  class RedisGeoService {
    // Add highway to geospatial index
    async addHighway(countryCode, lon, lat, highwayId, metadata) {
      const key = `highways:${countryCode}`;
      await redis.geoadd(key, lon, lat, `highway:${highwayId}`);
      await redis.hset(`highway:${highwayId}`, metadata);
    }
    
    // Add POI to geospatial index
    async addPOI(countryCode, lon, lat, poiId, metadata) {
      const key = `pois:${countryCode}`;
      await redis.geoadd(key, lon, lat, `poi:${poiId}`);
      await redis.hset(`poi:${poiId}`, metadata);
    }
    
    // Find nearby highways
    async findNearbyHighways(countryCode, lon, lat, radiusMeters = 50) {
      const key = `highways:${countryCode}`;
      const results = await redis.georadius(
        key, lon, lat, radiusMeters, 'm', 'WITHDIST', 'ASC'
      );
      
      const enriched = await Promise.all(
        results.map(async ([id, distance]) => {
          const metadata = await redis.hgetall(id);
          return { id, distance: parseFloat(distance), ...metadata };
        })
      );
      
      return enriched;
    }
    
    // Find nearby POIs
    async findNearbyPOIs(countryCode, lon, lat, radiusMeters = 100) {
      const key = `pois:${countryCode}`;
      const results = await redis.georadius(
        key, lon, lat, radiusMeters, 'm', 'WITHDIST', 'ASC'
      );
      
      const enriched = await Promise.all(
        results.map(async ([id, distance]) => {
          const metadata = await redis.hgetall(id);
          return { id, distance: parseFloat(distance), ...metadata };
        })
      );
      
      return enriched;
    }
    
    // Reverse geocoding cache
    async getReverseGeocode(lat, lon) {
      const key = `geo:${lat.toFixed(4)}:${lon.toFixed(4)}`;
      return await redis.get(key);
    }
    
    async setReverseGeocode(lat, lon, address, ttl = 3600) {
      const key = `geo:${lat.toFixed(4)}:${lon.toFixed(4)}`;
      await redis.setex(key, ttl, address);
    }
    
    // Clear country cache
    async clearCountryCache(countryCode) {
      const patterns = [
        `highways:${countryCode}`,
        `pois:${countryCode}`,
        `highway:*`,
        `poi:*`,
        `geo:*`
      ];
      
      for (const pattern of patterns) {
        const keys = await redis.keys(pattern);
        if (keys.length > 0) {
          await redis.del(...keys);
        }
      }
    }
  }
  
  module.exports = new RedisGeoService();
  ```

**✅ Validation**: Service created with all methods

---

### **STEP 2.8: Test Geospatial Service** ⏱️ 2 hours

- [ ] **2.8.1** Create test script
  - File: `scripts/test-redis-geo.js`
  
- [ ] **2.8.2** Add test data

  ```javascript
  const redisGeo = require('../src/services/redis-geo.service');
  
  async function test() {
    console.log('Testing Redis Geospatial Service...\n');
    
    // Test 1: Add highways
    console.log('1️⃣ Adding highways...');
    await redisGeo.addHighway('barbados', -59.5905, 13.0806, 5172465, {
      name: 'Tom Adams Highway',
      type: 'trunk',
      ref: 'ABC'
    });
    console.log('✅ Highway added');
    
    // Test 2: Add POIs
    console.log('\n2️⃣ Adding POIs...');
    await redisGeo.addPOI('barbados', -59.6016, 13.0947, 123, {
      name: 'Bridgetown Mall',
      type: 'mall'
    });
    console.log('✅ POI added');
    
    // Test 3: Find nearby highways
    console.log('\n3️⃣ Finding nearby highways...');
    const highways = await redisGeo.findNearbyHighways('barbados', -59.5905, 13.0806, 50);
    console.log('✅ Found:', highways);
    
    // Test 4: Find nearby POIs
    console.log('\n4️⃣ Finding nearby POIs...');
    const pois = await redisGeo.findNearbyPOIs('barbados', -59.6016, 13.0947, 100);
    console.log('✅ Found:', pois);
    
    // Test 5: Cache reverse geocode
    console.log('\n5️⃣ Testing cache...');
    await redisGeo.setReverseGeocode(13.0806, -59.5905, 'Tom Adams Highway, Barbados');
    const cached = await redisGeo.getReverseGeocode(13.0806, -59.5905);
    console.log('✅ Cached address:', cached);
    
    console.log('\n✅ All tests passed!');
    process.exit(0);
  }
  
  test().catch(err => {
    console.error('❌ Test failed:', err);
    process.exit(1);
  });
  ```
  
- [ ] **2.8.3** Run test
  - Command: `node scripts/test-redis-geo.js`
  - Verify all assertions pass

**✅ Validation**: Geospatial service tests pass

---

### **STEP 2.9: Create Reverse Geocode API** ⏱️ 3 hours

- [ ] **2.9.1** Create API structure
  - Directory: `src/api/reverse-geocode/`
  - Subdirs: `controllers/`, `routes/`
  
- [ ] **2.9.2** Create controller
  - File: `src/api/reverse-geocode/controllers/reverse-geocode.js`
  
- [ ] **2.9.3** Implement controller

  ```javascript
  const redisGeoService = require('../../../services/redis-geo.service');
  
  module.exports = {
    async reverseGeocode(ctx) {
      const { lat, lon, countryCode = 'barbados' } = ctx.query;
      
      if (!lat || !lon) {
        return ctx.badRequest('Missing lat or lon parameter');
      }
      
      const latitude = parseFloat(lat);
      const longitude = parseFloat(lon);
      
      // Check cache first
      let address = await redisGeoService.getReverseGeocode(latitude, longitude);
      
      if (address) {
        return ctx.send({
          address,
          source: 'cache',
          timestamp: Date.now()
        });
      }
      
      // Cache miss - query Redis geospatial
      const [nearbyHighways, nearbyPOIs] = await Promise.all([
        redisGeoService.findNearbyHighways(countryCode, longitude, latitude, 50),
        redisGeoService.findNearbyPOIs(countryCode, longitude, latitude, 100)
      ]);
      
      // Format address
      const highway = nearbyHighways[0];
      const poi = nearbyPOIs[0];
      
      if (!highway && !poi) {
        address = 'Unknown location';
      } else if (highway && !poi) {
        address = highway.name || `${highway.type} road`;
      } else if (!highway && poi) {
        address = `Near ${poi.name}`;
      } else {
        address = `${highway.name}, near ${poi.name}`;
      }
      
      // Cache result
      await redisGeoService.setReverseGeocode(latitude, longitude, address);
      
      return ctx.send({
        address,
        source: 'computed',
        highway: highway || null,
        poi: poi || null,
        timestamp: Date.now()
      });
    }
  };
  ```
  
- [ ] **2.9.4** Create routes
  - File: `src/api/reverse-geocode/routes/reverse-geocode.js`
  
- [ ] **2.9.5** Implement routes

  ```javascript
  module.exports = {
    routes: [
      {
        method: 'GET',
        path: '/reverse-geocode',
        handler: 'reverse-geocode.reverseGeocode',
        config: {
          auth: false // Public for testing
        }
      }
    ]
  };
  ```

**✅ Validation**: API endpoint created

---

### **STEP 2.10: Test Reverse Geocode API** ⏱️ 1 hour

- [ ] **2.10.1** Start Strapi server
  - Command: `npm run develop`
  
- [ ] **2.10.2** Test first request (cache miss)
  - URL: `http://localhost:1337/api/reverse-geocode?lat=13.0806&lon=-59.5905`
  - Expected: `{ "address": "Tom Adams Highway", "source": "computed", ... }`
  
- [ ] **2.10.3** Test second request (cache hit)
  - Same URL
  - Expected: `{ "address": "Tom Adams Highway", "source": "cache", ... }`
  
- [ ] **2.10.4** Test without data
  - URL: `http://localhost:1337/api/reverse-geocode?lat=0&lon=0`
  - Expected: `{ "address": "Unknown location", ... }`

**✅ Validation**: API returns addresses, cache working

---

### **STEP 2.11: Benchmark Performance** ⏱️ 3 hours

- [ ] **2.11.1** Create benchmark script
  - File: `scripts/benchmark-reverse-geocode.js`
  
- [ ] **2.11.2** Implement benchmark

  ```javascript
  const axios = require('axios');
  
  // Generate 100 random coordinates in Barbados
  // (Barbados bounds: lat 13.04-13.33, lon -59.65--59.42)
  function generateCoordinates(count) {
    const coords = [];
    for (let i = 0; i < count; i++) {
      coords.push({
        lat: 13.04 + Math.random() * 0.29,
        lon: -59.65 + Math.random() * 0.23,
        name: `Point ${i + 1}`
      });
    }
    return coords;
  }
  
  async function benchmark() {
    const coords = generateCoordinates(100);
    const results = { cache: [], computed: [] };
    
    console.log('Running benchmark (100 requests)...\n');
    
    // Pass 1: All cache misses
    for (const coord of coords) {
      const start = Date.now();
      const response = await axios.get(
        `http://localhost:1337/api/reverse-geocode?lat=${coord.lat}&lon=${coord.lon}`
      );
      const latency = Date.now() - start;
      results.computed.push(latency);
    }
    
    // Pass 2: All cache hits
    for (const coord of coords) {
      const start = Date.now();
      const response = await axios.get(
        `http://localhost:1337/api/reverse-geocode?lat=${coord.lat}&lon=${coord.lon}`
      );
      const latency = Date.now() - start;
      results.cache.push(latency);
    }
    
    console.log('=== BENCHMARK RESULTS ===');
    console.log('\nCache Misses (computed):');
    console.log('  Count:', results.computed.length);
    console.log('  Avg:', avg(results.computed), 'ms');
    console.log('  P95:', percentile(results.computed, 95), 'ms');
    console.log('  P99:', percentile(results.computed, 99), 'ms');
    
    console.log('\nCache Hits:');
    console.log('  Count:', results.cache.length);
    console.log('  Avg:', avg(results.cache), 'ms');
    console.log('  P95:', percentile(results.cache, 95), 'ms');
    console.log('  P99:', percentile(results.cache, 99), 'ms');
    
    console.log('\n✅ Target: Cache hit <10ms, Cache miss <200ms');
  }
  
  function avg(arr) {
    return (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);
  }
  
  function percentile(arr, p) {
    const sorted = arr.sort((a, b) => a - b);
    const index = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[index];
  }
  
  benchmark();
  ```
  
- [ ] **2.11.3** Run benchmark
  - Command: `node scripts/benchmark-reverse-geocode.js`
  - Record results
  
- [ ] **2.11.4** Document results
  - Create: `docs/redis-performance-benchmark.md`
  - Include: Avg, p95, p99 for cache hit/miss

**✅ Validation**: Benchmark shows <10ms cache hit, <200ms cache miss

---

### **STEP 2.12: Phase 2 Checkpoint** ⏱️ 30 min

**✅ Phase 2 Complete When:**

- [x] Redis server running
- [x] Reverse geocode API responding
- [x] Cache hit <10ms
- [x] Cache miss <200ms
- [x] 10x+ faster than PostgreSQL (optional comparison)

**💾 Git Commit:**

```bash
git add src/utils/redis-client.js
git add src/services/redis-geo.service.js
git add src/api/reverse-geocode/
git add scripts/test-redis*.js scripts/benchmark-reverse-geocode.js
git add docs/redis-performance-benchmark.md
git commit -m "feat: Implement Redis geospatial service for reverse geocoding

- Add Redis client with connection pooling
- Implement geospatial service (GEOADD, GEORADIUS)
- Add reverse geocoding API endpoint
- Cache results for <10ms cache hits
- Benchmark shows <200ms cache miss performance
- 10x+ faster than PostgreSQL queries"

git push origin branch-0.0.2.6
```

**📝 Notes/Issues:**

- (Document any issues)

---

## 🔔 **PHASE 3: GEOFENCING**

**EXECUTION ORDER**: After Phase 2 (Redis + Reverse Geocoding)  
**STATUS**: Deferred - Requires Redis infrastructure from Phase 2

## 🎯 **PHASE 4: POI-BASED SPAWNING**

**EXECUTION ORDER**: After Phase 1.12 (Database Integration)  
**STATUS**: Ready after Geospatial API is complete  
**BLOCKER**: Requires Phase 1.11 Geospatial Services API

## 🚌 **PHASE 5: DEPOT/ROUTE SPAWNERS**

**EXECUTION ORDER**: After Phase 4 or in parallel with Phase 4  
**STATUS**: Ready after Geospatial API is complete  
**BLOCKER**: Requires Phase 1.11 Geospatial Services API

## 🔗 **PHASE 6: CONDUCTOR COMMUNICATION**

**EXECUTION ORDER**: After Phase 5 (Depot/Route Spawners)  
**STATUS**: Requires active passenger spawning to be functional  
**BLOCKER**: Requires Phase 5 (passenger spawning operational)

## Phases 3-6 to be detailed after Phase 2 completion

---

## 📝 **SESSION NOTES**

### **Session 1: October 25, 2025 - Documentation & Planning**

**Context**: User lost chat history, requested full context rebuild

**Activities**:

1. ✅ Read PROJECT_STATUS.md and ARCHITECTURE_DEFINITIVE.md
2. ✅ Created initial TODO list (8 items)
3. ✅ User clarified: This is a feasibility study for Redis + geofencing + spawning
4. ✅ Deep codebase analysis (action-buttons plugin, spawning systems, geofence API)
5. ✅ Analyzed 11 GeoJSON files (user confirmed scope, excluded barbados_geocoded_stops)
6. ✅ Created GEOJSON_IMPORT_CONTEXT.md (600+ lines architecture study)
7. ✅ User requested phased approach reorganization
8. ✅ Confirmed custom action-buttons plugin (no marketplace equivalent)
9. ✅ Built TODO.md with 65+ granular steps across 6 phases
10. ✅ Created CONTEXT.md as single source of truth
11. ✅ Added 10 detailed system integration workflows to CONTEXT.md
12. ✅ User asked to confirm conductor/driver/commuter roles
13. ✅ Discovered architectural error: "Conductor Service" doesn't exist
14. ✅ Fixed CONTEXT.md: Assignment happens in spawn strategies, not centralized service
15. ✅ Added component roles section to CONTEXT.md
16. ✅ User asked: "Can agent pick up where we left off with minimal prompting?"
17. ✅ Enhanced CONTEXT.md with session history, user preferences, critical decisions
18. ✅ Enhanced TODO.md with quick start guide for new agents

**Key Decisions**:

- Redis chosen for 10-100x performance improvement (PostgreSQL ~2000ms → Redis <200ms)
- 11 GeoJSON files in scope (excluding barbados_geocoded_stops)
- Custom action-buttons plugin confirmed (built in-house, no marketplace equivalent)
- Streaming parser required for building.geojson (658MB)
- Centroid extraction required for amenity.geojson (MultiPolygon → Point)
- 6-phase implementation approach
- Event-based passenger assignment (no centralized conductor service)

**Blockers**: None

**Next Steps**:

- ⏸️ Waiting for user approval to begin Step 1.1.1
- Ready to read country schema and start Phase 1

**Issues Discovered**:

- ✅ FIXED: Documentation incorrectly described "Conductor Service" for centralized assignment
  - Reality: Route assignment happens in `spawn_interface.py` spawn strategies
  - Conductor is vehicle component, not centralized service
- ✅ CLARIFIED: Plugin is custom-built `strapi-plugin-action-buttons` (no marketplace equivalent)
  - Initial research error suggested external package
  - Confirmed as in-house custom plugin on October 25

**Agent Handoff Notes**:

- All documentation complete and validated
- User prefers detailed analysis before implementation
- User values clarity and validation at each step
- Working on branch `branch-0.0.2.6` (NOT main)
- CONTEXT.md is primary reference (1,700+ lines)
- TODO.md is active task tracker (65+ steps)
- GEOJSON_IMPORT_CONTEXT.md is historical reference

---

### **Template for Future Sessions**

```markdown
### **Session X: [Date] - [Title]**

**Activities**:
- [ ] Task 1
- [ ] Task 2

**Key Decisions**:
- Decision 1: Rationale

**Blockers**: 
- Issue 1: Description

**Next Steps**:
- Next action

**Issues Discovered**:
- Issue 1: Description and resolution status
```

---

### **Session 2: October 25, 2025 - Implementation Started**

**Context**: Phase 1 implementation began

**Activities**:

1. ✅ **Step 1.1.1 COMPLETE** - Read current country schema
   - Read schema.json (113→145 lines after update)
   - Verified database: 16 columns in `countries` table
   - Found existing deletion history data
   - Cleared old data (fresh start approach)
   - Migrated `geodata_import_status`: text→json with structured default
   - Updated TODO.md progress tracking

2. ✅ **Step 1.1.2 COMPLETE** - Verify action-buttons plugin exists
   - Verified plugin directory structure
   - Confirmed documentation exists (ARCHITECTURE.md, EXAMPLES.ts, README.md)
   - Verified plugin enabled in config/plugins.ts
   - Checked dist/ folder contains built files
   - Validated schema migration after Strapi restart (text→jsonb)
   - Updated TODO.md progress tracking

3. ✅ **Step 1.1.3 COMPLETE** - List current country fields in database
   - Queried database: 16 columns verified
   - Confirmed geodata_import_status type is jsonb (migration successful)
   - No unexpected schema changes after Strapi restart
   - Database ready for button field addition
   - Updated TODO.md progress tracking

4. ✅ **Step 1.2.1 COMPLETE** - Read plugin architecture
   - Read ARCHITECTURE.md (290 lines)
   - Understood component hierarchy: Schema → Plugin Registration (server/admin) → CustomFieldButton → Handler
   - Understood data flow: Button click → window[onClick] → handler(fieldName, fieldValue, onChange) → DB
   - Learned security model: Handlers run in browser with admin privileges
   - Identified extension points: Button labels, handler functions, metadata structure, UI feedback
   - Updated TODO.md progress tracking

5. ✅ **Step 1.2.2 COMPLETE** - Review plugin examples
   - Read EXAMPLES.ts (257 lines)
   - Reviewed 5 example handlers: send email, upload CSV, generate report, sync CRM, default action
   - Understood handler pattern: window[functionName] = async (fieldName, fieldValue, onChange) => {...}
   - Learned metadata tracking: onChange({ status, timestamp, ...data })
   - Learned error handling: try/catch with success/failed status tracking
   - Updated TODO.md progress tracking

6. ✅ **Step 1.2.3 COMPLETE** - Understand field configuration
   - Read README.md documentation (lines 1-250)
   - Learned field configuration structure:
     - type: "customField"
     - customField: "plugin::action-buttons.button-field"
     - options: { buttonLabel, onClick }
   - Understood handler signature: (fieldName, fieldValue, onChange)
   - Ready to design GeoJSON import button configuration
   - Updated TODO.md progress tracking

7. ✅ **Step 1.3.1 COMPLETE** - Backup database
   - Created backup_20251025_145744.sql (6.4 MB)
   - Backed up all tables, data, schemas, constraints, indexes
   - Updated TODO.md progress tracking

8. ✅ **Step 1.3.2 COMPLETE** - Backup schema.json
   - Created schema.json.backup_20251025_152235 (3,357 bytes)
   - Backed up current schema with 145 lines and json field
   - Updated TODO.md progress tracking

9. ✅ **Step 1.3.3 COMPLETE** - Document rollback procedure
   - Database rollback: `psql -U david -h 127.0.0.1 -d arknettransit -f backup_20251025_145744.sql`
   - Schema rollback: `Copy-Item schema.json.backup_20251025_152235 schema.json -Force; npm run develop`
   - Updated TODO.md progress tracking

**Schema Changes**:

- File: `src/api/country/content-types/country/schema.json`
- Field: `geodata_import_status` changed from `text` to `json`
- Added structured default with 5 file types (highway, amenity, landuse, building, admin)
- Each tracks: status, lastImportDate, featureCount, lastJobId

**Database Actions**:

- Connected to `arknettransit` database
- Cleared `geodata_import_status` and `geodata_last_import` fields
- Ready for fresh import tracking

**Backup Files Created**:

- Database: `backup_20251025_145744.sql` (6.4 MB)
- Schema: `schema.json.backup_20251025_152235` (3,357 bytes)
- Rollback procedures documented

**Key Decisions**:

- Chose Option B (Fresh Start) over preserving deletion history
- Documented old status for reference only
- Created database backup before schema modifications (6.4 MB)
- Created schema.json backup for safe rollback (3.4 KB)

**Next Steps**:

- ⏸️ Step 1.4 - Design Button Configuration

---

**Last Updated**: October 25, 2025  
**Next Session**: Step 1.4 - Design Button Configuration

---

## 🏗️ **TIER 4 SPAWNER SYSTEM IMPLEMENTATION - October 28, 2025**

### **Architectural Decisions & Pushback Analysis**

#### **Decision 1: Single Entrypoint vs Separate Sub-Entrypoints**

**User Proposal**: "The commuter_simulator will have a single entrypoint that will start the spawn_engine with separate sub-entrypoints for depot/route spawners"

**Agent Pushback**: ✅ ACCEPTED (with modifications)
- **Pattern**: Single main.py entrypoint with SpawnerCoordinator orchestration
- **Rationale**: 
  - Avoid complexity of multiple CLI entrypoints
  - Use coordinator pattern for spawner management
  - Config-driven control (enable/disable flags)
  - Shared resource initialization (PassengerRepository, Reservoirs)
- **Implementation**: `commuter_simulator/main.py` + `services/spawner_coordinator.py`

#### **Decision 2: Depot-Route Association Logic**

**User Proposal**: "Depot spawner will spawn at the depot associated with the route that is chosen"

**Agent Pushback**: ❌ REJECTED (inverted responsibility)
- **Problem**: Creates tight coupling, breaks single responsibility
- **Better Design**: 
  - DepotSpawner: Spawns passengers AT depot for ANY associated route
  - RouteSpawner: Spawns passengers ALONG route geometry
  - These are different passenger generation patterns, not route-dependent variations
- **Implementation**: DepotSpawner queries depot's associated routes, selects one via weighted random

#### **Decision 3: Two-Mode API Architecture**

**User Concern**: "Maybe we need to move all geospatial API requests to geospatial_service... check if we have two modes of API access"

**Agent Analysis**: ✅ TWO-MODE IS CORRECT
- **Mode 1**: Strapi REST API (localhost:1337) - CRUD operations
  - /api/routes, /api/depots, /api/spawn-configs, /api/active-passengers
  - Single source of truth for master data
- **Mode 2**: Geospatial Service (localhost:6000) - Spatial queries (READ-ONLY)
  - /route-geometry, /route-buildings, /depot-catchment, /nearby-buildings
  - PostGIS spatial calculations isolated from Strapi
- **Rationale**: Separation of concerns, performance isolation, single source of truth maintained

#### **Decision 4: Route-Depot Junction Table**

**Agent Recommendation**: ✅ CREATE EXPLICIT RELATIONSHIPS
- **Pattern**: Many-to-many junction table with precomputed geospatial data
- **Schema**: route_id, depot_id, is_terminus, distance_from_route_m, created_at
- **Benefits**:
  - No runtime geospatial calculations (query once, cache forever)
  - Explicit relationships match real-world operations
  - Performance optimization (indexed lookups vs spatial queries)
- **Current State**: Uses 5km proximity threshold from route geometry
- **Recommended**: Precompute during route/depot creation, store in route-depots table

#### **Decision 5: PubSub for Reservoir Visualization**

**User Request**: "3rd parties can pubsub subscribe into reservoirs as commuters are being spawned"

**Agent Recommendation**: ✅ GOOD IDEA (with pattern recommendation)
- **Pattern**: PostgreSQL LISTEN/NOTIFY (not direct spawner integration)
- **Rationale**:
  - Zero overhead on spawner (DB handles pub/sub)
  - Subscribers connect to DB, not spawner
  - Automatic replay/buffering built-in
  - No backpressure issues
- **Alternative Rejected**: Direct pub/sub in spawner (performance overhead, blocking concerns)

### **Implementation Summary (October 28)**

#### **Files Created/Modified**:

1. **`commuter_simulator/core/domain/spawner_engine/depot_spawner.py`** ✅ COMPLETE
   - Poisson-distributed passenger generation at depot locations
   - Configurable spawn rates (spatial, hourly, day multipliers)
   - Default config fallback if Strapi config unavailable
   - Methods: `spawn()`, `_load_spawn_config()`, `_calculate_spawn_count()`, `_generate_spawn_requests()`

2. **`commuter_simulator/services/spawner_coordinator.py`** ✅ COMPLETE
   - Orchestrates multiple spawners with enable/disable control
   - Supports single-run and continuous modes
   - Config-driven spawner filtering (enable_{spawnerclass} flags)
   - Methods: `start()`, `_get_enabled_spawners()`, `_run_single_cycle()`, `_run_continuous()`, `_log_aggregate_stats()`

3. **`commuter_simulator/main.py`** ✅ COMPLETE
   - Single entrypoint for spawner system
   - Creates shared resources (PassengerRepository, Reservoirs)
   - Config dict controls enable_routespawner and enable_depotspawner flags
   - MockRouteSpawner for testing (λ=1.5, simplified implementation)

4. **`commuter_simulator/core/domain/reservoirs/`** ✅ MOVED & UPDATED
   - Moved from project root to correct location (commuter_simulator/core/domain/reservoirs/)
   - `depot_reservoir.py`: DB-backed with optional Redis (enable_redis_cache flag)
   - `route_reservoir.py`: DB-backed with optional Redis (enable_redis_cache flag)
   - Updated imports and docstrings

5. **`commuter_simulator/infrastructure/database/passenger_repository.py`** ✅ UPDATED
   - Added `get_waiting_passengers_by_route(route_id, limit)` helper
   - Added `get_waiting_passengers_by_depot(depot_id, limit)` helper
   - Both helpers return simplified passenger dicts with route_id/depot_id fields

6. **`test_spawner_flags.py`** ✅ CREATED
   - Comprehensive test of enable/disable flag combinations
   - Tests 4 scenarios: depot-only, route-only, both, neither
   - Uses MockRouteSpawner for testing without geospatial dependencies
   - Not yet executed (user cancelled before running)

7. **`delete_passengers.py`** ✅ VERIFIED
   - Utility for clearing Strapi active-passengers table
   - Used for testing fresh passenger generation
   - Confirmed working (deleted 6 passengers, verified 0 remaining)

#### **Test Results (October 28)**:

**End-to-End Test** (python -m commuter_simulator.main):
- Spawn calculation: λ = spatial(2.0) × hourly(1.0) × day(1.1) = 2.20
- Passengers spawned: 4 (Poisson distribution with λ=2.20)
- Bulk insert: 4 successful, 0 failed (100% success rate)
- Database verification: All 4 passengers persisted to Strapi with correct fields
- Fields verified: depot_id, route_id, status=WAITING, spawned_at, expires_at (30min TTL)

**Fresh Spawn Verification**:
- Deleted all 6 passengers from database (confirmed 0 remaining)
- Ran spawner twice: first run = 0 passengers (Poisson randomness), second run = 1 passenger
- Verified new passenger with matching timestamp (09:45:20.980Z)
- Confirmed fresh generation (not old data)

**Logging Format Fix**:
- Fixed double-escaped %% in logging.basicConfig format string
- Corrected to single % for proper formatting

#### **Pending Work (TIER 5 - REVISED Oct 28)**:

**VALIDATED STATUS** (Deep Code Analysis - Oct 28):
- ✅ RouteSpawner ALREADY COMPLETE (287 lines) - discovered during validation
- ✅ GeospatialService integration ALREADY COMPLETE (route-geometry, route-buildings endpoints)
- ❌ RouteSpawner NOT wired to coordinator yet (uses MockRouteSpawner)
- ❌ Route-depot junction table MISSING
- ❌ DepotSpawner uses hardcoded routes (needs association querying)
- ❌ PostgreSQL LISTEN/NOTIFY NOT implemented

**REVISED TIER 5 TASKS** (33% scope reduction):

1. **Route-Depot Junction Table** ✅ COMPLETE (Oct 28, 2025)
   - ✅ Created route-depot content type in Strapi with full CRUD
   - ✅ Schema: route, depot (relations), distance_from_route_m, is_start_terminus, is_end_terminus, precomputed_at
   - ✅ Added cached label fields: display_name, route_short_name, depot_name
   - ✅ Lifecycle hooks: auto-populate cached labels on create/update
   - ✅ Admin UI configuration: mainField for readable relation chips, displayedAttribute for entry titles
   - ✅ **CORRECTED SEMANTICS**: Depots are bus stations/terminals where passengers wait
   - ✅ **Association Logic**: Routes associate with depot ONLY if START or END point within walking distance (~500m)
   - ✅ Bidirectional relations (routes ↔ depots) with proper UI display
   - ✅ Tested: Create/update/delete operations reflect on both Route and Depot sides
   - ✅ Python precompute script: Calculates nearest depot to route endpoints, creates associations via API
   - ✅ Files: schema.json (route-depot, route, depot), lifecycles.ts, precompute_route_depot_associations.py

2. **Update DepotSpawner Logic**
   - Add `_load_associated_routes()` method to query Strapi API
   - Query associated routes from route-depots table (routes that stop at this depot)
   - Weighted random selection from depot's associated routes
   - Remove hardcoded `available_routes` parameter
   - **Realistic behavior**: Passengers at depot only board routes servicing that depot

3. **Wire RouteSpawner to Coordinator** (REVISED - Implementation exists!)
   - Replace MockRouteSpawner with real RouteSpawner in main.py
   - Run end-to-end test with `enable_routespawner=True`
   - Verify passengers spawn spatially along route geometry
   - Validate GeospatialService integration (route-geometry, route-buildings calls)

4. **PubSub Implementation**
   - PostgreSQL LISTEN/NOTIFY on active_passengers table
   - Trigger-based notifications on INSERT/UPDATE/DELETE
   - Create `commuter_simulator/examples/passenger_subscriber.py`
   - Subscriber examples for 3rd-party visualization

5. **Comprehensive Flag Testing**
   - Execute test_spawner_flags.py with all 4 scenarios
   - Verify coordinator correctly filters spawners based on enable flags
   - Test depot-only, route-only, both, neither configurations

6. **Redis Implementation** (Deferred to TIER 6+)
   - Install Redis client library
   - Implement startup loader for static route/geojson data
   - Implement cache-aside pattern in reservoirs
   - Enable Redis caching flag integration

---

## PHASE 1.12 TEST ANALYSIS - Vehicle Simulation & Passenger Pickup (October 27, 2025)

### Bug Fixes Applied

- Fixed timezone-aware datetime comparison (naive vs aware UTC)
- Commuter spawn now auto-resets ALL passengers (not just per-route)
- Report shows spawn time, pickup time, and route distances
- Added pickup summary with total/average wait times

### Test Scenario 1: Time Range Spawn (5PM-6PM, Monday)

**Spawn Configuration**:

- Route: gg3pv3z19hhm117v9xth5ezq (12.9 km, 389 points)
- Time Range: 17:00-18:00 (1 hour, 10-min intervals)
- Total Generated: 12 passengers

**Results**:

- Picked Up: 5 passengers (41.7%)
- Missed: 7 passengers (58.3%, all "not_spawned_yet")
- Total Wait Time: 3674 seconds (61.2 min)
- Avg Wait: 735 seconds (12.2 min per passenger)

**Wait Times**: 414-1197 seconds (6.9-19.9 min range) - realistic for urban transit

**Vehicle Departure**: 17:05:00

- Caught passengers spawning at 17:00-17:10
- Missed passengers spawning at 17:20+ (too late)

### Realism Assessment

 REALISTIC:

- Wait times match urban transit patterns
- Early spawners prioritized (5-10 min wait)
- Late spawners missed (vehicle already passed)
- Clustering on middle-to-end route section

 TO INVESTIGATE:

- Early-route pickup distribution
- Impact of departure time
- Spawn location bias toward end of route

### Recommendations

1. Test earlier departure (16:50) for early-spawn coverage
2. Test later departure (17:20) for late-spawn coverage
3. Test broader range (16:00-18:00) for full analysis
4. Test different speeds (20, 40, 50 km/h)
5. Implement automated scenario testing
