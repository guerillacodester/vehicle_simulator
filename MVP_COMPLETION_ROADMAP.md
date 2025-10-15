# MVP COMPLETION ROADMAP

**Date**: October 14, 2025  
**Branch**: branch-0.0.2.3  
**Status**: Pre-Implementation Planning Complete

---

## CURRENT STATE ANALYSIS

### ✅ What's Working

- **Conductor-Driver Communication**: Socket.IO infrastructure exists
- **Engine Control**: Driver can start/stop engine on command
- **Capacity Tracking**: Conductor tracks passengers_on_board and seats_available
- **Full Detection**: `is_full()` method works correctly
- **Database Schema**: Vehicle table has capacity field (default: 11)
- **Passenger Database**: PassengerDatabase class exists with insert/mark_boarded methods
- **Socket.IO Events**: `conductor:ready:depart` event handler exists in VehicleDriver

### ❌ Critical Missing Pieces

1. **No Database Integration**: Conductor uses hardcoded capacity (40) instead of DB value
2. **No Passenger Queries**: Conductor never queries PassengerDatabase for eligible passengers
3. **No Callback Connection**: `on_full_callback` is always None, never wired up
4. **No Pickup Trigger**: Nothing calls conductor to check for passengers at stops
5. **40+ Hardcoded Values**: Operational parameters scattered across codebase

### ⚠️ Capacity Conflicts Found

- **Database schema default**: 11
- **constants.py**: 30 (`DEFAULT_VEHICLE_CAPACITY`)
- **conductor.py**: 40 (multiple locations)
- **vehicles.json**: 40 (per vehicle config)

**Decision**: Vehicle capacity MUST come from database, no hardcoded fallbacks

---

## HARDCODED VALUES INVENTORY

### 🚨 MUST BE DATABASE-DRIVEN

**Location**: `arknet_transit_simulator/vehicle/conductor.py`

- Line 115: `capacity: int = 40`
- Line 216: `capacity = 40`
- Line 218: `config_data['vehicle_defaults'].get('passengers', 40)`

**Location**: `commuter_service/constants.py`

- Line 41: `DEFAULT_VEHICLE_CAPACITY = 30`

**Location**: `arknet_transit_simulator/simulator.py`

- Line 381: `target_speed_mps = 25.0/3.6` (fallback max speed)

### ⚙️ SHOULD BE CONFIGURATION FILES

**ConductorConfig** (`conductor.py` lines 78-93):

- `pickup_radius_km: float = 0.2`
- `boarding_time_window_minutes: float = 5.0`
- `min_stop_duration_seconds: float = 15.0`
- `max_stop_duration_seconds: float = 180.0`
- `per_passenger_boarding_time: float = 8.0`
- `per_passenger_disembarking_time: float = 5.0`
- `monitoring_interval_seconds: float = 2.0`
- `gps_precision_meters: float = 10.0`
- `driver_response_timeout_seconds: float = 30.0`
- `passenger_boarding_timeout_seconds: float = 120.0`

**Distance Thresholds** (`constants.py`):

- Line 20: `DEFAULT_SEARCH_RADIUS_METERS = 100`
- Line 21: `MAX_BOARDING_DISTANCE_METERS = 50`
- Line 22: `DEPOT_PROXIMITY_THRESHOLD_METERS = 200`
- Line 23: `ROUTE_PROXIMITY_THRESHOLD_METERS = 100`
- Line 24: `MAX_WALKING_DISTANCE_METERS = 1000`
- Line 27: `DEFAULT_SEARCH_RADIUS_KM = 1.0`
- Line 28: `NEARBY_CELL_SEARCH_RADIUS_KM = 2.0`

**Time Intervals** (`constants.py`):

- Line 31: `DEFAULT_WAIT_TIME_MINUTES = 30`
- Line 32: `MIN_SPAWN_INTERVAL_MINUTES = 1`
- Line 33: `MAX_JOURNEY_TIME_MINUTES = 120`
- Line 36: `EXPIRATION_CHECK_INTERVAL_SECONDS = 10`
- Line 37: `SPAWN_CHECK_INTERVAL_SECONDS = 60`
- Line 38: `POSITION_UPDATE_INTERVAL_SECONDS = 5`

**Poisson Spawner** (`poisson_geojson_spawner.py`):

