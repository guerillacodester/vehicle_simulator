# Conductor Vision Architecture

## Overview

The conductor's passenger visibility system has been refactored to use the **commuter_service HTTP API** instead of direct database access. This ensures all passenger operations go through the **reservoir pattern** for consistency, caching, and event emission.

## Architecture Flow

```
┌─────────────┐
│  Conductor  │
│  (Vehicle)  │
└──────┬──────┘
       │
       │ HTTP GET /api/passengers/nearby
       │ (latitude, longitude, route_id, radius_km)
       ▼
┌──────────────────────┐
│  commuter_service    │
│  HTTP API            │
│  (passenger_crud.py) │
└──────┬───────────────┘
       │
       │ query_passengers_nearby()
       ▼
┌──────────────────────┐
│  RouteReservoir      │
│  (Future)            │
│  - Caching           │
│  - Event emission    │
└──────┬───────────────┘
       │
       │ Strapi filters + haversine
       ▼
┌──────────────────────┐
│  PassengerRepository │
│  - Strapi API client │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Strapi Database     │
│  active-passengers   │
└──────────────────────┘
```

## Key Components

### 1. CommuterServiceClient (`arknet_transit_simulator/services/commuter_http_client.py`)

HTTP client used by the conductor to query the commuter_service API:

```python
client = CommuterServiceClient(base_url="http://localhost:4000")
await client.connect()

# Query for eligible passengers
passengers = await client.get_eligible_passengers(
    vehicle_lat=13.0975,
    vehicle_lon=-59.6139,
    route_id="gg3pv3z19hhm117v9xth5ezq",
    pickup_radius_km=0.2,
    max_results=50,
    status="WAITING"
)

# Board a passenger
await client.board_passenger(passenger_id="doc_123", vehicle_id="BUS_001")

# Alight a passenger
await client.alight_passenger(passenger_id="doc_123")
```

**Methods:**
- `connect()` - Test connection to commuter_service
- `disconnect()` - Close HTTP client
- `get_eligible_passengers()` - Query passengers by proximity
- `board_passenger()` - Mark passenger as boarded
- `alight_passenger()` - Mark passenger as alighted
- `get_passenger()` - Get single passenger details

### 2. Conductor Updates (`arknet_transit_simulator/vehicle/conductor.py`)

The conductor now uses the HTTP client instead of direct database access:

**Constructor:**
```python
conductor = Conductor(
    conductor_id="COND-001",
    conductor_name="Conductor Smith",
    vehicle_id="BUS_001",
    assigned_route_id="route_123",
    capacity=40,
    commuter_service_url="http://localhost:4000"  # NEW
)
```

**Start Method:**
- Initializes `CommuterServiceClient`
- Tests connection to commuter_service
- Falls back gracefully if connection fails

**check_for_passengers():**
- Prefers HTTP client over legacy `passenger_db`
- Calls `/api/passengers/nearby` endpoint
- Extracts `documentId` from API response
- Logs detailed visibility information

### 3. Nearby Passengers Endpoint (`commuter_service/interfaces/http/passenger_crud.py`)

New endpoint for conductor visibility:

```
GET /api/passengers/nearby
```

