# Driver Engine Start - Triggers & Implementation Status

**Date:** October 14, 2025  
**Status:** Architecture Analysis

---

## Driver State Flow (How Drivers Begin Routes)

### Driver States (DriverState Enum)

```python
class DriverState(Enum):
    DISEMBARKED = "DISEMBARKED"  # Driver not on vehicle
    BOARDING = "BOARDING"        # Driver getting on vehicle  
    WAITING = "WAITING"          # Driver on vehicle, engine OFF, waiting for start trigger ⚠️
    ONBOARD = "ONBOARD"         # Driver is on vehicle and driving (engine ON) ✅
    DISEMBARKING = "DISEMBARKING" # Driver getting off vehicle
    BREAK = "BREAK"             # Driver on break
```

### Critical State: WAITING

**Line 263 in `vehicle_driver.py`:**
```python
# Set state to WAITING after successful boarding (engine off, waiting for start trigger)
self.current_state = DriverState.WAITING
```

**What this means:**
- Driver **boards** the vehicle → state becomes `WAITING`
- Engine is **OFF**, GPS is **ON** (broadcasting initial position)
- Driver is **waiting for external trigger** to start engine
- **No automatic engine start** after boarding

---

## ✅ What IS Implemented (Engine Start Methods)

### 1. Manual Engine Start Method

**File:** `arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py`  
**Lines:** 321-351

```python
async def start_engine(self) -> bool:
    """Start the vehicle engine - transitions driver from WAITING to ONBOARD state."""
    try:
        if self.current_state != DriverState.WAITING:
            self.logger.warning(
                f"Driver {self.person_name} cannot start engine - not in WAITING state "
                f"(current state: {self.current_state.value})"
            )
            return False
        
        if self.vehicle_engine:
            self.logger.info(f"Driver {self.person_name} starting engine for {self.vehicle_id}")
            engine_started = await self.vehicle_engine.start()
            if engine_started:
                # Transition from WAITING to ONBOARD
                self.current_state = DriverState.ONBOARD
                self.logger.info(
                    f"✅ Driver {self.person_name} started engine - now ONBOARD and ready to drive"
                )
                return True
            else:
                self.logger.error(f"Failed to start engine for {self.vehicle_id}")
                return False
        else:
            self.logger.warning(f"No engine available for vehicle {self.vehicle_id}")
            return False
            
    except Exception as e:
        self.logger.error(f"Engine start failed for driver {self.person_name}: {e}")
        return False
```

**Behavior:**
- ✅ Method exists and works
- ✅ Checks driver is in WAITING state
- ✅ Starts engine device
- ✅ Transitions to ONBOARD state
- ✅ Returns success/failure status

**Issue:** This method must be **called externally** - it doesn't trigger automatically.

### 2. Socket.IO Trigger (Conductor Signal)

**File:** `arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py`  
**Lines:** 150-158

```python
@self.sio.on('conductor:ready:depart')
async def on_ready_to_depart(data):
    """Handle ready-to-depart signal from conductor (Priority 2)."""
    self.logger.info(f"[{self.person_name}] Conductor ready to depart: {data}")
    
    # Restart engine if in WAITING state
    if self.current_state == DriverState.WAITING:
        await self.start_engine()
        self.logger.info(f"[{self.person_name}] Engine restarted, resuming journey")
```

**Behavior:**
- ✅ Listens for Socket.IO event `conductor:ready:depart`
- ✅ Checks if driver is in WAITING state
- ✅ Calls `start_engine()` method
- ✅ Logs engine restart

**When this triggers:**
- When **conductor** emits `conductor:ready:depart` event
- Typically after passengers have boarded
- Or after a stop when ready to continue

**File:** `arknet_transit_simulator/vehicle/conductor.py`  
**Lines:** 600-629

```python
async def _signal_driver_continue(self) -> None:
    """Signal driver to continue driving (Priority 2: Socket.IO + callback fallback)."""
    
    signal_data = {
        'vehicle_id': self.vehicle_id,
        'conductor_id': self.component_id,
        'passenger_count': self.passengers_on_board,
        'timestamp': datetime.now().isoformat()
    }
    
    self.logger.info(f"Conductor {self.component_id} signaling driver to continue")
    
    # Try Socket.IO first
    if self.use_socketio and self.sio_connected:
        try:
            await self.sio.emit('conductor:ready:depart', signal_data)
            self.logger.info(f"Conductor ready to depart with {self.passengers_on_board} passengers")
        except Exception as e:
            self.logger.error(f"Socket.IO emit failed: {e}")
```

**Issue:** Conductor must **explicitly call** `_signal_driver_continue()` - this doesn't happen automatically.

---

