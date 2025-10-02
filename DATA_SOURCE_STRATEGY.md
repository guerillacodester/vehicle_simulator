# Data Source Strategy for Spawning Engine

## Overview

The spawning engine needs data from two sources: **Strapi API** (operational data) and **GeoJSON files** (geometric/static data). This document defines what comes from where.

---

## Data Source Matrix

| Data Type | Source | Reason | Update Frequency |
|-----------|--------|--------|------------------|
| **Route Geometry** | GeoJSON | Complex line strings, large files | Rarely (route redesign) |
| **Depot Locations** | Strapi API | Operational status needed | Occasionally (new depots) |
| **Bus Stop Locations** | GeoJSON | Many points, spatial queries | Rarely (stop changes) |
| **Route Metadata** | Strapi API | Name, schedule, active status | Frequently (schedule updates) |
| **Vehicle Assignments** | Strapi API | Real-time operational data | Very frequently (live) |
| **Spawn Rate Config** | Config File | Tunable parameters | As needed (tuning) |
| **Time Patterns** | Config File | Rush hour definitions | Seasonally |

---

## Detailed Breakdown

### **From Strapi API** (Real-time Operational Data)

#### 1. **Depot Information**

```javascript
GET /api/depots?populate=*

Response:
{
  "data": [
    {
      "id": 1,
      "attributes": {
        "name": "Central Depot",
        "code": "DEPOT_001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "capacity": 50,
        "status": "active",  // operational, maintenance, closed
        "routes": [...]      // associated routes
      }
    }
  ]
}
```

**Use Case**:

- Spawn commuters only at **active** depots
- Adjust spawn rates based on **capacity**
- Filter by **assigned routes**

#### 2. **Route Operational Status**

```javascript
GET /api/routes?populate=*

Response:
{
  "data": [
    {
      "id": 1,
      "attributes": {
        "name": "Route A",
        "code": "ROUTE_A",
        "status": "active",      // active, suspended, maintenance
        "service_type": "regular", // express, limited, local
        "popularity": 0.85,      // 0-1 score for spawn weighting
        "depots": [...],         // starting depots
        "geometry": {...}        // may include basic geometry
      }
    }
  ]
}
```

**Use Case**:

- Spawn commuters only on **active** routes
- Weight spawn rates by **popularity**
- Filter by **service type** (express gets fewer stops)

#### 3. **Vehicle Availability** (Optional - for adaptive spawning)

```javascript
GET /api/vehicles?populate=*&filters[status]=active

Response:
{
  "data": [
    {
      "id": 1,
      "attributes": {
        "vehicle_number": "BUS-001",
        "route": { "id": 1, "code": "ROUTE_A" },
        "depot": { "id": 1, "code": "DEPOT_001" },
        "status": "active",
        "current_passengers": 15,
        "capacity": 40
      }
    }
  ]
}
```

**Use Case** (Advanced):

- Reduce spawning if **no vehicles** on route
- Increase spawning if vehicles are **under capacity**
- Balance demand across routes

---

### **From GeoJSON Files** (Static Geometric Data)

#### 1. **Route Geometry** (line strings)

```json
// data/routes/route_geometries.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "route_id": "ROUTE_A",
        "route_name": "Route A",
        "direction": "outbound",
        "length_km": 12.5
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-74.0060, 40.7128],  // Many coordinate pairs
          [-74.0055, 40.7130],
          // ... hundreds of points
        ]
      }
    }
  ]
}
```

**Use Case**:

- **Sample random points** along route for route spawning
- Calculate **distance-based spawn probabilities**
- Ensure commuters spawn **on actual route paths**

**Why GeoJSON?**

- ✅ Large line strings (hundreds of coordinates)
- ✅ Spatial operations (point sampling)
- ✅ Rarely changes
- ✅ Self-contained for offline development

#### 2. **Bus Stop Locations**

