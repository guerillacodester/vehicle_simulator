# Conductor Spatial Awareness Analysis

## Current State Issues

### 1. ❌ Proximity Radius - Partially DB-Bound
**Status:** The `pickup_radius_km` IS stored in the database (`operational-configurations` table), but there are issues:

```python
# conductor.py line 89
pickup_radius_km: float = 0.2  # Hardcoded default
```

**Problem:**
- Default is hardcoded (0.2 km)
- Loaded from DB via `ConductorConfig.from_config_service()` 
- BUT initialization happens **after** conductor construction
- If DB connection fails, falls back to hardcoded value

**Database Configuration:**
```json
{
  "section": "conductor.proximity",
  "parameter": "pickup_radius_km",
  "value": "0.2",
  "constraints": {
    "min": 0.05,
    "max": 5.0,
    "step": 0.05,
    "unit": "kilometers"
  }
}
```

### 2. ✅ Distance Calculation - Internal Brain (Good)
**Status:** Conductor has its own haversine implementation

```python
# conductor.py line 956
def _calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
    """Calculate distance between two GPS points in kilometers."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))  # Earth radius in km
```

**Analysis:**
- ✅ Self-contained - no external dependency
- ✅ Fast - simple haversine formula
- ✅ Reliable - works offline
- ❌ Duplicated - same logic exists in multiple places

**Duplication Found:**
1. `conductor.py` - haversine implementation
2. `commuter_service/interfaces/http/passenger_crud.py` - haversine for `/api/passengers/nearby`
3. `commuter_service/infrastructure/database/passenger_repository.py` - haversine for proximity queries
4. `geospatial_service/api/spatial.py` - PostGIS `ST_Distance()` for spatial queries

### 3. ❌ Position Awareness - Driver-Dependent (Fragile)
**Status:** Conductor gets position from driver, NOT geospatial_service

```python
# conductor.py line 630
async def update_vehicle_position(self, latitude: float, longitude: float):
    """Update current vehicle GPS position for proximity calculations."""
    self.current_vehicle_position = (latitude, longitude)
```

**How Position is Obtained:**
```
GPS Device → Driver → Conductor.update_vehicle_position()
```

**Problems:**
1. **Tight Coupling:** Conductor depends on driver calling `update_vehicle_position()`
2. **No Validation:** Position could be stale, invalid, or missing
3. **No Geospatial Context:** Conductor doesn't know if it's on-route, at depot, etc.
4. **No Alternative Source:** If driver fails, conductor is blind

### 4. ❌ Geospatial Service - Not Used (Waste)
**Status:** `geospatial_service` exists with powerful capabilities but conductor doesn't use it

**Available Endpoints:**
```
GET /spatial/route-geometry/{route_id}
  - Full route coordinates
  - Total distance in meters
  - Segment data

GET /spatial/route-segment-distance/{route_id}
  - Distance between two points on route
  - "SINGLE SOURCE OF TRUTH for route segment distance"

GET /spatial/buildings-near-route
  - Buildings within buffer distance of route
  - Uses PostGIS ST_Distance

GET /spatial/nearest-poi
  - Find nearest point of interest
  - Optimized spatial queries
```

**Why This Matters:**
- Geospatial service uses **PostGIS spatial indexing** (fast!)
- Conductor uses **Python haversine loops** (slow for many passengers)
- Geospatial service has **route geometry awareness**
- Conductor has **no context** of route shape

## Recommended Architecture

### Solution 1: Hybrid Approach (Recommended)

