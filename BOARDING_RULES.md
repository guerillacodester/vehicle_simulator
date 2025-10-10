# 🚌 Vehicle Boarding Rules

**Date:** October 10, 2025  
**Status:** Business Rules Defined

---

## Rule 1: Depot Boarding Eligibility

A vehicle can START accepting passengers (conductor can look for passengers and allow boarding) if and only if:

### ✅ Required Conditions (ALL must be true):

1. **Location Check:** Vehicle is physically inside its assigned depot geofence
   - Query: `check_point_in_geofences(vehicle.lat, vehicle.lon, ARRAY['depot'])`
   - Must return the depot matching `vehicle.assigned_depot_id`

2. **Queue Position Check:** Vehicle is FIRST in the departure queue
   - Query depot queue: `SELECT * FROM vehicle_queue WHERE depot_id = ? ORDER BY queue_position`
   - Vehicle must have `queue_position = 1` (or be the oldest vehicle waiting)

### ❌ Cannot Board If:

- Vehicle is NOT in depot geofence (even if first in queue)
- Vehicle is in depot but NOT first in queue (other vehicles ahead)
- Vehicle is at wrong depot (geofence doesn't match assigned_depot_id)
- Vehicle is moving/en-route
- Vehicle is in a non-depot geofence (boarding zone, service area, etc.)

---

## Implementation Requirements

### 1. LocationService Methods Needed

```python
class LocationService:
    def is_vehicle_in_assigned_depot(vehicle_id: str, lat: float, lon: float) -> bool:
        """
        Check if vehicle is inside its assigned depot geofence
        
        Returns:
            True if vehicle is inside correct depot geofence
            False otherwise
        """
        
    def get_depot_at_location(lat: float, lon: float) -> Optional[str]:
        """
        Get depot ID at current location
        
        Returns:
            depot_id if inside depot geofence
            None if not in any depot
        """
```

### 2. Queue Service Methods Needed

```python
class QueueService:
    def is_vehicle_first_in_queue(vehicle_id: str, depot_id: str) -> bool:
        """
        Check if vehicle is first in departure queue
        
        Returns:
            True if vehicle is #1 in queue
            False otherwise
        """
        
    def get_vehicle_queue_position(vehicle_id: str, depot_id: str) -> Optional[int]:
        """
        Get vehicle's position in depot queue
        
        Returns:
            Integer position (1 = first)
            None if not in queue
        """
```

### 3. Vehicle Boarding Logic

```python
class Vehicle:
    def can_accept_passengers(self) -> bool:
        """
        Determine if vehicle can start boarding process
        
        Business Rule:
            Vehicle must be in assigned depot geofence AND first in queue
        """
        # Check location
        in_correct_depot = LocationService.is_vehicle_in_assigned_depot(
            vehicle_id=self.id,
            lat=self.current_lat,
            lon=self.current_lon
        )
        
        if not in_correct_depot:
            return False
        
        # Check queue position
        is_first = QueueService.is_vehicle_first_in_queue(
            vehicle_id=self.id,
            depot_id=self.assigned_depot_id
        )
        
        return is_first
    
    def start_boarding_process(self):
        """
        Conductor starts looking for passengers
        
        Prerequisites:
            - can_accept_passengers() returns True
        
        Actions:
            1. Set vehicle status to "BOARDING"
            2. Notify conductor to start accepting passengers
            3. Open doors
            4. Start boarding timer
        """
        if not self.can_accept_passengers():
            raise Exception(
                f"Vehicle {self.id} cannot board: "
                f"Not in depot or not first in queue"
            )
        
        self.status = "BOARDING"
        self.boarding_started_at = datetime.now()
        # ... conductor logic
```

---

## Database Schema Requirements

### Vehicle Queue Table (if not exists)

```sql
CREATE TABLE IF NOT EXISTS vehicle_queue (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(255) NOT NULL,
    depot_id VARCHAR(255) NOT NULL,
    queue_position INTEGER NOT NULL,
    entered_queue_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(depot_id, queue_position),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (depot_id) REFERENCES depots(depot_id)
);

CREATE INDEX idx_vehicle_queue_depot ON vehicle_queue(depot_id, queue_position);
CREATE INDEX idx_vehicle_queue_vehicle ON vehicle_queue(vehicle_id);
```

### Vehicle Status States

```python
VehicleStatus = Enum(
    "VehicleStatus",
    [
        "IN_DEPOT",        # Parked, waiting in queue
        "BOARDING",        # Accepting passengers (first in queue, in depot)
        "READY_TO_DEPART", # Full or timeout, ready to leave
        "EN_ROUTE",        # Driving on route
        "RETURNING",       # Heading back to depot
    ]
)
```

---

## Event Flow Example

### Scenario: Vehicle Ready to Board

```
1. Vehicle arrives at depot
   - Status: IN_DEPOT
   - Location: (13.098168, -59.621582) → Inside Cheapside Depot geofence
   - Queue position: 3

2. Vehicle waits while others depart
   - Queue position: 3 → 2 → 1

3. Vehicle becomes first in queue
   - can_accept_passengers() → True
   - Conductor receives notification
   
4. Conductor starts boarding
   - Status: IN_DEPOT → BOARDING
   - Doors open
   - Accepts passengers

5. Vehicle becomes full or timeout
   - Status: BOARDING → READY_TO_DEPART
   - Doors close
   - Departs depot

6. Vehicle exits depot geofence
   - Status: READY_TO_DEPART → EN_ROUTE
   - Follows route
```

---

## Testing Scenarios

### ✅ Test Case 1: Happy Path
```python
# Vehicle at correct depot, first in queue
vehicle.lat = 13.098168
vehicle.lon = -59.621582
vehicle.assigned_depot_id = "BGI_CHEAPSIDE_03"
queue_position = 1

assert vehicle.can_accept_passengers() == True
```

### ❌ Test Case 2: Wrong Location
```python
# Vehicle NOT in depot geofence
vehicle.lat = 13.200  # Random location
vehicle.lon = -59.600
queue_position = 1

assert vehicle.can_accept_passengers() == False
```

### ❌ Test Case 3: Not First in Queue
```python
# Vehicle in depot but 3rd in queue
vehicle.lat = 13.098168
vehicle.lon = -59.621582
queue_position = 3

assert vehicle.can_accept_passengers() == False
```

### ❌ Test Case 4: Wrong Depot
```python
# Vehicle in Speightstown depot but assigned to Cheapside
vehicle.lat = 13.252068  # Speightstown coordinates
vehicle.lon = -59.642543
vehicle.assigned_depot_id = "BGI_CHEAPSIDE_03"  # Wrong depot!
queue_position = 1

assert vehicle.can_accept_passengers() == False
```

---

## Next Implementation Steps

1. ✅ Depot geofences exist (5 created)
2. 🟡 Create `LocationService.is_vehicle_in_assigned_depot()`
3. 🟡 Create `QueueService.is_vehicle_first_in_queue()`
4. 🟡 Update `Vehicle.can_accept_passengers()`
5. 🟡 Update `Conductor` to check eligibility before boarding
6. 🟡 Create vehicle queue management system
7. 🟡 Write tests for all scenarios

---

## Questions/Considerations

1. **Queue Management:**
   - How do vehicles enter the queue? (Automatic on arrival?)
   - What happens if vehicle #1 leaves without boarding? (Move queue up?)
   - Do we need queue reservations?

2. **Edge Cases:**
   - What if vehicle leaves depot geofence during boarding? (Cancel boarding?)
   - What if conductor tries to board when not eligible? (Block with error?)
   - What if GPS is inaccurate at depot boundary? (Add buffer zone?)

3. **Performance:**
   - Cache geofence checks? (Vehicles don't move much in depot)
   - How often to check queue position? (On vehicle arrival? Every second?)
   - Materialized view for queue positions?

---

## Integration Points

### Socket.IO Events

```python
# Vehicle becomes eligible to board
emit('vehicle:boarding_eligible', {
    'vehicle_id': 'vehicle_123',
    'depot_id': 'BGI_CHEAPSIDE_03',
    'queue_position': 1,
    'timestamp': '2025-10-10T14:30:00Z'
})

# Conductor starts boarding
emit('vehicle:boarding_started', {
    'vehicle_id': 'vehicle_123',
    'conductor_id': 'conductor_456',
    'max_capacity': 14,
    'current_passengers': 0
})
```

### API Endpoints

```
GET  /api/vehicles/:id/boarding-eligibility
POST /api/vehicles/:id/start-boarding
GET  /api/depots/:id/queue
POST /api/depots/:id/queue/add-vehicle
```

