# Proper Vehicle Departure Flow - Conductor-Driven

**Date:** October 14, 2025  
**Correct Behavior:** Conductor signals driver to depart when vehicle is full

---

## ✅ Correct Departure Logic

### The Proper Flow:

```
1. Driver boards vehicle at depot
   └─ State: WAITING (engine OFF, ready to receive signals)

2. Conductor monitors passenger boarding
   ├─ Checks for nearby passengers
   ├─ Boards passengers one by one
   └─ Tracks: passengers_on_board / capacity

3. Vehicle reaches capacity (40/40 passengers)
   └─ Conductor detects: is_full() == True
   └─ Conductor calls: on_full_callback()

4. Conductor signals driver to depart
   └─ Emit: 'conductor:ready:depart'

5. Driver receives signal
   └─ Calls: start_engine()
   └─ State: WAITING → ONBOARD
   └─ Engine: OFF → ON

6. Vehicle begins route
   └─ Driver navigates along route coordinates
```

---

## Current Implementation Status

### ✅ What IS Working:

**1. Conductor detects full vehicle** (Line 707 in conductor.py):
```python
def board_passengers(self, count: int) -> bool:
    # ... boarding logic ...
    
    # Check if vehicle is now full
    if self.is_full():
        logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL! Signaling driver to depart")
        if self.on_full_callback:
            self.on_full_callback()  # ✅ Callback exists
            
    return True
```

**2. Conductor can signal driver** (Line 618 in conductor.py):
```python
async def _signal_driver_continue(self) -> None:
    """Signal driver to continue driving."""
    
    signal_data = {
        'vehicle_id': self.vehicle_id,
        'conductor_id': self.component_id,
        'passenger_count': self.passengers_on_board,
        'timestamp': datetime.now().isoformat()
    }
    
    if self.use_socketio and self.sio_connected:
        await self.sio.emit('conductor:ready:depart', signal_data)  # ✅ Signal exists
```

**3. Driver listens for conductor signal** (Line 150 in vehicle_driver.py):
```python
@self.sio.on('conductor:ready:depart')
async def on_ready_to_depart(data):
    """Handle ready-to-depart signal from conductor."""
    self.logger.info(f"[{self.person_name}] Conductor ready to depart: {data}")
    
    # Restart engine if in WAITING state
    if self.current_state == DriverState.WAITING:
        await self.start_engine()  # ✅ Engine start exists
        self.logger.info(f"[{self.person_name}] Engine restarted, resuming journey")
```

### ❌ What's MISSING (The Critical Link):

**Problem:** The `on_full_callback` is never connected to `_signal_driver_continue()`

**Current state (Line 157 in conductor.py):**
```python
self.on_full_callback: Optional[Callable] = None  # ❌ Always None!
```

**What happens:**
1. Vehicle fills up (40/40 passengers)
2. Conductor detects: `is_full() == True`
3. Conductor calls: `on_full_callback()` 
4. **Nothing happens** because callback is `None`
5. Driver stays in WAITING state forever
6. Vehicle doesn't move

---

## 🔧 Required Implementation

### Solution: Connect the Callback

**File:** `arknet_transit_simulator/vehicle/conductor.py`

**Add to `__init__` method (around line 170):**

```python
def __init__(
    self,
    conductor_id: str,
    conductor_name: str,
    vehicle_id: str,
    assigned_route_id: str = None,
    capacity: int = 40,
    config: ConductorConfig = None,
    sio_url: str = "http://localhost:3000",
    use_socketio: bool = True
):
    # ... existing initialization ...
    
    # Enhanced callbacks
    self.on_full_callback: Optional[Callable] = None
    self.on_empty_callback: Optional[Callable] = None
    
    # ✅ NEW: Connect full callback to driver signal
    self.on_full_callback = self._handle_vehicle_full
    
    # ... rest of init ...
```

**Add new method to Conductor class:**

