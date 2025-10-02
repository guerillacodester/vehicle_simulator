# ArkNet Transit System - Full MVP Architecture

## 🎯 System Overview

The ArkNet Transit System simulates realistic public transportation with statistically-accurate passenger spawning based on real-world geographic data, land use patterns, and cultural behaviors.

---

## 🏗️ Architecture Components

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         STRAPI HUB (Node.js)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   REST API       │  │  Socket.IO Hub   │  │  Admin UI        │ │
│  │  (Geographic     │  │  (Real-time      │  │  (GeoJSON        │ │
│  │   Data)          │  │   Events)        │  │   Upload)        │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│         ▲                      ▲                       │            │
└─────────┼──────────────────────┼───────────────────────┼────────────┘
          │                      │                       │
          │                      │                       ▼
          │                      │              PostgreSQL + PostGIS
          │                      │              (Geographic Data Store)
          │                      │
┌─────────┼──────────────────────┼───────────────────────────────────┐
│         │                      │           PYTHON SERVICES          │
│         │                      │                                    │
│  ┌──────▼──────────┐  ┌────────▼────────┐  ┌────────────────────┐ │
│  │  COMMUTER       │  │   DEPOT         │  │   ROUTE            │ │
│  │  SERVICE        │  │   RESERVOIR     │  │   RESERVOIR        │ │
│  │                 │  │                 │  │                    │ │
│  │ • Poisson       │  │ • Outbound      │  │ • Bidirectional    │ │
│  │   Spawning      │  │   Commuters     │  │   Commuters        │ │
│  │ • GeoJSON       │  │ • FIFO Queue    │  │ • Grid-based       │ │
│  │   Integration   │  │ • Proximity     │  │   Indexing         │ │
│  │ • Statistics    │  │   Query         │  │ • Proximity        │ │
│  │ • Behaviors     │  │                 │  │   Query            │ │
│  └─────────────────┘  └─────────────────┘  └────────────────────┘ │
│         │                      │                       │            │
│         └──────────────────────┴───────────────────────┘            │
│                                │                                    │
│                                ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              VEHICLE SIMULATOR (Python)                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │  CONDUCTOR   │  │   DRIVER     │  │   VEHICLE        │  │   │
│  │  │              │  │              │  │   STATE          │  │   │
│  │  │ • Query      │  │ • Route      │  │                  │  │   │
│  │  │   Commuters  │  │   Following  │  │ • Position       │  │   │
│  │  │ • Boarding   │  │ • Stop/Go    │  │ • Speed          │  │   │
│  │  │   Logic      │  │   Control    │  │ • Capacity       │  │   │
│  │  │ • Pickup     │  │              │  │ • Passengers     │  │   │
│  │  │   Decision   │  │              │  │                  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### 1. Geographic Data Import (Strapi → PostgreSQL)

```text
Admin UI → Upload GeoJSON Files → Strapi Lifecycle Hooks → PostGIS Database
```

**Files Uploaded per Country:**

- `pois_geojson_file` → POIs (bus stations, hospitals, schools, markets)
- `place_names_geojson_file` → Places (cities, towns, villages)
- `landuse_geojson_file` → Landuse zones (residential, commercial, industrial)
- `regions_geojson_file` → Administrative boundaries (states, districts)

**Processing:**

- Chunked imports (100 records/batch)
- Coordinate validation
- OSM type mapping
- Centroid calculation for polygons
- GeoJSON geometry storage

---

### 2. Commuter Spawning (Poisson Distribution)

```text
Time + Location + Statistics → Poisson Rate → Spawn Commuter → Reservoir
```

**Spawning Algorithm:**

```python
# Poisson lambda (expected spawns per hour) = f(time, location, land_use)
lambda_rate = base_rate * time_multiplier * location_multiplier

# Statistical spawning
spawn_count = np.random.poisson(lambda_rate * time_window_hours)

# Spawn location selection
for _ in range(spawn_count):
    if spawn_type == "depot":
        spawn_at_depot()  # OUTBOUND only
    else:
        spawn_along_route()  # BIDIRECTIONAL
```