- Lines 434-436: `peak_multiplier = 2.5` or `1.0`
- Line 442: `activity_multiplier = 1.0`
- Lines 776-777: `mu: float = 1.5, sigma: float = 0.7`
- Line 835: `max_distance_km: float = 2.0`
- Priority base values: 0.5, 0.7, 0.8, 0.9
- Rush hour bonus: 0.2

**System Settings** (`constants.py`):

- Line 42: `MAX_QUERY_RESULTS = 50`
- Line 47: `SOCKETIO_RECONNECT_DELAY_SECONDS = 5`
- Line 48: `SOCKETIO_MAX_RECONNECT_ATTEMPTS = 10`
- Line 51: `DB_QUERY_TIMEOUT_SECONDS = 30`
- Line 52: `DB_CONNECTION_POOL_SIZE = 10`
- Line 55: `API_REQUEST_TIMEOUT_SECONDS = 30`
- Line 56: `API_RETRY_ATTEMPTS = 3`
- Line 57: `API_RETRY_DELAY_SECONDS = 2`
- Line 60: `LOG_STATS_INTERVAL_SECONDS = 300`
- Line 63: `BASE_SPAWN_RATE_MULTIPLIER = 1.0`
- Line 64: `MIN_SPAWN_RATE = 0.01`
- Line 65: `MAX_SPAWN_RATE = 10.0`

### ✅ OK AS CONSTANTS (Physical/System Limits)

- Earth radius values (6371000m, 6371.0km)
- Grid cell size (0.01°, 1.0km)
- Priority bounds (0.0 - 1.0)
- Precision digits (6 for coords, 2 for distance, 3 for priority)

---

## PHASE 1: FIX DATABASE-DRIVEN VALUES (CRITICAL)

### Step 1.1: Fix Vehicle Capacity Flow

**Problem**: Conductor uses hardcoded capacity (40) instead of database value

**Files to Modify**:

1. `arknet_transit_simulator/simulator.py` (lines 300-420)
2. `arknet_transit_simulator/vehicle/conductor.py` (lines 115, 216, 218)

**Implementation**:

```python
# In simulator.py - fetch capacity from database
from arknet_transit_simulator.services.vehicle_performance import VehiclePerformanceService

# When creating conductor
performance = VehiclePerformanceService.get_performance_by_reg_code(vehicle_id)
vehicle_capacity = performance.capacity  # or query vehicle table directly

conductor = Conductor(
    vehicle_id=vehicle_assignment.vehicle_id,
    capacity=vehicle_capacity,  # EXPLICIT DB VALUE
    passenger_db=passenger_db,
    socketio_url="http://localhost:5000"
)
```

**Acceptance Criteria**:

- ✅ Conductor gets capacity from vehicle database record
- ✅ Different vehicles can have different capacities
- ✅ No hardcoded fallback to 40 or 30
- ✅ Loud warning if capacity not found in DB

### Step 1.2: Add Vehicle Performance to Conductor Config

**Problem**: Conductor doesn't know vehicle's max speed or other performance

**Files to Modify**:

1. `arknet_transit_simulator/simulator.py` (add performance query)
2. `arknet_transit_simulator/vehicle/conductor.py` (add max_speed_kmh field)

**Acceptance Criteria**:

- ✅ Conductor knows vehicle's max speed
- ✅ Can adjust boarding expectations based on vehicle type

---

## PHASE 2: INTEGRATE CONDUCTOR WITH PASSENGER DATABASE (CRITICAL)

### Step 2.1: Add PassengerDatabase Client to Conductor

**Problem**: Conductor has no connection to passenger database

**Files to Modify**:

- `arknet_transit_simulator/vehicle/conductor.py` (lines 110-135)
- `arknet_transit_simulator/simulator.py` (create and pass PassengerDatabase)

**Implementation Pattern**:

```python
# In simulator.py
from commuter_service.passenger_db import PassengerDatabase

# Create shared passenger DB instance
passenger_db = PassengerDatabase(strapi_url="http://localhost:1337")
await passenger_db.connect()

# Pass to conductor
conductor = Conductor(
    vehicle_id=vehicle_id,
    capacity=vehicle_capacity,
    passenger_db=passenger_db,  # NEW
    socketio_url="http://localhost:5000"
)
```

**Acceptance Criteria**:

- ✅ Conductor has active PassengerDatabase connection
- ✅ Can query passengers when needed

### Step 2.2: Implement Passenger Eligibility Query

**Problem**: Conductor can't find eligible passengers near vehicle

**File to Modify**: `commuter_service/passenger_db.py` (add after line 293)

