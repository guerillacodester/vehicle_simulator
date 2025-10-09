# Socket.IO Integration Roadmap - Priority 2 Implementation

## 🎯 Executive Summary

**Goal**: Add real-time Socket.IO communication layer to existing vehicle simulation system  
**Scope**: ~100 lines of new code across 3 Python classes + 6 TypeScript event types  
**Risk**: **VERY LOW** - Adding communication layer, not changing core logic  
**Estimated Time**: 2.5 hours (revised from 3 hours)

---

## 📋 PRE-FLIGHT CHECKLIST

### ✅ What Already Exists (DO NOT RECREATE)

- [x] **VehicleDriver class** (448 lines)
  - Has `start_engine()` method (line 186-215)
  - Has `stop_engine()` method (line 217-246)
  - Has complete navigation system
  - Has GPS device management
  - **Just needs**: Socket.IO client + event handlers

- [x] **Conductor class** (715 lines)
  - Has passenger management (`board_passengers`, `alight_passengers`)
  - Has callback-based driver signaling
  - Has stop operation management
  - **Just needs**: Socket.IO client + event emission

- [x] **LocationAwareCommuter class** (in `commuter_service/`)
  - Has boarding/disembarking logic
  - Already has Socket.IO via `BaseReservoir`
  - **Just needs**: Emit passenger lifecycle events

- [x] **Socket.IO Infrastructure**
  - `DepotReservoir` has Socket.IO client (connected to depot server)
  - `RouteReservoir` has Socket.IO client (connected to route server)
  - `BaseReservoir` provides Socket.IO base class

### ❌ What Needs to Be Created

- [ ] 6 TypeScript event type definitions (in `message-format.ts`)
- [ ] Socket.IO client in `Conductor` class (~30 lines)
- [ ] Socket.IO client in `VehicleDriver` class (~50 lines)
- [ ] Event emission in `LocationAwareCommuter` (~10 lines)
- [ ] Integration tests for Socket.IO communication

---

## 🛠️ IMPLEMENTATION PLAN

### STEP 1: TypeScript Event Definitions (10 minutes)

**File**: `commuter_service/message-format.ts`

**Add these 6 event types**:

```typescript
// Driver → Server (Location Broadcasting)
export interface DriverLocationUpdate {
  vehicle_id: string;
  driver_id: string;
  latitude: number;
  longitude: number;
  speed: number;
  heading: number;
  timestamp: string;
}

// Conductor → Server (Stop Request)
export interface ConductorStopRequest {
  vehicle_id: string;
  conductor_id: string;
  stop_id: string;
  passengers_boarding: number;
  passengers_disembarking: number;
  duration_seconds: number;
  gps_position: [number, number];
}

// Conductor → Server (Ready to Depart)
export interface ConductorReadyToDepart {
  vehicle_id: string;
  conductor_id: string;
  passenger_count: number;
  timestamp: string;
}

// Conductor → Server (Query Passengers)
export interface ConductorQueryPassengers {
  depot_id: string;
  route_id: string;
  current_position: [number, number];
}

// Server → Conductor (Passenger Response)
export interface PassengerQueryResponse {
  passengers: Array<{
    passenger_id: string;
    pickup_lat: number;
    pickup_lon: number;
    dropoff_lat: number;
    dropoff_lon: number;
    time_window_start: string;
    time_window_end: string;
  }>;
}

// Passenger → Server (Lifecycle Events)
export interface PassengerLifecycleEvent {
  passenger_id: string;
  event_type: 'board' | 'alight' | 'waiting' | 'cancelled';
  vehicle_id?: string;
  location: [number, number];
  timestamp: string;
}
```

**Verification**:
```bash
cd commuter_service
npm run build  # Should compile without errors
```

---

### STEP 2: Add Socket.IO to Conductor (30 minutes)

**File**: `arknet_transit_simulator/vehicle/conductor.py`

**Changes Required**:

