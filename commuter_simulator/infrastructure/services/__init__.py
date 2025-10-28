"""
Infrastructure Services

FastAPI-based spawner services that expose spawning endpoints over HTTP.
Each service streams spawned passengers as NDJSON in real-time.

Services:
- RouteSpawnerService: GET /spawn/route/{route_id}
- DepotSpawnerService: GET /spawn/depot/{depot_id}

These are lightweight wrappers around spawner_engine classes.
"""

__all__ = [
    'RouteSpawnerService',
    'DepotSpawnerService',
]
