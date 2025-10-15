# Vehicle Capacity Behavior - Current State & Missing Features

**Date:** October 14, 2025  
**Status:** Architecture Analysis

---

## Current Implementation (What IS Working)

### ✅ Capacity Tracking

**File:** `arknet_transit_simulator/vehicle/conductor.py`

The conductor **does** track vehicle capacity:

```python
# Initialization (lines 126-132)
self.capacity = capacity  # Default: 40 passengers
self.passengers_on_board = 0
self.seats_available = capacity
```

### ✅ Boarding Capacity Check

**Method:** `board_passengers(count)` (lines 680-712)

When passengers try to board:

```python
def board_passengers(self, count: int) -> bool:
    if count <= 0:
        return False
        
    # CHECK: Will this exceed capacity?
    if self.passengers_on_board + count > self.capacity:
        available = self.capacity - self.passengers_on_board
        logger.info(f"Conductor {self.vehicle_id}: Only {available} seats available, can't board {count}")
        return False  # ❌ REJECT boarding
        
    # Board the passengers
    self.passengers_on_board += count
    self.seats_available = self.capacity - self.passengers_on_board
    
    logger.info(f"Conductor {self.vehicle_id}: Boarded {count} passengers ({self.passengers_on_board}/{self.capacity})")
    
    # CHECK: Is vehicle now full?
    if self.is_full():
        logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL! Signaling driver to depart")
        if self.on_full_callback:
            self.on_full_callback()  # ✅ Notify someone
            
    return True
```

**Behavior:**

- ✅ Prevents over-capacity boarding
- ✅ Tracks available seats
- ✅ Detects when vehicle becomes full
- ✅ Calls optional `on_full_callback` when capacity reached

### ✅ Capacity Status Methods

```python
def is_full(self) -> bool:
    """Check if vehicle is at capacity"""
    return self.passengers_on_board >= self.capacity

def is_empty(self) -> bool:
    """Check if vehicle has no passengers"""
    return self.passengers_on_board == 0

def has_seats_available(self) -> bool:
    """Check if vehicle has available seats"""
    return self.seats_available > 0
```

### ✅ Disembarking (Alighting)

**Method:** `alight_passengers(count)` (lines 713-730)

When passengers get off:

```python
def alight_passengers(self, count: int = None) -> int:
    """Passengers alighting (getting off)"""
    if count is None:
        count = self.passengers_on_board  # Alight ALL
        
    alighted = min(count, self.passengers_on_board)
    self.passengers_on_board -= alighted
    self.seats_available = self.capacity - self.passengers_on_board
    
    logger.info(f"Conductor {self.vehicle_id}: {alighted} passengers alighted ({self.passengers_on_board}/{self.capacity})")
    
    # Check if vehicle is now empty
    if self.is_empty() and self.on_empty_callback:
        self.on_empty_callback()  # ✅ Notify when empty
        
    return alighted
```

**Behavior:**

- ✅ Removes passengers from count
- ✅ Updates seats_available
- ✅ Calls optional `on_empty_callback` when last passenger leaves

### ✅ Driver Integration (Socket.IO)

**File:** `arknet_transit_simulator/vehicle/driver/navigation/vehicle_driver.py`

The driver **can** receive signals from conductor:

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

**Conductor sends signal** (lines 618 in conductor.py):

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
        await self.sio.emit('conductor:ready:depart', signal_data)
        self.logger.info(f"Conductor ready to depart with {self.passengers_on_board} passengers")
```

**Behavior:**

- ✅ Conductor can signal driver to continue/depart
- ✅ Driver can receive and respond to signals
- ✅ Includes passenger count in signal

---

## ❌ What's NOT Implemented (Missing Features)

### 1. ❌ No Automatic "Full Vehicle" Behavior

**Problem:** When `on_full_callback` is called, **nothing happens automatically**.

**Current State:**

```python
if self.is_full():
    logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL!")
    if self.on_full_callback:
        self.on_full_callback()  # ⚠️ Callback is OPTIONAL and likely None