#### 2.1 Add Imports (Line ~10)

```python
import socketio
from typing import Optional, Callable, List, Dict, Tuple
from datetime import datetime
```

#### 2.2 Add Socket.IO Client to __init__ (Line ~100)

```python
class Conductor(BasePerson):
    def __init__(
        self,
        component_id: str,
        vehicle_id: str,
        route_id: str,
        capacity: int = 40,
        sio_url: str = "http://localhost:3000",  # NEW
        use_socketio: bool = True  # NEW
    ):
        super().__init__(component_id, "Conductor")
        
        # Existing attributes
        self.vehicle_id = vehicle_id
        self.assigned_route_id = route_id
        self.capacity = capacity
        self.passengers_on_board = 0
        
        # Callback mechanisms (KEEP AS FALLBACK)
        self.driver_callback: Optional[Callable] = None
        self.depot_callback: Optional[Callable] = None
        
        # NEW: Socket.IO client
        self.use_socketio = use_socketio
        self.sio_connected = False
        
        if self.use_socketio:
            self.sio = socketio.AsyncClient()
            self.sio_url = sio_url
            self._setup_socketio_handlers()
        else:
            self.sio = None
```

#### 2.3 Add Socket.IO Connection Logic (NEW method ~line 150)

```python
def _setup_socketio_handlers(self):
    """Set up Socket.IO event handlers"""
    
    @self.sio.event
    async def connect():
        self.sio_connected = True
        self.logger.info(f"[{self.component_id}] Socket.IO connected")
    
    @self.sio.event
    async def disconnect():
        self.sio_connected = False
        self.logger.warning(f"[{self.component_id}] Socket.IO disconnected")

async def _connect_socketio(self):
    """Connect to Socket.IO server"""
    if not self.use_socketio or self.sio_connected:
        return
    
    try:
        await self.sio.connect(self.sio_url)
        self.logger.info(f"[{self.component_id}] Connected to Socket.IO: {self.sio_url}")
    except Exception as e:
        self.logger.error(f"[{self.component_id}] Socket.IO connection failed: {e}")
        self.use_socketio = False  # Fall back to callbacks
```

#### 2.4 Modify _start_implementation (Line ~220)

```python
async def _start_implementation(self) -> bool:
    """Start conductor operations"""
    try:
        # Connect to Socket.IO (NEW)
        if self.use_socketio:
            await self._connect_socketio()
        
        # Existing code
        await self.transition_to(ConductorState.MONITORING)
        
        # Start monitoring task
        asyncio.create_task(self._monitor_passengers())
        
        return True
    except Exception as e:
        self.logger.error(f"Failed to start: {e}")
        return False
```

#### 2.5 Replace driver_callback with Socket.IO (Line ~441)

**BEFORE** (existing code):
```python
async def _signal_driver_stop(self, stop_operation: StopOperation):
    """Signal driver to stop vehicle"""
    if not self.driver_callback:
        self.logger.warning("No driver callback set!")
        return
    
    signal_data = {
        'action': 'stop_vehicle',
        'duration': stop_operation.requested_duration,
        'passengers_boarding': len(stop_operation.passengers_boarding),
        'passengers_disembarking': len(stop_operation.passengers_disembarking),
        'gps_position': stop_operation.gps_position
    }
    
    self.driver_callback(self.component_id, signal_data)
```

**AFTER** (with Socket.IO):
```python
async def _signal_driver_stop(self, stop_operation: StopOperation):
    """Signal driver to stop vehicle"""
    
    signal_data = {
        'vehicle_id': self.vehicle_id,
        'conductor_id': self.component_id,
        'stop_id': stop_operation.stop_id,
        'passengers_boarding': len(stop_operation.passengers_boarding),
        'passengers_disembarking': len(stop_operation.passengers_disembarking),
        'duration_seconds': stop_operation.requested_duration,
        'gps_position': list(stop_operation.gps_position)
    }
    
    # Try Socket.IO first
    if self.use_socketio and self.sio_connected:
        try:
            await self.sio.emit('conductor:request:stop', signal_data)
            self.logger.info(f"[{self.component_id}] Sent stop request via Socket.IO")
            return
        except Exception as e:
            self.logger.error(f"Socket.IO emit failed: {e}, falling back to callback")
    
    # Fallback to callback
    if self.driver_callback:
        self.driver_callback(self.component_id, signal_data)
    else:
        self.logger.warning("No communication method available for driver!")
```

