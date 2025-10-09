# Priority 2: Real-Time Passenger Coordination - Granular Step-by-Step Plan

## Overview
Break down Socket.IO conductor-driver integration into small, testable increments.
**Each step must be verified working before proceeding to the next.**

---

## STEP 1: Socket.IO Event Type Definitions (15 minutes)

### Goal
Define the message format for conductor-driver-passenger communication without implementing any functionality yet.

### Tasks
1. Add new event type enums to TypeScript
2. Define message payload interfaces
3. Validate TypeScript compiles without errors

### Files to Modify
- `arknet_fleet_manager/arknet-fleet-api/src/socketio/message-format.ts`

### New Event Types to Add
```typescript
// Conductor events
CONDUCTOR_QUERY_PASSENGERS = 'conductor:query:passengers'
CONDUCTOR_READY_TO_DEPART = 'conductor:ready:depart'
CONDUCTOR_PASSENGER_COUNT = 'conductor:passenger:count'

// Driver events  
DRIVER_START_JOURNEY = 'driver:start:journey'
DRIVER_LOCATION_UPDATE = 'driver:location:update'
DRIVER_STOP_AT_DESTINATION = 'driver:stop:destination'

// Passenger events
PASSENGER_BOARD_VEHICLE = 'passenger:board:vehicle'
PASSENGER_MONITOR_JOURNEY = 'passenger:monitor:journey'
PASSENGER_REQUEST_STOP = 'passenger:request:stop'
PASSENGER_DISEMBARK = 'passenger:disembark'
```

### Verification Tests
```bash
cd arknet_fleet_manager/arknet-fleet-api
npm run build
# Expected: No TypeScript errors
```

### Success Criteria
- ✅ TypeScript compiles successfully
- ✅ New event types are defined
- ✅ Message payload interfaces created
- ✅ No breaking changes to existing Socket.IO code

### Deliverable
Working TypeScript with new event types defined but not yet used.

---

## STEP 2: Simple Conductor Socket.IO Connection (20 minutes)

### Goal
Create a minimal Socket.IO client in Python that can connect to Strapi and emit a test event.

### Tasks
1. Install `python-socketio` package if not present
2. Create basic Socket.IO client in conductor.py
3. Test connection to Strapi Socket.IO server
4. Emit a simple test event

### Files to Modify
- `arknet_transit_simulator/vehicle/conductor.py`

### Implementation
```python
# Add Socket.IO client
import socketio

class Conductor:
    def __init__(self, route_id: str):
        self.route_id = route_id
        self.sio = socketio.Client()
        
    def connect_to_server(self, url: str = 'http://localhost:1337'):
        """Connect to Strapi Socket.IO server"""
        try:
            self.sio.connect(url)
            print(f"✅ Conductor connected to {url}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def test_emit(self):
        """Test event emission"""
        self.sio.emit('test:conductor', {'message': 'Hello from conductor'})
        print("✅ Test event emitted")
```

### Verification Tests
```python
# Create test script: test_conductor_socketio.py
from arknet_transit_simulator.vehicle.conductor import Conductor

# Test connection
conductor = Conductor(route_id="1A")
connected = conductor.connect_to_server()
assert connected, "Conductor should connect to server"

# Test event emission
conductor.test_emit()
print("✅ STEP 2 COMPLETE: Conductor can connect and emit events")
```

### Success Criteria
- ✅ Python Socket.IO client installed
- ✅ Conductor connects to Strapi successfully
- ✅ Test event emitted without errors
- ✅ Connection visible in Strapi logs

### Deliverable
Working Socket.IO connection from Python conductor to Strapi server.

---

## STEP 3: Conductor Query Depot Reservoir (30 minutes)

### Goal
Make conductor query the depot reservoir via Socket.IO and receive passenger list.

### Tasks
1. Add Socket.IO event handler in Strapi for passenger queries
2. Conductor emits passenger query event with route_id filter
3. Strapi responds with matching passengers from depot reservoir
4. Conductor receives and logs passenger data