## ❌ What Is NOT Implemented

### 1. ❌ Automatic Engine Start After Boarding

**Current behavior:**
- Driver boards → state = `WAITING`
- Engine stays **OFF** indefinitely
- **Nothing** automatically starts the engine

**Expected behavior (Not Implemented):**
```python
async def _start_implementation(self) -> bool:
    """Driver boards vehicle and starts vehicle components."""
    # ... GPS setup, boarding logic ...
    
    # After successful boarding:
    self.current_state = DriverState.WAITING
    
    # ❌ THIS IS MISSING:
    if self.auto_start_engine:
        self.logger.info("Auto-starting engine after boarding...")
        await asyncio.sleep(2.0)  # Brief delay
        await self.start_engine()
```

### 2. ❌ Schedule-Based Engine Start

**What's missing:** No scheduled departure times

**Current state:**
- No schedule service integration
- No departure time configuration
- No automatic "time to depart" trigger

**Expected behavior (Not Implemented):**
```python
class VehicleDriver:
    def __init__(self, ..., scheduled_departure_time: Optional[datetime] = None):
        self.scheduled_departure_time = scheduled_departure_time
        self.schedule_monitor_task = None
    
    async def _monitor_scheduled_departure(self):
        """Background task to start engine at scheduled time."""
        while self._running and self.current_state == DriverState.WAITING:
            if self.scheduled_departure_time:
                now = datetime.now()
                if now >= self.scheduled_departure_time:
                    self.logger.info(f"Scheduled departure time reached: {self.scheduled_departure_time}")
                    await self.start_engine()
                    break
            await asyncio.sleep(1.0)
```

**Why this matters:**
- Real transit systems run on schedules
- Vehicles should depart at specific times
- Currently requires manual trigger

### 3. ❌ Dispatcher/Schedule Service Integration

**What's missing:** No dispatcher-driven start triggers

**Current dispatcher role:**
- ✅ Gets vehicle assignments from API
- ✅ Gets driver assignments from API
- ✅ Gets route information
- ❌ **Does NOT** tell drivers when to start engine
- ❌ **Does NOT** track departure schedules
- ❌ **Does NOT** monitor vehicle readiness

**Expected behavior (Not Implemented):**
```python
class Dispatcher:
    async def manage_scheduled_departures(self):
        """Monitor and trigger scheduled vehicle departures."""
        while self.running:
            # Check all scheduled departures
            for schedule_entry in self.departure_schedule:
                if schedule_entry.departure_time <= datetime.now():
                    driver = self.get_driver_for_vehicle(schedule_entry.vehicle_id)
                    if driver and driver.current_state == DriverState.WAITING:
                        # Trigger engine start via Socket.IO
                        await self.sio.emit('dispatcher:start_route', {
                            'vehicle_id': schedule_entry.vehicle_id,
                            'route_id': schedule_entry.route_id,
                            'scheduled_time': schedule_entry.departure_time.isoformat()
                        })
            
            await asyncio.sleep(10.0)  # Check every 10 seconds
```

### 4. ❌ Depot Manager Coordination

**What's missing:** No depot-level departure coordination

**Current depot manager:**
- ✅ Initializes depot components
- ✅ Distributes routes to drivers
- ❌ **Does NOT** coordinate departures
- ❌ **Does NOT** trigger engine starts
- ❌ **Does NOT** manage departure queues

**File:** `arknet_transit_simulator/simulator.py`  
**Lines:** 298-302

```python
# Now distribute routes to operational vehicles (drivers onboard with GPS running)
if active_drivers:
    logger.info(f"🗺️ Distributing routes to {len(active_drivers)} operational vehicles...")
    await self.depot.distribute_routes_to_operational_vehicles(active_drivers)
else:
    logger.info("🗺️ No active drivers found for route distribution")
```

**What happens:**
- Routes are **distributed** to drivers
- Drivers are in **WAITING** state
- **Nothing** tells them to start engines

**Expected behavior (Not Implemented):**
```python
class DepotManager:
    async def initiate_scheduled_departure(self, vehicle_id: str, route_id: str):
        """Coordinate vehicle departure from depot."""
        driver = self.get_driver(vehicle_id)
        
        if not driver:
            self.logger.error(f"No driver found for vehicle {vehicle_id}")
            return False
        
        # Check readiness
        if driver.current_state != DriverState.WAITING:
            self.logger.warning(f"Driver not ready (state: {driver.current_state})")
            return False
        
        # Trigger engine start
        self.logger.info(f"Initiating departure for {vehicle_id} on route {route_id}")
        success = await driver.start_engine()
        
        if success:
            self.logger.info(f"✅ Vehicle {vehicle_id} departed from depot")
            # Emit event for tracking
            await self.emit_departure_event(vehicle_id, route_id)
            return True
        else:
            self.logger.error(f"❌ Failed to start engine for {vehicle_id}")
            return False
```