**Factors Affecting Spawn Rate:**

1. **Time of Day:**
   - Peak hours (6-9 AM, 4-7 PM): 2.5x multiplier
   - Off-peak: 1.0x multiplier
   - Late night: 0.3x multiplier

2. **Location Type (from Landuse):**
   - Residential: High morning outbound, high evening inbound
   - Commercial: High all day, very high evening
   - Industrial: Steady daytime
   - Education: Morning/afternoon peaks

3. **POI Importance:**
   - Bus stations: 3.0x multiplier
   - Hospitals: 1.5x multiplier
   - Schools: 2.0x (during school hours)
   - Markets: 1.8x

4. **Population Density:**
   - High density (city): 10 spawns/hour/km²
   - Medium density (town): 5 spawns/hour/km²
   - Low density (village): 2 spawns/hour/km²

---

### 3. Depot Reservoir (Outbound Commuters)

**Purpose:** Manage commuters waiting at depot (bus terminal, train station)

**Characteristics:**

- **Direction:** OUTBOUND only (leaving depot to go along route)
- **Queue Type:** FIFO (First In, First Out)
- **Organization:** One queue per `(depot_id, route_id)` combination

**Spawning:**

```python
# Spawn commuter at depot
commuter = await depot_reservoir.spawn_commuter(
    depot_id="DEPOT_BRIDGETOWN",
    route_id="ROUTE_1A",
    depot_location=(13.0969, -59.6202),  # Bridgetown Bus Terminal
    destination=(13.1939, -59.5342),     # Speightstown
    priority=3,  # 1=low, 5=high
    max_wait_time=timedelta(minutes=30)
)

# Commuter added to depot queue
# Waits for vehicle on ROUTE_1A to arrive and query
```

**Vehicle Query (Conductor):**

```python
# Vehicle arrives at depot
commuters = depot_reservoir.query_commuters_sync(
    depot_id="DEPOT_BRIDGETOWN",
    route_id="ROUTE_1A",
    vehicle_location=(13.0970, -59.6203),  # Current GPS position
    max_distance=500,  # 500m radius search
    max_count=30  # Vehicle capacity
)

# Returns FIFO-ordered list of commuters within 500m
# Conductor tells Driver to stop/pickup
```

**Boarding Flow:**

```text
1. Vehicle approaches depot
2. Conductor queries depot reservoir
3. Depot returns available commuters (FIFO, proximity-filtered)
4. Conductor evaluates capacity
5. Conductor tells Driver: "Stop at depot"
6. Driver stops vehicle
7. Conductor triggers boarding
8. Commuters marked as picked_up
9. Commuters removed from depot reservoir
10. Vehicle departs
```

---

### 4. Route Reservoir (Bidirectional Commuters)

**Purpose:** Manage commuters along route paths (at bus stops, on streets)

**Characteristics:**

- **Direction:** BIDIRECTIONAL (inbound + outbound)
- **Organization:** Grid-based spatial indexing (~1km cells)
- **Query:** Proximity-based (vehicle location + direction + radius)

**Spawning (Outbound):**

```python
# Commuter spawns at bus stop along route
# Going FROM suburb TO city center
commuter = await route_reservoir.spawn_commuter(
    route_id="ROUTE_1A",
    current_location=(13.1500, -59.5500),  # St. James (suburb)
    destination=(13.0969, -59.6202),       # Bridgetown (city center)
    direction=CommuterDirection.OUTBOUND,   # Same direction as vehicle
    priority=0.5,
    nearest_stop={"stop_id": "STOP_45", "name": "Holetown Junction"}
)
```

**Spawning (Inbound):**

