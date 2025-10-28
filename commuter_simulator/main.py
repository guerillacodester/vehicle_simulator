"""
Commuter Simulator - Main Entry Point

Single entry point for commuter spawning system.
Orchestrates DepotSpawner and RouteSpawner with enable/disable control.
"""

import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from commuter_simulator.services.spawner_coordinator import SpawnerCoordinator
from commuter_simulator.core.domain.spawner_engine import DepotSpawner, SpawnerInterface, SpawnRequest
from commuter_simulator.core.domain.reservoirs import RouteReservoir, DepotReservoir
from commuter_simulator.infrastructure.database.passenger_repository import PassengerRepository
import random
import uuid


class MockRouteSpawner(SpawnerInterface):
    """Simplified RouteSpawner for testing enable/disable flags (no geospatial deps)"""
    
    def __init__(self, reservoir, config, route_id: str):
        super().__init__(reservoir, config)
        self.route_id = route_id
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def spawn(self, current_time: datetime, time_window_minutes: int = 60):
        """Generate test passengers along route"""
        # Simple Poisson calculation (λ=1.5 for testing)
        import numpy as np
        spawn_count = np.random.poisson(1.5)
        
        self.logger.info(f"Route {self.route_id}: spawning {spawn_count} passengers (test mode)")
        
        spawn_requests = []
        for i in range(spawn_count):
            passenger_id = f"ROUTE_{self.route_id}_{uuid.uuid4().hex[:8].upper()}"
            spawn_requests.append(SpawnRequest(
                passenger_id=passenger_id,
                spawn_location=(33.75 + random.uniform(-0.01, 0.01), -84.39 + random.uniform(-0.01, 0.01)),
                destination_location=(33.75 + random.uniform(-0.01, 0.01), -84.39 + random.uniform(-0.01, 0.01)),
                route_id=self.route_id,
                spawn_time=current_time,
                spawn_context="ROUTE",
                priority=1.0,
                generation_method="poisson_test"
            ))
        
        return spawn_requests


async def main():
    """Main entrypoint for commuter spawning system"""
    
    config = {
        'enable_routespawner': False,
        'enable_depotspawner': True,
        'enable_redis_cache': False,
        'continuous_mode': False,
        'spawn_interval_seconds': 60,
    }
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("="*80)
    logger.info("COMMUTER SPAWNING SYSTEM - STARTING")
    logger.info("="*80)
    
    passenger_repo = None
    
    try:
        logger.info(" [1/4] Initializing PassengerRepository...")
        passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")
        await passenger_repo.connect()
        logger.info(" PassengerRepository connected")
        
        logger.info("  [2/4] Creating reservoirs...")
        
        route_reservoir = RouteReservoir(
            passenger_repository=passenger_repo,
            enable_redis_cache=False
        )
        
        depot_reservoir = DepotReservoir(
            depot_id="DEPOT_01",
            passenger_repository=passenger_repo,
            enable_redis_cache=False
        )
        logger.info(" Reservoirs created")
        
        logger.info(" [3/4] Creating spawners...")
        
        # RouteSpawner (mock for testing)
        route_spawner = MockRouteSpawner(
            reservoir=route_reservoir,
            config={},
            route_id="TEST_ROUTE_1"
        )
        
        # DepotSpawner
        depot_spawner = DepotSpawner(
            reservoir=depot_reservoir,
            config={},
            depot_id="DEPOT_01",
            depot_location=(33.7490, -84.3880),
            available_routes=["route_1", "route_2"]
        )
        logger.info(" Spawners created")
        
        logger.info(" [4/4] Starting coordinator...")
        spawners = [route_spawner, depot_spawner]
        coordinator = SpawnerCoordinator(spawners=spawners, config=config)
        await coordinator.start(current_time=datetime.utcnow(), time_window_minutes=60)
        
        logger.info("="*80)
        logger.info(" SPAWNING CYCLE COMPLETE")
        logger.info("="*80)
        
    except KeyboardInterrupt:
        logger.info("  Shutting down...")
    except Exception as e:
        logger.error(f" Error: {e}", exc_info=True)
    finally:
        if passenger_repo:
            await passenger_repo.disconnect()
        logger.info(" Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