### Files to Modify
- `arknet_fleet_manager/arknet-fleet-api/src/socketio/handlers.ts` (or create new handler file)
- `arknet_transit_simulator/vehicle/conductor.py`

### Strapi Handler (TypeScript)
```typescript
// Handle conductor passenger queries
socket.on('conductor:query:passengers', async (data, callback) => {
  const { route_id, depot_id } = data;
  
  // Query depot reservoir for passengers
  const passengers = await queryDepotPassengers(route_id, depot_id);
  
  callback({
    success: true,
    passengers: passengers,
    count: passengers.length
  });
});
```

### Conductor Implementation (Python)
```python
def query_depot_passengers(self, depot_id: int) -> list:
    """Query depot for passengers waiting for this route"""
    response = None
    
    def callback(data):
        nonlocal response
        response = data
    
    self.sio.emit('conductor:query:passengers', {
        'route_id': self.route_id,
        'depot_id': depot_id
    }, callback=callback)
    
    # Wait for response
    self.sio.sleep(1)
    return response.get('passengers', []) if response else []
```

### Verification Tests
```python
# test_conductor_query_depot.py
from arknet_transit_simulator.vehicle.conductor import Conductor

conductor = Conductor(route_id="1A")
conductor.connect_to_server()

# Query depot 20 (Cheapside Terminal)
passengers = conductor.query_depot_passengers(depot_id=20)

print(f"✅ Found {len(passengers)} passengers at depot 20")
assert len(passengers) > 0, "Should find passengers at depot"
assert passengers[0]['route_id'] == "1A", "Passengers should match route"

print("✅ STEP 3 COMPLETE: Conductor can query depot reservoir")
```

### Success Criteria
- ✅ Socket.IO handler responds to conductor queries
- ✅ Conductor receives passenger list from depot
- ✅ Passengers are filtered by route_id
- ✅ Response includes passenger count

### Deliverable
Working query-response pattern between conductor and depot reservoir.

---

## STEP 4: Conductor-Driver Signal Communication (25 minutes)

### Goal
Conductor sends "ready to depart" signal to driver, driver acknowledges and starts.

### Tasks
1. Add driver Socket.IO client
2. Conductor emits ready signal when enough passengers
3. Driver listens for ready signal
4. Driver responds with acknowledgment

### Files to Modify
- `arknet_transit_simulator/vehicle/driver.py`
- `arknet_transit_simulator/vehicle/conductor.py`

### Driver Implementation (Python)
```python
import socketio

class Driver:
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.sio = socketio.Client()
        self.ready_to_start = False
        
        # Setup event handlers
        @self.sio.on('conductor:ready:depart')
        def on_ready_signal(data):
            print(f"✅ Driver received ready signal: {data['passenger_count']} passengers")
            self.ready_to_start = True
    
    def connect_to_server(self, url: str = 'http://localhost:1337'):
        self.sio.connect(url)
        print(f"✅ Driver connected to {url}")
    
    def start_journey(self):
        if self.ready_to_start:
            print("🚗 Driver starting journey...")
            self.sio.emit('driver:start:journey', {
                'vehicle_id': self.vehicle_id,
                'status': 'departed'
            })
            return True
        return False
```

### Conductor Signal (Python)
```python
def signal_driver_ready(self, passenger_count: int):
    """Signal driver that vehicle is ready to depart"""
    self.sio.emit('conductor:ready:depart', {
        'route_id': self.route_id,
        'passenger_count': passenger_count,
        'timestamp': time.time()
    })
    print(f"✅ Conductor signaled driver: {passenger_count} passengers ready")
```

### Verification Tests
```python
# test_conductor_driver_communication.py
from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver import Driver
import time

# Setup conductor and driver
conductor = Conductor(route_id="1A")
driver = Driver(vehicle_id="BUS-001")

conductor.connect_to_server()
driver.connect_to_server()

# Conductor signals ready
conductor.signal_driver_ready(passenger_count=15)
time.sleep(1)  # Allow signal to propagate

# Driver should be ready to start
assert driver.ready_to_start, "Driver should receive ready signal"

# Driver starts journey
started = driver.start_journey()
assert started, "Driver should start journey after signal"

print("✅ STEP 4 COMPLETE: Conductor-driver communication working")
```

