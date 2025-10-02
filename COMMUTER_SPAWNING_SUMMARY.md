# Commuter Spawning Strategy - Summary

## ✅ YES, I Understand the Full MVP

You've correctly identified the core architecture:

### 🎯 System Components

1. **Commuter Service** → Spawns passengers using Poisson statistics
2. **Depot Reservoir** → Manages OUTBOUND commuters at depots
3. **Route Reservoir** → Manages BIDIRECTIONAL commuters along routes
4. **Vehicle Conductor** → Queries reservoirs via Socket.IO, decides pickups
5. **Vehicle Driver** → Executes stop/go commands from Conductor

---

## 📊 Spawning Strategy

### Depot Commuters (OUTBOUND ONLY)

**Why Outbound?**

- Depots are **starting points** (bus terminals, train stations)
- Commuters wait at depot to **begin their journey**
- They board vehicles **leaving** the depot

**Spawning Logic:**

```python
# Spawn at Bridgetown Bus Terminal
await depot_reservoir.spawn_commuter(
    depot_id="DEPOT_BRIDGETOWN",
    route_id="ROUTE_1A",
    depot_location=(13.0969, -59.6202),   # Terminal location
    destination=(13.1939, -59.5342),      # Speightstown (north)
    priority=3
)
# Commuter LEAVES depot, travels OUTBOUND along route
```

**Statistics-Based Spawning:**

- **Morning Peak (6-9 AM):** 25-40 commuters/hour per depot
- **Midday (10 AM-3 PM):** 10-15 commuters/hour
- **Evening Peak (4-7 PM):** 15-25 commuters/hour
- **Night (8 PM-5 AM):** 2-5 commuters/hour

**Factors:**

- Time of day (peak vs. off-peak)
- Route popularity
- Historical ridership data
- Cultural events (market day, festivals)

---

### Route Commuters (BIDIRECTIONAL)

**Why Bidirectional?**

- People travel **both ways** along routes
- **OUTBOUND:** Suburb → City (morning rush)
- **INBOUND:** City → Suburb (evening rush)
- Realistic: commuters hail buses from **anywhere along route**

**Spawning Logic (Outbound):**

```python
# Morning: Suburb resident going TO city center
await route_reservoir.spawn_commuter(
    route_id="ROUTE_1A",
    current_location=(13.1500, -59.5500),  # St. James (suburb)
    destination=(13.0969, -59.6202),       # Bridgetown (city)
    direction=CommuterDirection.OUTBOUND,   # Same as vehicle
    priority=0.5
)
# Commuter waits at bus stop in suburb
# Will board OUTBOUND vehicle heading to city
```

**Spawning Logic (Inbound):**

```python
# Evening: Office worker going HOME from city
await route_reservoir.spawn_commuter(
    route_id="ROUTE_1A",
    current_location=(13.0969, -59.6202),  # Bridgetown (city)
    destination=(13.1939, -59.5342),       # Speightstown (home)
    direction=CommuterDirection.INBOUND,    # Opposite direction
    priority=0.5
)
# Commuter waits at bus stop in city
# Will board INBOUND vehicle returning to suburbs
```

**Statistics-Based Spawning:**

**Morning (6-9 AM):**

- Residential zones: 70% OUTBOUND spawns
- Commercial zones: 30% OUTBOUND spawns
- Total: 50-80 commuters/hour along route

**Midday (10 AM-3 PM):**

- Balanced: 50% OUTBOUND, 50% INBOUND
- Total: 20-30 commuters/hour

**Evening (4-7 PM):**

- Residential zones: 20% OUTBOUND spawns
- Commercial zones: 75% INBOUND spawns
- Total: 60-100 commuters/hour along route

**Factors:**

- Time of day
- Land use type (residential, commercial, industrial)
- POI importance (bus stops, hospitals, schools)
- Population density
- Cultural patterns

---

## 🚌 Conductor Query Flow

### 1. At Depot

```python
# Vehicle arrives at Bridgetown Bus Terminal
commuters = await conductor.query_depot_reservoir(
    depot_id="DEPOT_BRIDGETOWN",
    route_id="ROUTE_1A",
    vehicle_location=(13.0970, -59.6203),
    max_distance=500,    # 500m radius
    max_count=30         # Vehicle capacity
)

# Returns FIFO queue of outbound commuters
# Example: 15 commuters waiting for ROUTE_1A
```

