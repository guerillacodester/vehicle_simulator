# REVISED Priority 2: Granular Step-by-Step Plan (Based on Existing Code)

## 🎯 Overview

This plan leverages **existing, working code** and just adds Socket.IO layer for real-time coordination.

**Key Discovery**: VehicleDriver, Conductor, and LocationAwareCommuter already exist with full logic!

---

## ✅ STEP 1: Add Socket.IO Event Types (10 minutes)

### What to Do
Add 6 new event types to existing TypeScript file.

### File to Modify
`arknet_fleet_manager/arknet-fleet-api/src/socketio/message-format.ts`

### Changes
Add to existing `EventTypes` object:

```typescript
export const EventTypes = {
  // ... existing events ...
  
  // NEW: Conductor Events
  CONDUCTOR_QUERY_PASSENGERS: 'conductor:query:passengers',
  CONDUCTOR_READY_TO_DEPART: 'conductor:ready:depart',
  
  // NEW: Driver Events
  DRIVER_START_JOURNEY: 'driver:start:journey',
  DRIVER_LOCATION_UPDATE: 'driver:location:update',
  
  // NEW: Passenger Events
  PASSENGER_BOARD_VEHICLE: 'passenger:board:vehicle',
  PASSENGER_REQUEST_STOP: 'passenger:request:stop',
} as const;
```

### Verification
```bash
cd arknet_fleet_manager/arknet-fleet-api
npm run build
# Should compile with no errors
```

### Success Criteria
- ✅ TypeScript compiles successfully
- ✅ 6 new event types added
- ✅ No breaking changes to existing code

---

## ✅ STEP 2: Add Socket.IO to Existing Conductor (20 minutes)

### What to Do
Extend the **existing 715-line Conductor class** with Socket.IO client.

### File to Modify
`arknet_transit_simulator/vehicle/conductor.py`

### Changes

**1. Add import at top:**
```python
import socketio
```

**2. Add to `__init__` method (around line 145):**
```python
def __init__(self, ...):
    # ... existing code ...
    
    # NEW: Socket.IO client
    self.sio = None
    self.sio_connected = False
    self.socketio_url = "http://localhost:1337"
```

**3. Add new method after `set_depot_callback` (around line 230):**
```python
async def connect_to_socketio(self, url: str = None) -> bool:
    """Connect conductor to Socket.IO server for real-time communication"""
    try:
        if url:
            self.socketio_url = url
        
        self.sio = socketio.AsyncClient()
        
        # Setup event handlers
        @self.sio.on('connect')
        async def on_connect():
            self.logger.info(f"✅ Conductor {self.component_id} connected to Socket.IO")
            self.sio_connected = True
        
        @self.sio.on('disconnect')
        async def on_disconnect():
            self.logger.warning(f"❌ Conductor {self.component_id} disconnected from Socket.IO")
            self.sio_connected = False
        
        # Connect
        await self.sio.connect(self.socketio_url)
        return True
        
    except Exception as e:
        self.logger.error(f"Socket.IO connection failed: {e}")
        return False
```

### Verification Test
```python
# test_conductor_socketio.py
import asyncio
from arknet_transit_simulator.vehicle.conductor import Conductor

async def test_connection():
    conductor = Conductor.from_config(
        conductor_id="COND001",
        conductor_name="Test Conductor",
        vehicle_id="BUS001",
        route_id="1A"
    )
    
    connected = await conductor.connect_to_socketio()
    assert connected, "Conductor should connect to Socket.IO"
    print("✅ STEP 2 COMPLETE: Conductor Socket.IO connection working")

asyncio.run(test_connection())
```

### Success Criteria
- ✅ Conductor connects to Strapi Socket.IO server
- ✅ Connection visible in Strapi logs
- ✅ No errors in Python
- ✅ Existing conductor logic still works

---

## ✅ STEP 3: Wire Conductor to Existing Depot Reservoir (15 minutes)

### What to Do
Add method to query depot reservoir via Socket.IO (reservoir already has Socket.IO!)

