# Conductor Query Logic - CONFIRMED ✅

## 🎯 Your Understanding is 100% CORRECT

**YES, the Conductor queries different reservoirs based on vehicle location:**

---

## 📍 The Logic

### **When Vehicle is AT DEPOT:**

```python
if self.is_at_depot(position):
    # Query DEPOT RESERVOIR only
    depot_commuters = await self.query_depot_reservoir(
        depot_id=self.current_depot,
        route_id=route_id,
        vehicle_location=position,
        max_count=capacity_remaining
    )
```

**Why?**

- Depot has **OUTBOUND passengers** waiting in FIFO queue
- These passengers are **starting their journey**
- They're waiting specifically at the depot/terminal
- Need to board before vehicle departs

---

### **When Vehicle is ON ROUTE (Traveling):**

```python
else:  # Not at depot = on route
    # Query ROUTE RESERVOIR only
    route_commuters = await self.query_route_reservoir(
        route_id=route_id,
        vehicle_location=position,
        direction=direction,  # IMPORTANT: Match direction!
        max_count=capacity_remaining,
        max_distance=1000  # 1km lookahead
    )
```

**Why?**

- Route has **BIDIRECTIONAL passengers** along the route
- These passengers are at **bus stops, streets, anywhere along route**
- They're waiting for vehicles going their direction (INBOUND or OUTBOUND)
- Need proximity + direction matching

---

## 🔄 Complete Conductor Loop

```python
class VehicleConductor:
    async def update_loop(self):
        """Main conductor logic - runs every second"""
        while self.running:
            position = self.vehicle.get_position()
            capacity_remaining = self.vehicle.capacity - len(self.vehicle.passengers)
            
            # DECISION POINT: Where are we?
            
            if self.is_at_depot(position):
                # ✅ AT DEPOT → Query Depot Reservoir
                await self.query_depot_reservoir(...)
                
            else:
                # ✅ ON ROUTE → Query Route Reservoir
                await self.query_route_reservoir(...)
            
            # Also check if passengers want to get off
            await self.check_passenger_alighting(position)
            
            await asyncio.sleep(1)  # Update every second
```

---

## 🎭 Real-World Example

### **Morning Route - Bus #47 on Route 1A (OUTBOUND)**

**7:00 AM - At Bridgetown Depot:**

```text
Vehicle Status: Parked at depot
Conductor Logic: is_at_depot() → TRUE
Conductor Action: Query DEPOT RESERVOIR
Query Result: 25 passengers waiting for Route 1A
Conductor Decision: Board all 25 (capacity allows)
Boarding Complete: Vehicle has 25 passengers
```

**7:05 AM - Departing Depot:**

```text
Vehicle Status: Leaving depot, entering route
Conductor Logic: is_at_depot() → FALSE
Conductor Action: Query ROUTE RESERVOIR
Query Parameters: route_id="ROUTE_1A", direction="outbound", search_radius=1000m
```

**7:10 AM - Holetown Junction (On Route):**

```text
Vehicle Status: Traveling outbound, 5km from depot
Conductor Logic: is_at_depot() → FALSE
Conductor Action: Query ROUTE RESERVOIR (continuous)
Query Result: 3 OUTBOUND passengers at bus stop 200m ahead
Conductor Decision: Stop and pick them up
New Passenger Count: 28
```

**7:15 AM - St. James (On Route):**

```text
Vehicle Status: Traveling outbound, 8km from depot
Conductor Logic: is_at_depot() → FALSE
Conductor Action: Query ROUTE RESERVOIR
Query Result: 2 INBOUND passengers at bus stop (going opposite direction)
Conductor Decision: IGNORE (wrong direction, not our passengers)
Query Result: 1 OUTBOUND passenger 150m ahead
Conductor Decision: Stop and pick up
New Passenger Count: 29
```

**7:20 AM - Speightstown Terminus (End of Route):**

```text
Vehicle Status: Reached end of route, passengers alighting
Conductor Logic: Check passenger destinations
All passengers get off (reached their destinations)
Vehicle now empty, ready to return INBOUND
```

**7:25 AM - Returning to Depot (INBOUND):**

