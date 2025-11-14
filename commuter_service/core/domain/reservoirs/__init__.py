"""
Reservoirs - DB-backed commuter storage with optional Redis caching

Receives spawned commuters from spawner services and persists them to Strapi.
Serves as single source-of-truth interface for conductor to query passengers.

Reservoirs:
- RouteReservoir: DB-backed storage for route-spawned passengers
- DepotReservoir: DB-backed storage for depot-spawned passengers

Both implement ReservoirInterface from spawner_engine.
All passengers persisted to Strapi; optional Redis cache for performance.
"""

from .route_reservoir import RouteReservoir
from .depot_reservoir import DepotReservoir

__all__ = [
    'RouteReservoir',
    'DepotReservoir',
]