#### 2.6 Replace continue signal (Line ~509)

**AFTER** (with Socket.IO):
```python
async def _signal_driver_continue(self):
    """Signal driver to continue journey"""
    
    signal_data = {
        'vehicle_id': self.vehicle_id,
        'conductor_id': self.component_id,
        'passenger_count': self.passengers_on_board,
        'timestamp': datetime.now().isoformat()
    }
    
    # Try Socket.IO first
    if self.use_socketio and self.sio_connected:
        try:
            await self.sio.emit('conductor:ready:depart', signal_data)
            self.logger.info(f"[{self.component_id}] Sent depart signal via Socket.IO")
            return
        except Exception as e:
            self.logger.error(f"Socket.IO emit failed: {e}, falling back to callback")
    
    # Fallback to callback
    if self.driver_callback:
        signal_data_old = {
            'action': 'continue_journey',
            'passengers_onboard': self.passengers_on_board
        }
        self.driver_callback(self.component_id, signal_data_old)
    else:
        self.logger.warning("No communication method available for driver!")
```

#### 2.7 Add Passenger Query via Socket.IO (NEW method)

```python
async def _query_passengers_socketio(self, route_id: str, current_position: Tuple[float, float]) -> List[Dict]:
    """Query passengers via Socket.IO"""
    
    if not self.use_socketio or not self.sio_connected:
        # Fall back to depot_callback
        if self.depot_callback:
            return self.depot_callback(route_id)
        return []
    
    try:
        response = await self.sio.call('conductor:query:passengers', {
            'depot_id': 'MainDepot',  # Could be configurable
            'route_id': route_id,
            'current_position': list(current_position)
        })
        
        return response.get('passengers', [])
    
    except Exception as e:
        self.logger.error(f"Passenger query via Socket.IO failed: {e}")
        
        # Fallback to callback
        if self.depot_callback:
            return self.depot_callback(route_id)
        return []
```

**Verification**:
```bash
# No syntax errors
python -m py_compile arknet_transit_simulator/vehicle/conductor.py

# Test in isolation
python -m pytest tests/test_conductor_socketio.py
```

---

### STEP 3: Add Socket.IO to VehicleDriver (45 minutes)

**File**: `arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py`

**Changes Required**:

#### 3.1 Add Imports (Line ~10)

```python
import socketio
import asyncio
from typing import Optional, List, Tuple, Dict
from datetime import datetime
```

#### 3.2 Add Socket.IO Client to __init__ (Line ~30)

```python
class VehicleDriver(BasePerson):
    def __init__(
        self,
        driver_id: str,
        driver_name: str,
        vehicle_id: str,
        route_coordinates: List[List[float]],
        sio_url: str = "http://localhost:3000",  # NEW
        use_socketio: bool = True  # NEW
    ):
        super().__init__(driver_id, "VehicleDriver")
        
        # Existing attributes
        self.driver_name = driver_name
        self.vehicle_id = vehicle_id
        self.route_coordinates = route_coordinates
        
        # Component references
        self.vehicle_engine: Optional[Engine] = None
        self.vehicle_gps: Optional[GPSDevice] = None
        
        # NEW: Socket.IO client
        self.use_socketio = use_socketio
        self.sio_connected = False
        self.location_broadcast_task = None
        
        if self.use_socketio:
            self.sio = socketio.AsyncClient()
            self.sio_url = sio_url
            self._setup_socketio_handlers()
        else:
            self.sio = None
```

