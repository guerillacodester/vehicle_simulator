"""Test RouteSpawner to see building counts and spawn calculation"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test():
    from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
    from commuter_service.core.domain.reservoirs.route_reservoir import RouteReservoir
    from commuter_service.infrastructure.spawn.config_loader import SpawnConfigLoader
    from commuter_service.infrastructure.geospatial.client import GeospatialClient
    from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
    import httpx
    
    # Get Route 1
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:1337/api/routes?filters[short_name][$eq]=1")
        route = r.json()['data'][0]
        route_doc_id = route['documentId']
    
    print(f"Testing RouteSpawner for Route 1 (documentId: {route_doc_id})")
    print("=" * 80)
    
    # Initialize components
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
        route_id=route_doc_id,
        config_loader=config_loader,
        geo_client=geo_client
    )
    
    # Test spawn at peak hour (Monday 8 AM)
    test_time = datetime(2024, 11, 4, 8, 0, 0)
    
    print(f"Test time: {test_time} (Monday 8 AM)")
    print()
    print("Spawning (check logs for building count)...")
    
    spawn_requests = await route_spawner.spawn(
        current_time=test_time,
        time_window_minutes=60
    )
    
    print(f"Generated {len(spawn_requests)} spawn requests")
    
    await passenger_repo.disconnect()

asyncio.run(test())
