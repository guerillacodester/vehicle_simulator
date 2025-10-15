# Conductor-Passenger Integration Guide

**Date:** October 14, 2025  
**Status:** System Architecture & Integration Requirements

---

## Current System State

### ✅ What's Working

1. **Commuter Service (Microservice)**
   - ✅ Spawning passengers using Poisson distribution
   - ✅ Log-normal distance-based trip generation
   - ✅ Depot vs Route temporal patterns (different spawn rates)
   - ✅ Passengers stored in Strapi `/api/active-passengers`
   - ✅ Socket.IO events for real-time spawn notifications
   - ✅ Location-aware commuters with pickup eligibility logic

2. **Vehicle Simulator**
   - ✅ Conductor component exists (`arknet_transit_simulator/vehicle/conductor.py`)
   - ✅ `board_passengers(count)` method for boarding
   - ✅ Capacity management and tracking
   - ✅ Vehicle GPS position tracking

3. **Database Integration**
   - ✅ `PassengerDatabase.query_passengers_near_location()` API exists
   - ✅ Endpoint: `GET /api/active-passengers/near-location`
   - ✅ Parameters: `lat`, `lon`, `radius`, `route_id`, `status`

---

## ❌ What's Missing (Integration Gap)

### The conductor does NOT currently

1. ❌ Query the `/api/active-passengers` endpoint
2. ❌ Check for nearby passengers when vehicle stops
3. ❌ Evaluate pickup eligibility
4. ❌ Update passenger status from WAITING → ONBOARD
5. ❌ Remove passengers from reservoir when boarded

### The commuter service does NOT

1. ❌ Receive vehicle position updates
2. ❌ Know which vehicles are on which routes
3. ❌ Track which passengers have been picked up

---

## 🔧 How to Enable Conductor-Passenger Pickup

### Architecture Overview

```
┌─────────────────────┐         ┌──────────────────────┐
│  Vehicle Simulator  │         │  Commuter Service    │
│                     │         │                      │
│  ┌──────────────┐   │         │  ┌───────────────┐   │
│  │  Conductor   │   │◄────────┤  │  Route        │   │
│  │              │   │  Query  │  │  Reservoir    │   │
│  │  - Checks    │   │  Nearby │  │               │   │
│  │  - Boards    │   │  Pass.  │  │  - Spawns     │   │
│  │  - Updates   │   ├────────►│  │  - Tracks     │   │
│  └──────────────┘   │  Update │  │  - Expires    │   │
│         │           │  Status │  └───────────────┘   │
│         ▼           │         │         │            │
│  ┌──────────────┐   │         │         ▼            │
│  │   Vehicle    │   │         │  ┌───────────────┐   │
│  │              │   │         │  │  Strapi DB    │   │
│  │  - GPS       │   │         │  │               │   │
│  │  - Route     │   │         │  │  /api/active- │   │
│  └──────────────┘   │         │  │  passengers   │   │
└─────────────────────┘         │  └───────────────┘   │
                                └──────────────────────┘
```

### Step 1: Add Passenger Query to Conductor

**File:** `arknet_transit_simulator/vehicle/conductor.py`

Add this method to the `Conductor` class:

```python
async def check_for_nearby_passengers(
    self, 
    vehicle_position: Tuple[float, float],
    route_id: str,
    radius_meters: float = 200.0
) -> List[Dict]:
    """
    Query commuter service for passengers near vehicle position.
    
    Args:
        vehicle_position: (latitude, longitude)
        route_id: Current route ID
        radius_meters: Search radius (default 200m)
    
    Returns:
        List of eligible passengers with pickup details
    """
    if not hasattr(self, 'passenger_db'):
        from commuter_service.passenger_db import PassengerDatabase
        self.passenger_db = PassengerDatabase()
        await self.passenger_db.connect()
    
    lat, lon = vehicle_position
    
    # Query nearby passengers
    nearby_passengers = await self.passenger_db.query_passengers_near_location(
        latitude=lat,
        longitude=lon,
        radius_meters=radius_meters,
        route_id=route_id,
        status="WAITING"
    )
    
    logger.info(f"Conductor {self.vehicle_id}: Found {len(nearby_passengers)} nearby passengers")
    
    # Filter by pickup eligibility
    eligible = []
    for passenger in nearby_passengers:
        # Check if passenger is actually eligible
        if self._is_passenger_eligible(passenger, vehicle_position):
            eligible.append(passenger)
    
    return eligible

def _is_passenger_eligible(
    self,
    passenger: Dict,
    vehicle_position: Tuple[float, float]
) -> bool:
    """Check if passenger qualifies for pickup based on location/route/capacity."""
    # Check capacity
    if self.passengers_on_board >= self.capacity:
        return False
    
    # Check walking distance (already filtered by query radius, but double-check)
    spawn_loc = (passenger['spawn_lat'], passenger['spawn_lon'])
    distance_m = self._calculate_distance_meters(spawn_loc, vehicle_position)
    
    # Use passenger's max walking distance if available
    max_walk = passenger.get('max_walking_distance_m', self.config.pickup_radius_km * 1000)
    if distance_m > max_walk:
        return False
    
    # Check direction compatibility (passenger destination should be ahead on route)
    # TODO: Add route direction logic
    
    return True

def _calculate_distance_meters(
    self, 
    point1: Tuple[float, float], 
    point2: Tuple[float, float]
) -> float:
    """Calculate distance between two GPS points in meters."""
    from geopy.distance import geodesic
    return geodesic(point1, point2).meters
```

### Step 2: Trigger Passenger Checks on Vehicle Stop

**File:** `arknet_transit_simulator/vehicle/conductor.py`

Modify the stop handling logic (around line 470):

```python
async def _prepare_stop_operation(self, boarding: List[str], disembarking: List[str]) -> None:
    """Prepare a stop operation."""
    
    # Get current vehicle position from driver
    vehicle_pos = await self.get_current_vehicle_position()
    route_id = self.assigned_route_id  # Assume this is set during initialization
    
    # CHECK FOR NEARBY PASSENGERS
    eligible_passengers = await self.check_for_nearby_passengers(
        vehicle_position=vehicle_pos,
        route_id=route_id,
        radius_meters=self.config.pickup_radius_km * 1000
    )
    
    logger.info(f"Conductor {self.vehicle_id}: {len(eligible_passengers)} passengers eligible for pickup")
    
    # Board eligible passengers
    boarded_count = 0
    for passenger in eligible_passengers:
        if self.passengers_on_board < self.capacity:
            # Board the passenger
            success = await self._board_single_passenger(passenger)
            if success:
                boarded_count += 1
                boarding.append(passenger['id'])
        else:
            logger.warning(f"Conductor {self.vehicle_id}: Vehicle full, cannot board passenger {passenger['id']}")
            break
    
    logger.info(f"Conductor {self.vehicle_id}: Boarded {boarded_count} passengers")
    
    # Continue with existing stop logic...
```

### Step 3: Update Passenger Status After Boarding

Add this method to handle individual passenger boarding:

```python
async def _board_single_passenger(self, passenger: Dict) -> bool:
    """
    Board a single passenger and update their status.
    
    Args:
        passenger: Passenger dict from commuter service
    
    Returns:
        True if successfully boarded
    """
    try:
        # Board locally
        if not self.board_passengers(1):
            return False
        
        # Update passenger status in database
        if hasattr(self, 'passenger_db'):
            await self.passenger_db.update_passenger_status(
                passenger_id=passenger['id'],
                new_status="ONBOARD",
                vehicle_id=self.vehicle_id,
                boarded_at=datetime.now().isoformat()
            )
        
        logger.info(f"Conductor {self.vehicle_id}: Boarded passenger {passenger['id']}")
        return True
        
    except Exception as e:
        logger.error(f"Conductor {self.vehicle_id}: Error boarding passenger: {e}")
        return False
```

### Step 4: Add Database Update Method

**File:** `commuter_service/passenger_db.py`