```python
async def _handle_vehicle_full(self) -> None:
    """
    Handle vehicle reaching full capacity.
    Called automatically when vehicle fills up.
    Signals driver to depart from depot/stop.
    """
    self.logger.info(
        f"🚌 Vehicle {self.vehicle_id} FULL ({self.passengers_on_board}/{self.capacity}) - "
        f"Signaling driver to depart"
    )
    
    # Signal driver to start engine and depart
    await self._signal_driver_continue()
    
    # Emit telemetry event
    if self.use_socketio and self.sio_connected:
        try:
            await self.sio.emit('conductor:vehicle:full', {
                'vehicle_id': self.vehicle_id,
                'conductor_id': self.component_id,
                'capacity': self.capacity,
                'passengers_on_board': self.passengers_on_board,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            self.logger.error(f"Failed to emit vehicle full event: {e}")
```

**Update `board_passengers` to handle async callback:**

Since `on_full_callback` is now async, we need to handle it properly:

```python
def board_passengers(self, count: int) -> bool:
    """Board passengers onto the vehicle"""
    if count <= 0:
        return False
        
    if self.passengers_on_board + count > self.capacity:
        available = self.capacity - self.passengers_on_board
        logger.info(f"Conductor {self.vehicle_id}: Only {available} seats available, can't board {count}")
        return False
        
    # Board the passengers
    self.passengers_on_board += count
    self.seats_available = self.capacity - self.passengers_on_board
    
    logger.info(f"Conductor {self.vehicle_id}: Boarded {count} passengers ({self.passengers_on_board}/{self.capacity})")
    
    # Check if vehicle is now full
    if self.is_full():
        logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL! Signaling driver to depart")
        if self.on_full_callback:
            # ✅ NEW: Schedule async callback
            if asyncio.iscoroutinefunction(self.on_full_callback):
                asyncio.create_task(self.on_full_callback())
            else:
                self.on_full_callback()
            
    return True
```

---

## Complete Flow After Implementation

### Step-by-Step Execution:

```
┌─────────────────────────────────────────────────────────────┐
│ DEPOT DEPARTURE: Conductor-Driven Full Vehicle Logic       │
└─────────────────────────────────────────────────────────────┘

1. Driver boards vehicle at depot
   ├─ VehicleDriver.start() called
   ├─ Engine: OFF
   ├─ GPS: ON (broadcasting position)
   └─ State: WAITING

2. Conductor boards vehicle
   ├─ Conductor.start() called
   ├─ passengers_on_board: 0
   ├─ seats_available: 40
   └─ on_full_callback: _handle_vehicle_full ✅

3. Passengers begin boarding
   ├─ Conductor queries: query_passengers_near_location()
   ├─ Finds: 50 passengers waiting at depot
   └─ Begins boarding loop...

4. First passenger boards
   ├─ Conductor: board_passengers(1)
   ├─ passengers_on_board: 0 → 1
   ├─ seats_available: 40 → 39
   └─ is_full(): False

5. More passengers board...
   ├─ board_passengers(1) × 39 more times
   ├─ passengers_on_board: 1 → 2 → 3 → ... → 39
   └─ seats_available: 39 → 38 → 37 → ... → 1

6. Final passenger boards (40th)
   ├─ Conductor: board_passengers(1)
   ├─ passengers_on_board: 39 → 40
   ├─ seats_available: 1 → 0
   └─ is_full(): True ✅

7. Conductor detects full vehicle
   ├─ Log: "VEHICLE FULL! Signaling driver to depart"
   └─ Calls: on_full_callback() → _handle_vehicle_full()

8. Conductor signals driver
   ├─ _handle_vehicle_full() executes
   ├─ Calls: _signal_driver_continue()
   └─ Emits: 'conductor:ready:depart' via Socket.IO

9. Driver receives signal
   ├─ Socket.IO event: 'conductor:ready:depart' received
   ├─ Checks: current_state == WAITING ✅
   └─ Calls: start_engine()

10. Engine starts
    ├─ Engine device: OFF → ON
    ├─ Driver state: WAITING → ONBOARD
    └─ Log: "Engine started - now ONBOARD and ready to drive"

11. Vehicle begins route
    ├─ Driver navigation loop active
    ├─ Vehicle moves along route coordinates
    └─ GPS broadcasts position updates

12. Rejected passengers remain at depot
    ├─ 10 passengers still waiting (50 - 40 = 10)
    ├─ Status: WAITING
    └─ Will board next vehicle
```