### Success Criteria
- ✅ Driver connects to Socket.IO server
- ✅ Conductor can signal driver
- ✅ Driver receives and processes signal
- ✅ Driver acknowledges with start journey event

### Deliverable
Working bidirectional conductor-driver communication via Socket.IO.

---

## STEP 5: Passenger Boarding Logic (30 minutes)

### Goal
When driver starts journey, passengers board and their status updates.

### Tasks
1. Create passenger boarding event
2. Update passenger status to "on_board"
3. Track which vehicle passenger is on
4. Emit boarding confirmation

### Files to Modify
- `arknet_transit_simulator/passengers/commuter.py`
- `arknet_transit_simulator/vehicle/conductor.py`

### Passenger Implementation (Python)
```python
class Commuter:
    def __init__(self, passenger_id: str, destination: dict):
        self.passenger_id = passenger_id
        self.destination = destination
        self.vehicle_id = None
        self.status = "waiting"
        self.sio = socketio.Client()
    
    def board_vehicle(self, vehicle_id: str):
        """Board a vehicle"""
        self.vehicle_id = vehicle_id
        self.status = "on_board"
        
        self.sio.emit('passenger:board:vehicle', {
            'passenger_id': self.passenger_id,
            'vehicle_id': vehicle_id,
            'destination': self.destination,
            'timestamp': time.time()
        })
        
        print(f"✅ Passenger {self.passenger_id} boarded {vehicle_id}")
```

### Conductor Boarding Process (Python)
```python
def board_passengers(self, passengers: list, vehicle_id: str):
    """Board passengers onto vehicle"""
    boarded = []
    
    for passenger_data in passengers:
        # Create passenger object
        passenger = Commuter(
            passenger_id=passenger_data['id'],
            destination=passenger_data['destination']
        )
        
        # Board passenger
        passenger.board_vehicle(vehicle_id)
        boarded.append(passenger)
    
    print(f"✅ Boarded {len(boarded)} passengers onto {vehicle_id}")
    return boarded
```

### Verification Tests
```python
# test_passenger_boarding.py
from arknet_transit_simulator.passengers.commuter import Commuter
from arknet_transit_simulator.vehicle.conductor import Conductor

# Setup
conductor = Conductor(route_id="1A")
conductor.connect_to_server()

# Get passengers from depot
passengers = conductor.query_depot_passengers(depot_id=20)

# Board passengers
boarded = conductor.board_passengers(passengers[:5], vehicle_id="BUS-001")

assert len(boarded) == 5, "Should board 5 passengers"
assert all(p.status == "on_board" for p in boarded), "All should be on_board"
assert all(p.vehicle_id == "BUS-001" for p in boarded), "All on same vehicle"

print("✅ STEP 5 COMPLETE: Passenger boarding logic working")
```

### Success Criteria
- ✅ Passengers can board vehicles
- ✅ Passenger status updates to "on_board"
- ✅ Vehicle assignment tracked
- ✅ Boarding events emitted via Socket.IO

### Deliverable
Working passenger boarding with status tracking.

---

## STEP 6: Location-Aware Journey Monitoring (35 minutes)

### Goal
Passengers monitor vehicle location and detect when near destination.

### Tasks
1. Driver emits location updates during journey
2. Passengers subscribe to vehicle location updates
3. Passengers calculate distance to destination
4. Passengers emit stop request when < 100m from destination

### Files to Modify
- `arknet_transit_simulator/vehicle/driver.py`
- `arknet_transit_simulator/passengers/commuter.py`

### Driver Location Updates (Python)
```python
def broadcast_location(self, lat: float, lon: float):
    """Broadcast current vehicle location"""
    self.sio.emit('driver:location:update', {
        'vehicle_id': self.vehicle_id,
        'latitude': lat,
        'longitude': lon,
        'timestamp': time.time()
    })
```