```python
# Commuter spawns in city center
# Going FROM city TO suburb (return journey)
commuter = await route_reservoir.spawn_commuter(
    route_id="ROUTE_1A",
    current_location=(13.0969, -59.6202),  # Bridgetown (city center)
    destination=(13.1939, -59.5342),       # Speightstown (north coast)
    direction=CommuterDirection.INBOUND,    # Opposite direction
    priority=0.5,
    nearest_stop={"stop_id": "STOP_12", "name": "Fairchild Street"}
)
```

**Vehicle Query (Conductor):**

```python
# Vehicle traveling outbound (depot → terminus)
outbound_commuters = route_reservoir.query_commuters_sync(
    route_id="ROUTE_1A",
    vehicle_location=(13.1200, -59.5800),  # Current GPS position
    direction=CommuterDirection.OUTBOUND,   # Match vehicle direction
    max_distance=1000,  # 1km radius search
    max_count=5  # Remaining capacity
)

# Returns outbound commuters within 1km, sorted by distance
# Conductor evaluates if worth stopping
```

**Boarding Flow (Along Route):**

```text
1. Vehicle traveling along route (outbound)
2. Conductor periodically queries route reservoir
3. Route returns eligible commuters (matching direction, proximity)
4. Conductor evaluates:
   - Distance to commuter (<100m = definitely stop)
   - Remaining capacity
   - Commuter priority
   - Schedule adherence
5. IF stop_worthy:
   - Conductor tells Driver: "Stop ahead - commuter at 50m"
   - Driver decelerates, stops
   - Conductor triggers boarding
   - Commuters marked as picked_up
   - Commuters removed from route reservoir
6. Vehicle continues
```

---

### 5. Conductor Logic (Decision Making)

**Role:** Acts as vehicle's brain for passenger operations

**Responsibilities:**

1. Query reservoirs for commuters
2. Decide when to stop
3. Coordinate boarding/alighting
4. Manage capacity
5. Communicate with Driver

**Decision Algorithm:**

```python
class VehicleConductor:
    async def update_loop(self):
        """Main conductor logic loop"""
        while self.running:
            # Get current state
            position = self.vehicle.get_position()
            capacity_remaining = self.vehicle.capacity - len(self.vehicle.passengers)
            route_id = self.vehicle.route_id
            direction = self.vehicle.direction
            
            # 1. CHECK DEPOT (if at depot)
            if self.is_at_depot(position):
                depot_commuters = await self.query_depot_reservoir(
                    depot_id=self.current_depot,
                    route_id=route_id,
                    vehicle_location=position,
                    max_count=capacity_remaining
                )
                
                if depot_commuters:
                    await self.execute_depot_boarding(depot_commuters)
            
            # 2. CHECK ROUTE (if traveling)
            else:
                route_commuters = await self.query_route_reservoir(
                    route_id=route_id,
                    vehicle_location=position,
                    direction=direction,
                    max_count=capacity_remaining,
                    max_distance=1000  # 1km lookahead
                )
                
                if route_commuters:
                    # Evaluate each commuter
                    for commuter in route_commuters:
                        distance = self.calculate_distance(position, commuter.current_location)
                        
                        if self.should_stop_for_commuter(commuter, distance, capacity_remaining):
                            await self.execute_route_pickup(commuter)
                            break  # One stop at a time
            
            # 3. CHECK ALIGHTING
            await self.check_passenger_alighting(position)
            
            await asyncio.sleep(1)  # Update every second
    
    def should_stop_for_commuter(self, commuter, distance, capacity_remaining):
        """Decide if vehicle should stop"""
        # Must have capacity
        if capacity_remaining <= 0:
            return False
        
        # Very close = always stop
        if distance < 50:
            return True
        
        # Close + high priority = stop
        if distance < 200 and commuter.priority > 0.7:
            return True
        
        # Moderate distance + medium priority + good capacity
        if distance < 500 and commuter.priority > 0.5 and capacity_remaining > 5:
            return True
        
        # Don't stop if too far
        return False
    
    async def execute_depot_boarding(self, commuters):
        """Board commuters at depot"""
        # Tell driver to stop
        await self.driver.stop_vehicle()
        
        # Wait for stop
        await asyncio.sleep(2)
        
        # Board each commuter
        for commuter in commuters:
            await self.board_commuter(commuter)
            await asyncio.sleep(0.5)  # Boarding time per person
        
        # Emit boarding complete event
        await self.emit_event("boarding:completed", {
            "vehicle_id": self.vehicle.id,
            "count": len(commuters),
            "location": "depot"
        })
        
        # Tell driver to continue
        await self.driver.resume_vehicle()
    
    async def execute_route_pickup(self, commuter):
        """Pick up commuter along route"""
        # Tell driver to stop ahead
        await self.driver.stop_at_location(commuter.current_location)
        
        # Wait for stop
        await asyncio.sleep(3)
        
        # Board commuter
        await self.board_commuter(commuter)
        
        # Emit pickup event
        await self.emit_event("commuter:picked_up", {
            "vehicle_id": self.vehicle.id,
            "commuter_id": commuter.commuter_id,
            "location": commuter.current_location
        })
        
        # Tell driver to continue
        await self.driver.resume_vehicle()
```