#### 3.3 Add Socket.IO Handlers (NEW method ~line 100)

```python
def _setup_socketio_handlers(self):
    """Set up Socket.IO event handlers"""
    
    @self.sio.event
    async def connect():
        self.sio_connected = True
        self.logger.info(f"[{self.driver_name}] Socket.IO connected")
    
    @self.sio.event
    async def disconnect():
        self.sio_connected = False
        self.logger.warning(f"[{self.driver_name}] Socket.IO disconnected")
    
    @self.sio.on('conductor:request:stop')
    async def on_stop_request(data):
        """Handle stop request from conductor"""
        self.logger.info(f"[{self.driver_name}] Stop request: {data}")
        
        # Stop engine
        if self.vehicle_engine and self.current_state == DriverState.ONBOARD:
            await self.stop_engine()
            
            # Wait for specified duration
            duration = data.get('duration_seconds', 30)
            await asyncio.sleep(duration)
            
            # Signal we're ready (conductor will send continue signal)
            self.logger.info(f"[{self.driver_name}] Stop complete, waiting for conductor")
    
    @self.sio.on('conductor:ready:depart')
    async def on_ready_to_depart(data):
        """Handle ready-to-depart signal from conductor"""
        self.logger.info(f"[{self.driver_name}] Conductor ready, restarting engine")
        
        # Restart engine
        if self.vehicle_engine and self.current_state == DriverState.WAITING:
            await self.start_engine()

async def _connect_socketio(self):
    """Connect to Socket.IO server"""
    if not self.use_socketio or self.sio_connected:
        return
    
    try:
        await self.sio.connect(self.sio_url)
        self.logger.info(f"[{self.driver_name}] Connected to Socket.IO: {self.sio_url}")
    except Exception as e:
        self.logger.error(f"[{self.driver_name}] Socket.IO connection failed: {e}")
        self.use_socketio = False  # Disable Socket.IO on failure
```

#### 3.4 Add Location Broadcasting (NEW method)

```python
async def _broadcast_location_loop(self):
    """Background task to broadcast location via Socket.IO"""
    
    while self._running and self.use_socketio:
        try:
            if self.sio_connected and self.current_state == DriverState.ONBOARD:
                # Get current telemetry
                telemetry = self.step()
                
                if telemetry:
                    location_data = {
                        'vehicle_id': self.vehicle_id,
                        'driver_id': self.component_id,
                        'latitude': telemetry['latitude'],
                        'longitude': telemetry['longitude'],
                        'speed': telemetry.get('speed', 0),
                        'heading': telemetry.get('heading', 0),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    await self.sio.emit('driver:location:update', location_data)
            
            # Broadcast every 5 seconds
            await asyncio.sleep(5.0)
        
        except Exception as e:
            self.logger.error(f"Location broadcast error: {e}")
            await asyncio.sleep(5.0)  # Continue trying
```

#### 3.5 Modify _start_implementation (Line ~99)

```python
async def _start_implementation(self) -> bool:
    """Start driver operations"""
    try:
        # Connect to Socket.IO (NEW)
        if self.use_socketio:
            await self._connect_socketio()
        
        # Existing code: Board vehicle
        await self.transition_to(DriverState.BOARDING)
        await asyncio.sleep(2.0)  # Boarding delay
        
        # Start GPS
        if self.vehicle_gps:
            await self.vehicle_gps.start()
        
        # Transition to WAITING (engine OFF)
        await self.transition_to(DriverState.WAITING)
        
        # Start location broadcasting (NEW)
        if self.use_socketio:
            self.location_broadcast_task = asyncio.create_task(
                self._broadcast_location_loop()
            )
        
        return True
    
    except Exception as e:
        self.logger.error(f"Failed to start: {e}")
        return False
```

#### 3.6 Modify _stop_implementation (Line ~152)

