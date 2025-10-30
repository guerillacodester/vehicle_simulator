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

from commuter_simulator.application.coordinators import SpawnerCoordinator
from commuter_simulator.domain.services.spawning import DepotSpawner, RouteSpawner, SpawnerInterface, SpawnRequest
from commuter_simulator.domain.services.reservoirs import RouteReservoir, DepotReservoir
from commuter_simulator.infrastructure.persistence.strapi.passenger_repository import PassengerRepository
from commuter_simulator.infrastructure.config.spawn_config_loader import SpawnConfigLoader
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
import random
import uuid


async def main():
    """Main entrypoint for commuter spawning system"""
    
    config = {
        'enable_routespawner': True,  # Now using real RouteSpawner
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
        
        # Initialize config loader and geospatial client
        config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
        geo_client = GeospatialClient(base_url="http://localhost:6000")
        
        # RouteSpawner - using Route 1 (documentId from Strapi)
        route_spawner = RouteSpawner(
            reservoir=route_reservoir,
            config={},
            route_id="gg3pv3z19hhm117v9xth5ezq",  # Route 1 documentId
            config_loader=config_loader,
            geo_client=geo_client
        )
        
        # DepotSpawner - uses Speightstown Bus Terminal with documentId
        depot_spawner = DepotSpawner(
            reservoir=depot_reservoir,
            config={},
            depot_id="SPT_NORTH_01",
            depot_location=(13.252068, -59.642543),  # Speightstown coordinates
            depot_document_id="ft3t8jc5jnzg461uod6to898",  # Strapi v5 documentId
            strapi_url="http://localhost:1337",
            available_routes=None  # Will query from route-depots junction table
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