---

### 6. Driver Logic (Vehicle Control)

**Role:** Executes physical vehicle movement

**Responsibilities:**

1. Follow route path
2. Obey speed limits
3. Stop when commanded
4. Accelerate/decelerate smoothly
5. Update GPS position

**Control Algorithm:**

```python
class VehicleDriver:
    async def drive_loop(self):
        """Main driving loop"""
        while self.running:
            # Check for stop commands
            if self.should_stop:
                await self.execute_stop()
                continue
            
            # Follow route
            next_waypoint = self.get_next_waypoint()
            
            # Calculate heading
            heading = self.calculate_bearing(self.position, next_waypoint)
            
            # Adjust speed
            target_speed = self.get_target_speed()
            self.speed = self.smooth_acceleration(self.speed, target_speed)
            
            # Move vehicle
            new_position = self.calculate_new_position(
                self.position,
                heading,
                self.speed,
                time_delta=1.0
            )
            
            self.position = new_position
            
            # Emit position update
            await self.emit_position_update()
            
            await asyncio.sleep(1)
    
    async def execute_stop(self):
        """Stop the vehicle"""
        # Decelerate to zero
        while self.speed > 0:
            self.speed = max(0, self.speed - 2)  # 2 m/s² deceleration
            await asyncio.sleep(0.1)
        
        # Wait for conductor signal
        while self.should_stop:
            await asyncio.sleep(0.5)
```

---

## 🔄 Socket.IO Event Flow

### Namespaces

1. **`/depot-reservoir`** - Depot commuter management
2. **`/route-reservoir`** - Route commuter management
3. **`/vehicle-events`** - Vehicle state and commands

### Event Sequences

#### Depot Boarding Sequence

```text
1. Commuter Service → /depot-reservoir
   EVENT: commuter:spawned
   DATA: {commuter_id, depot_id, route_id, destination}

2. Vehicle Conductor → /depot-reservoir
   EVENT: vehicle:query_commuters
   DATA: {depot_id, route_id, vehicle_location, available_seats}

3. Depot Reservoir → /depot-reservoir
   EVENT: vehicle:commuters_found
   DATA: {commuters: [...], total_count}

4. Vehicle Conductor → /depot-reservoir
   EVENT: commuter:picked_up
   DATA: {commuter_id, vehicle_id}

5. Depot Reservoir → /depot-reservoir
   EVENT: depot_reservoir:updated
   DATA: {depot_id, route_id, queue_length}
```

#### Route Pickup Sequence

```text
1. Commuter Service → /route-reservoir
   EVENT: commuter:spawned
   DATA: {commuter_id, route_id, current_location, direction}

2. Vehicle Conductor → /route-reservoir
   EVENT: vehicle:query_commuters
   DATA: {route_id, vehicle_location, direction, search_radius, available_seats}

3. Route Reservoir → /route-reservoir
   EVENT: vehicle:commuters_found
   DATA: {commuters: [...], total_count}

4. Vehicle Conductor → /route-reservoir
   EVENT: commuter:picked_up
   DATA: {commuter_id, vehicle_id}

5. Route Reservoir → /route-reservoir
   EVENT: route_reservoir:updated
   DATA: {route_id, direction, total_commuters}
```

