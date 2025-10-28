"""
Spawner Engine - Generates commuters (passengers) for the simulation.

Architecture:
- SpawnerInterface: Abstract base class defining spawner contracts
- ReservoirInterface: Abstract push-based storage for spawned commuters
- RouteSpawner: Generates passengers along transit routes
- DepotSpawner: Generates passengers at depot pickup locations

All spawners are decoupled from persistence - they push to reservoirs.
Reservoirs are decoupled from spawning - they receive push operations.
"""

from commuter_simulator.core.domain.spawner_engine.base_spawner import (
    SpawnerInterface,
    ReservoirInterface,
    SpawnRequest
)
from commuter_simulator.core.domain.spawner_engine.route_spawner import RouteSpawner
from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner

__all__ = [
    'SpawnerInterface',
    'ReservoirInterface',
    'SpawnRequest',
    'RouteSpawner',
    'DepotSpawner',
]
