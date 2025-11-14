# Commuter Simulator - Clean Architecture

This package follows **Clean Architecture** principles with clear separation of concerns across four layers.

## Architecture Overview

```
commuter_service/
├── domain/              # Business logic (pure, no external dependencies)
├── application/         # Use cases and orchestration
├── infrastructure/      # External systems (DB, APIs, config)
├── interfaces/          # Entry points (HTTP, CLI)
├── scripts/             # One-off utilities
├── tests/               # Test suite
└── main.py              # Application entry point
```

## Dependency Rules

**Inward dependencies only:**
- `domain/` → NO dependencies on other layers
- `application/` → depends on `domain/`
- `infrastructure/` → implements interfaces from `domain/`
- `interfaces/` → depends on `application/` and `infrastructure/`

## Layer Details

### 1. Domain Layer (`domain/`)

**Pure business logic** with no external dependencies.

```
domain/
├── models/              # Business entities (Passenger, Route, Depot)
├── repositories/        # Abstract repository interfaces
└── services/            # Domain services
    ├── spawning/        # Passenger spawning logic
    │   ├── base_spawner.py
    │   ├── depot_spawner.py
    │   └── route_spawner.py
    └── reservoirs/      # Passenger reservoir management
        ├── depot_reservoir.py
        └── route_reservoir.py
```

**Key Principles:**
- No imports from `infrastructure/`, `application/`, or `interfaces/`
- Contains core business rules and domain logic
- Framework-agnostic (works without FastAPI, Strapi, etc.)

**Import example:**
```python
from commuter_service.domain.services.spawning import DepotSpawner, RouteSpawner
from commuter_service.domain.services.reservoirs import RouteReservoir
```

### 2. Application Layer (`application/`)

**Use cases and orchestration** - coordinates domain services.

```
application/
├── coordinators/        # Multi-service orchestration
│   └── spawner_coordinator.py
└── queries/             # Read-side operations
    └── manifest_query.py
```

**Responsibilities:**
- Orchestrate multiple domain services
- Implement use cases (e.g., "spawn passengers for all routes")
- Handle cross-cutting concerns (logging, metrics)
- Transform data for presentation

**Import example:**
```python
from commuter_service.application.coordinators import SpawnerCoordinator
from commuter_service.application.queries import enrich_manifest_rows
```

### 3. Infrastructure Layer (`infrastructure/`)

**External systems and implementations** - adapters to the outside world.

```
infrastructure/
├── persistence/
│   └── strapi/          # Strapi repository implementations
│       └── passenger_repository.py
├── geospatial/          # GeospatialService client
│   └── client.py
├── config/              # Configuration loaders
│   └── spawn_config_loader.py
├── events/              # Event system (LISTEN/NOTIFY)
└── services/            # External service adapters
```

**Responsibilities:**
- Implement repository interfaces from `domain/`
- Connect to external systems (Strapi, PostGIS, Redis)
- Handle infrastructure concerns (caching, retries, connection pooling)

**Import example:**
```python
from commuter_service.infrastructure.persistence.strapi import PassengerRepository
from commuter_service.infrastructure.geospatial.client import GeospatialClient
from commuter_service.infrastructure.config import SpawnConfigLoader
```

### 4. Interfaces Layer (`interfaces/`)

**Entry points** - how external world interacts with the system.

```
interfaces/
├── http/                # REST API (FastAPI)
│   └── manifest_api.py
└── cli/                 # Command-line tools
    └── list_passengers.py
```

**Responsibilities:**
- HTTP endpoints (FastAPI)
- CLI scripts
- Input validation and serialization
- Authentication/authorization (future)

**Usage examples:**
```bash
# HTTP API
uvicorn commuter_service.interfaces.http.manifest_api:app --port 4000

# CLI
python -m commuter_service.interfaces.cli.list_passengers --route 1 --json
```

## Entry Points

### Main Application
```bash
python -m commuter_service.main
```
Starts the spawner coordinator with configured spawners.

### HTTP API
```bash
uvicorn commuter_service.interfaces.http.manifest_api:app --port 4000
```
RESTful API for passenger manifest queries.

### CLI Tools
```bash
python -m commuter_service.interfaces.cli.list_passengers --help
```
Console diagnostic and reporting tools.

## Benefits of This Structure

✅ **Testability** - Domain logic isolated and easy to unit test
✅ **Maintainability** - Clear boundaries, easy to locate code
✅ **Flexibility** - Swap infrastructure without touching business logic
✅ **Scalability** - Add features without breaking existing code
✅ **Clarity** - New developers understand structure immediately

## Migration Notes

**Old structure** (deprecated):
```python
# OLD (still works but deprecated)
from commuter_service.services.manifest_builder import enrich_manifest_rows
from commuter_service.core.domain.spawner_engine import DepotSpawner
from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
```

**New structure** (use this):
```python
# NEW (clean architecture)
from commuter_service.application.queries import enrich_manifest_rows
from commuter_service.domain.services.spawning import DepotSpawner
from commuter_service.infrastructure.persistence.strapi import PassengerRepository
```

## Future Enhancements

- Add `domain/models/` for explicit entity classes
- Add `domain/repositories/` for abstract interfaces
- Add `application/commands/` for write operations
- Add `interfaces/graphql/` for GraphQL API (optional)
- Add `interfaces/websocket/` for real-time streams