### Passenger Journey Monitoring (Python)
```python
from geopy.distance import distance

class Commuter:
    def start_monitoring_journey(self):
        """Monitor vehicle location during journey"""
        
        @self.sio.on('driver:location:update')
        def on_location_update(data):
            if data['vehicle_id'] == self.vehicle_id:
                self._check_destination_proximity(
                    data['latitude'], 
                    data['longitude']
                )
    
    def _check_destination_proximity(self, vehicle_lat: float, vehicle_lon: float):
        """Check if vehicle is near destination"""
        dest_lat = self.destination['latitude']
        dest_lon = self.destination['longitude']
        
        dist = distance(
            (vehicle_lat, vehicle_lon),
            (dest_lat, dest_lon)
        ).meters
        
        if dist < 100:  # Within 100 meters
            self.request_stop()
    
    def request_stop(self):
        """Request vehicle stop at destination"""
        self.sio.emit('passenger:request:stop', {
            'passenger_id': self.passenger_id,
            'vehicle_id': self.vehicle_id,
            'destination': self.destination
        })
        print(f"✅ Passenger {self.passenger_id} requested stop")
```

### Verification Tests
```python
# test_journey_monitoring.py
from arknet_transit_simulator.vehicle.driver import Driver
from arknet_transit_simulator.passengers.commuter import Commuter

# Setup
driver = Driver(vehicle_id="BUS-001")
driver.connect_to_server()

passenger = Commuter(
    passenger_id="PAX-001",
    destination={'latitude': 13.0979, 'longitude': -59.6143}
)
passenger.vehicle_id = "BUS-001"
passenger.connect_to_server()
passenger.start_monitoring_journey()

# Simulate journey - far from destination
driver.broadcast_location(13.2500, -59.6500)
time.sleep(0.5)
assert passenger.status != "stop_requested", "Should not request stop when far"

# Simulate journey - near destination
driver.broadcast_location(13.0980, -59.6144)  # ~10 meters away
time.sleep(0.5)
assert passenger.status == "stop_requested", "Should request stop when near"

print("✅ STEP 6 COMPLETE: Location-aware journey monitoring working")
```

### Success Criteria
- ✅ Driver broadcasts location updates
- ✅ Passengers receive location updates
- ✅ Distance calculation working
- ✅ Stop request emitted when < 100m

### Deliverable
Working real-time journey monitoring with proximity detection.

---

## STEP 7: Passenger Disembarkment (20 minutes)

### Goal
When driver stops at destination, passengers disembark and complete journey.

### Tasks
1. Driver handles stop requests
2. Driver stops at destination
3. Passengers disembark
4. Journey completion recorded

### Files to Modify
- `arknet_transit_simulator/vehicle/driver.py`
- `arknet_transit_simulator/passengers/commuter.py`

### Driver Stop Handling (Python)
```python
def handle_stop_requests(self):
    """Handle passenger stop requests"""
    
    @self.sio.on('passenger:request:stop')
    def on_stop_request(data):
        print(f"🛑 Stop requested by {data['passenger_id']}")
        self.stop_at_destination(data['destination'])

def stop_at_destination(self, destination: dict):
    """Stop vehicle at destination"""
    self.sio.emit('driver:stop:destination', {
        'vehicle_id': self.vehicle_id,
        'location': destination,
        'timestamp': time.time()
    })
    print(f"🛑 Vehicle stopped at destination")
```

### Passenger Disembarkment (Python)
```python
def disembark(self):
    """Disembark from vehicle"""
    self.status = "journey_complete"
    
    self.sio.emit('passenger:disembark', {
        'passenger_id': self.passenger_id,
        'vehicle_id': self.vehicle_id,
        'destination': self.destination,
        'timestamp': time.time()
    })
    
    self.vehicle_id = None
    print(f"✅ Passenger {self.passenger_id} completed journey")
```