**New Method to Add**:

```python
async def get_eligible_passengers(
    self,
    vehicle_lat: float,
    vehicle_lon: float,
    route_id: str,
    pickup_radius_km: float = 0.2,
    max_results: int = 50
) -> List[Dict]:
    """Find eligible passengers near vehicle location."""
    if not self.session:
        return []
    
    # Calculate bounding box
    import math
    lat_delta = pickup_radius_km / 111.0
    lon_delta = pickup_radius_km / (111.0 * math.cos(math.radians(vehicle_lat)))
    
    params = {
        "filters[route_id][$eq]": route_id,
        "filters[status][$eq]": "WAITING",
        "filters[latitude][$gte]": vehicle_lat - lat_delta,
        "filters[latitude][$lte]": vehicle_lat + lat_delta,
        "filters[longitude][$gte]": vehicle_lon - lon_delta,
        "filters[longitude][$lte]": vehicle_lon + lon_delta,
        "sort": "priority:desc",
        "pagination[limit]": max_results
    }
    
    try:
        async with self.session.get(
            f"{self.strapi_url}/api/active-passengers",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('data', [])
            return []
    except Exception as e:
        print(f"❌ Error fetching eligible passengers: {e}")
        return []
```

**Acceptance Criteria**:

- ✅ Can query passengers near vehicle
- ✅ Returns only WAITING passengers on correct route
- ✅ Sorted by priority (high to low)

### Step 2.3: Implement Individual Passenger Boarding

**Problem**: Conductor only tracks count, not individual passengers

**File to Modify**: `arknet_transit_simulator/vehicle/conductor.py` (lines 120, 690-713)

**Changes Needed**:

```python
# Add to __init__
self.boarded_passengers: List[str] = []  # Track passenger IDs

# Modify board_passengers method
async def board_passengers(self, passenger_ids: List[str]) -> bool:
    """Board specific passengers onto vehicle."""
    if not passenger_ids:
        return False
    
    # Check capacity
    available_seats = self.capacity - self.passengers_on_board
    if len(passenger_ids) > available_seats:
        logger.warning(f"Not enough seats: {len(passenger_ids)} passengers, {available_seats} seats")
        passenger_ids = passenger_ids[:available_seats]
    
    # Mark each as boarded in database
    boarded_count = 0
    for passenger_id in passenger_ids:
        success = await self.passenger_db.mark_boarded(passenger_id)
        if success:
            self.boarded_passengers.append(passenger_id)
            boarded_count += 1
    
    # Update counts
    self.passengers_on_board += boarded_count
    self.seats_available = self.capacity - self.passengers_on_board
    
    logger.info(f"Boarded {boarded_count} passengers ({self.passengers_on_board}/{self.capacity})")
    
    # Check if full
    if self.is_full():
        logger.info(f"VEHICLE FULL! Signaling driver")
        if self.on_full_callback:
            self.on_full_callback()
    
    return True
```

**Acceptance Criteria**:

- ✅ Tracks individual passenger IDs
- ✅ Updates database when passengers board
- ✅ Respects capacity limits

### Step 2.4: Add Pickup Check Loop

**Problem**: Conductor doesn't actively check for passengers

**File to Modify**: `arknet_transit_simulator/vehicle/conductor.py` (add new method)

**New Method**:

```python
async def check_for_passengers(
    self, 
    vehicle_lat: float, 
    vehicle_lon: float, 
    route_id: str
) -> int:
    """
    Check for eligible passengers at current location and board them.
    Returns: Number of passengers boarded
    """
    if self.is_full():
        logger.info(f"Vehicle full, not checking for passengers")
        return 0
    
    # Query database
    eligible = await self.passenger_db.get_eligible_passengers(
        vehicle_lat=vehicle_lat,
        vehicle_lon=vehicle_lon,
        route_id=route_id,
        pickup_radius_km=self.config.pickup_radius_km,
        max_results=self.seats_available
    )
    
    if not eligible:
        logger.info(f"No eligible passengers at this location")
        return 0
    
    # Extract IDs and board
    passenger_ids = [p['attributes']['passenger_id'] for p in eligible]
    logger.info(f"Found {len(passenger_ids)} eligible passengers")
    
    success = await self.board_passengers(passenger_ids)
    return len(passenger_ids) if success else 0
```

**Acceptance Criteria**:

- ✅ Conductor queries for passengers at each stop
- ✅ Boards eligible passengers automatically
- ✅ Returns count of boarded passengers