```

**What's Missing:**

- ❌ No one sets the `on_full_callback` (it's always `None`)
- ❌ Conductor doesn't automatically signal driver to skip stops
- ❌ Conductor doesn't automatically stop checking for passengers
- ❌ Vehicle doesn't automatically bypass remaining stops
- ❌ No "express mode" when full

**Expected Behavior (Not Implemented):**
When vehicle is full, conductor should:

1. Stop querying for nearby passengers (why check if no seats?)
2. Signal driver: "Vehicle full, skip remaining pickup stops"
3. Only stop for **disembarking** passengers (not boarding)
4. Resume normal stops after passengers alight and seats open up

### 2. ❌ No "Skip Stop" Logic When Full

**Problem:** Conductor will still check for passengers at every stop, even when full.

**Current State:**

- Conductor monitors for passengers continuously
- At each stop, conductor evaluates nearby passengers
- Tries to board them → `board_passengers()` → **FAILS** (capacity check)
- Wastes time checking passengers who can't board

**What's Missing:**

- ❌ No logic to skip passenger pickup when full
- ❌ No "express mode" to only handle disembarking
- ❌ No optimization to reduce unnecessary queries
- ❌ No passenger notification ("vehicle full, wait for next one")

**Expected Behavior (Not Implemented):**

```python
async def check_for_nearby_passengers(self, vehicle_position, route_id):
    # ✅ SHOULD CHECK THIS FIRST
    if self.is_full():
        self.logger.info("Vehicle full, skipping passenger query")
        return []  # Don't waste time querying
    
    # Only query if seats available
    nearby = await self.passenger_db.query_passengers_near_location(...)
    return nearby
```

### 3. ❌ No Partial Boarding When Nearly Full

**Problem:** If vehicle has 2 seats but 5 passengers waiting, none can board.

**Current State:**

```python
if self.passengers_on_board + count > self.capacity:
    logger.info(f"Only {available} seats available, can't board {count}")
    return False  # ❌ Rejects ALL passengers
```

**What's Missing:**

- ❌ No partial boarding (board as many as fit)
- ❌ No priority-based selection (who boards first?)
- ❌ No "standing room" concept (some systems allow over-capacity)

**Expected Behavior (Not Implemented):**

```python
async def board_available_passengers(self, eligible_passengers):
    """Board as many passengers as seats allow."""
    seats = self.seats_available
    
    if seats == 0:
        self.logger.info("Vehicle full, no boarding")
        return 0
    
    # Sort by priority
    sorted_passengers = sorted(eligible_passengers, 
                               key=lambda p: p['priority'], 
                               reverse=True)
    
    # Board top N passengers
    to_board = sorted_passengers[:seats]
    
    for passenger in to_board:
        await self._board_single_passenger(passenger)
    
    # Notify rejected passengers
    rejected = sorted_passengers[seats:]
    for passenger in rejected:
        await self._notify_passenger_rejected(passenger, reason="VEHICLE_FULL")
    
    return len(to_board)
```

### 4. ❌ No "Standing Room" or Over-Capacity Handling

**Problem:** Real buses sometimes allow standing passengers (over-capacity).

**Current State:**

- Hard capacity limit (exactly 40 passengers)
- No concept of "seated" vs "standing" capacity
- No over-capacity configuration

**What's Missing:**

- ❌ No `seated_capacity` vs `total_capacity` distinction
- ❌ No standing room configuration
- ❌ No comfort level tracking (crowded vs comfortable)
- ❌ No safety limits (maximum standing passengers)

**Expected Behavior (Not Implemented):**

```python
self.seated_capacity = 40  # Seats
self.standing_capacity = 20  # Standing room
self.total_capacity = 60  # Max allowed

def comfort_level(self) -> str:
    """Calculate comfort level."""
    if self.passengers_on_board <= self.seated_capacity:
        return "COMFORTABLE"  # Everyone seated
    elif self.passengers_on_board <= self.seated_capacity * 1.2:
        return "CROWDED"  # Some standing
    else:
        return "PACKED"  # Very crowded