```python
async def _stop_implementation(self) -> bool:
    """Stop driver operations"""
    try:
        # Cancel location broadcasting (NEW)
        if self.location_broadcast_task:
            self.location_broadcast_task.cancel()
            try:
                await self.location_broadcast_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect Socket.IO (NEW)
        if self.use_socketio and self.sio_connected:
            await self.sio.disconnect()
        
        # Existing code: Disembark
        await self.transition_to(DriverState.DISEMBARKING)
        
        # Stop GPS
        if self.vehicle_gps:
            await self.vehicle_gps.stop()
        
        # Stop engine
        if self.vehicle_engine:
            await self.stop_engine()
        
        await self.transition_to(DriverState.DISEMBARKED)
        
        return True
    
    except Exception as e:
        self.logger.error(f"Failed to stop: {e}")
        return False
```

**Verification**:
```bash
# No syntax errors
python -m py_compile arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py

# Test in isolation
python -m pytest tests/test_driver_socketio.py
```

---

### STEP 4: Add Passenger Events to LocationAwareCommuter (15 minutes)

**File**: `commuter_service/location_aware_commuter.py`

**Changes Required**:

#### 4.1 Add Event Emission in board_vehicle (Line ~TBD)

**BEFORE** (existing):
```python
async def board_vehicle(self, vehicle_id: str):
    """Board a vehicle"""
    self.state = CommuterState.ONBOARD
    self.current_vehicle_id = vehicle_id
    self.logger.info(f"Passenger {self.person_id} boarded vehicle {vehicle_id}")
```

**AFTER** (with Socket.IO):
```python
async def board_vehicle(self, vehicle_id: str):
    """Board a vehicle"""
    self.state = CommuterState.ONBOARD
    self.current_vehicle_id = vehicle_id
    
    # Emit event via Socket.IO
    if hasattr(self, 'sio') and self.sio.connected:
        await self.sio.emit('passenger:board:vehicle', {
            'passenger_id': self.person_id,
            'event_type': 'board',
            'vehicle_id': vehicle_id,
            'location': [self.current_location.latitude, self.current_location.longitude],
            'timestamp': datetime.now().isoformat()
        })
    
    self.logger.info(f"Passenger {self.person_id} boarded vehicle {vehicle_id}")
```

#### 4.2 Add Event Emission in disembark (Line ~TBD)

**AFTER** (with Socket.IO):
```python
async def disembark_vehicle(self):
    """Disembark from vehicle"""
    vehicle_id = self.current_vehicle_id
    self.state = CommuterState.ARRIVED
    self.current_vehicle_id = None
    
    # Emit event via Socket.IO
    if hasattr(self, 'sio') and self.sio.connected:
        await self.sio.emit('passenger:alight:vehicle', {
            'passenger_id': self.person_id,
            'event_type': 'alight',
            'vehicle_id': vehicle_id,
            'location': [self.current_location.latitude, self.current_location.longitude],
            'timestamp': datetime.now().isoformat()
        })
    
    self.logger.info(f"Passenger {self.person_id} alighted from vehicle {vehicle_id}")
```

**Verification**:
```bash
cd commuter_service
python -m pytest tests/test_commuter_socketio.py
```

---

### STEP 5: Integration Testing (30 minutes)

#### 5.1 Create Socket.IO Server Mock (for testing)

**File**: `tests/mock_socketio_server.py`

