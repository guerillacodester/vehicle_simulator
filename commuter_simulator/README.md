# Commuter Simulator - Modern Architecture

A redesigned passenger spawning and management system with clean separation of concerns.

## Structure

```text
commuter_simulator/
├── infrastructure/          # External integrations (SINGLE SOURCE OF TRUTH)
│   ├── database/           # ✓ Strapi API client (ONLY place for API access)
│   ├── geospatial/         # GIS utilities
│   └── events/             # Event bus
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
from commuter_simulator.infrastructure.database import StrapiApiClient
from commuter_simulator.services.socketio import SocketIOService, EventTypes

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