```json
// data/routes/bus_stops.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "stop_id": "STOP_001",
        "stop_name": "Main Street",
        "route_ids": ["ROUTE_A", "ROUTE_B"],
        "amenities": ["shelter", "bench"],
        "ridership": "high"  // high/medium/low
      },
      "geometry": {
        "type": "Point",
        "coordinates": [-74.0060, 40.7128]
      }
    }
  ]
}
```

**Use Case**:

- Spawn commuters **near bus stops** (more realistic)
- Weight by **ridership** levels
- Prefer stops with **amenities** (higher spawn probability)

**Why GeoJSON?**

- ✅ Many stop points (could be 100+ per route)
- ✅ Spatial queries (find nearest stop)
- ✅ Self-contained with properties
- ✅ Easy to visualize/edit

---

### **From Configuration Files** (Tunable Parameters)

#### 1. **Spawn Rate Configuration**

```python
# commuter_service/spawner_config.py

@dataclass
class SpawnerConfig:
    # Time-of-day patterns (multipliers)
    rush_hour_morning: tuple = (7, 9)      # 7am-9am
    rush_hour_evening: tuple = (17, 19)    # 5pm-7pm
    rush_hour_multiplier: float = 3.0      # 3x normal rate
    
    off_peak_multiplier: float = 0.3       # 30% of normal
    weekend_multiplier: float = 0.5        # 50% of normal
    
    # Base spawn rates (commuters per minute)
    depot_spawn_rate_base: float = 2.0     # 2 per minute
    route_spawn_rate_base: float = 1.0     # 1 per minute
    
    # Location-based multipliers
    urban_multiplier: float = 1.5          # Dense areas
    suburban_multiplier: float = 1.0       # Normal
    rural_multiplier: float = 0.5          # Sparse areas
    
    # Distribution settings
    spawn_distribution: str = "poisson"    # poisson, uniform, normal
    min_spawn_interval_seconds: float = 5.0
    max_spawn_interval_seconds: float = 300.0
```

---

## Proposed Architecture

### **Data Flow Diagram**

```text
┌─────────────────────────────────────────────────────────┐
│                  SPAWNING ENGINE                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐      ┌──────────────────┐       │
│  │ Depot Spawner    │      │ Route Spawner    │       │
│  └──────────────────┘      └──────────────────┘       │
│           │                         │                  │
│           ├─────────┬───────────────┤                  │
│           │         │               │                  │
│           ▼         ▼               ▼                  │
│  ┌────────────┐ ┌────────┐  ┌──────────────┐         │
│  │ Strapi API │ │ Config │  │ GeoJSON      │         │
│  │            │ │        │  │ Files        │         │
│  │ • Depots   │ │ • Rates│  │ • Geometries │         │
│  │ • Routes   │ │ • Times│  │ • Bus Stops  │         │
│  │ • Status   │ └────────┘  └──────────────┘         │
│  └────────────┘                                       │
│           │                         │                  │
│           ▼                         ▼                  │
│  ┌────────────────┐       ┌──────────────────┐       │
│  │ Depot          │       │ Route            │       │
│  │ Reservoir      │       │ Reservoir        │       │
│  └────────────────┘       └──────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### **Implementation Classes**

#### 1. **Data Providers** (Abstraction Layer)

```python
class DepotDataProvider:
    """Fetches depot data from Strapi API"""
    async def get_active_depots(self) -> List[Depot]:
        # GET /api/depots?filters[status]=active
        pass
    
    async def get_depots_for_route(self, route_id: str) -> List[Depot]:
        pass

class RouteDataProvider:
    """Combines Strapi API + GeoJSON data"""
    async def get_active_routes(self) -> List[Route]:
        # GET /api/routes?filters[status]=active
        pass
    
    def load_route_geometry(self, route_id: str) -> LineString:
        # Load from GeoJSON file
        pass
    
    def load_bus_stops(self, route_id: str) -> List[Point]:
        # Load from GeoJSON file
        pass
```

#### 2. **Spawning Strategies**

```python
class DepotSpawningStrategy:
    """Spawns commuters at depots using Strapi data"""
    
    def __init__(
        self, 
        depot_provider: DepotDataProvider,
        depot_reservoir: DepotReservoir,
        config: SpawnerConfig
    ):
        pass
    
    async def spawn_cycle(self):
        """
        1. Fetch active depots from Strapi
        2. Calculate spawn rate based on time-of-day
        3. Spawn commuters into depot reservoir
        """
        pass

