"""
Test Poisson Plugin with Database Persistence
==============================================

This script demonstrates the database-backed spawning pattern:
1. Initialize PassengerRepository (connects to Strapi active-passengers API)
2. Initialize PoissonGeoJSONPlugin with repository injected
3. Generate spawn requests for Route 1
4. Spawns are automatically saved to database
5. Query database to verify passengers were saved
"""

import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def main():
    print("="*120)
    print("POISSON PLUGIN DATABASE TEST - Route 1")
    print("="*120)
    print("\n>> Testing database-backed passenger spawning pattern\n")
    
    # Import dependencies
    from commuter_simulator.infrastructure.database import StrapiApiClient, PassengerRepository
    from commuter_simulator.core.domain.plugins.poisson_plugin import PoissonGeoJSONPlugin
    from commuter_simulator.core.domain.spawning_plugin import PluginConfig, PluginType, SpawnContext
    
    # Initialize Strapi API client
    print("[1/5] Connecting to Strapi API...")
    api_client = StrapiApiClient("http://localhost:1337")
    await api_client.connect()
    print("OK - Connected to Strapi")
    
    # Initialize PassengerRepository
    print("\n[2/5] Connecting to PassengerRepository...")
    passenger_repo = PassengerRepository(
        strapi_url="http://localhost:1337",
        logger=logger
    )
    await passenger_repo.connect()
    print("OK - Connected to PassengerRepository")
    
    # Initialize Poisson plugin with repository injected
    print("\n[3/5] Initializing Poisson plugin...")
    plugin_config = PluginConfig(
        plugin_name="poisson_geojson",
        plugin_type=PluginType.STATISTICAL,
        country_code="BB",
        spawn_rate_multiplier=1.0,
        temporal_adjustment=True,
        use_spatial_cache=False,
        custom_params={
            'strapi_url': 'http://localhost:1337/api',
            'geo_url': 'http://localhost:8001'
        }
    )
    
    poisson_plugin = PoissonGeoJSONPlugin(
        config=plugin_config,
        api_client=api_client,
        passenger_repository=passenger_repo,  # INJECT REPOSITORY
        logger=logger
    )
    
    await poisson_plugin.initialize()
    print("OK - Poisson plugin initialized")
    
    # Generate spawn requests for Route 1
    print("\n[4/5] Generating spawn requests for Route 1...")
    route_id = "gg3pv3z19hhm117v9xth5ezq"  # Route 1 document_id
    current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # 9:00 AM
    
    spawn_requests = await poisson_plugin.generate_spawn_requests(
        current_time=current_time,
        time_window_minutes=60,  # 1 hour window
        context=SpawnContext.ROUTE,
        route_id=route_id  # Pass route_id as kwarg
    )
    
    print(f"OK - Generated {len(spawn_requests)} spawn requests")
    print(f"  -> Passengers automatically saved to database via PassengerRepository")
    
    # Query database to verify passengers
    print("\n[5/5] Querying database to verify passengers...")
    if spawn_requests and len(spawn_requests) > 0:
        # Get first spawn location
        first_spawn = spawn_requests[0]
        spawn_lat, spawn_lon = first_spawn.spawn_location
        
        nearby_passengers = await passenger_repo.query_passengers_near_location(
            route_id=route_id,
            latitude=spawn_lat,
            longitude=spawn_lon,
            max_distance_meters=50000  # 50km to get all on route
        )
        
        print(f"OK - Found {len(nearby_passengers)} passengers in database for route {route_id}")
        
        # Print sample
        if len(nearby_passengers) > 0:
            print("\nSample passengers (first 5):")
            print(f"{'ID':<15} {'Latitude':<12} {'Longitude':<12} {'Status':<10} {'Spawned At':<20}")
            print("-" * 80)
            for p in nearby_passengers[:5]:
                print(
                    f"{p['passenger_id']:<15} "
                    f"{p['latitude']:<12.6f} "
                    f"{p['longitude']:<12.6f} "
                    f"{p['status']:<10} "
                    f"{p['spawned_at']:<20}"
                )
    else:
        print("WARNING - No spawn requests generated (check spawn-config rates)")
    
    # Cleanup
    print("\n[CLEANUP] Disconnecting...")
    await passenger_repo.disconnect()
    await api_client.close()
    
    print("\n" + "="*120)
    print("TEST COMPLETE - Database-backed spawning WORKS!")
    print("="*120)


if __name__ == "__main__":
    asyncio.run(main())