Add this method (if it doesn't exist):

```python
async def update_passenger_status(
    self,
    passenger_id: str,
    new_status: str,
    vehicle_id: Optional[str] = None,
    boarded_at: Optional[str] = None
) -> bool:
    """
    Update passenger status when they board a vehicle.
    
    Args:
        passenger_id: Passenger unique ID
        new_status: New status (WAITING/ONBOARD/COMPLETED)
        vehicle_id: Vehicle ID that picked them up
        boarded_at: ISO timestamp of boarding
    
    Returns:
        True if update successful
    """
    if not self.session:
        return False
    
    try:
        payload = {
            'status': new_status
        }
        if vehicle_id:
            payload['vehicle_id'] = vehicle_id
        if boarded_at:
            payload['boarded_at'] = boarded_at
        
        async with self.session.put(
            f"{self.strapi_url}/api/active-passengers/{passenger_id}",
            json={'data': payload}
        ) as response:
            if response.status == 200:
                print(f"✅ Updated passenger {passenger_id} status to {new_status}")
                return True
            else:
                print(f"❌ Failed to update passenger status: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Error updating passenger status: {e}")
        return False
```

---

## 📊 What Happens When Conductor Boards Passengers

### Current Flow (After Integration)

1. **Vehicle Stops**
   - Driver signals conductor vehicle has stopped
   - Conductor gets current GPS position from vehicle

2. **Conductor Queries Nearby Passengers**

   ```python
   GET /api/active-passengers/near-location?lat=13.098&lon=-59.621&radius=200&route_id=1A&status=WAITING
   ```

   - Returns passengers within 200m
   - Filtered by route and WAITING status

3. **Eligibility Check**
   - Conductor evaluates each passenger:
     - ✅ Within walking distance?
     - ✅ Destination ahead on route?
     - ✅ Seats available?
     - ✅ Priority score acceptable?

4. **Boarding Process**
   - For each eligible passenger:
     - `conductor.board_passengers(1)` → Updates local capacity
     - `passenger_db.update_passenger_status(id, "ONBOARD", vehicle_id)` → Updates database
     - Socket.IO event emitted: `{type: "passenger:boarded", passenger_id, vehicle_id}`

5. **Database State Changes**

   ```json
   {
     "id": "PASS_12345",
     "status": "WAITING"  ← Changed to "ONBOARD"
     "vehicle_id": null,  ← Changed to "VEH_001"
     "boarded_at": null,  ← Changed to "2025-10-14T22:15:30Z"
     "spawn_lat": 13.098,
     "spawn_lon": -59.621,
     "destination_lat": 13.252,
     "destination_lon": -59.642
   }
   ```

6. **Reservoir Updates**
   - Route/Depot Reservoir receives Socket.IO event
   - Removes passenger from active tracking
   - Updates metrics (passengers_picked_up counter)

7. **Journey Tracking**
   - Passenger now tracked on vehicle
   - Conductor monitors proximity to destination
   - When near destination:
     - `alight_passengers(1)` → Updates capacity
     - `update_passenger_status(id, "COMPLETED")` → Marks completed

---

## 🚀 Quick Start Integration

### Minimal Working Example

Add to `Conductor.__init__()`:

```python
self.passenger_db = None  # Will be initialized on first use
self.assigned_route_id = None  # Set by driver/dispatcher
```

Add polling loop to conductor monitoring:

```python
async def _passenger_monitoring_loop(self):
    """Background task to check for passengers when vehicle stops."""
    while self.running:
        if self.vehicle_state == VehicleState.STOPPED:
            # Vehicle is stopped - check for passengers
            vehicle_pos = await self.get_current_vehicle_position()
            if vehicle_pos and self.assigned_route_id:
                eligible = await self.check_for_nearby_passengers(
                    vehicle_position=vehicle_pos,
                    route_id=self.assigned_route_id
                )
                
                if eligible:
                    logger.info(f"Conductor: {len(eligible)} passengers waiting to board")
                    # Board them automatically or signal driver
        
        await asyncio.sleep(self.config.monitoring_interval_seconds)
```

Start the loop in `Conductor.start()`:

```python
self._passenger_task = asyncio.create_task(self._passenger_monitoring_loop())
```

---

## 📈 Expected Behavior After Integration

### Scenario: Vehicle on Route 1A approaches Bridgetown

1. **10:15:00** - Commuter Service spawns 3 passengers at Bridgetown depot
   - Passengers stored in DB with status=WAITING
   - Socket.IO event: `commuter:spawned` emitted

2. **10:16:30** - Vehicle #1 (Route 1A) approaches Bridgetown
   - GPS: (13.098, -59.621)
   - Speed drops below 5 km/h
   - Driver signals conductor: "APPROACHING_STOP"

3. **10:16:35** - Conductor queries passengers

   ```
   Found 3 passengers within 200m:
   - PASS_001 (Priority 0.8, Distance 45m)
   - PASS_002 (Priority 0.6, Distance 120m)
   - PASS_003 (Priority 0.3, Distance 180m)
   ```

4. **10:16:40** - Eligibility evaluation

   ```
   PASS_001: ✅ Eligible (close, high priority, destination ahead)
   PASS_002: ✅ Eligible (medium priority, acceptable distance)
   PASS_003: ✅ Eligible (low priority but within range)
   ```

5. **10:16:45** - Boarding process

   ```
   Boarding PASS_001... ✅ Success (1/40 capacity)
   Boarding PASS_002... ✅ Success (2/40 capacity)
   Boarding PASS_003... ✅ Success (3/40 capacity)
   ```

6. **10:16:50** - Database updated

   ```
   PASS_001: status=ONBOARD, vehicle_id=VEH_001, boarded_at=10:16:45
   PASS_002: status=ONBOARD, vehicle_id=VEH_001, boarded_at=10:16:46
   PASS_003: status=ONBOARD, vehicle_id=VEH_001, boarded_at=10:16:47
   ```

7. **10:16:55** - Conductor signals driver

   ```
   "All passengers boarded (3), vehicle can depart"
   ```

8. **10:17:00** - Vehicle departs
   - 3 passengers onboard
   - Next stop: Speightstown (13.252, -59.642)

---

## 🔍 Testing the Integration

### Test 1: Manual Passenger Spawn + Vehicle Query

```python
# Terminal 1: Start commuter service
python start_commuter_service.py

# Terminal 2: Spawn test passenger
from commuter_service.passenger_db import PassengerDatabase
db = PassengerDatabase()
await db.connect()

test_passenger = {
    'id': 'TEST_001',
    'spawn_lat': 13.098,
    'spawn_lon': -59.621,
    'destination_lat': 13.252,
    'destination_lon': -59.642,
    'route_id': '1A',
    'status': 'WAITING',
    'priority': 0.7
}

await db.add_passenger(test_passenger)

# Terminal 3: Query as conductor would
nearby = await db.query_passengers_near_location(
    latitude=13.098,
    longitude=-59.621,
    radius_meters=200,
    route_id='1A',
    status='WAITING'
)

print(f"Found {len(nearby)} passengers")
# Expected: Found 1 passengers
```

### Test 2: Full Boarding Flow

```python
# Start vehicle simulator with conductor
# Watch logs for:
# - Conductor checking for passengers
# - Passengers found
# - Boarding process
# - Status updates
```

---

## 🎯 Summary

**To enable conductor-passenger pickup:**

1. ✅ **Add query logic** to `Conductor.check_for_nearby_passengers()`
2. ✅ **Trigger checks** when vehicle stops
3. ✅ **Board passengers** with `_board_single_passenger()`
4. ✅ **Update status** via `passenger_db.update_passenger_status()`
5. ✅ **Start monitoring** loop in conductor

**Current gap:** The conductor has all the *methods* to board passengers, but doesn't *query* the commuter service database to find them.

**Fix:** Add the query integration methods above and start the monitoring loop.

**Expected result:** When a vehicle stops, the conductor will automatically:

- Check for nearby passengers
- Evaluate eligibility
- Board qualified passengers
- Update database status
- Signal driver when ready to depart

Would you like me to implement these changes to the conductor now?