### File to Modify
`arknet_transit_simulator/vehicle/conductor.py`

### Changes

**Add method after `connect_to_socketio` (around line 260):**
```python
async def query_depot_passengers_socketio(self, depot_id: str) -> list:
    """Query depot for passengers via Socket.IO"""
    if not self.sio_connected:
        self.logger.warning("Socket.IO not connected, cannot query depot")
        return []
    
    try:
        # Emit query event
        response = await self.sio.call(
            'conductor:query:passengers',
            {
                'depot_id': depot_id,
                'route_id': self.assigned_route_id,
                'conductor_id': self.component_id
            },
            timeout=5
        )
        
        passengers = response.get('passengers', [])
        self.logger.info(
            f"✅ Conductor {self.component_id} found {len(passengers)} passengers "
            f"at depot {depot_id} for route {self.assigned_route_id}"
        )
        
        return passengers
        
    except Exception as e:
        self.logger.error(f"Failed to query depot via Socket.IO: {e}")
        return []
```

### Verification Test
```python
# test_conductor_depot_query.py
import asyncio
from arknet_transit_simulator.vehicle.conductor import Conductor

async def test_query():
    conductor = Conductor.from_config(
        conductor_id="COND001",
        conductor_name="Test Conductor",
        vehicle_id="BUS001",
        route_id="1A"
    )
    
    await conductor.connect_to_socketio()
    
    # Query Cheapside Terminal (depot 20)
    passengers = await conductor.query_depot_passengers_socketio("20")
    
    print(f"✅ Found {len(passengers)} passengers")
    assert isinstance(passengers, list), "Should return list"
    print("✅ STEP 3 COMPLETE: Conductor can query depot via Socket.IO")

asyncio.run(test_query())
```

### Success Criteria
- ✅ Conductor emits query event
- ✅ Depot reservoir responds (it already has Socket.IO!)
- ✅ Conductor receives passenger list
- ✅ List contains route-filtered passengers

---

## ✅ STEP 4: Add Socket.IO to Existing VehicleDriver (40 minutes)

### What to Do
Extend the **existing 448-line VehicleDriver** with Socket.IO for real-time events.

### File to Modify
`arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py`

### Changes

**1. Add import at top:**
```python
import socketio
from datetime import datetime
```

**2. Add to `__init__` method (around line 70):**
```python
def __init__(self, ...):
    # ... existing code ...
    
    # NEW: Socket.IO client
    self.sio = None
    self.sio_connected = False
    self.socketio_url = "http://localhost:1337"
```

**3. Add new method after `set_vehicle_components` (around line 255):**
```python
async def connect_to_socketio(self, url: str = None) -> bool:
    """Connect driver to Socket.IO server"""
    try:
        if url:
            self.socketio_url = url
        
        self.sio = socketio.AsyncClient()
        
        # Setup event handlers
        @self.sio.on('connect')
        async def on_connect():
            self.logger.info(f"✅ Driver {self.person_name} connected to Socket.IO")
            self.sio_connected = True
        
        @self.sio.on('conductor:ready:depart')
        async def on_ready_signal(data):
            """Conductor signals vehicle ready to depart"""
            self.logger.info(f"🚦 Ready to depart signal: {data}")
            
            # Start engine (uses EXISTING method!)
            started = await self.start_engine()
            
            if started:
                # Acknowledge departure
                await self.sio.emit('driver:start:journey', {
                    'vehicle_id': self.vehicle_id,
                    'driver_id': self.component_id,
                    'passenger_count': data.get('passenger_count', 0),
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.sio.on('conductor:request:stop')
        async def on_stop_request(data):
            """Conductor requests vehicle stop"""
            self.logger.info(f"🛑 Stop request: {data}")
            
            # Stop engine (uses EXISTING method!)
            await self.stop_engine()
        
        # Connect
        await self.sio.connect(self.socketio_url)
        return True
        
    except Exception as e:
        self.logger.error(f"Socket.IO connection failed: {e}")
        return False
```