```python
import socketio
import asyncio
from aiohttp import web

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# Track events
events_received = []

@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@sio.on('driver:location:update')
async def on_driver_location(sid, data):
    print(f"Driver location: {data}")
    events_received.append(('driver:location:update', data))

@sio.on('conductor:request:stop')
async def on_conductor_stop(sid, data):
    print(f"Conductor stop request: {data}")
    events_received.append(('conductor:request:stop', data))
    
    # Simulate stop acknowledgment
    await sio.emit('conductor:request:stop', data, to=sid)

@sio.on('conductor:ready:depart')
async def on_conductor_depart(sid, data):
    print(f"Conductor ready to depart: {data}")
    events_received.append(('conductor:ready:depart', data))

@sio.on('conductor:query:passengers')
async def on_query_passengers(sid, data):
    print(f"Passenger query: {data}")
    
    # Mock response
    return {
        'passengers': [
            {
                'passenger_id': 'P001',
                'pickup_lat': 40.7128,
                'pickup_lon': -74.0060,
                'dropoff_lat': 40.7589,
                'dropoff_lon': -73.9851
            }
        ]
    }

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=3000)
```

#### 5.2 Create Integration Test

**File**: `tests/test_socketio_integration.py`

```python
import pytest
import asyncio
from arknet_transit_simulator.vehicle.conductor import Conductor
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver

@pytest.mark.asyncio
async def test_conductor_driver_socketio_communication():
    """Test Socket.IO communication between conductor and driver"""
    
    # Create conductor with Socket.IO
    conductor = Conductor(
        component_id="COND001",
        vehicle_id="VEH001",
        route_id="1A",
        capacity=40,
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Create driver with Socket.IO
    driver = VehicleDriver(
        driver_id="DRV001",
        driver_name="John Doe",
        vehicle_id="VEH001",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851]],
        sio_url="http://localhost:3000",
        use_socketio=True
    )
    
    # Start both
    await conductor.start()
    await driver.start()
    
    # Wait for Socket.IO connections
    await asyncio.sleep(2.0)
    
    # Verify connections
    assert conductor.sio_connected == True
    assert driver.sio_connected == True
    
    # Simulate stop request from conductor
    stop_operation = StopOperation(
        stop_id="STOP001",
        stop_name="Main Street",
        latitude=40.7128,
        longitude=-74.0060,
        passengers_boarding=['P001', 'P002'],
        passengers_disembarking=['P003'],
        requested_duration=30.0,
        start_time=datetime.now(),
        gps_position=(40.7128, -74.0060)
    )
    
    await conductor._signal_driver_stop(stop_operation)
    
    # Wait for processing
    await asyncio.sleep(1.0)
    
    # Verify driver received signal (check state or logs)
    # TODO: Add state verification
    
    # Cleanup
    await conductor.stop()
    await driver.stop()
```

**Run Tests**:
```bash
# Start mock server in background
python tests/mock_socketio_server.py &

# Run integration tests
pytest tests/test_socketio_integration.py -v

# Stop mock server
pkill -f mock_socketio_server
```

---

### STEP 6: Update Simulator Initialization (15 minutes)

**File**: `arknet_transit_simulator/simulator.py`

**Modify _create_and_start_driver** (Line ~312):

**BEFORE**:
```python
driver = VehicleDriver(
    driver_id=assignment.driver_id,
    driver_name=assignment.driver_name,
    vehicle_id=assignment.vehicle_id,
    route_coordinates=route_coordinates
)
```

**AFTER**:
```python
# Get Socket.IO config from environment or config file
sio_url = os.getenv('SOCKETIO_URL', 'http://localhost:3000')
use_socketio = os.getenv('USE_SOCKETIO', 'true').lower() == 'true'

driver = VehicleDriver(
    driver_id=assignment.driver_id,
    driver_name=assignment.driver_name,
    vehicle_id=assignment.vehicle_id,
    route_coordinates=route_coordinates,
    sio_url=sio_url,
    use_socketio=use_socketio
)
```

**Add Conductor Creation** (NEW - if not already exists):

```python
# Create conductor for vehicle
conductor = Conductor(
    component_id=f"COND_{assignment.vehicle_id}",
    vehicle_id=assignment.vehicle_id,
    route_id=assignment.route_id,
    capacity=vehicle_capacity,
    sio_url=sio_url,
    use_socketio=use_socketio
)

# Link conductor to driver (callback fallback)
conductor.set_driver_callback(driver.handle_conductor_signal)

# Start conductor
await conductor.start()
```

