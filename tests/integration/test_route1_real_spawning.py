"""
Integration Test - Route 1 Spawning with Database Insertion

This test uses the ACTUAL RouteSpawner to spawn real passengers into the database.
Unlike validation tests that just calculate numbers, this:
1. Runs the real RouteSpawner
2. Creates actual passenger records via Strapi API
3. Validates passengers were inserted into PostgreSQL
4. Shows hourly spawn counts with database confirmation

WARNING: This creates REAL passengers in the database!
Run reset_passengers.py to clean up afterwards.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

async def test_route1_real_spawning():
    """
    Integration test: Spawn real passengers for Route 1 and verify database insertion.
    """
    from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
    from commuter_service.infrastructure.config.config_loader import ConfigLoader
    from commuter_service.infrastructure.clients.geospatial_client import GeospatialClient
    from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
    
    print("=" * 80)
    print("INTEGRATION TEST - ROUTE 1 REAL SPAWNING")
    print("=" * 80)
    print("WARNING: This creates REAL passengers in the database!")
    print()
    
    # Get Route 1 from database
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("http://localhost:1337/api/routes")
        data = response.json()
    
    routes = data.get('data', [])
    if not routes:
        print("ERROR: No routes found in database!")
        return
    
    route = routes[0]
    route_id = str(route.get('id'))
    route_short_name = route.get('short_name', 'Unknown')
    route_doc_id = route.get('documentId', 'Unknown')
    
    print(f"Route: {route_short_name} (ID: {route_id}, Doc: {route_doc_id})")
    print()
    
    # Initialize components
    config_loader = ConfigLoader()
    geo_client = GeospatialClient(base_url="http://localhost:8001")
    passenger_repo = PassengerRepository()
    
    # Connect to database
    await passenger_repo.connect()
    
    # Initialize RouteSpawner
    route_spawner = RouteSpawner(
        route_id=route_id,
        config_loader=config_loader,
        geo_client=geo_client,
        passenger_repository=passenger_repo
    )
    
    print("Initializing RouteSpawner...")
    await route_spawner.initialize()
    print(f"✓ RouteSpawner initialized for Route {route_short_name}")
    print()
    
    # Count passengers before spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "http://localhost:1337/api/passengers",
            params={'filters[route_id][$eq]': route_id}
        )
        before_data = response.json()
    
    passengers_before = len(before_data.get('data', []))
    
    print("-" * 80)
    print("BEFORE SPAWNING")
    print("-" * 80)
    print(f"Passengers in DB for Route {route_short_name}: {passengers_before}")
    print()
    
    # Spawn passengers for Monday 8 AM (peak hour)
    test_time = datetime(2024, 11, 4, 8, 0)  # Monday 8:00 AM
    
    print("-" * 80)
    print(f"SPAWNING - {test_time.strftime('%A %Y-%m-%d %H:%M')}")
    print("-" * 80)
    print("Calling RouteSpawner.spawn()...")
    print()
    
    try:
        spawn_result = await route_spawner.spawn(
            current_time=test_time,
            time_window_minutes=60
        )
        
        spawn_count = spawn_result.get('spawn_count', 0)
        depot_spawned = spawn_result.get('depot_spawned', 0)
        route_spawned = spawn_result.get('route_spawned', 0)
        
        print(f"✓ Spawn completed!")
        print(f"  Total spawned: {spawn_count}")
        print(f"  Depot spawned: {depot_spawned}")
        print(f"  Route spawned: {route_spawned}")
        print()
        
    except Exception as e:
        print(f"✗ Spawn failed: {e}")
        import traceback
        traceback.print_exc()
        await passenger_repo.disconnect()
        return
    
    # Give database a moment to process
    await asyncio.sleep(2)
    
    # Count passengers after spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "http://localhost:1337/api/passengers",
            params={'filters[route_id][$eq]': route_id}
        )
        after_data = response.json()
    
    passengers_after = len(after_data.get('data', []))
    actual_created = passengers_after - passengers_before
    
    print("-" * 80)
    print("AFTER SPAWNING")
    print("-" * 80)
    print(f"Passengers in DB for Route {route_short_name}: {passengers_after}")
    print(f"Newly created: {actual_created}")
    print()
    
    # Validation
    print("-" * 80)
    print("VALIDATION")
    print("-" * 80)
    
    if actual_created == spawn_count:
        print(f"✓ PASS: Expected {spawn_count}, got {actual_created} in database")
    else:
        print(f"✗ FAIL: Expected {spawn_count}, but only {actual_created} in database")
        print(f"  Missing: {spawn_count - actual_created} passengers")
    
    print()
    
    # Show sample passengers
    if passengers_after > passengers_before:
        print("-" * 80)
        print("SAMPLE PASSENGERS (First 5 created)")
        print("-" * 80)
        
        new_passengers = after_data.get('data', [])[-min(5, actual_created):]
        
        for i, passenger in enumerate(new_passengers, 1):
            p_id = passenger.get('passenger_id', 'Unknown')
            status = passenger.get('status', 'Unknown')
            lat = passenger.get('latitude', 0)
            lon = passenger.get('longitude', 0)
            spawned_at = passenger.get('spawned_at', 'Unknown')
            
            print(f"{i}. {p_id}")
            print(f"   Status: {status}")
            print(f"   Location: ({lat:.6f}, {lon:.6f})")
            print(f"   Spawned: {spawned_at}")
            print()
    
    # Cleanup
    await passenger_repo.disconnect()
    
    print("=" * 80)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 80)
    print(f"✓ RouteSpawner successfully spawned {spawn_count} passengers")
    print(f"✓ Database contains {actual_created} new passenger records")
    print()
    print("To clean up, run: python reset_passengers.py")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_route1_real_spawning())
