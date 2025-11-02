"""""""""

Commuter Simulator - Main Entry Point

Commuter Simulator - Passenger Seeding ToolCommuter Simulator - Passenger Seeding Tool

Single entry point for commuter spawning system.

Orchestrates DepotSpawner and RouteSpawner with enable/disable control.

"""

Seeds database with realistic passenger manifest for simulation.Seeds database with realistic passenger manifest for simulation.

import asyncio

import sysBased on working integration test pattern.Based on working integration test pattern.

import logging

import configparser

from datetime import datetime

from pathlib import PathUsage:Usage:



# Add project root to path    python commuter_service/main.py --day monday --route 1    python commuter_service/main.py --day monday --route 1

sys.path.insert(0, str(Path(__file__).parent.parent))

    python commuter_service/main.py --day monday --route all --depot-spawning    python commuter_service/main.py --day monday --route all --depot-spawning

from commuter_service.core.application.coordinators import SpawnerCoordinator

from commuter_service.core.domain.services.spawning import DepotSpawner, RouteSpawner, SpawnerInterface, SpawnRequest""""""

from commuter_service.core.domain.services.reservoirs import RouteReservoir, DepotReservoir

from commuter_service.infrastructure.persistence.strapi.passenger_repository import PassengerRepository

from commuter_service.infrastructure.config.spawn_config_loader import SpawnConfigLoader

from commuter_service.infrastructure.geospatial.client import GeospatialClientimport asyncioimport asyncio

from commuter_service.infrastructure.database.strapi_client import StrapiApiClient

from arknet_transit_simulator.services.config_service import ConfigurationServiceimport sysimport sys

import random

import uuidimport loggingimport logging



import httpximport httpx

def load_infrastructure_config():

    """Load infrastructure endpoints from config.ini (ports, URLs, etc.)"""import argparseimport argparse

    config_path = Path(__file__).parent.parent / "config.ini"

from datetime import datetime, timedeltafrom datetime import datetime, timedelta

    if not config_path.exists():

        raise FileNotFoundError(f"config.ini not found at {config_path}")from pathlib import Pathfrom pathlib import Path



    config = configparser.ConfigParser()

    config.read(config_path, encoding='utf-8')

# Add project root to path# Add project root to path

    return {

        # Infrastructure endpoints onlysys.path.insert(0, str(Path(__file__).parent.parent))sys.path.insert(0, str(Path(__file__).parent.parent))

        'strapi_url': config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337'),

        'geospatial_port': config.getint('infrastructure', 'geospatial_port', fallback=6000),



        # Redis cache (infrastructure setting)from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawnerfrom commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner

        'enable_redis_cache': config.getboolean('commuter_service', 'enable_redis_cache', fallback=False),

    }from commuter_service.core.domain.spawner_engine.depot_spawner import DepotSpawnerfrom commuter_service.core.domain.spawner_engine.depot_spawner import DepotSpawner



from commuter_service.domain.services.reservoirs.route_reservoir import RouteReservoirfrom commuter_service.domain.services.reservoirs.route_reservoir import RouteReservoir

async def load_operational_config(config_service: ConfigurationService) -> dict:

    """Load operational configuration from database (operational-configurations)"""from commuter_service.domain.services.reservoirs.depot_reservoir import DepotReservoirfrom commuter_service.domain.services.reservoirs.depot_reservoir import DepotReservoir

    return {

        'continuous_mode': await config_service.get('passenger_spawning.operational.continuous_mode', default=True),from commuter_service.infrastructure.config.spawn_config_loader import SpawnConfigLoaderfrom commuter_service.infrastructure.config.spawn_config_loader import SpawnConfigLoader

        'spawn_interval_seconds': await config_service.get('passenger_spawning.operational.spawn_interval_seconds', default=60),

        'enable_routespawner': await config_service.get('passenger_spawning.operational.enable_routespawner', default=True),from commuter_service.infrastructure.geospatial.client import GeospatialClientfrom commuter_service.infrastructure.geospatial.client import GeospatialClient

        'enable_depotspawner': await config_service.get('passenger_spawning.operational.enable_depotspawner', default=True),

    }from commuter_service.infrastructure.persistence.strapi.passenger_repository import PassengerRepositoryfrom commuter_service.infrastructure.persistence.strapi.passenger_repository import PassengerRepository





