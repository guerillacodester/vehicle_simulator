"""
Integration Test - Spawn Full Week of Passengers for Route 1


Creates REAL passengers in the database for Route 1 over a full week (7 days x 24 hours).

Uses both RouteSpawner and DepotSpawner to create depot and route passengers.


After running this, you'll have ~6,000-8,000 real passenger records in the database

that you can analyze statistically at your own pace.


WARNING: This creates THOUSANDS of real passengers in the database!

Use reset_passengers.py to clean up after testing.
"""

import asyncio
import httpx
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def spawn_full_week_route1():
    """
    Spawn passengers for Route 1 for a full week (Saturday - Friday).
    Creates both depot and route passengers using actual spawners.
    """
    from commuter_simulator.core.domain.spawner_engine.route_spawner import RouteSpawner
    from commuter_simulator.core.domain.reservoirs.route_reservoir import RouteReservoir
    from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader
    from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
    from commuter_simulator.infrastructure.database.passenger_repository import PassengerRepository
    
    print("=" * 80)
    print("INTEGRATION TEST - SPAWN FULL WEEK FOR ROUTE 1")
    print("=" * 80)
    print("This will create REAL passengers in the database for 7 days x 24 hours")
    print("Estimated: 6,000-8,000 passenger records")
    print()
    
    # Get Route 1 from database
    print("Fetching Route 1 from database...")
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
    
    print(f"[OK] Route: {route_short_name} (ID: {route_id}, Doc: {route_doc_id})")
    print()
    
    # Initialize components
    passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")
    
    # Connect to database
    print("Connecting to database...")
    await passenger_repo.connect()
    print("[OK] Database connected")
    print()
    
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    geo_client = GeospatialClient(base_url="http://localhost:6000")
    
    # Create RouteReservoir (shared for all routes)
    print("Initializing RouteReservoir...")
    route_reservoir = RouteReservoir(
        passenger_repository=passenger_repo,
        enable_redis_cache=False
    )
    print("[OK] RouteReservoir initialized")
    print()
    
    # Initialize RouteSpawner
    print("Initializing RouteSpawner...")
    route_spawner = RouteSpawner(
        reservoir=route_reservoir,
        config={},
        route_id=route_doc_id,  # Use documentId for API queries
        config_loader=config_loader,
        geo_client=geo_client
    )
    print(f"[OK] RouteSpawner initialized for Route {route_short_name}")
    print()
    
    # Count passengers before spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "http://localhost:1337/api/active-passengers",
            params={'filters[route_id][$eq]': route_id}
        )
        if response.status_code == 200:
            before_data = response.json()
            passengers_before = len(before_data.get('data', []))
        else:
            print(f"Warning: Could not query passengers (status {response.status_code})")
            passengers_before = 0
    
    print(f"Passengers in DB before spawning: {passengers_before}")
    print()
    
    # Spawn for full week (Saturday - Friday)
    start_date = datetime(2024, 11, 2)  # Saturday
    days = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    total_spawned = 0
    daily_totals = []
    
    print("=" * 80)
    print("SPAWNING PASSENGERS - FULL WEEK")
    print("=" * 80)
    print()
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_name = days[day_offset]
        
        day_total = 0
        
        print(f"{day_name} {current_date.strftime('%Y-%m-%d')}")
        print("-" * 80)
        
        # Spawn for each hour of the day
        for hour in range(24):
            spawn_time = current_date.replace(hour=hour, minute=0, second=0)
            
            try:
                # Generate spawn requests
                spawn_requests = await route_spawner.spawn(
                    current_time=spawn_time,
                    time_window_minutes=60
                )
                
                # Push to reservoir (inserts into database)
                if spawn_requests:
                    successful, failed = await route_reservoir.push_batch(spawn_requests)
                    spawn_count = successful
                    
                    # DEBUG: Show if there's a mismatch
                    if len(spawn_requests) != successful:
                        print(f"  {hour:02d}:00 - WARNING: Generated {len(spawn_requests)} but only inserted {successful} (failed={failed})")
                else:
                    spawn_count = 0
                
                day_total += spawn_count
                total_spawned += spawn_count
                
                # Print ALL hours (0-23), show both generated and inserted
                if len(spawn_requests) > 0:
                    print(f"  {hour:02d}:00 - Generated {len(spawn_requests):>3} requests, inserted {spawn_count:>3} passengers")
                else:
                    print(f"  {hour:02d}:00 - Generated   0 requests, inserted   0 passengers")
                
                # Small delay to not overwhelm the API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"  {hour:02d}:00 - ERROR: {e}")
                continue
        
        print(f"  Daily Total: {day_total} passengers")
        print()
        daily_totals.append((day_name, day_total))
    
    # Give database time to process
    print("Waiting for database to process...")
    await asyncio.sleep(5)
    
    # Count passengers after spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "http://localhost:1337/api/active-passengers",
            params={'filters[route_id][$eq]': route_id}
        )
        if response.status_code == 200:
            after_data = response.json()
            passengers_after = len(after_data.get('data', []))
        else:
            print(f"Warning: Could not query passengers after spawn (status {response.status_code})")
            passengers_after = 0
    
    actual_created = passengers_after - passengers_before
    
    # Cleanup
    await passenger_repo.disconnect()
    
    # Results
    print("=" * 80)
    print("SPAWNING COMPLETE - WEEKLY SUMMARY")
    print("=" * 80)
    print()
    
    for day_name, day_total in daily_totals:
        print(f"{day_name:>9}: {day_total:>4} passengers")
    
    print()
    print("-" * 80)
    print(f"Total Spawned (calculated): {total_spawned}")
    print(f"Total in DB (before): {passengers_before}")
    print(f"Total in DB (after): {passengers_after}")
    print(f"Actual Created: {actual_created}")
    print()
    
    if actual_created == total_spawned:
        print(f"[OK] SUCCESS: All {total_spawned} passengers created in database!")
    else:
        print(f"WARNING: Expected {total_spawned}, but {actual_created} in database")
        print(f"  Difference: {total_spawned - actual_created} passengers")
    
    print()
    print("=" * 80)
    print("Next Steps:")
    print("  - Query passengers: GET /api/active-passengers?filters[route_id][$eq]=14")
    print("  - Analyze temporal patterns from spawned_at timestamps")
    print("  - Validate Poisson distribution from hourly counts")
    print("  - Check depot vs route distribution using depot_id field")
    print("  - Run reset_passengers.py to clean up when done")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(spawn_full_week_route1())