```text
Vehicle Status: Traveling INBOUND (back to depot)
Conductor Logic: is_at_depot() → FALSE
Conductor Action: Query ROUTE RESERVOIR
Query Parameters: direction="inbound" (NOW DIFFERENT!)
Query Result: 5 INBOUND passengers along route
Conductor Decision: Pick them up
```

**7:40 AM - Back at Bridgetown Depot:**

```text
Vehicle Status: Parked at depot
Conductor Logic: is_at_depot() → TRUE
Conductor Action: Query DEPOT RESERVOIR (again!)
Query Result: 18 new passengers waiting
Cycle repeats...
```

---

## 🔑 Key Differences

| Aspect | Depot Reservoir | Route Reservoir |
|--------|----------------|-----------------|
| **When Queried** | Vehicle AT depot | Vehicle ON route |
| **Passenger Direction** | OUTBOUND only | BIDIRECTIONAL |
| **Search Criteria** | depot_id + route_id | route_id + direction + proximity |
| **Search Radius** | 500m (tight) | 1000m (wider) |
| **Queue Type** | FIFO queue | Spatial grid |
| **Passenger Location** | At depot/terminal | Along route (bus stops, streets) |
| **Boarding Pattern** | All at once | One stop at a time |

---

## 🎯 Why Two Reservoirs?

### **Different Behaviors, Different Data Structures**

**Depot Reservoir:**

- Passengers **start journeys** here
- All going **same direction** (outbound from depot)
- **FIFO fairness** (first come, first served)
- **Batch boarding** (load many at once)
- Location known (depot GPS coordinates)

**Route Reservoir:**

- Passengers **anywhere along route**
- Going **both directions** (to/from depot)
- **Proximity matching** (nearest to vehicle)
- **Incremental pickup** (stop-by-stop)
- Location varies (distributed along route)

**It would be inefficient to combine them!**

---

## ✅ Confirmation Summary

**Your statement:**
> "Conductor only requests from depot reservoir when parked, and when on route, from the route reservoir?"

**Answer:** **ABSOLUTELY CORRECT!** ✅

**Logic:**

```text
IF vehicle.is_at_depot():
    query(depot_reservoir)
ELSE:
    query(route_reservoir)
```

**Simple as that!**

---

## 🚀 Additional Detail: The "is_at_depot()" Check

```python
def is_at_depot(self, position: tuple[float, float]) -> bool:
    """Check if vehicle is currently at a depot"""
    
    # Get all depots on this route
    depots = self.get_route_depots(self.vehicle.route_id)
    
    for depot in depots:
        distance = calculate_distance(position, depot.location)
        
        # Within 100m of depot = "at depot"
        if distance < 100:
            self.current_depot = depot.depot_id
            return True
    
    return False
```

**Parameters:**

- Distance threshold: **< 100 meters** = AT depot
- Checks all depots on route (some routes have multiple terminals)
- Updates `current_depot` when detected

---

## 📊 Query Frequency

**Depot Query:**

- Only when `is_at_depot() == True`
- Typically: 2-3 times per route cycle (start depot, end depot)
- Duration: ~2-5 minutes per depot stop

**Route Query:**

- Continuously when `is_at_depot() == False`
- Every 1 second while traveling
- Duration: ~20-40 minutes per route leg

**Result:** Route queries are much more frequent!

---

## 🎬 Final Confirmation

**Yes, you understand perfectly!**

1. ✅ **At Depot** → Query **Depot Reservoir**
2. ✅ **On Route** → Query **Route Reservoir**
3. ✅ **Two separate data sources** for two different scenarios
4. ✅ **Direction matters** for route queries (not depot)
5. ✅ **Simple boolean check** determines which to query

**This is the core logic of the intelligent conductor!** 🚌🧠

---

## 💡 Bonus Insight

The conductor could theoretically query both simultaneously, but:

**❌ Why Not Query Both?**

- Inefficient (unnecessary network traffic)
- Confusing (mixing depot + route passengers)
- Wrong behavior (depot passengers at depot, route passengers on route)
- Slower (double latency)

**✅ Why Separate?**

- Efficient (only query what's relevant)
- Clear (depot vs. route logic separated)
- Correct (right passengers at right time)
- Fast (single query per update)

**Separation of concerns = Better design!** 🎯