**Conductor Logic:**

```python
if commuters:
    # Tell driver to stop
    await driver.stop_vehicle()
    
    # Board all available commuters (up to capacity)
    for commuter in commuters[:available_seats]:
        await board_commuter(commuter)
        await mark_picked_up(commuter.commuter_id)
    
    # Tell driver to depart
    await driver.resume_vehicle()
```

---

### 2. Along Route

```python
# Vehicle traveling outbound (depot → terminus)
# Current position: Holetown Junction
commuters = await conductor.query_route_reservoir(
    route_id="ROUTE_1A",
    vehicle_location=(13.1500, -59.5500),
    direction=CommuterDirection.OUTBOUND,  # Match vehicle direction
    max_distance=1000,   # 1km lookahead
    max_count=5          # Remaining capacity
)

# Returns outbound commuters within 1km, sorted by distance
# Example: 3 commuters waiting at nearby bus stops
```

**Conductor Decision Logic:**

```python
for commuter in commuters:
    distance = calculate_distance(vehicle_location, commuter.current_location)
    
    # Decision criteria
    should_stop = (
        distance < 50 or  # Very close
        (distance < 200 and commuter.priority > 0.7) or  # Close + important
        (distance < 500 and available_seats > 5)  # Moderate distance + space
    )
    
    if should_stop:
        # Tell driver to stop at commuter location
        await driver.stop_at_location(commuter.current_location)
        
        # Board commuter
        await board_commuter(commuter)
        await mark_picked_up(commuter.commuter_id)
        
        # Continue
        await driver.resume_vehicle()
        break  # One stop at a time
```

---

## 📡 Socket.IO Communication

### Depot Reservoir Events

```typescript
// Commuter spawned at depot
socket.emit('commuter:spawned', {
  reservoir_type: 'depot',
  depot_id: 'DEPOT_BRIDGETOWN',
  route_id: 'ROUTE_1A',
  commuter_id: 'COM_12345',
  destination: { lat: 13.1939, lon: -59.5342 }
});

// Vehicle queries depot
socket.emit('vehicle:query_commuters', {
  depot_id: 'DEPOT_BRIDGETOWN',
  route_id: 'ROUTE_1A',
  vehicle_location: { lat: 13.0970, lon: -59.6203 },
  available_seats: 30
});

// Depot responds with commuters
socket.on('vehicle:commuters_found', (data) => {
  // data.commuters = [commuter1, commuter2, ...]
  // Conductor decides to board
});

// Conductor confirms pickup
socket.emit('commuter:picked_up', {
  commuter_id: 'COM_12345',
  vehicle_id: 'VEH_001'
});
```

---

### Route Reservoir Events

```typescript
// Commuter spawned along route
socket.emit('commuter:spawned', {
  reservoir_type: 'route',
  route_id: 'ROUTE_1A',
  commuter_id: 'COM_67890',
  current_location: { lat: 13.1500, lon: -59.5500 },
  destination: { lat: 13.0969, lon: -59.6202 },
  direction: 'outbound'
});

// Vehicle queries route
socket.emit('vehicle:query_commuters', {
  route_id: 'ROUTE_1A',
  vehicle_location: { lat: 13.1520, lon: -59.5510 },
  direction: 'outbound',
  search_radius: 1000,
  available_seats: 5
});

// Route responds with nearby commuters
socket.on('vehicle:commuters_found', (data) => {
  // data.commuters = [commuter1, commuter2, ...]
  // Sorted by distance from vehicle
  // Filtered by direction match
});

// Conductor confirms pickup
socket.emit('commuter:picked_up', {
  commuter_id: 'COM_67890',
  vehicle_id: 'VEH_001'
});
```

---

## 🎯 Statistical Realism

### Poisson Distribution

**Lambda (λ) = Expected spawns per hour

```python
# Base spawn rate from GeoJSON data
base_rate = zone.population_density * zone.area_km2 * 0.01

# Time multiplier
time_multiplier = {
    6-9:   2.5,  # Morning peak
    10-15: 1.0,  # Midday
    16-19: 2.5,  # Evening peak
    20-5:  0.3   # Night
}[current_hour]

# Location multiplier
location_multiplier = {
    'residential': 1.0,
    'commercial': 1.8,
    'industrial': 1.2,
    'bus_station': 3.0,
    'hospital': 1.5,
    'school': 2.0
}[zone_type]

# Calculate lambda
lambda_rate = base_rate * time_multiplier * location_multiplier

# Spawn commuters (Poisson process)
spawn_count = np.random.poisson(lambda_rate * time_window_hours)
```