```
┌─────────────────────────────────────────────────────┐
│                   CONDUCTOR                         │
│                                                     │
│  Position Awareness:                                │
│  ┌──────────────────────────────────────┐          │
│  │ Primary: GPS → Driver → Conductor    │          │
│  │ Fallback: Geospatial Service Cache   │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Distance Calculation:                              │
│  ┌──────────────────────────────────────┐          │
│  │ Internal: Haversine (fast, simple)   │          │
│  │ Used for: Quick proximity checks     │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Passenger Visibility:                              │
│  ┌──────────────────────────────────────┐          │
│  │ commuter_service API                 │          │
│  │ → Uses geospatial_service internally │          │
│  │ → PostGIS spatial queries            │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Proximity Radius:                                  │
│  ┌──────────────────────────────────────┐          │
│  │ DB: operational-configurations       │          │
│  │ Real-time updates via config service │          │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

### Solution 2: Full Geospatial Integration (Advanced)

```
┌─────────────────────────────────────────────────────┐
│                   CONDUCTOR                         │
│                                                     │
│  Position Awareness:                                │
│  ┌──────────────────────────────────────┐          │
│  │ geospatial_service.get_vehicle_pos() │          │
│  │ - Route context awareness            │          │
│  │ - Waypoint proximity                 │          │
│  │ - On-route validation                │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Distance Calculation:                              │
│  ┌──────────────────────────────────────┐          │
│  │ geospatial_service.calculate_distance│          │
│  │ - PostGIS ST_Distance                │          │
│  │ - Spatial indexing (fast!)           │          │
│  │ - Route-aware distance               │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Passenger Visibility:                              │
│  ┌──────────────────────────────────────┐          │
│  │ geospatial_service.find_passengers() │          │
│  │ - ST_DWithin (spatial query)         │          │
│  │ - Route buffer filtering             │          │
│  │ - Depot proximity checks             │          │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Fix Proximity Radius (Immediate)

**Goal:** Ensure pickup_radius is always DB-bound, never hardcoded

**Changes:**
1. Remove hardcoded default from `ConductorConfig`
2. Make config loading mandatory during conductor initialization
3. Add validation to ensure radius is within constraints (0.05 - 5.0 km)
4. Allow runtime updates via WebSocket config events

**Code:**
```python
# conductor.py - BEFORE
class ConductorConfig:
    pickup_radius_km: float = 0.2  # HARDCODED ❌

# conductor.py - AFTER
class ConductorConfig:
    pickup_radius_km: float = Field(default=None)  # Must load from DB ✅
    
    async def validate(self):
        if self.pickup_radius_km is None:
            raise ValueError("pickup_radius_km must be loaded from database")
        if not (0.05 <= self.pickup_radius_km <= 5.0):
            raise ValueError(f"pickup_radius_km {self.pickup_radius_km} out of bounds")
```

### Phase 2: Enhance Position Awareness (Short-term)

**Goal:** Add validation and fallback for conductor position

**Changes:**
1. Add position timestamp tracking
2. Validate position staleness (reject if > 30 seconds old)
3. Add geospatial_service fallback for position lookup
4. Log position updates with route context

**Code:**
```python
class Conductor:
    def __init__(self, ...):
        self.current_vehicle_position: Optional[Tuple[float, float]] = None
        self.position_timestamp: Optional[datetime] = None  # NEW
        self.position_source: str = "unknown"  # NEW: "gps", "driver", "cache"
    
    async def update_vehicle_position(self, latitude: float, longitude: float, source: str = "driver"):
        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            self.logger.error(f"Invalid position: ({latitude}, {longitude})")
            return
        
        self.current_vehicle_position = (latitude, longitude)
        self.position_timestamp = datetime.now()
        self.position_source = source
        
        self.logger.debug(
            f"Position updated: ({latitude:.6f}, {longitude:.6f}) "
            f"source={source} age=0s"
        )
    
    def is_position_stale(self, max_age_seconds: float = 30.0) -> bool:
        if not self.position_timestamp:
            return True
        age = (datetime.now() - self.position_timestamp).total_seconds()
        return age > max_age_seconds
    
    async def _ensure_valid_position(self) -> bool:
        if self.current_vehicle_position and not self.is_position_stale():
            return True
        
        # Fallback: query geospatial_service for last known position
        self.logger.warning("Position stale, attempting fallback...")
        # TODO: Implement geospatial_service position query
        return False
```

### Phase 3: Delegate Distance to Geospatial Service (Medium-term)

**Goal:** Use geospatial_service for passenger proximity queries

**Changes:**
1. Add `/api/passengers/nearby` endpoint to geospatial_service
2. Use PostGIS `ST_DWithin` instead of haversine loops
3. Filter passengers by route geometry buffer
4. Cache results by vehicle position grid