**4. Add location broadcast method:**
```python
async def broadcast_location(self) -> bool:
    """Broadcast current vehicle location via Socket.IO"""
    if not self.sio_connected:
        return False
    
    if self.current_state != DriverState.ONBOARD:
        return False  # Only broadcast when driving
    
    try:
        # Get current position from last_position or route
        if self.last_position:
            lat, lon = self.last_position
        elif self.route:
            lon, lat = self.route[0]
        else:
            return False
        
        await self.sio.emit('driver:location:update', {
            'vehicle_id': self.vehicle_id,
            'latitude': lat,
            'longitude': lon,
            'speed': 0.0,  # TODO: Get from telemetry
            'timestamp': datetime.now().isoformat()
        })
        
        return True
        
    except Exception as e:
        self.logger.error(f"Failed to broadcast location: {e}")
        return False
```

### Verification Test
```python
# test_driver_socketio.py
import asyncio
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver

async def test_driver():
    # Sample route (Bridgetown to Oistins)
    route = [
        (-59.6130, 13.0827),  # Start
        (-59.6200, 13.0800),  # Mid
        (-59.6300, 13.0750)   # End
    ]
    
    driver = VehicleDriver(
        driver_id="DRV001",
        driver_name="Test Driver",
        vehicle_id="BUS001",
        route_coordinates=route,
        route_name="1A"
    )
    
    # Connect to Socket.IO
    connected = await driver.connect_to_socketio()
    assert connected, "Driver should connect"
    
    print("✅ STEP 4 COMPLETE: Driver Socket.IO working")

asyncio.run(test_driver())
```

### Success Criteria
- ✅ Driver connects to Socket.IO
- ✅ Driver listens for conductor signals
- ✅ `start_engine()` triggered by Socket.IO event
- ✅ Location broadcast works
- ✅ Existing navigation still works

---

## ✅ STEP 5: Add Socket.IO Events to Existing LocationAwareCommuter (20 minutes)

### What to Do
Extend **existing LocationAwareCommuter** to emit boarding events via Socket.IO.

### File to Modify
`commuter_service/location_aware_commuter.py`

### Changes

**1. Add to class (around line 100):**
```python
class LocationAwareCommuter:
    def __init__(self, ...):
        # ... existing code ...
        
        # NEW: Socket.IO client reference (set by reservoir)
        self.sio = None
```

**2. Modify existing `board_vehicle` method (around line 250):**
```python
def board_vehicle(self) -> bool:
    """Board a vehicle (EXISTING METHOD - just add event emission)"""
    if self.state != CommuterState.WAITING_TO_BOARD:
        return False
    
    # EXISTING: Update state
    self.state = CommuterState.ONBOARD
    self.boarded_at = datetime.now()
    
    # NEW: Emit Socket.IO event if client available
    if self.sio:
        asyncio.create_task(self.sio.emit('passenger:board:vehicle', {
            'passenger_id': self.person_id,
            'vehicle_id': self.current_vehicle_id,
            'timestamp': datetime.now().isoformat()
        }))
    
    return True
```

### Success Criteria
- ✅ Existing boarding logic preserved
- ✅ Socket.IO event emitted when available
- ✅ No errors if Socket.IO not connected

---

## ✅ STEP 6: Add Location Monitoring to Existing Commuter (25 minutes)

### What to Do
Wire existing distance calculation to driver location updates.

### File to Modify
`commuter_service/location_aware_commuter.py`

### Changes