```

### 5. ❌ No Passenger Rejection Tracking

**Problem:** When passengers can't board, they're not notified or tracked.

**Current State:**

- `board_passengers(count)` returns `False` → passenger not boarded
- **No one knows** which passengers were rejected
- **No database update** for rejected passengers
- Passengers stay in WAITING state forever

**What's Missing:**

- ❌ No rejected passenger tracking
- ❌ No database status update (WAITING → REJECTED → WAITING)
- ❌ No notification to passenger ("next bus in 15 minutes")
- ❌ No wait time tracking for rejected passengers
- ❌ No metrics (passengers_rejected_count)

**Expected Behavior (Not Implemented):**

```python
async def _handle_rejected_passenger(self, passenger_id, reason):
    """Handle passenger rejection due to full vehicle."""
    
    # Update passenger status
    await self.passenger_db.update_passenger_status(
        passenger_id=passenger_id,
        new_status="WAITING",  # Still waiting
        rejection_count=passenger.get('rejection_count', 0) + 1,
        last_rejected_at=datetime.now().isoformat(),
        rejection_reason=reason  # "VEHICLE_FULL"
    )
    
    # Emit Socket.IO event
    await self.sio.emit('passenger:rejected', {
        'passenger_id': passenger_id,
        'vehicle_id': self.vehicle_id,
        'reason': reason,
        'next_vehicle_eta': 15  # minutes
    })
    
    # Log metrics
    self.metrics['passengers_rejected'] += 1
```

### 6. ❌ No "Next Vehicle" Information

**Problem:** Rejected passengers don't know when next vehicle arrives.

**Current State:**

- Passenger waits indefinitely
- No visibility into vehicle schedule
- No ETA for next available vehicle
- No alternative route suggestions

**What's Missing:**

- ❌ No vehicle schedule integration
- ❌ No "next vehicle in X minutes" estimate
- ❌ No alternative route suggestions
- ❌ No passenger notification system

### 7. ❌ No Dynamic Stop Duration Based on Capacity

**Problem:** Stop duration is fixed, doesn't consider how full vehicle is.

**Current State:**

```python
conductor_config.min_stop_duration_seconds = 15.0
conductor_config.max_stop_duration_seconds = 180.0
```

**What's Missing:**

- ❌ Stop duration doesn't scale with available seats
- ❌ Full vehicle spends same time at stop as empty vehicle
- ❌ No "quick stop" when only disembarking (no boarding possible)

**Expected Behavior (Not Implemented):**

```python
def calculate_stop_duration(self):
    """Calculate stop duration based on capacity."""
    
    if self.is_full():
        # Only disembarking - shorter stop
        disembarking_count = len(self.disembarking_queue)
        return disembarking_count * self.config.per_passenger_disembarking_time
    
    else:
        # Normal stop - boarding + disembarking
        boarding_time = len(self.boarding_queue) * self.config.per_passenger_boarding_time
        disembarking_time = len(self.disembarking_queue) * self.config.per_passenger_disembarking_time
        return max(boarding_time + disembarking_time, self.config.min_stop_duration_seconds)
```

---

## 📊 What SHOULD Happen When Vehicle Is Full

### Ideal Flow (Not Currently Implemented)

```
┌─────────────────────────────────────────────────────────┐
│ SCENARIO: Vehicle reaches capacity (40/40 passengers)  │
└─────────────────────────────────────────────────────────┘

Step 1: Conductor detects full vehicle
  ├─ board_passengers() called
  ├─ passengers_on_board == capacity
  ├─ is_full() returns True
  └─ Trigger on_full_callback() ✅

Step 2: Conductor changes behavior  ❌ NOT IMPLEMENTED
  ├─ Set state to "EXPRESS_MODE"
  ├─ Stop querying for nearby passengers (waste of time)
  ├─ Only monitor for disembarking passengers
  └─ Emit event: {type: "vehicle:full", vehicle_id, route_id}

Step 3: Driver receives notification  ⚠️ PARTIAL
  ├─ Conductor emits 'conductor:ready:depart' ✅
  ├─ Driver should skip remaining pickup stops  ❌
  ├─ Driver only stops for:
  │   ├─ Scheduled route stops (disembarking)
  │   └─ Passenger pull-cord requests
  └─ Driver displays "FULL - NO BOARDING" sign  ❌

Step 4: Rejected passengers notified  ❌ NOT IMPLEMENTED
  ├─ Passengers at stop see vehicle approach
  ├─ System checks: is_full() == True
  ├─ Update passenger status: "REJECTED_FULL"
  ├─ Notify passenger:
  │   └─ "Vehicle full. Next bus: Route 1A in 12 minutes"
  └─ Emit Socket.IO: {type: "passenger:rejected", reason: "VEHICLE_FULL"}

Step 5: Seats become available  ✅ IMPLEMENTED
  ├─ Vehicle reaches stop with disembarking passengers
  ├─ alight_passengers(5) called
  ├─ passengers_on_board: 40 → 35
  ├─ seats_available: 0 → 5
  └─ is_full() now returns False