class RouteSpawningStrategy:
    """Spawns commuters along routes using GeoJSON + Strapi"""
    
    def __init__(
        self,
        route_provider: RouteDataProvider,
        route_reservoir: RouteReservoir,
        config: SpawnerConfig
    ):
        pass
    
    async def spawn_cycle(self):
        """
        1. Fetch active routes from Strapi
        2. Load route geometry from GeoJSON
        3. Sample random points along route
        4. Bias towards bus stops (from GeoJSON)
        5. Calculate spawn rate based on time/location
        6. Spawn commuters into route reservoir
        """
        pass
```

---

## Benefits of Hybrid Approach

### ✅ **Performance**

- Strapi: Fast queries for operational data
- GeoJSON: No API overhead for geometric operations
- Cached geometry data (load once, use many times)

### ✅ **Flexibility**

- Update operational status in Strapi (real-time)
- Update routes/geometry in GeoJSON (rarely)
- Adjust spawn rates in config (tuning)

### ✅ **Offline Development**

- Can run with GeoJSON files only
- Mock Strapi API for testing
- No internet dependency for geometry

### ✅ **Scalability**

- Strapi handles real-time operational data
- GeoJSON handles bulk geometric data
- Separate concerns, separate optimization

### ✅ **Maintainability**

- Clear separation of concerns
- Easy to swap data sources
- Testable in isolation

---

## Implementation Phases

### **Phase 1: File-Based (Current Sprint)**

```python
# Use GeoJSON for everything initially
depot_provider = GeoJSONDepotProvider("data/routes/depots.geojson")
route_provider = GeoJSONRouteProvider("data/routes/")
```

### **Phase 2: Hybrid (Next Sprint)**

```python
# Combine Strapi API + GeoJSON
depot_provider = StrapiDepotProvider(api_url="http://localhost:1337")
route_provider = HybridRouteProvider(
    api_client=strapi_client,
    geojson_path="data/routes/"
)
```

### **Phase 3: Full API (Future)**

```python
# Everything from Strapi (if geometry moved to DB)
depot_provider = StrapiDepotProvider(api_url="...")
route_provider = StrapiRouteProvider(api_url="...")
```

---

## Recommendation

### **For This Sprint (Phase 2.3)**

**Start with GeoJSON-based implementation**:

- ✅ Faster to implement
- ✅ No API dependencies
- ✅ Self-contained testing
- ✅ Works offline

**Design with abstraction**:

- ✅ Use provider interfaces
- ✅ Easy to swap implementations
- ✅ Future-proof for Strapi integration

**Implementation Order**:

1. Create `GeoJSONDepotProvider` (reads depots.geojson)
2. Create `GeoJSONRouteProvider` (reads route_geometries.geojson)
3. Implement `DepotSpawningStrategy` (uses provider)
4. Implement `RouteSpawningStrategy` (uses provider + geometry)
5. Create `StatisticalSpawner` (orchestrates both)
6. Test with existing GeoJSON files

**Later (Phase 2.4 or 3)**:

- Implement `StrapiDepotProvider`
- Implement `HybridRouteProvider`
- Swap providers without changing spawning logic

---

## Questions for You

1. **Do you have the GeoJSON files ready?**
   - `data/routes/route_geometries.geojson`
   - `data/routes/depots.geojson`
   - `data/routes/bus_stops.geojson`

2. **Should we implement the provider abstraction now or later?**
   - Option A: Start with GeoJSON-only, refactor later
   - Option B: Build provider interface from the start

3. **What's the priority for Strapi integration?**
   - This sprint (Phase 2.3)?
   - Next sprint (Phase 3)?
   - Later?

4. **Any specific spawn rate requirements?**
   - Commuters per minute during rush hour?
   - Target total active commuters?
   - Performance limits?

Let me know your preferences and I'll start implementing! 🚀
