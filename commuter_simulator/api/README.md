# Manifest API

⚠️ **Note**: This directory is deprecated. The API has been moved to clean architecture structure.

**New location**: `commuter_simulator/interfaces/http/manifest_api.py`

FastAPI service providing enriched passenger manifests for UI consumption.

## Features

- **Enriched data**: Route positions, reverse geocoded addresses, travel distances
- **Flexible filtering**: By route, depot, status, time range
- **Ordered results**: Sorted by distance from route start when route_id provided
- **CORS enabled**: Ready for browser consumption
- **Single source of truth**: Uses `manifest_query` module (shared with CLI)

## Endpoints

### `GET /api/manifest`

Query passenger manifest with optional filters.

**Query Parameters:**
- `route` (optional): Filter by route_id
- `depot` (optional): Filter by depot_id
- `status` (optional): Filter by status (WAITING, BOARDED, ALIGHTED)
- `start` (optional): Filter spawned_at >= ISO8601 timestamp
- `end` (optional): Filter spawned_at <= ISO8601 timestamp
- `limit` (default: 100, max: 1000): Maximum passengers to return
- `sort` (default: "spawned_at:asc"): Sort order

**Response:**
```json
{
  "count": 3,
  "route_id": "1",
  "depot_id": null,
  "ordered_by_route_position": true,
  "passengers": [
    {
      "index": 1,
      "spawned_at": "2025-10-29T15:59:30.000Z",
      "passenger_id": "DEPOT_SPT_NORTH_01_BFBCD35E",
      "route_id": "1",
      "depot_id": "DEPOT_01",
      "latitude": 13.252068,
      "longitude": -59.642543,
      "destination_lat": 13.098567,
      "destination_lon": -59.618234,
      "status": "WAITING",
      "route_position_m": 245.7,
      "travel_distance_km": 17.42,
      "start_address": "Highway 1, St. Peter",
      "stop_address": "Bridgetown, St. Michael",
      "trip_summary": "Highway 1, St. Peter → Bridgetown, St. Michael | 17.42"
    }
  ]
}
```

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "manifest_api",
  "timestamp": "2025-10-29T16:30:00.000Z"
}
```

## Running the Service

### Development

```powershell
# Ensure dependencies are installed (fastapi, uvicorn, httpx)
pip install fastapi uvicorn httpx

# Set environment variables
$env:STRAPI_URL = "http://localhost:1337"
$env:GEO_URL = "http://localhost:6000"
$env:STRAPI_TOKEN = "your-token-here"  # Optional

# Run the API (NEW PATH)
uvicorn commuter_simulator.interfaces.http.manifest_api:app --host 0.0.0.0 --port 4000 --reload
```

### Production

```powershell
# Run with multiple workers (NEW PATH)
uvicorn commuter_simulator.interfaces.http.manifest_api:app --host 0.0.0.0 --port 4000 --workers 4
```

## Environment Variables

- `STRAPI_URL` (default: `http://localhost:1337`): Strapi API base URL
- `GEO_URL` (default: `http://localhost:6000`): GeospatialService base URL
- `STRAPI_TOKEN` (optional): Bearer token for Strapi API authentication
- `GEOCODE_CONCURRENCY` (default: 5): Max concurrent reverse geocoding requests

## Testing

```powershell
# Health check
curl http://localhost:4000/health

# Get all passengers (up to 100)
curl http://localhost:4000/api/manifest

# Get passengers for a specific route (ordered by route position)
curl "http://localhost:4000/api/manifest?route=1&limit=50"

# Filter by status and time range
curl "http://localhost:4000/api/manifest?status=WAITING&start=2025-10-29T00:00:00Z&end=2025-10-29T23:59:59Z"

# Get passengers at a specific depot
curl "http://localhost:4000/api/manifest?depot=DEPOT_01&limit=20"
```

## API Documentation

Once running, visit:
- Interactive docs: <http://localhost:4000/docs>
- OpenAPI schema: <http://localhost:4000/openapi.json>

## Integration with UI

### Fetch manifest for a route

```javascript
const response = await fetch('http://localhost:4000/api/manifest?route=1&limit=100');
const data = await response.json();

// Display passengers ordered by route position
data.passengers.forEach(passenger => {
  console.log(`${passenger.index}. ${passenger.trip_summary}`);
  console.log(`   Position: ${passenger.route_position_m}m from start`);
  console.log(`   Status: ${passenger.status}`);
});
```

### Real-time updates

For real-time passenger events, use the streaming endpoint from `visualizer/app.py` (WebSocket) or the console tool `stream_passenger_events.py` (PostgreSQL NOTIFY).

## Architecture

```
UI/Frontend
    ↓ HTTP GET
Manifest API (port 4000)
    ↓ async calls
├─ manifest_builder.py (enrichment logic)
│   ├─ fetch_passengers() → Strapi API
│   ├─ fetch_route_coords() → GeospatialService
│   └─ reverse_geocode() → GeospatialService
└─ Returns enriched JSON
```

This API is the HTTP wrapper around the shared `manifest_builder` module, ensuring consistent manifest formatting across CLI, API, and future UI components.