---

## Alternative Scenarios

### Scenario A: Scheduled Departure Time Reached Before Full

**Problem:** What if departure time is 8:00 AM but only 20/40 seats filled?

**Solution (Not Yet Implemented):**
```python
async def _handle_vehicle_full(self) -> None:
    """Handle vehicle full OR scheduled departure time."""
    
    reason = "FULL" if self.is_full() else "SCHEDULED_TIME"
    
    self.logger.info(
        f"🚌 Departing: {reason} - "
        f"{self.passengers_on_board}/{self.capacity} passengers"
    )
    
    await self._signal_driver_continue()
```

**Additional trigger needed:**
```python
async def _monitor_scheduled_departure(self):
    """Monitor for scheduled departure time."""
    while self.running and not self.is_full():
        if self.scheduled_departure_time:
            if datetime.now() >= self.scheduled_departure_time:
                self.logger.info("⏰ Scheduled departure time reached")
                await self._handle_vehicle_full()
                break
        await asyncio.sleep(1.0)
```

### Scenario B: Maximum Wait Time (Timeout)

**Problem:** What if only 10 passengers board and vehicle waits forever?

**Solution (Not Yet Implemented):**
```python
async def _monitor_boarding_timeout(self):
    """Depart after maximum wait time even if not full."""
    
    max_wait_seconds = self.config.max_boarding_wait_seconds  # e.g., 300 (5 min)
    elapsed = 0
    
    while elapsed < max_wait_seconds and not self.is_full():
        await asyncio.sleep(10)
        elapsed += 10
    
    if not self.is_full():
        self.logger.info(
            f"⏱️ Max boarding wait time reached "
            f"({self.passengers_on_board}/{self.capacity} passengers) - Departing"
        )
        await self._handle_vehicle_full()
```

### Scenario C: Minimum Passenger Threshold

**Problem:** Should vehicle depart with only 1 passenger if full wait time reached?

**Solution (Not Yet Implemented):**
```python
async def can_depart(self) -> bool:
    """Check if vehicle can depart based on policies."""
    
    # Policy 1: Vehicle is full
    if self.is_full():
        return True
    
    # Policy 2: Minimum passengers met AND (scheduled time OR timeout)
    min_passengers = self.config.min_passengers_for_departure  # e.g., 5
    if self.passengers_on_board >= min_passengers:
        if self.scheduled_time_reached() or self.max_wait_time_reached():
            return True
    
    # Policy 3: Special override (emergency, last bus of day, etc.)
    if self.departure_override:
        return True
    
    return False
```

---

## Configuration Options

### Conductor Departure Policies:

```python
class ConductorConfig:
    # Existing configs...
    
    # NEW: Departure policies
    depart_when_full: bool = True  # Signal driver when full
    min_passengers_for_departure: int = 5  # Minimum to depart
    max_boarding_wait_seconds: float = 300.0  # Max wait (5 min)
    scheduled_departure_priority: bool = True  # Depart on schedule even if not full
    allow_standing_room: bool = False  # Allow over-capacity
    standing_capacity: int = 0  # Additional standing passengers
```

---

## Implementation Checklist

### ✅ Already Implemented:
- [x] Conductor tracks capacity (`passengers_on_board`, `seats_available`)
- [x] Conductor detects full vehicle (`is_full()`)
- [x] Conductor has full callback mechanism (`on_full_callback`)
- [x] Conductor can signal driver (`_signal_driver_continue()`)
- [x] Driver listens for conductor signal (`conductor:ready:depart`)
- [x] Driver can start engine (`start_engine()`)