Step 6: Resume normal operation  ❌ NOT IMPLEMENTED
  ├─ Conductor detects has_seats_available() == True
  ├─ Exit EXPRESS_MODE
  ├─ Resume querying for nearby passengers
  ├─ Signal driver: "Resume normal stops"
  └─ Emit event: {type: "vehicle:seats_available", count: 5}
```

---

## 🔧 Implementation Checklist

### Priority 1: Essential Full-Vehicle Handling

- [ ] **Set on_full_callback in conductor initialization**
  - Connect callback to driver notification system
  - Emit "vehicle:full" event when capacity reached

- [ ] **Skip passenger queries when full**

  ```python
  async def check_for_nearby_passengers(self, vehicle_position, route_id):
      if self.is_full():
          return []  # Don't waste time querying
      # ... rest of method
  ```

- [ ] **Implement partial boarding**

  ```python
  def board_available_passengers(self, eligible_passengers):
      seats = self.seats_available
      if seats == 0:
          return 0
      
      # Board top N by priority
      to_board = eligible_passengers[:seats]
      # ... board them
  ```

### Priority 2: Passenger Experience

- [ ] **Track rejected passengers**
  - Update database with rejection reason
  - Increment rejection_count
  - Record last_rejected_at timestamp

- [ ] **Notify rejected passengers**
  - Socket.IO event: "passenger:rejected"
  - Include reason: "VEHICLE_FULL"
  - Provide next_vehicle_eta

- [ ] **Provide next vehicle information**
  - Query vehicle schedule
  - Calculate ETA for next vehicle on route
  - Send to rejected passengers

### Priority 3: Driver Integration

- [ ] **Implement "express mode" signaling**

  ```python
  await self.sio.emit('conductor:express_mode', {
      'vehicle_id': self.vehicle_id,
      'reason': 'VEHICLE_FULL',
      'resume_normal_stops_after_disembark': True
  })
  ```

- [ ] **Driver responds to express mode**
  - Skip non-essential stops
  - Only stop for disembarking passengers
  - Display "FULL" indicator

### Priority 4: Advanced Features

- [ ] **Implement standing room capacity**
  - seated_capacity = 40
  - standing_capacity = 20
  - total_capacity = 60
  - Comfort level tracking

- [ ] **Dynamic stop duration**
  - Scale with available seats
  - Quick stop when full (disembark only)
  - Normal stop when seats available

- [ ] **Metrics tracking**
  - passengers_rejected_count
  - avg_rejection_wait_time
  - capacity_utilization_percentage

---

## 🎯 Summary

### ✅ What IS Working

1. Capacity tracking (40 passengers default)
2. Board prevention when full (`board_passengers()` returns False)
3. Capacity status methods (`is_full()`, `has_seats_available()`)
4. Disembarking updates seats correctly
5. Optional callbacks (`on_full_callback`, `on_empty_callback`)
6. Driver-conductor Socket.IO communication

### ❌ What Is NOT Working

1. **on_full_callback is never set** (always None)
2. **No automatic behavior when full**
3. **No skip-stop logic** (conductor still queries at every stop)
4. **No partial boarding** (all-or-nothing approach)
5. **No passenger rejection tracking**
6. **No "express mode"** for driver
7. **No next-vehicle information** for rejected passengers
8. **No standing room** or over-capacity handling
9. **Stop duration doesn't scale** with capacity

### 🚀 Quick Win Implementation

**Minimum changes to get basic full-vehicle handling:**

1. **Add to conductor initialization:**

   ```python
   self.on_full_callback = self._handle_vehicle_full
   ```

2. **Add method:**

   ```python
   async def _handle_vehicle_full(self):
       """Handle vehicle reaching capacity."""
       self.logger.info(f"Vehicle {self.vehicle_id} FULL - entering express mode")
       await self.sio.emit('vehicle:full', {
           'vehicle_id': self.vehicle_id,
           'capacity': self.capacity,
           'timestamp': datetime.now().isoformat()
       })
   ```

3. **Update passenger check:**

   ```python
   async def check_for_nearby_passengers(self, ...):
       if self.is_full():
           self.logger.debug("Vehicle full, skipping passenger query")
           return []
       # ... rest of method
   ```

**These 3 changes would provide basic full-vehicle handling.**

---

Would you like me to implement any of these features tomorrow when we work on the conductor-passenger integration?