### 5. ❌ Conductor-Initiated First Departure

**What's missing:** Conductor doesn't initiate first departure

**Current conductor behavior:**
- ✅ Can signal driver to **continue** after stops (`conductor:ready:depart`)
- ❌ **Does NOT** signal initial departure from depot
- ❌ **Does NOT** check if all passengers boarded for initial departure
- ❌ **Does NOT** coordinate with depot for departure clearance

**Expected behavior (Not Implemented):**
```python
class Conductor:
    async def initiate_depot_departure(self):
        """Signal driver to depart from depot after loading passengers."""
        
        # Check if at depot
        if not self.at_depot:
            self.logger.warning("Not at depot, cannot initiate departure")
            return False
        
        # Check passenger loading complete
        if self.boarding_in_progress:
            self.logger.info("Waiting for passenger boarding to complete...")
            return False
        
        # Signal driver
        self.logger.info(f"All passengers loaded ({self.passengers_on_board}/{self.capacity})")
        self.logger.info("Signaling driver to depart from depot")
        
        await self.sio.emit('conductor:ready:depart', {
            'vehicle_id': self.vehicle_id,
            'departure_type': 'DEPOT_DEPARTURE',
            'passenger_count': self.passengers_on_board,
            'timestamp': datetime.now().isoformat()
        })
```

### 6. ❌ External API/Command Trigger

**What's missing:** No external control interface

**Expected features (Not Implemented):**
- REST API endpoint: `POST /api/vehicles/{id}/start-engine`
- WebSocket command: `{"command": "START_ENGINE", "vehicle_id": "ZR400"}`
- Dashboard button: "Start Vehicle ZR400"
- CLI command: `./vehicle_sim start-engine ZR400`

**Example implementation (Not Implemented):**
```python
# FastAPI endpoint
@app.post("/api/vehicles/{vehicle_id}/start-engine")
async def start_vehicle_engine(vehicle_id: str):
    """External API to start vehicle engine."""
    driver = simulator.get_driver_for_vehicle(vehicle_id)
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    if driver.current_state != DriverState.WAITING:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot start engine in state: {driver.current_state.value}"
        )
    
    success = await driver.start_engine()
    
    return {
        "vehicle_id": vehicle_id,
        "engine_started": success,
        "driver_state": driver.current_state.value
    }
```

---

## Current Workflow (Manual Trigger Required)

### What Actually Happens Now:

```
1. Simulator starts
   └─ CleanVehicleSimulator.initialize()

2. Drivers created and board vehicles
   └─ _create_and_start_driver()
       ├─ Create VehicleDriver instance
       ├─ Create GPS device
       ├─ Create Engine (for ZR400)
       └─ driver.start() → boards vehicle
           ├─ Turn on GPS
           ├─ Set initial position
           └─ Set state to WAITING ⚠️

3. Routes distributed to drivers
   └─ depot.distribute_routes_to_operational_vehicles()
       └─ Drivers receive route assignments

4. ❌ NOTHING HAPPENS ❌
   ├─ Drivers stay in WAITING state
   ├─ Engines stay OFF
   └─ Vehicles don't move

5. Manual intervention required:
   ├─ Call driver.start_engine() manually, OR
   ├─ Conductor emits conductor:ready:depart, OR
   └─ External trigger via code/API
```

### What Should Happen (Not Implemented):

```
1. Simulator starts with schedule data
   └─ Load departure schedules from database

2. Drivers board and wait at depot
   └─ State: WAITING at depot position

3. Scheduled departure time approaches
   └─ Dispatcher/Depot monitors schedule

4. Departure time reached
   └─ Depot Manager: initiate_scheduled_departure()
       ├─ Check vehicle readiness
       ├─ Check conductor ready
       ├─ Check passenger loading complete
       └─ Trigger engine start

5. Engine starts automatically
   └─ Driver: WAITING → ONBOARD
       ├─ Engine: OFF → ON
       └─ Vehicle begins route navigation

6. Vehicle completes route
   └─ Returns to depot, waits for next scheduled departure
```

---

## 🎯 Summary: Who Can Start the Engine?

### ✅ Currently Implemented Triggers:

1. **Manual `driver.start_engine()` call**
   - Direct method call from code
   - Requires explicit invocation
   - No automatic trigger

2. **Conductor Socket.IO signal**
   - Event: `conductor:ready:depart`
   - Triggered by conductor after stops
   - Requires conductor to call `_signal_driver_continue()`