---

## 🧪 TESTING STRATEGY

### Unit Tests

1. **test_conductor_socketio.py**
   - Test Socket.IO connection/disconnection
   - Test stop signal emission
   - Test depart signal emission
   - Test passenger query via Socket.IO
   - Test fallback to callbacks when Socket.IO fails

2. **test_driver_socketio.py**
   - Test Socket.IO connection/disconnection
   - Test location broadcast
   - Test stop request handling
   - Test depart signal handling
   - Test fallback when Socket.IO unavailable

3. **test_commuter_socketio.py**
   - Test board event emission
   - Test alight event emission
   - Test event payload structure

### Integration Tests

1. **test_conductor_driver_communication.py**
   - End-to-end stop/depart cycle
   - Location updates during journey
   - Passenger boarding/alighting events
   - Socket.IO server failure recovery

2. **test_full_journey.py**
   - Complete vehicle journey with Socket.IO
   - Multiple stops with passengers
   - Real-time location tracking
   - Event ordering verification

### Performance Tests

1. **test_socketio_throughput.py**
   - 10 vehicles broadcasting locations simultaneously
   - Measure event latency
   - Measure server load
   - Verify no message loss

---

## 📊 VERIFICATION CHECKLIST

### After Each Step

- [ ] Code compiles without syntax errors
- [ ] No new linter warnings
- [ ] Unit tests pass
- [ ] Manual Socket.IO server test shows events

### Before Final Commit

- [ ] All 6 TypeScript event types defined
- [ ] Conductor has Socket.IO client with fallback
- [ ] VehicleDriver has Socket.IO client with event handlers
- [ ] LocationAwareCommuter emits lifecycle events
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] No performance regression
- [ ] Existing callback system still works as fallback

---

## 🚨 ROLLBACK PLAN

If Socket.IO integration causes issues:

1. **Set environment variable**: `USE_SOCKETIO=false`
2. **System falls back to callbacks** (already implemented)
3. **No code changes needed** - fallback is built-in

### Emergency Hotfix

```python
# In Conductor and VehicleDriver __init__
self.use_socketio = False  # Force disable Socket.IO
```

This immediately reverts to callback-based communication.

---

## 📈 SUCCESS METRICS

### Functional Requirements

- [ ] Driver location updates broadcast every 5 seconds
- [ ] Conductor stop/depart signals delivered in <500ms
- [ ] Passenger events logged on server within 1 second
- [ ] 100% fallback to callbacks if Socket.IO unavailable

### Performance Requirements

- [ ] No impact on navigation loop (<1% CPU increase)
- [ ] Socket.IO events add <50ms latency
- [ ] System supports 50+ concurrent vehicles

### Reliability Requirements

- [ ] Automatic reconnection on Socket.IO disconnect
- [ ] Graceful degradation to callbacks
- [ ] No crashes on server unavailability
- [ ] Event queue prevents message loss

---

## 🎯 PRIORITY 2 COMPLETE WHEN:

✅ All 6 TypeScript event types defined and compiled  
✅ Conductor sends stop/depart signals via Socket.IO  
✅ VehicleDriver receives signals and broadcasts location  
✅ LocationAwareCommuter emits board/alight events  
✅ Integration tests verify end-to-end communication  
✅ Existing callback system preserved as fallback  
✅ Documentation updated with Socket.IO architecture  

**ESTIMATED TOTAL TIME**: 2.5 hours  
**RISK LEVEL**: Very Low  
**IMPACT**: Real-time vehicle tracking and conductor-driver coordination  

---

## 🚀 READY TO START?

**Next Command**: 
```bash
# Open TypeScript file for event definitions
code commuter_service/message-format.ts
```

**First Task**: Add 6 event type definitions (Step 1, ~10 minutes)