### ❌ Missing Implementation:
- [ ] **Connect `on_full_callback` to `_handle_vehicle_full`** (CRITICAL)
- [ ] **Handle async callback in `board_passengers()`** (CRITICAL)
- [ ] Add `_handle_vehicle_full()` method
- [ ] Add scheduled departure time monitoring
- [ ] Add maximum boarding wait timeout
- [ ] Add minimum passenger threshold
- [ ] Add departure policy configuration
- [ ] Emit telemetry events for departure triggers

### Priority 1 (Critical - Makes System Work):
1. Connect `on_full_callback = self._handle_vehicle_full` in `__init__`
2. Add `_handle_vehicle_full()` method
3. Update `board_passengers()` to handle async callback

**These 3 changes will enable the correct flow:** Vehicle fills → Conductor signals → Driver starts → Vehicle departs

### Priority 2 (Enhanced Policies):
4. Add scheduled departure time monitoring
5. Add max wait timeout
6. Add min passenger threshold

---

## Code Changes Required

### File: `arknet_transit_simulator/vehicle/conductor.py`

**Change 1: Connect callback in __init__ (around line 170)**
```python
# Enhanced callbacks
self.on_full_callback: Optional[Callable] = None
self.on_empty_callback: Optional[Callable] = None

# ✅ ADD THIS LINE:
self.on_full_callback = self._handle_vehicle_full
```

**Change 2: Add _handle_vehicle_full method (after line 670)**
```python
async def _handle_vehicle_full(self) -> None:
    """Handle vehicle reaching full capacity - signal driver to depart."""
    self.logger.info(
        f"🚌 Vehicle {self.vehicle_id} FULL ({self.passengers_on_board}/{self.capacity}) - "
        f"Signaling driver to depart"
    )
    await self._signal_driver_continue()
```

**Change 3: Update board_passengers to handle async callback (line 707)**
```python
# Check if vehicle is now full
if self.is_full():
    logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL! Signaling driver to depart")
    if self.on_full_callback:
        # ✅ CHANGE THIS:
        if asyncio.iscoroutinefunction(self.on_full_callback):
            asyncio.create_task(self.on_full_callback())
        else:
            self.on_full_callback()
```

---

## Expected Behavior After Implementation

### Test Scenario:

```python
# 1. Create conductor and driver
conductor = Conductor(vehicle_id="ZR400", capacity=40)
driver = VehicleDriver(vehicle_id="ZR400", route_coordinates=[...])

# 2. Start both
await conductor.start()
await driver.start()

# 3. Driver state
print(driver.current_state)  # Output: DriverState.WAITING

# 4. Board passengers
for i in range(40):
    conductor.board_passengers(1)
    print(f"Boarded {i+1}/40 passengers")

# 5. After 40th passenger:
# Output: "VEHICLE FULL! Signaling driver to depart"
# Output: "Conductor ready to depart with 40 passengers"
# Output: "Driver starting engine - now ONBOARD and ready to drive"

# 6. Driver state changed
print(driver.current_state)  # Output: DriverState.ONBOARD

# 7. Vehicle begins moving
# GPS position updates every 2 seconds as vehicle navigates route
```

---

## Summary

### Correct Logic:
**Conductor controls departure, not driver.**

When vehicle is **full** (40/40 passengers):
1. Conductor detects via `is_full()`
2. Conductor calls `on_full_callback()` → `_handle_vehicle_full()`
3. Conductor signals driver via `conductor:ready:depart` Socket.IO event
4. Driver receives signal and starts engine
5. Vehicle departs and begins route

### Missing Piece:
**The callback connection:** `self.on_full_callback = self._handle_vehicle_full`

**Just 3 code changes needed to make this work!**