### ❌ Missing Triggers:

1. **Automatic start after boarding** ❌
2. **Schedule-based departure** ❌
3. **Dispatcher coordination** ❌
4. **Depot departure clearance** ❌
5. **Conductor initial departure signal** ❌
6. **External API/command** ❌
7. **Passenger loading completion trigger** ❌
8. **Time-based auto-start** ❌

---

## 🔧 Implementation Recommendations

### Priority 1: Automatic Start After Boarding (Quick Win)

**Add to VehicleDriver class:**

```python
def __init__(self, ..., auto_start_after_boarding: bool = True):
    self.auto_start_after_boarding = auto_start_after_boarding
    # ... rest of init

async def _start_implementation(self) -> bool:
    """Driver boards vehicle and starts vehicle components."""
    # ... existing boarding logic ...
    
    # After successful boarding:
    self.current_state = DriverState.WAITING
    
    # NEW: Auto-start engine if enabled
    if self.auto_start_after_boarding:
        self.logger.info("Auto-starting engine after 3-second boarding delay...")
        await asyncio.sleep(3.0)  # Brief delay for realism
        success = await self.start_engine()
        if success:
            self.logger.info("✅ Engine auto-started, ready to drive")
        else:
            self.logger.error("❌ Auto-start failed, manual start required")
    else:
        self.logger.info("Engine auto-start disabled, waiting for external trigger")
    
    return True
```

**Benefits:**
- Simple to implement (5 lines of code)
- Vehicles start immediately after boarding
- Can be disabled with flag for manual control

### Priority 2: Schedule-Based Departure

**Add to VehicleDriver initialization:**

```python
async def _monitor_scheduled_departure(self):
    """Background task to start engine at scheduled time."""
    while self._running and self.current_state == DriverState.WAITING:
        if self.scheduled_departure_time:
            now = datetime.now()
            seconds_until_departure = (self.scheduled_departure_time - now).total_seconds()
            
            if seconds_until_departure <= 0:
                self.logger.info(f"⏰ Scheduled departure time reached!")
                await self.start_engine()
                break
            elif seconds_until_departure <= 60:
                self.logger.info(f"⏱️ Departing in {int(seconds_until_departure)} seconds...")
        
        await asyncio.sleep(5.0)  # Check every 5 seconds

async def _start_implementation(self) -> bool:
    # ... existing boarding logic ...
    
    # Start schedule monitor
    if self.scheduled_departure_time:
        self.schedule_monitor_task = asyncio.create_task(
            self._monitor_scheduled_departure()
        )
```

### Priority 3: Conductor First Departure Signal

**Add to Conductor class:**

```python
async def signal_departure_from_depot(self):
    """Signal initial departure from depot after passenger loading."""
    if not self.at_depot:
        return False
    
    # Wait for passenger boarding if in progress
    while self.boarding_in_progress:
        await asyncio.sleep(1.0)
    
    self.logger.info(f"Depot departure: {self.passengers_on_board} passengers loaded")
    
    # Signal driver to start engine
    await self.sio.emit('conductor:ready:depart', {
        'vehicle_id': self.vehicle_id,
        'departure_type': 'DEPOT_INITIAL_DEPARTURE',
        'passenger_count': self.passengers_on_board
    })
```

---

## 📊 Quick Reference Table

| Trigger Type | Implemented? | Who Initiates | When It Happens |
|--------------|--------------|---------------|-----------------|
| Manual `start_engine()` | ✅ Yes | Developer/Code | Explicit call |
| Conductor Socket.IO | ✅ Yes | Conductor | After stops (resume) |
| Auto-start after boarding | ❌ No | System | After driver boards |
| Scheduled departure | ❌ No | Schedule Service | At scheduled time |
| Dispatcher coordination | ❌ No | Dispatcher | Based on schedule |
| Depot departure clearance | ❌ No | Depot Manager | After loading complete |
| Conductor first departure | ❌ No | Conductor | Initial depot departure |
| External API/command | ❌ No | External System | User/API request |
| Passenger loading complete | ❌ No | Conductor | All passengers boarded |

---

## What Needs to Be Built:

1. **Auto-start flag** - Enable automatic engine start after boarding
2. **Schedule service** - Load and manage departure schedules
3. **Dispatcher scheduling** - Monitor and trigger scheduled departures
4. **Depot coordination** - Manage departure queues and clearances
5. **Conductor first departure** - Signal initial departure from depot
6. **External control API** - REST/WebSocket interface for manual control

**Current State:** Drivers board vehicles and wait indefinitely in `WAITING` state unless manually triggered.

**Goal State:** Vehicles automatically depart based on schedules, conductor signals, or manual triggers.
