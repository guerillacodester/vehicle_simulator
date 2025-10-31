"""
Commuter Simulator - Main Entry Point

Single entry point for commuter spawning system.
Orchestrates DepotSpawner and RouteSpawner with enable/disable control.
"""

import asyncio
import sys
import logging
import configparser
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
from commuter_simulator.infrastructure.database.strapi_client import StrapiApiClient
from arknet_transit_simulator.services.config_service import ConfigurationService
import random
import uuid


def load_infrastructure_config():
    """Load infrastructure endpoints from config.ini (ports, URLs, etc.)"""
    config_path = Path(__file__).parent.parent / "config.ini"
    
    if not config_path.exists():
        raise FileNotFoundError(f"config.ini not found at {config_path}")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    return {
        # Infrastructure endpoints only
        'strapi_url': config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337'),
        'geospatial_port': config.getint('infrastructure', 'geospatial_port', fallback=6000),
        
        # Redis cache (infrastructure setting)
        'enable_redis_cache': config.getboolean('commuter_simulator', 'enable_redis_cache', fallback=False),
    }


async def load_operational_config(config_service: ConfigurationService) -> dict:
    """Load operational configuration from database (operational-configurations)"""
    return {
        'continuous_mode': await config_service.get('passenger_spawning.operational.continuous_mode', default=True),
        'spawn_interval_seconds': await config_service.get('passenger_spawning.operational.spawn_interval_seconds', default=60),
        'enable_routespawner': await config_service.get('passenger_spawning.operational.enable_routespawner', default=True),
        'enable_depotspawner': await config_service.get('passenger_spawning.operational.enable_depotspawner', default=True),
    }


async def main():
    """Main entrypoint for commuter spawning system"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("="*80)
    logger.info("COMMUTER SPAWNING SYSTEM - STARTING")
    logger.info("="*80)
    
    # Load infrastructure config (endpoints, ports)
    infra_config = load_infrastructure_config()
    logger.info(f" Strapi: {infra_config['strapi_url']}")
    logger.info(f" Geospatial: port {infra_config['geospatial_port']}")
    
    # Initialize operational config service (database-driven settings)
    config_service = ConfigurationService()
    await config_service.initialize()
    logger.info(" ConfigurationService initialized")
    
    # Load operational settings from database
    operational_config = await load_operational_config(config_service)
    logger.info(f" Continuous mode: {operational_config['continuous_mode']}")
    logger.info(f" Spawn interval: {operational_config['spawn_interval_seconds']}s")
    logger.info(f" Route spawner: {'ENABLED' if operational_config['enable_routespawner'] else 'DISABLED'}")
    logger.info(f" Depot spawner: {'ENABLED' if operational_config['enable_depotspawner'] else 'DISABLED'}")
    
    # Merge configs for coordinator
    config = {**infra_config, **operational_config}
    
    passenger_repo = None
    strapi_client = None
    config_service_initialized = True
    
    try:
        logger.info(" [1/5] Querying routes and depots from database...")
        
        # Query all routes and depots from Strapi
        strapi_client = StrapiApiClient(base_url=infra_config['strapi_url'])
        await strapi_client.connect()
        
        routes = await strapi_client.get_all_routes()
        depots = await strapi_client.get_all_depots()
        
        # Filter to active routes with spawn configs (spawn configs are queried per-route by RouteSpawner)
        active_routes = [r for r in routes if r.is_active]
        active_depots = [d for d in depots if d.is_active]
        
        logger.info(f" Found {len(active_routes)} active routes")
        logger.info(f" Found {len(active_depots)} active depots")
        
        if not active_routes and not active_depots:
            logger.warning("⚠️  No active routes or depots found in database!")
            return
        
        logger.info(" [2/5] Initializing PassengerRepository...")
        passenger_repo = PassengerRepository(strapi_url=infra_config['strapi_url'])
        await passenger_repo.connect()
        logger.info(" PassengerRepository connected")
        
        logger.info(" [3/5] Creating reservoirs...")
        
        # Single route reservoir (shared by all route spawners)
        route_reservoir = RouteReservoir(
            passenger_repository=passenger_repo,
            enable_redis_cache=infra_config['enable_redis_cache']
        )
        logger.info(" Route reservoir created")
        
        logger.info(" [4/5] Creating spawners...")
        
        # Initialize shared resources
        config_loader = SpawnConfigLoader(api_base_url=f"{infra_config['strapi_url']}/api")
        geo_client = GeospatialClient(base_url=f"http://localhost:{infra_config['geospatial_port']}")
        
        spawners = []
        
        # Create RouteSpawner for EACH active route (if enabled)
        if operational_config['enable_routespawner'] and active_routes:
            for route in active_routes:
                route_spawner = RouteSpawner(
                    reservoir=route_reservoir,
                    config={},
                    route_id=route.id,  # Use actual route ID from database
                    config_loader=config_loader,
                    geo_client=geo_client
                )
                spawners.append(route_spawner)
                logger.info(f" ✅ RouteSpawner created for route: {route.short_name}")
        
        # Create DepotSpawner for EACH active depot (if enabled)
        if operational_config['enable_depotspawner'] and active_depots:
            for depot in active_depots:
                # Each depot gets its own reservoir
                depot_reservoir = DepotReservoir(
                    depot_id=depot.depot_id,
                    passenger_repository=passenger_repo,
                    enable_redis_cache=infra_config['enable_redis_cache']
                )
                
                depot_spawner = DepotSpawner(
                    reservoir=depot_reservoir,
                    config={},
                    depot_id=depot.depot_id,
                    depot_location=(depot.latitude, depot.longitude),
                    depot_document_id=str(depot.id),  # Use documentId for route-depot queries
                    strapi_url=infra_config['strapi_url'],
                    available_routes=None  # Will query from route-depots junction table
                )
                spawners.append(depot_spawner)
                logger.info(f" ✅ DepotSpawner created for depot: {depot.name}")
        
        if not spawners:
            logger.warning("⚠️  No spawners created! Check enable flags and database content.")
            return
        
        logger.info(f" Total spawners created: {len(spawners)}")
        
        logger.info(" [5/5] Starting coordinator...")
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
        if strapi_client:
            await strapi_client.close()
        if passenger_repo:
            await passenger_repo.disconnect()
        if config_service_initialized:
            await config_service.shutdown()
        logger.info(" Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