**New Endpoint:**
```python
# geospatial_service/api/spatial.py
@router.get("/passengers-in-proximity")
async def find_passengers_in_proximity(
    vehicle_lat: float,
    vehicle_lon: float,
    route_id: str,
    radius_meters: float = 200.0
):
    """
    Find passengers within proximity of vehicle using PostGIS.
    
    Uses ST_DWithin for optimized spatial query with spatial index.
    Filters by route to avoid cross-route pickups.
    
    Returns passengers sorted by distance (closest first).
    """
    query = """
        SELECT 
            ap.id,
            ap.passenger_id,
            ap.latitude,
            ap.longitude,
            ST_Distance(
                ST_MakePoint(ap.longitude, ap.latitude)::geography,
                ST_MakePoint($1, $2)::geography
            ) AS distance_meters
        FROM active_passengers ap
        WHERE ap.route_id = $3
          AND ap.status = 'WAITING'
          AND ST_DWithin(
              ST_MakePoint(ap.longitude, ap.latitude)::geography,
              ST_MakePoint($1, $2)::geography,
              $4
          )
        ORDER BY distance_meters ASC
    """
    
    # Execute with PostGIS spatial index (FAST!)
    results = await postgis_client.execute(
        query, 
        vehicle_lon, vehicle_lat, route_id, radius_meters
    )
    
    return {
        "vehicle_position": {"lat": vehicle_lat, "lon": vehicle_lon},
        "radius_meters": radius_meters,
        "route_id": route_id,
        "passengers": results,
        "count": len(results)
    }
```

**Conductor Update:**
```python
# conductor.py
async def check_for_passengers(self, vehicle_lat, vehicle_lon, route_id):
    # NEW: Use geospatial_service for proximity query
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.geospatial_service_url}/spatial/passengers-in-proximity",
            params={
                "vehicle_lat": vehicle_lat,
                "vehicle_lon": vehicle_lon,
                "route_id": route_id,
                "radius_meters": self.config.pickup_radius_km * 1000
            }
        )
        data = response.json()
        passengers = data["passengers"]
    
    # Board passengers (already sorted by distance)
    passenger_ids = [p["passenger_id"] for p in passengers]
    return await self.board_passengers_by_id(passenger_ids)
```

### Phase 4: Route Context Awareness (Long-term)

**Goal:** Conductor understands route geometry and waypoints

**Features:**
1. Load route geometry on shift start
2. Track progress along route (current segment, waypoint)
3. Pre-fetch passengers at upcoming waypoints
4. Validate position is on-route (detect GPS errors)

**Benefits:**
- Predictive passenger loading (cache ahead)
- Detect GPS drift/errors
- Optimize stop scheduling
- Better passenger visibility

## Summary Table

| Component | Current State | Should Be | Priority |
|-----------|---------------|-----------|----------|
| **Proximity Radius** | DB-bound with hardcoded fallback | DB-bound, no fallback | HIGH |
| **Distance Calc** | Internal haversine | Keep internal for speed | LOW |
| **Position Source** | Driver only | Driver + validation + fallback | HIGH |
| **Geospatial Service** | Not used | Use for passenger queries | MEDIUM |
| **Route Awareness** | None | Load geometry, track progress | LOW |
| **Config Updates** | Static after load | Real-time via WebSocket | MEDIUM |

## Immediate Actions

### 1. Fix Hardcoded Defaults
```bash
# Edit conductor.py
# Remove: pickup_radius_km: float = 0.2
# Add: pickup_radius_km: Optional[float] = None
# Add validation in from_config_service()
```

### 2. Add Position Validation
```bash
# Add position_timestamp tracking
# Add is_position_stale() check
# Reject queries if position > 30s old
```

### 3. Document Spatial Architecture
```bash
# Create SPATIAL_ARCHITECTURE.md
# Document all distance calculation points
# Plan geospatial_service integration
```

## Questions to Answer

1. **Should we delegate ALL distance calculations to geospatial_service?**
   - Pro: Single source of truth, PostGIS optimization
   - Con: Network dependency, latency for simple checks

2. **Should conductor cache route geometry?**
   - Pro: Faster context awareness, offline capability
   - Con: Memory usage, stale data risk

3. **Should position come from geospatial_service?**
   - Pro: Validation, route context, fallback
   - Con: Additional network call, complexity

**Recommendation:** 
- Keep internal haversine for simple checks
- Use geospatial_service for complex spatial queries (passenger proximity with route buffer)
- Add position validation but keep driver as primary source
- Make proximity radius **strictly DB-bound** with runtime updates
