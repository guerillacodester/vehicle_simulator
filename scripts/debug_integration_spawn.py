"""
Debug the integration test spawning - check what RouteSpawner.spawn() returns
"""
import asyncio
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def debug_spawn():
    from commuter_simulator.core.domain.spawner_engine.route_spawner import RouteSpawner
    from commuter_simulator.core.domain.reservoirs.route_reservoir import RouteReservoir
    from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader
    from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
    from commuter_simulator.infrastructure.database.passenger_repository import PassengerRepository
    
    print("Initializing components...")
    passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")
    await passenger_repo.connect()
    
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    geo_client = GeospatialClient(base_url="http://localhost:6000")
    
    route_reservoir = RouteReservoir(
        passenger_repository=passenger_repo,
        enable_redis_cache=False
    )
    
    route_spawner = RouteSpawner(
        reservoir=route_reservoir,
        config={},
        route_id="qcqg8vbhd20aiu5yj1rjp1s8",  # Route 1 documentId
        config_loader=config_loader,
        geo_client=geo_client
    )
    
    print("\nTesting spawns at different hours:")
    print("=" * 80)
    
    # Test Saturday 2024-11-02 at different hours
    test_hours = [5, 6, 7, 8, 9, 10, 15, 17, 20]
    
    for hour in test_hours:
        spawn_time = datetime(2024, 11, 2, hour, 0, 0)
        
        try:
            spawn_requests = await route_spawner.spawn(
                current_time=spawn_time,
                time_window_minutes=60
            )
            
            print(f"Hour {hour:02d}:00 - Generated {len(spawn_requests)} spawn requests")
            
            if len(spawn_requests) > 0:
                # Show first request details
                first = spawn_requests[0]
                print(f"  Sample: origin={first.origin_lat:.6f},{first.origin_lon:.6f}, "
                      f"context={first.spawn_context}")
        
        except Exception as e:
            print(f"Hour {hour:02d}:00 - ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    await passenger_repo.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_spawn())