async def main():

    """Main entrypoint for commuter spawning system"""



    logging.basicConfig(# Day of week to date mapping# Day of week to date mapping

        level=logging.INFO,

        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',DAY_TO_DATE = {DAY_TO_DATE = {

        datefmt='%H:%M:%S'

    )    'monday': datetime(2024, 11, 4),    'monday': datetime(2024, 11, 4),

    logger = logging.getLogger(__name__)

    'tuesday': datetime(2024, 11, 5),    'tuesday': datetime(2024, 11, 5),

    logger.info("="*80)

    logger.info("COMMUTER SPAWNING SYSTEM - STARTING")    'wednesday': datetime(2024, 11, 6),    'wednesday': datetime(2024, 11, 6),

    logger.info("="*80)

    'thursday': datetime(2024, 11, 7),    'thursday': datetime(2024, 11, 7),

    # Load infrastructure config (endpoints, ports)

    infra_config = load_infrastructure_config()    'friday': datetime(2024, 11, 8),    'friday': datetime(2024, 11, 8),

    logger.info(f"?? Strapi: {infra_config['strapi_url']}")

    logger.info(f"???  Geospatial: port {infra_config['geospatial_port']}")    'saturday': datetime(2024, 11, 2),    'saturday': datetime(2024, 11, 2),



    # Initialize operational config service (database-driven settings)    'sunday': datetime(2024, 11, 3),    'sunday': datetime(2024, 11, 3),

    config_service = ConfigurationService()

    await config_service.initialize()}}

    logger.info("??  ConfigurationService initialized")



    # Load operational settings from database

    operational_config = await load_operational_config(config_service)

    logger.info(f"?? Continuous mode: {operational_config['continuous_mode']}")

    logger.info(f"??  Spawn interval: {operational_config['spawn_interval_seconds']}s")async def main():async def main():

    logger.info(f"?? Route spawner: {'ENABLED' if operational_config['enable_routespawner'] else 'DISABLED'}")

    logger.info(f"?? Depot spawner: {'ENABLED' if operational_config['enable_depotspawner'] else 'DISABLED'}")    """Seed passengers for specified day and route"""    """Main entrypoint for passenger seeding"""



    # Merge configs for coordinator        

    config = {**infra_config, **operational_config}

    # Parse arguments    # Parse arguments

    passenger_repo = None

    strapi_client = None    parser = argparse.ArgumentParser(description='Seed passengers for simulation')    parser = argparse.ArgumentParser(description='Seed passengers for simulation')

    config_service_initialized = True

    parser.add_argument('--day', type=str, required=True,    parser.add_argument('--day', type=str, required=True,

    try:

        logger.info("?? [1/5] Querying routes and depots from database...")                       choices=list(DAY_TO_DATE.keys()),                       choices=list(DAY_TO_DATE.keys()),



        # Query all routes and depots from Strapi                       help='Day of week to seed')                       help='Day of week to seed')

        strapi_client = StrapiApiClient(base_url=infra_config['strapi_url'])

        await strapi_client.connect()    parser.add_argument('--route', type=str, default='all',    parser.add_argument('--route', type=str, default='all',



        routes = await strapi_client.get_all_routes()                       help='Route short_name (e.g., "1"), or "all"')                       help='Route short_name (e.g., "1"), or "all"')

        depots = await strapi_client.get_all_depots()

    parser.add_argument('--depot-spawning', action='store_true',    parser.add_argument('--depot-spawning', action='store_true',

        # Filter to active routes with spawn configs (spawn configs are queried per-route by RouteSpawner)

        active_routes = [r for r in routes if r.is_active]                       help='Also spawn depot passengers')                       help='Also spawn depot passengers')

        active_depots = [d for d in depots if d.is_active]

        

        logger.info(f"?? Found {len(active_routes)} active routes")

        logger.info(f"?? Found {len(active_depots)} active depots")    args = parser.parse_args()    args = parser.parse_args()



        if not active_routes and not active_depots:        

            logger.warning("??  No active routes or depots found in database!")

            return    logging.basicConfig(    logging.basicConfig(



        logger.info("?? [2/5] Initializing PassengerRepository...")        level=logging.INFO,        level=logging.INFO,

        passenger_repo = PassengerRepository(strapi_url=infra_config['strapi_url'])

        await passenger_repo.connect()        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',

        logger.info("? PassengerRepository connected")

        datefmt='%H:%M:%S'        datefmt='%H:%M:%S'

        logger.info("???  [3/5] Creating reservoirs...")

    )    )

        # Single route reservoir (shared by all route spawners)

        route_reservoir = RouteReservoir(    logger = logging.getLogger(__name__)    logger = logging.getLogger(__name__)

            passenger_repository=passenger_repo,

            enable_redis_cache=infra_config['enable_redis_cache']        

        )

        logger.info("? Route reservoir created")    print("=" * 80)    logger.info("="*80)



        logger.info("?? [4/5] Creating spawners...")    print("PASSENGER SEEDING")    logger.info("COMMUTER SPAWNING SYSTEM - STARTING")



        # Initialize shared resources    print("=" * 80)    logger.info("="*80)

        config_loader = SpawnConfigLoader(api_base_url=f"{infra_config['strapi_url']}/api")

        geo_client = GeospatialClient(base_url=f"http://localhost:{infra_config['geospatial_port']}")    print(f"Day: {args.day.upper()}")    



        spawners = []    print(f"Route: {args.route}")    # Load infrastructure config (endpoints, ports)



        # Create RouteSpawner for EACH active route (if enabled)    print(f"Depot spawning: {'YES' if args.depot_spawning else 'NO'}")    infra_config = load_infrastructure_config()

        if operational_config['enable_routespawner'] and active_routes:

            for route in active_routes:    print("=" * 80)    logger.info(f" Strapi: {infra_config['strapi_url']}")

                route_spawner = RouteSpawner(

                    reservoir=route_reservoir,    print()    logger.info(f" Geospatial: port {infra_config['geospatial_port']}")

                    config={},

                    route_id=route.document_id,  # Use documentId for API queries        

                    config_loader=config_loader,

                    geo_client=geo_client    base_date = DAY_TO_DATE[args.day]    # Initialize operational config service (database-driven settings)

                )

                spawners.append(route_spawner)        config_service = ConfigurationService()

                logger.info(f"  ? RouteSpawner created for route: {route.short_name}")

    # Get routes from database    await config_service.initialize()

        # Create DepotSpawner for EACH active depot (if enabled)

        if operational_config['enable_depotspawner'] and active_depots:    print("Fetching routes from database...")    logger.info(" ConfigurationService initialized")

            for depot in active_depots:

                # Each depot gets its own reservoir    async with httpx.AsyncClient(timeout=10.0) as client:    

                depot_reservoir = DepotReservoir(

                    depot_id=depot.depot_id,        response = await client.get("http://localhost:1337/api/routes")    # Load operational settings from database

                    passenger_repository=passenger_repo,

                    enable_redis_cache=infra_config['enable_redis_cache']        data = response.json()    operational_config = await load_operational_config(config_service)

                )

        logger.info(f" Continuous mode: {operational_config['continuous_mode']}")

                depot_spawner = DepotSpawner(

                    reservoir=depot_reservoir,    routes = data.get('data', [])    logger.info(f" Spawn interval: {operational_config['spawn_interval_seconds']}s")

                    config={},

                    depot_id=depot.depot_id,    if not routes:    logger.info(f" Route spawner: {'ENABLED' if operational_config['enable_routespawner'] else 'DISABLED'}")

                    depot_location=(depot.latitude, depot.longitude),

                    depot_document_id=depot.document_id,  # Use documentId for route-depot queries        print("ERROR: No routes found!")    logger.info(f" Depot spawner: {'ENABLED' if operational_config['enable_depotspawner'] else 'DISABLED'}")

                    strapi_url=infra_config['strapi_url'],

                    available_routes=None  # Will query from route-depots junction table        return    

                )

                spawners.append(depot_spawner)        # Merge configs for coordinator

                logger.info(f"  ? DepotSpawner created for depot: {depot.name}")

    # Filter routes    config = {**infra_config, **operational_config}

        if not spawners:

            logger.warning("??  No spawners created! Check enable flags and database content.")    if args.route == 'all':    

            return

        selected_routes = routes    passenger_repo = None

        logger.info(f"?? Total spawners created: {len(spawners)}")

        print(f"?? Seeding ALL {len(routes)} routes")    strapi_client = None

        logger.info("?? [5/5] Starting coordinator...")

        coordinator = SpawnerCoordinator(spawners=spawners, config=config)    else:    config_service_initialized = True



        # CRITICAL: time_window_minutes MUST equal the actual simulation time per cycle        selected_routes = [r for r in routes if r.get('short_name') == args.route]    

        # to maintain proper Poisson statistics. If cycles run every 10s, time_window = 10/60 minutes.

        # This ensures spawn rates are correctly scaled to real-world time, not cycle frequency.        if not selected_routes:    try:

        spawn_interval_seconds = operational_config.get('spawn_interval_seconds', 60)

        time_window_minutes = spawn_interval_seconds / 60.0            print(f"ERROR: Route '{args.route}' not found!")        logger.info(" [1/5] Querying routes and depots from database...")



        logger.info(f"??  Spawn interval: {spawn_interval_seconds}s = {time_window_minutes:.4f} minutes per cycle")            print(f"Available: {', '.join([r.get('short_name', '?') for r in routes])}")        

        await coordinator.start(current_time=datetime.utcnow(), time_window_minutes=time_window_minutes)

            return        # Query all routes and depots from Strapi

        logger.info("="*80)

        logger.info("? SPAWNING CYCLE COMPLETE")        route = selected_routes[0]        strapi_client = StrapiApiClient(base_url=infra_config['strapi_url'])

        logger.info("="*80)

        print(f"?? Route {route.get('short_name')} - {route.get('long_name', 'N/A')}")        await strapi_client.connect()

    except KeyboardInterrupt:

        logger.info("?? Shutting down...")            

    except Exception as e:

        logger.error(f"? Error: {e}", exc_info=True)    print()        routes = await strapi_client.get_all_routes()

    finally:

        if strapi_client:            depots = await strapi_client.get_all_depots()

            await strapi_client.close()

        if passenger_repo:    # Initialize components        

            await passenger_repo.disconnect()

        if config_service_initialized:    passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")        # Filter to active routes with spawn configs (spawn configs are queried per-route by RouteSpawner)

            await config_service.shutdown()

        logger.info("?? Shutdown complete")    await passenger_repo.connect()        active_routes = [r for r in routes if r.is_active]



    logger.info("? Database connected")        active_depots = [d for d in depots if d.is_active]

if __name__ == "__main__":

    asyncio.run(main())            


    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")        logger.info(f" Found {len(active_routes)} active routes")

    geo_client = GeospatialClient(base_url="http://localhost:6000")        logger.info(f" Found {len(active_depots)} active depots")

            

    # Create route spawners        if not active_routes and not active_depots:

    route_spawners = []            logger.warning("??  No active routes or depots found in database!")

    for route in selected_routes:            return

        route_doc_id = route.get('documentId')        

                logger.info(" [2/5] Initializing PassengerRepository...")

        # Get depot for route        passenger_repo = PassengerRepository(strapi_url=infra_config['strapi_url'])

        async with httpx.AsyncClient(timeout=10.0) as client:        await passenger_repo.connect()

            try:        logger.info(" PassengerRepository connected")

                response = await client.get(f"http://localhost:6000/routes/by-document-id/{route_doc_id}/depot")        

                depot_info = response.json().get('depot')        logger.info(" [3/5] Creating reservoirs...")

            except:        

                logger.warning(f"No depot for route {route.get('short_name')}")        # Single route reservoir (shared by all route spawners)

                continue        route_reservoir = RouteReservoir(

                    passenger_repository=passenger_repo,

        route_reservoir = RouteReservoir(            enable_redis_cache=infra_config['enable_redis_cache']

            passenger_repository=passenger_repo,        )

            enable_redis_cache=False        logger.info(" Route reservoir created")

        )        

                logger.info(" [4/5] Creating spawners...")

        spawner = RouteSpawner(        

            reservoir=route_reservoir,        # Initialize shared resources

            config={},        config_loader = SpawnConfigLoader(api_base_url=f"{infra_config['strapi_url']}/api")

            route_id=route_doc_id,        geo_client = GeospatialClient(base_url=f"http://localhost:{infra_config['geospatial_port']}")

            config_loader=config_loader,        

            geo_client=geo_client        spawners = []

        )        

        route_spawners.append((route, spawner, route_reservoir))        # Create RouteSpawner for EACH active route (if enabled)

        logger.info(f"? RouteSpawner: Route {route.get('short_name')}")        if operational_config['enable_routespawner'] and active_routes:

                for route in active_routes:

    # Create depot spawners if enabled                route_spawner = RouteSpawner(

    depot_spawners = []                    reservoir=route_reservoir,

    if args.depot_spawning:                    config={},

        async with httpx.AsyncClient(timeout=10.0) as client:                    route_id=route.document_id,  # Use documentId for API queries

            response = await client.get("http://localhost:1337/api/depots")                    config_loader=config_loader,

            depots_data = response.json()                    geo_client=geo_client

                        )

        depots = depots_data.get('data', [])                spawners.append(route_spawner)

        print(f"\n?? Found {len(depots)} depots")                logger.info(f" ? RouteSpawner created for route: {route.short_name}")

                

        for depot in depots:        # Create DepotSpawner for EACH active depot (if enabled)

            depot_doc_id = depot.get('documentId')        if operational_config['enable_depotspawner'] and active_depots:

            depot_coords = depot.get('location', {}).get('coordinates', [])            for depot in active_depots:

            if len(depot_coords) != 2:                # Each depot gets its own reservoir

                continue                depot_reservoir = DepotReservoir(

                                depot_id=depot.depot_id,

            depot_location = (depot_coords[1], depot_coords[0])                    passenger_repository=passenger_repo,

                                enable_redis_cache=infra_config['enable_redis_cache']

            depot_reservoir = DepotReservoir(                )

                depot_id=depot_doc_id,                

                passenger_repository=passenger_repo,                depot_spawner = DepotSpawner(

                enable_redis_cache=False                    reservoir=depot_reservoir,

            )                    config={},

                                depot_id=depot.depot_id,

            spawner = DepotSpawner(                    depot_location=(depot.latitude, depot.longitude),

                reservoir=depot_reservoir,                    depot_document_id=depot.document_id,  # Use documentId for route-depot queries

                config={},                    strapi_url=infra_config['strapi_url'],

                depot_id=depot_doc_id,                    available_routes=None  # Will query from route-depots junction table

                depot_location=depot_location,                )

                available_routes=[r.get('documentId') for r in selected_routes],                spawners.append(depot_spawner)

                depot_document_id=depot_doc_id,                logger.info(f" ? DepotSpawner created for depot: {depot.name}")

                config_loader=config_loader,        

                geo_client=geo_client        if not spawners:

            )            logger.warning("??  No spawners created! Check enable flags and database content.")

            depot_spawners.append((depot, spawner, depot_reservoir))            return

            logger.info(f"? DepotSpawner: {depot.get('name')}")        

            logger.info(f" Total spawners created: {len(spawners)}")

    print()        

    print("=" * 80)        logger.info(" [5/5] Starting coordinator...")

    print(f"SEEDING {args.day.upper()} {base_date.strftime('%Y-%m-%d')}")        coordinator = SpawnerCoordinator(spawners=spawners, config=config)

    print("=" * 80)        

    print()        # CRITICAL: time_window_minutes MUST equal the actual simulation time per cycle

            # to maintain proper Poisson statistics. If cycles run every 10s, time_window = 10/60 minutes.

    # Seed for each hour        # This ensures spawn rates are correctly scaled to real-world time, not cycle frequency.

    total_route = 0        spawn_interval_seconds = operational_config.get('spawn_interval_seconds', 60)

    total_depot = 0        time_window_minutes = spawn_interval_seconds / 60.0

            

    for hour in range(24):        logger.info(f" ??  Spawn interval: {spawn_interval_seconds}s = {time_window_minutes:.4f} minutes per cycle")

        current_time = base_date.replace(hour=hour, minute=0, second=0)        await coordinator.start(current_time=datetime.utcnow(), time_window_minutes=time_window_minutes)

        hour_route = 0        

        hour_depot = 0        logger.info("="*80)

                logger.info(" SPAWNING CYCLE COMPLETE")

        print(f"? {current_time.strftime('%H:%M')} - ", end='', flush=True)        logger.info("="*80)

                

        # Route passengers    except KeyboardInterrupt:

        for route, spawner, reservoir in route_spawners:        logger.info("  Shutting down...")

            try:    except Exception as e:

                spawn_requests = await spawner.spawn(current_time=current_time, time_window_minutes=60)        logger.error(f" Error: {e}", exc_info=True)

                if spawn_requests:    finally:

                    successful, failed = await reservoir.push_batch(spawn_requests)        if strapi_client:

                    hour_route += successful            await strapi_client.close()

            except Exception as e:        if passenger_repo:

                logger.error(f"Route spawn error: {e}")            await passenger_repo.disconnect()

                if config_service_initialized:

        # Depot passengers            await config_service.shutdown()

        for depot, spawner, reservoir in depot_spawners:        logger.info(" Shutdown complete")

            try:

                spawn_requests = await spawner.spawn(current_time=current_time, time_window_minutes=60)

                if spawn_requests:if __name__ == "__main__":

                    successful, failed = await reservoir.push_batch(spawn_requests)    asyncio.run(main())

                    hour_depot += successful
            except Exception as e:
                logger.error(f"Depot spawn error: {e}")
        
        hour_total = hour_route + hour_depot
        total_route += hour_route
        total_depot += hour_depot
        
        if args.depot_spawning:
            print(f"Route: {hour_route:>3}, Depot: {hour_depot:>3}, Total: {hour_total:>3}")
        else:
            print(f"Route: {hour_route:>3}")
        
        await asyncio.sleep(0.1)
    
    # Cleanup
    await passenger_repo.disconnect()
    
    # Results
    print()
    print("=" * 80)
    print("? SEEDING COMPLETE!")
    print("=" * 80)
    print(f"Route passengers: {total_route}")
    if args.depot_spawning:
        print(f"Depot passengers: {total_depot}")
        print(f"Total: {total_route + total_depot}")
    print()
    print("Next steps:")
    print("  python scripts/show_route_manifest.py --day monday --start-hour 7 --end-hour 9")
    print("  python scripts/check_spawn_data.py")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