**Add new method:**
```python
async def start_journey_monitoring(self, sio_client):
    """Monitor vehicle location during journey (NEW METHOD)"""
    self.sio = sio_client
    
    @sio_client.on('driver:location:update')
    async def on_location_update(data):
        if data.get('vehicle_id') != self.current_vehicle_id:
            return  # Not our vehicle
        
        # Use EXISTING proximity check method!
        vehicle_lat = data['latitude']
        vehicle_lon = data['longitude']
        
        # Check if near destination (uses EXISTING method!)
        distance = self.calculate_distance_to_point(
            (vehicle_lat, vehicle_lon)
        )
        
        if distance < 100:  # Within 100 meters
            await self._request_stop()
    
    async def _request_stop(self):
        """Request stop when near destination"""
        await self.sio.emit('passenger:request:stop', {
            'passenger_id': self.person_id,
            'vehicle_id': self.current_vehicle_id,
            'destination': {
                'latitude': self.destination_location[0],
                'longitude': self.destination_location[1]
            }
        })
```

### Success Criteria
- ✅ Commuter receives driver location updates
- ✅ Existing distance calculation works
- ✅ Stop request emitted when < 100m

---

## ✅ STEP 7: Add Disembarkment Events (15 minutes)

### What to Do
Add Socket.IO event emission to existing disembark logic.

### File to Modify
`commuter_service/location_aware_commuter.py`

### Changes

**Find existing disembark method and add event:**
```python
def disembark(self) -> bool:
    """Disembark from vehicle (EXISTING METHOD)"""
    if self.state != CommuterState.ONBOARD:
        return False
    
    # EXISTING: Update state
    self.state = CommuterState.COMPLETED
    self.completed_at = datetime.now()
    
    # NEW: Emit Socket.IO event
    if self.sio:
        asyncio.create_task(self.sio.emit('passenger:disembark', {
            'passenger_id': self.person_id,
            'vehicle_id': self.current_vehicle_id,
            'timestamp': datetime.now().isoformat()
        }))
    
    return True
```

### Success Criteria
- ✅ Existing disembark logic preserved
- ✅ Socket.IO event emitted
- ✅ Journey marked complete

---

## ✅ STEP 8: Integration Test (30 minutes)

### What to Do
Create end-to-end test using all existing components.

### New File
`tests/test_priority2_integration.py`

### Test Code
```python
import asyncio
from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver

async def test_complete_journey():
    """Test complete passenger journey using EXISTING components"""
    
    # Setup route
    route = [(-59.6130, 13.0827), (-59.6200, 13.0800)]
    
    # Create components (ALL EXIST!)
    conductor = Conductor.from_config("COND001", "Test Conductor", "BUS001", "1A")
    driver = VehicleDriver("DRV001", "Test Driver", "BUS001", route, "1A")
    
    # Connect to Socket.IO (NEW!)
    await conductor.connect_to_socketio()
    await driver.connect_to_socketio()
    
    # Query passengers (NEW!)
    passengers = await conductor.query_depot_passengers_socketio("20")
    print(f"✅ Found {len(passengers)} passengers")
    
    # Signal driver ready (NEW!)
    await conductor.sio.emit('conductor:ready:depart', {
        'passenger_count': len(passengers)
    })
    
    # Wait for driver to start
    await asyncio.sleep(2)
    
    # Check driver started engine
    assert driver.current_state == DriverState.ONBOARD
    
    print("✅ STEP 8 COMPLETE: End-to-end journey working!")

asyncio.run(test_complete_journey())
```

### Success Criteria
- ✅ All components connect
- ✅ Passenger query works
- ✅ Conductor signals driver
- ✅ Driver starts engine
- ✅ No errors

---

## 📊 FINAL SUMMARY

| Step | Description | Time | Complexity |
|------|-------------|------|------------|
| 1 | Add event types | 10 min | Low |
| 2 | Conductor Socket.IO | 20 min | Low |
| 3 | Wire conductor to depot | 15 min | Low |
| 4 | Driver Socket.IO | 40 min | Medium |
| 5 | Commuter boarding events | 20 min | Low |
| 6 | Journey monitoring | 25 min | Low |
| 7 | Disembarkment events | 15 min | Low |
| 8 | Integration test | 30 min | Medium |
| **TOTAL** | | **~2.5 hours** | |

**Key Point**: We're **extending existing, working code** with Socket.IO, not creating from scratch!