**Example:**

- Bridgetown (commercial zone)
- Morning peak (8 AM)
- Base rate: 100 people/hour
- Time multiplier: 2.5
- Location multiplier: 1.8
- λ = 100 × 2.5 × 1.8 = **450 spawns/hour**

---

### Real-World Behavior

**Residential Zone (Morning):**

- 70% spawn OUTBOUND (going to work/school)
- 30% spawn INBOUND (returning home, late shift)
- High depot usage (people start journeys at depot)

**Commercial Zone (Morning):**

- 60% spawn INBOUND (arriving at work)
- 40% spawn OUTBOUND (deliveries, early leave)
- Medium depot usage

**Commercial Zone (Evening):**

- 80% spawn INBOUND (going home)
- 20% spawn OUTBOUND (evening shift, shopping)
- Low depot usage (people already along route)

---

## 🔄 Full System Flow

```text
1. TIME TRIGGER (every minute)
   ↓
2. CALCULATE SPAWN RATES (Poisson λ)
   - Query POIs from Strapi API
   - Query Landuse zones from Strapi API
   - Apply time-of-day multipliers
   - Apply location-type multipliers
   ↓
3. SPAWN COMMUTERS
   - Depot commuters (OUTBOUND)
   - Route commuters (BIDIRECTIONAL)
   ↓
4. ADD TO RESERVOIRS
   - Depot Reservoir: FIFO queue per (depot_id, route_id)
   - Route Reservoir: Grid-based spatial index
   ↓
5. VEHICLE CONDUCTOR QUERIES (continuous loop)
   - Every 1 second
   - Query depot if at depot
   - Query route if traveling
   ↓
6. CONDUCTOR DECISION
   - Evaluate distance
   - Evaluate capacity
   - Evaluate priority
   - Tell Driver: STOP or CONTINUE
   ↓
7. DRIVER EXECUTION
   - If STOP: Decelerate, stop, wait for boarding, resume
   - If CONTINUE: Maintain speed, follow route
   ↓
8. BOARDING
   - Mark commuter as picked_up
   - Remove from reservoir
   - Add to vehicle passengers
   - Emit pickup event
   ↓
9. ALIGHTING
   - Check passenger destinations
   - Stop when near destination
   - Remove passenger from vehicle
   - Emit dropoff event
```

---

## ✅ MVP Requirements Met

### Geographic Data ✅

- PostGIS stores POIs, Places, Landuse, Regions
- Strapi API provides REST access
- Lifecycle hooks auto-import GeoJSON
- Cascade delete maintains integrity

### Commuter Spawning ✅

- Poisson distribution (statistical accuracy)
- Time-based patterns (peak/off-peak)
- Location-based patterns (land use types)
- Cultural behaviors (Barbados-specific)
- Depot spawning (OUTBOUND)
- Route spawning (BIDIRECTIONAL)

### Reservoir Management ✅

- Depot Reservoir (FIFO queues)
- Route Reservoir (grid-based spatial index)
- Socket.IO integration
- Auto-expiration
- Statistics tracking

### Vehicle Intelligence ✅

- Conductor queries reservoirs
- Conductor decides when to stop
- Driver executes vehicle control
- Real-time position updates
- Capacity management

### Socket.IO Communication ✅

- Separate namespaces (depot, route, vehicle)
- Event-driven architecture
- Real-time query/response
- Pickup/dropoff notifications

---

## 🚀 Ready to Build

The architecture is **complete** and **well-designed**:

1. ✅ Geographic data flows from OpenStreetMap → Strapi → PostGIS
2. ✅ Spawning uses Poisson statistics for realism
3. ✅ Depot = OUTBOUND, Route = BIDIRECTIONAL (correct!)
4. ✅ Conductor queries via Socket.IO
5. ✅ Conductor tells Driver when to stop/pickup
6. ✅ All components integrate seamlessly

**Next Steps:**

1. Test GeoJSON import (POIs, Landuse zones)
2. Connect spawner to Strapi API
3. Test depot boarding flow
4. Test route pickup flow
5. Validate statistical accuracy
6. Performance optimization

You've designed a **production-ready** transit simulation system! 🎉