---

## PHASE 3: CONNECT CONDUCTOR TO DRIVER (CRITICAL)

### Step 3.1: Wire on_full_callback in Simulator

**Problem**: `on_full_callback` is always None, never connected

**File to Modify**: `arknet_transit_simulator/simulator.py` (lines 300-420)

**Implementation**:

```python
# Create conductor for this vehicle
conductor = Conductor(
    vehicle_id=vehicle_assignment.vehicle_id,
    capacity=vehicle_capacity,
    passenger_db=passenger_db,
    socketio_url="http://localhost:5000",
    tick_time=1.0
)

# Wire the callback to signal driver
conductor.on_full_callback = conductor._signal_driver_continue

# Store with driver
driver.conductor = conductor

# Start conductor
await conductor.start()
```

**Acceptance Criteria**:

- ✅ Conductor created for each active vehicle
- ✅ on_full_callback connected to signal method
- ✅ Driver can access conductor

### Step 3.2: Trigger Passenger Check from Driver

**Problem**: No one calls `check_for_passengers()`

**File to Modify**: `arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py`

**Code to Add** (in navigation loop):

```python
# When arriving at a route point
if self.is_at_route_point(current_position, route_point):
    logger.info(f"Arrived at route point, checking for passengers")
    
    # Stop vehicle
    await self.stop_engine()
    
    # Let conductor check for passengers
    if hasattr(self, 'conductor') and self.conductor:
        boarded = await self.conductor.check_for_passengers(
            vehicle_lat=current_position[0],
            vehicle_lon=current_position[1],
            route_id=self.route_name
        )
        logger.info(f"Conductor boarded {boarded} passengers")
    
    # Wait for signal if not full
    if not self.conductor.is_full():
        logger.info(f"Waiting for conductor signal or timeout")
        self.current_state = DriverState.WAITING
        # Socket.IO handler will restart engine when conductor signals
    else:
        # Vehicle full, depart immediately
        await self.start_engine()
```

**Acceptance Criteria**:

- ✅ Driver stops at route points
- ✅ Conductor checks for passengers
- ✅ Driver waits for signal if not full
- ✅ Driver departs immediately if full

---

## PHASE 4: CONFIGURATION MIGRATION (HIGH PRIORITY)

### Step 4.1: Create Central Configuration File

**Problem**: 40+ hardcoded operational parameters

**File to Create**: `arknet_transit_simulator/config/operational_config.yaml`

**Configuration Structure**:

```yaml
conductor:
  pickup_radius_km: 0.2
  boarding_time_window_minutes: 5.0
  min_stop_duration_seconds: 15.0
  max_stop_duration_seconds: 180.0
  per_passenger_boarding_time: 8.0
  per_passenger_disembarking_time: 5.0
  monitoring_interval_seconds: 2.0
  gps_precision_meters: 10.0
  driver_response_timeout_seconds: 30.0
  passenger_boarding_timeout_seconds: 120.0

passenger_spawning:
  search_radius_meters: 100
  max_boarding_distance_meters: 50
  depot_proximity_threshold_meters: 200
  route_proximity_threshold_meters: 100
  max_walking_distance_meters: 1000
  default_wait_time_minutes: 30
  min_spawn_interval_minutes: 1
  max_journey_time_minutes: 120

poisson_spawner:
  peak_multiplier_morning: 2.5
  peak_multiplier_offpeak: 1.0
  distance_mu: 1.5
  distance_sigma: 0.7
  max_distance_km: 2.0
  priority_default: 0.5
  priority_medical: 0.9
  priority_work: 0.8
  priority_school: 0.7
  priority_rush_hour_bonus: 0.2

system:
  expiration_check_interval_seconds: 10
  spawn_check_interval_seconds: 60
  position_update_interval_seconds: 5
  max_query_results: 50
  log_stats_interval_seconds: 300
  socketio_reconnect_delay_seconds: 5
  socketio_max_reconnect_attempts: 10
  db_query_timeout_seconds: 30
  db_connection_pool_size: 10
  api_request_timeout_seconds: 30
  api_retry_attempts: 3
  api_retry_delay_seconds: 2
```

**Acceptance Criteria**:

- ✅ Single source of truth for all config
- ✅ Easy to adjust without code changes
- ✅ Version controlled

### Step 4.2: Update Code to Load from Config

**Files to Modify**:

1. `arknet_transit_simulator/vehicle/conductor.py`
2. `commuter_service/constants.py`
3. `commuter_service/poisson_geojson_spawner.py`

**Acceptance Criteria**:

- ✅ All hardcoded values removed
- ✅ Values loaded from config file
- ✅ Defaults only as last resort

---

## PHASE 5: TESTING & VALIDATION (MEDIUM PRIORITY)

### Step 5.1: End-to-End Integration Test

**File to Create**: `tests/test_e2e_conductor_flow.py`

**Test Flow**:

1. Start Strapi (passenger DB)
2. Spawn 15 passengers along route (vehicle capacity = 11)
3. Start simulator with one vehicle
4. Monitor: conductor queries → boards → full → departs
5. Assert: 11 boarded, 4 waiting

**Acceptance Criteria**:

- ✅ Passengers spawn correctly
- ✅ Conductor finds and boards them
- ✅ Vehicle fills to capacity
- ✅ Driver receives signal and departs

### Step 5.2: Capacity Validation Test

**Test Cases**:

- Small vehicle (capacity 5)
- Medium vehicle (capacity 11)
- Large vehicle (capacity 40)

**Acceptance Criteria**:

- ✅ Small vehicles fill faster
- ✅ Large vehicles take more passengers
- ✅ No hardcoded values interfere

---

## PHASE 6: CLEANUP & DOCUMENTATION (LOW PRIORITY)

### Step 6.1: Remove Dead Code

**Files to Clean**:

- Delete auto-generated .md documents
- Remove commented debug code
- Clean up test files

### Step 6.2: Add Inline Documentation

**Documentation Needed**:

- Conductor passenger flow
- Capacity flow from DB
- Examples in README

---

## MVP COMPLETION CHECKLIST

### Critical Path (Must Complete)

- [ ] **1.1**: Fix vehicle capacity to come from database
- [ ] **1.2**: Add vehicle performance to conductor
- [ ] **2.1**: Connect conductor to PassengerDatabase
- [ ] **2.2**: Implement passenger eligibility query
- [ ] **2.3**: Track individual passengers
- [ ] **2.4**: Add conductor pickup check loop
- [ ] **3.1**: Wire on_full_callback
- [ ] **3.2**: Trigger passenger check from driver
- [ ] **5.1**: End-to-end integration test

### Important (Should Complete)

- [ ] **4.1**: Create central config file
- [ ] **4.2**: Load all values from config
- [ ] **5.2**: Capacity validation tests

### Nice to Have (Post-MVP)

- [ ] **6.1**: Code cleanup
- [ ] **6.2**: Documentation

---

## EFFORT ESTIMATES

- **Phase 1**: 2-3 hours (database integration)
- **Phase 2**: 4-6 hours (passenger database queries/boarding)
- **Phase 3**: 2-3 hours (conductor-driver connection)
- **Phase 4**: 3-4 hours (configuration migration)
- **Phase 5**: 2-3 hours (testing)
- **Phase 6**: 1-2 hours (cleanup)

**Total: 14-21 hours to working MVP**

---

## KEY ARCHITECTURAL DECISIONS

1. **Capacity Source**: Always from vehicle database, never hardcoded
2. **Passenger Tracking**: Individual passenger IDs, not just counts
3. **Configuration**: Central YAML file for all operational parameters
4. **Callback Pattern**: Conductor signals driver via on_full_callback
5. **Query Pattern**: Conductor queries database at each stop
6. **Priority Order**: Database passengers sorted by priority (high to low)

---

## CURRENT IMPLEMENTATION STATUS

**Files Requiring Modification**:

1. `arknet_transit_simulator/simulator.py` - Add conductor creation and wiring
2. `arknet_transit_simulator/vehicle/conductor.py` - Add passenger DB integration
3. `arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py` - Add stop detection
4. `commuter_service/passenger_db.py` - Add get_eligible_passengers method
5. `arknet_transit_simulator/config/operational_config.yaml` - Create new file

**Dependencies**:

- Strapi API running (passenger database)
- Vehicle database with capacity field populated
- Socket.IO server running (conductor-driver communication)

---

## NEXT IMMEDIATE STEPS

1. **Start with Phase 1.1**: Fix capacity flow from database
2. **Then Phase 2.1**: Connect conductor to PassengerDatabase
3. **Then Phase 2.2**: Implement passenger eligibility query
4. **Test incrementally**: After each phase, verify it works

**Ready to begin implementation when you are!**
