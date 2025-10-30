# Geospatial Services Layer

High-performance spatial query service for vehicle and passenger simulators.

## Purpose

Provides optimized PostGIS spatial operations without going through Strapi's ORM overhead:

- Geofencing checks (ST_Contains)
- Reverse geocoding (address lookups)
- Spatial proximity queries (ST_DWithin)
- Route buffer queries for passenger spawning
- Depot catchment area queries

## Architecture

**Phase 1 (MVP - Current)**: Implemented as Strapi custom controllers

- Location: `arknet_fleet_manager/arknet-fleet-api/src/api/geospatial/`
- Access: `http://localhost:1337/api/geospatial/*`
- Simpler deployment (one service)

**Phase 2 (Production - Future)**: Separate FastAPI service

- Location: `geospatial_service/` (this folder)
- Access: `http://localhost:6000/*`
- Independent scaling and optimization
- Direct PostGIS connection (read-only)

## Migration Path

1. Start with Strapi custom controllers (Phase 1)
2. Test and validate with both simulators
3. When performance bottlenecks appear (>1000 req/s), migrate to Phase 2
4. Change simulator URLs, zero business logic changes

## Directory Structure (Phase 2 - Future)

```text
geospatial_service/
├── README.md              # This file
├── main.py                # FastAPI app entry point
├── requirements.txt       # Python dependencies
├── api/
│   ├── __init__.py
│   ├── geofence.py       # Geofencing endpoints
│   ├── geocoding.py      # Reverse geocoding
│   └── spatial.py        # General spatial queries
├── services/
│   ├── __init__.py
│   └── postgis_client.py # Direct PostGIS connection
└── config/
    ├── __init__.py
    └── database.py       # DB configuration

```

## API Endpoints (When Implemented)

### Geofencing

- `POST /geofence/check` - Check which zones contain a point
- `POST /geofence/batch` - Batch geofence checks

### Reverse Geocoding

- `POST /geocode/reverse` - Lat/lon to address
- `POST /geocode/batch` - Batch reverse geocoding

### Spatial Queries

- `GET /nearby/buildings` - Buildings within radius
- `GET /nearby/pois` - POIs within radius
- `GET /route/buildings` - Buildings along route buffer
- `GET /depot/catchment` - Buildings in depot catchment area

## Consumed By

- **arknet_transit_simulator** - Geofencing for vehicles
- **commuter_simulator** - Route/depot reservoir spawning queries

## Status

⏳ **Not Yet Implemented** - Placeholder for Phase 2 migration
📍 **Current**: Use Strapi custom controllers at `/api/geospatial/*`