### Verification Tests
```python
# test_passenger_disembarkment.py
# ... (setup code)

# Passenger near destination requests stop
passenger.request_stop()
time.sleep(0.5)

# Driver stops
driver.stop_at_destination(passenger.destination)
time.sleep(0.5)

# Passenger disembarks
passenger.disembark()

assert passenger.status == "journey_complete", "Journey should be complete"
assert passenger.vehicle_id is None, "Should not be on vehicle anymore"

print("✅ STEP 7 COMPLETE: Passenger disembarkment working")
```

### Success Criteria
- ✅ Driver receives stop requests
- ✅ Driver stops at destinations
- ✅ Passengers disembark
- ✅ Journey completion recorded

### Deliverable
Complete passenger journey cycle from boarding to disembarkment.

---

## STEP 8: Integration Test - Complete Journey (30 minutes)

### Goal
End-to-end test of complete passenger journey from depot to destination.

### Tasks
1. Create comprehensive integration test
2. Test all components working together
3. Verify data flow through entire system
4. Document any issues

### Integration Test
```python
# test_complete_journey.py
"""
Complete passenger journey integration test:
1. Conductor queries depot for passengers
2. Conductor signals driver when ready
3. Driver starts journey
4. Passengers board vehicle
5. Passengers monitor journey
6. Passengers request stop near destination
7. Driver stops and passengers disembark
"""

import asyncio
from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver import Driver

async def test_complete_journey():
    # Setup
    conductor = Conductor(route_id="1A")
    driver = Driver(vehicle_id="BUS-001")
    
    conductor.connect_to_server()
    driver.connect_to_server()
    
    # Step 1: Query depot
    passengers = conductor.query_depot_passengers(depot_id=20)
    print(f"✅ Found {len(passengers)} passengers")
    
    # Step 2: Signal driver
    conductor.signal_driver_ready(len(passengers))
    await asyncio.sleep(1)
    
    # Step 3: Driver starts
    driver.start_journey()
    
    # Step 4: Board passengers
    boarded = conductor.board_passengers(passengers[:5], "BUS-001")
    print(f"✅ Boarded {len(boarded)} passengers")
    
    # Step 5: Monitor journey
    for passenger in boarded:
        passenger.start_monitoring_journey()
    
    # Step 6: Simulate journey to destination
    # ... (location updates)
    
    # Step 7: Passengers disembark
    # ... (verify completion)
    
    print("✅ STEP 8 COMPLETE: End-to-end journey successful!")

if __name__ == "__main__":
    asyncio.run(test_complete_journey())
```

### Success Criteria
- ✅ All 7 previous steps work together
- ✅ Complete journey cycle executes successfully
- ✅ No errors or exceptions
- ✅ All passengers reach destinations

### Deliverable
Fully working Priority 2 implementation with verified end-to-end functionality.

---

## Testing Strategy

### After Each Step
1. ✅ Run verification test
2. ✅ Check console output for errors
3. ✅ Verify Socket.IO events in Strapi logs
4. ✅ Confirm expected behavior
5. ✅ Document any issues before proceeding

### Rollback Plan
If a step fails:
1. Review error messages
2. Check Socket.IO connection status
3. Verify event payloads match expected format
4. Test components in isolation
5. Fix issue before proceeding to next step

---

## Progress Tracking

| Step | Description | Status | Time |
|------|-------------|--------|------|
| 1 | Socket.IO Event Definitions | ⏳ Not Started | 15min |
| 2 | Conductor Socket.IO Connection | ⏳ Not Started | 20min |
| 3 | Query Depot Reservoir | ⏳ Not Started | 30min |
| 4 | Conductor-Driver Signals | ⏳ Not Started | 25min |
| 5 | Passenger Boarding | ⏳ Not Started | 30min |
| 6 | Journey Monitoring | ⏳ Not Started | 35min |
| 7 | Passenger Disembarkment | ⏳ Not Started | 20min |
| 8 | Integration Test | ⏳ Not Started | 30min |
| **TOTAL** | | | **~3 hours** |

---

## Ready to Begin?

**Start with Step 1:** Socket.IO Event Type Definitions

This is the safest first step - just adding TypeScript definitions without changing any behavior.

Would you like to begin with Step 1?
