# Commuter Service - Integrated Passenger Management

An integrated passenger spawning and manifest system with clean separation of concerns.

## Overview

The **Commuter Service** is a dual-interface service that provides:
1. **HTTP API** (port 4000): Manifest queries for enriched passenger listings
2. **Background Spawning**: Passenger generation and lifecycle management

**Note**: Previously split into separate "commuter_simulator" and "manifest_api" services, this was merged on Nov 1, 2025 for better cohesion. The launcher runs the HTTP interface by default (`interfaces/http/commuter_manifest.py`), which integrates with the application layer.

## Interfaces

### HTTP Interface (Default)
- **Module**: `commuter_service.interfaces.http.manifest_api`
- **Port**: 4000 (configurable via `config.ini`)
- **Endpoints**:
  - `GET /api/manifest?route=<id>&limit=100` - Enriched passenger manifest
  - `GET /health` - Service health check
  - `GET /docs` - Swagger UI

### Background Interface (Alternative)
- **Module**: `commuter_service.main`
- **Purpose**: Background passenger spawning without HTTP server
- **Use Case**: When manifest API is not needed, only spawning logic

### CLI Interface
- **Module**: `commuter_service.interfaces.cli.manifest_cli`
- **Purpose**: Terminal-based manifest visualization
- **Module**: `commuter_service.interfaces.cli.seed`
- **Purpose**: Passenger seeding tool

## Structure

```text
commuter_service/
├── infrastructure/          # External integrations (SINGLE SOURCE OF TRUTH)
│   ├── database/           # ✓ Strapi API client (ONLY place for API access)
│   ├── geospatial/         # GIS utilities
│   └── events/             # Event bus
│
├── application/            # Use cases and application logic
│   ├── queries/           # Query use cases (manifest, passengers)
│   └── coordinators/      # Spawning coordinators
│
├── services/               # Application services
│   ├── depot_reservoir/   # Depot-based spawning
│   ├── route_reservoir/   # Route-based spawning
│   └── socketio/          # ✓ Real-time communication (PORTED)
│
├── core/                   # Core business logic
│   ├── models/            # Data models
│   ├── repositories/      # Domain data access (uses infrastructure)
│   └── domain/            # Business logic & algorithms
│
├── interfaces/             # External interfaces
│   ├── http/              # FastAPI manifest API
│   └── cli/               # Command-line tools
│
├── config/                 # Configuration management
└── utils/                  # Shared utilities
    ├── logging/           # Logging setup
    └── validation/        # Data validation
```

## Key Principles

### 1. Single Source of Truth

- **API Access**: `infrastructure/database/strapi_client.py` is the ONLY place where API calls are made
- **Socket.IO**: `services/socketio/service.py` handles all real-time communication
- All other modules must use these services, never make direct HTTP/Socket calls

### 2. Clear Separation

- **Infrastructure**: External systems (database, sockets, GIS)
- **Services**: High-level application services (depot/route reservoirs)
- **Core**: Business logic, independent of infrastructure
- **Utils**: Reusable utilities

### 3. Dependency Flow

```text
Services → Core → Infrastructure
         ↓
       Utils
```

## Ported Components

### ✓ Socket.IO Service

- Location: `services/socketio/service.py`
- Original: `commuter_service/socketio_client.py`
- Changes:
  - Simplified API
  - Better error handling
  - Cleaner logging

### ✓ API Client

- Location: `infrastructure/database/strapi_client.py`
- Original: `commuter_service/strapi_api_client.py`
- Changes:
  - Single source of truth enforced
  - Clear separation from business logic

## Next Steps

1. Port depot reservoir service
2. Port route reservoir service
3. Implement geospatial utilities
4. Add configuration management
5. Set up logging infrastructure

## Usage Example

```python
from commuter_service.infrastructure.database import StrapiApiClient
from commuter_service.services.socketio import SocketIOService, EventTypes

# Single source of truth for data
async with StrapiApiClient("http://localhost:1337") as api:
    depots = await api.get_all_depots()
    routes = await api.get_all_routes()

# Single source of truth for events
socket = SocketIOService(
    url="http://localhost:1337",
    namespace="/depot-reservoir"
)
await socket.connect()
await socket.emit(EventTypes.COMMUTER_SPAWNED, passenger_data)
```