---

## 📈 Statistical Accuracy

### Real-World Behavior Modeling

**1. Temporal Patterns (Time-based)

```python
# Morning rush (6-9 AM)
- Residential → Commercial: HIGH
- Depot → Routes: VERY HIGH
- Direction: Mostly OUTBOUND

# Midday (10 AM - 3 PM)
- Commercial → Commercial: MEDIUM
- POI-based: STEADY
- Direction: BALANCED

# Evening rush (4-7 PM)
- Commercial → Residential: HIGH
- Routes → Depot: HIGH  
- Direction: Mostly INBOUND

# Night (8 PM - 5 AM)
- All zones: LOW
- Entertainment → Residential: MEDIUM
- Direction: MOSTLY INBOUND
```

**2. Spatial Patterns (Location-based)

```python
# Residential zones
spawn_weight = {
    "morning_outbound": 2.5,    # Going to work
    "evening_inbound": 2.0,     # Coming home
    "midday": 0.5               # Low activity
}

# Commercial zones
spawn_weight = {
    "morning_inbound": 1.5,     # Arriving at work
    "midday": 1.8,              # Lunch, shopping
    "evening_outbound": 2.5     # Leaving work
}

# Industrial zones
spawn_weight = {
    "morning_inbound": 2.0,     # Shift workers arriving
    "evening_outbound": 2.0,    # Shift workers leaving
    "night": 0.8                # Night shift
}
```

**3. Cultural Behaviors (Barbados-specific)

```python
# Market day (Saturday)
if day_of_week == "Saturday":
    market_spawn_multiplier = 3.0
    
# Sunday church
if day_of_week == "Sunday" and hour in [7, 8, 9]:
    religious_poi_multiplier = 4.0
    
# Crop Over Festival (July-August)
if is_festival_season:
    evening_spawn_multiplier = 2.5
```

---

## 🎯 MVP Success Metrics

### System Performance

- ✅ Spawn 100+ commuters/hour during peak
- ✅ Query response time < 100ms
- ✅ Vehicle pickup decision < 1 second
- ✅ Support 50 concurrent vehicles
- ✅ Handle 1000+ active commuters

### Statistical Accuracy

- ✅ Peak/off-peak ratio: 2.5:1
- ✅ Residential morning outbound: 70%
- ✅ Commercial evening outbound: 65%
- ✅ Depot queue length: 5-30 commuters
- ✅ Route commuter density: 2-5 per km

### User Experience

- ✅ Realistic boarding patterns
- ✅ Natural stop decisions
- ✅ Cultural behavior authenticity
- ✅ Geographic accuracy
- ✅ Temporal pattern matching

---

## 🚀 Next Implementation Steps

1. **Configure GeoData Permissions** ✅
2. **Test GeoJSON Import Flow** ⏳
3. **Connect Spawner to Database** ⏳
4. **Implement Conductor Query Logic** ⏳
5. **Test Depot Boarding Flow** ⏳
6. **Test Route Pickup Flow** ⏳
7. **Add Statistical Validation** ⏳
8. **Performance Optimization** ⏳

---

## 📝 Key Technical Decisions

1. **Bidirectional Route Commuters:** Realistic because people travel both TO and FROM city center
2. **Depot = Outbound Only:** Depots are starting points, not destinations
3. **Grid-based Spatial Indexing:** Fast proximity queries for route reservoir
4. **FIFO Depot Queues:** Fair boarding order
5. **Poisson Distribution:** Statistical realism based on expected rates
6. **Conductor/Driver Separation:** Clean separation of decision vs. execution
7. **Socket.IO Namespaces:** Isolated event streams for depot vs. route
8. **PostGIS Storage:** Efficient geographic queries and calculations