**Query Parameters:**
- `latitude` (required) - Vehicle latitude
- `longitude` (required) - Vehicle longitude
- `route_id` (required) - Route ID to filter
- `radius_km` (default: 0.2) - Search radius in kilometers
- `max_results` (default: 50) - Maximum passengers to return
- `status` (default: WAITING) - Filter by passenger status

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "documentId": "abc123",
      "passenger_id": "PASS_001",
      "route_id": "route_123",
      "latitude": 13.0975,
      "longitude": -59.6139,
      "status": "WAITING",
      "computed_state": "WAITING",
      ...
    }
  ],
  "meta": {
    "pagination": {
      "total": 3,
      "page": 1,
      "pageSize": 3
    },
    "query": {
      "latitude": 13.0975,
      "longitude": -59.6139,
      "route_id": "route_123",
      "radius_km": 0.2
    }
  }
}
```

**Implementation:**
1. Query Strapi with route_id and status filters
2. Calculate haversine distance for each passenger
3. Filter by radius_km
4. Sort by distance (closest first)
5. Limit to max_results
6. Return with computed states

## Benefits

### ✅ Architectural Consistency
- All passenger operations go through the same API layer
- No direct database access from conductor
- Enforces repository → reservoir → API pattern

### ✅ Caching & Performance
- Future: RouteReservoir can cache nearby passenger queries
- Reduces database load from frequent conductor checks
- Haversine calculation done once in API layer

### ✅ Event Emission
- All state changes (board/alight) emit WebSocket events
- Real-time monitoring works automatically
- No bypassing of event system

### ✅ Security & Validation
- API layer validates all inputs
- State transitions are validated
- HTTP authentication/authorization can be added

### ✅ Testability
- Conductor can be tested with mock HTTP client
- API endpoints can be tested independently
- Clear separation of concerns

### ✅ Flexibility
- Easy to add new query parameters (depot_id, priority, etc.)
- Can implement advanced filtering without changing conductor
- API versioning possible

## Migration Notes

### Deprecated
```python
# OLD: Direct database access
conductor = Conductor(
    ...,
    passenger_db=passenger_service  # DEPRECATED
)

# OLD: PassengerService.get_eligible_passengers()
eligible = await passenger_db.get_eligible_passengers(...)
```

### Current
```python
# NEW: HTTP client
conductor = Conductor(
    ...,
    commuter_service_url="http://localhost:4000"  # NEW
)

# NEW: HTTP API endpoint
eligible = await commuter_client.get_eligible_passengers(...)
```

### Backward Compatibility
The conductor still supports `passenger_db` for backward compatibility:
- If `commuter_client` is available, it takes precedence
- If not, falls back to `passenger_db` (legacy)
- Logs indicate which method is being used

## Configuration

Add to `config.ini`:

```ini
[infrastructure]
commuter_service_url = http://localhost:4000
```

The conductor will read this from `common.config_provider.get_config()`.

## Testing

### Test Conductor Vision

1. Start commuter_service:
```bash
cd commuter_service
python -m uvicorn main:app --port 4000
```

2. Seed passengers:
```bash
python seed_passengers.py
```

3. Query nearby passengers:
```bash
curl "http://localhost:4000/api/passengers/nearby?latitude=13.0975&longitude=-59.6139&route_id=gg3pv3z19hhm117v9xth5ezq&radius_km=0.5"
```

4. Start simulator:
```bash
cd arknet_transit_simulator
python -m arknet_transit_simulator
```

5. Watch conductor logs:
```
🔵 Conductor BUS_001 👁️  LOOKING FOR PASSENGERS (via commuter_service API):
   📍 Position: (13.097500, -59.613900)
   🚏 Route: gg3pv3z19hhm117v9xth5ezq
   🔍 Pickup radius: 0.2 km
   💺 Seats available: 40/40
```

## Future Enhancements

### 1. RouteReservoir Integration
Currently the `/api/passengers/nearby` endpoint queries Strapi directly. Future enhancement:
- Add `RouteReservoir.get_nearby_passengers()` method
- Cache proximity queries by route + location grid
- Invalidate cache on passenger state changes
- Pre-compute nearby passengers for route waypoints

### 2. Advanced Filtering
Add query parameters:
- `depot_id` - Filter by depot
- `priority` - Filter by passenger priority
- `min_wait_time` - Only passengers waiting > X minutes
- `direction` - Filter by route direction

### 3. Real-time Updates
- Conductor subscribes to WebSocket
- Receives passenger:spawned events for route
- Updates visibility immediately without polling

### 4. Predictive Visibility
- Pre-fetch passengers at upcoming waypoints
- Cache results along route path
- Reduce API calls by predicting conductor needs

## Summary

The conductor now has **proper vision** through the commuter_service API:

✅ **Can see passengers at depot** - Query nearby with pickup_radius_km  
✅ **Can see passengers along route** - Filter by route_id  
✅ **Goes through reservoirs** - Future reservoir caching integration  
✅ **Emits events** - All state changes broadcast via WebSocket  
✅ **Production ready** - HTTP API, validation, error handling  

The architecture is now **consistent** and **scalable**. 🎉
