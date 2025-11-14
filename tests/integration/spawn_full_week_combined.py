"""
Integration Test - Spawn Full Week COMBINED (Depot + Route) for Route 1

Creates REAL passengers in the database for Route 1 over a full week (7 days x 24 hours).

Uses BOTH DepotSpawner AND RouteSpawner simultaneously to create:
- Depot passengers: Spawned at terminal/depot location
- Route passengers: Spawned along route corridor

This simulates REALISTIC passenger demand where both types spawn concurrently.

After running this, you'll have ~6,000-8,000 real passenger records in the database.

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


async def spawn_full_week_combined():
    """
    Spawn passengers for Route 1 for a full week (Saturday - Friday).
    Creates BOTH depot and route passengers using actual spawners SIMULTANEOUSLY.
    """
    from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
    from commuter_service.core.domain.spawner_engine.depot_spawner import DepotSpawner
    from commuter_service.core.domain.reservoirs.route_reservoir import RouteReservoir
    from commuter_service.core.domain.reservoirs.depot_reservoir import DepotReservoir
    from commuter_service.infrastructure.spawn.config_loader import SpawnConfigLoader
    from commuter_service.infrastructure.geospatial.client import GeospatialClient
    from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
    
    print("=" * 80)
    print("INTEGRATION TEST - SPAWN FULL WEEK COMBINED (DEPOT + ROUTE) FOR ROUTE 1")
    print("=" * 80)
    print("This will create REAL passengers in the database for 7 days x 24 hours")
    print("Both depot and route passengers spawn SIMULTANEOUSLY (realistic simulation)")
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
    
    # Get depot for this route
    print("Fetching depot information...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"http://localhost:6000/routes/by-document-id/{route_doc_id}/depot")
        depot_info = response.json().get('depot')
        depot_doc_id = depot_info['documentId']
        depot_lat = depot_info['latitude']
        depot_lon = depot_info['longitude']
    print(f"[OK] Depot: {depot_doc_id} at ({depot_lat}, {depot_lon})")
    print()
    
    # Create Reservoirs
    print("Initializing Reservoirs...")
    route_reservoir = RouteReservoir(
        passenger_repository=passenger_repo,
        enable_redis_cache=False
    )
    depot_reservoir = DepotReservoir(
        depot_id=depot_doc_id,
        passenger_repository=passenger_repo,
        enable_redis_cache=False
    )
    print("[OK] RouteReservoir and DepotReservoir initialized")
    print()
    
    # Initialize BOTH Spawners
    print("Initializing Spawners...")
    route_spawner = RouteSpawner(
        reservoir=route_reservoir,
        config={},
        route_id=route_doc_id,
        config_loader=config_loader,
        geo_client=geo_client
    )
    depot_spawner = DepotSpawner(
        reservoir=depot_reservoir,
        config={},
        depot_id=depot_doc_id,
        depot_location=(depot_lat, depot_lon),
        available_routes=[route_doc_id],
        depot_document_id=depot_doc_id,
        config_loader=config_loader,
        geo_client=geo_client
    )
    print(f"[OK] RouteSpawner and DepotSpawner initialized for Route {route_short_name}")
    print()
    
    # Count passengers before spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("http://localhost:1337/api/active-passengers")
        if response.status_code == 200:
            before_data = response.json()
            passengers_before = before_data.get('meta', {}).get('pagination', {}).get('total', 0)
        else:
            print(f"Warning: Could not query passengers (status {response.status_code})")
            passengers_before = 0
    
    print(f"Passengers in DB before spawning: {passengers_before}")
    print()
    
    # Spawn for full week (Saturday - Friday)
    start_date = datetime(2024, 11, 2)  # Saturday
    days = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    total_depot = 0
    total_route = 0
    daily_totals = []
    
    print("=" * 80)
    print("SPAWNING PASSENGERS - FULL WEEK (DEPOT + ROUTE COMBINED)")
    print("=" * 80)
    print()
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_name = days[day_offset]
        
        day_depot = 0
        day_route = 0
        
        print(f"{day_name} {current_date.strftime('%Y-%m-%d')}")
        print("-" * 80)
        
        # Spawn for each hour of the day
        for hour in range(24):
            spawn_time = current_date.replace(hour=hour, minute=0, second=0)
            
            try:
                # SPAWN BOTH DEPOT AND ROUTE SIMULTANEOUSLY
                depot_requests, route_requests = await asyncio.gather(
                    depot_spawner.spawn(current_time=spawn_time, time_window_minutes=60),
                    route_spawner.spawn(current_time=spawn_time, time_window_minutes=60)
                )
                
                # Push both to their respective reservoirs
                depot_count = 0
                route_count = 0
                
                if depot_requests:
                    successful, failed = await depot_reservoir.push_batch(depot_requests)
                    depot_count = successful
                    if failed > 0:
                        print(f"  {hour:02d}:00 - DEPOT WARNING: {failed} failed insertions")
                
                if route_requests:
                    successful, failed = await route_reservoir.push_batch(route_requests)
                    route_count = successful
                    if failed > 0:
                        print(f"  {hour:02d}:00 - ROUTE WARNING: {failed} failed insertions")
                
                day_depot += depot_count
                day_route += route_count
                total_depot += depot_count
                total_route += route_count
                
                # Print combined spawn counts
                total_hour = depot_count + route_count
                if total_hour > 0:
                    print(f"  {hour:02d}:00 - Depot: {depot_count:>3}, Route: {route_count:>3}, Total: {total_hour:>3}")
                else:
                    print(f"  {hour:02d}:00 - Depot:   0, Route:   0, Total:   0")
                
                # Small delay to not overwhelm the API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"  {hour:02d}:00 - ERROR: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        day_total = day_depot + day_route
        print(f"  Daily Total: Depot={day_depot}, Route={day_route}, Combined={day_total}")
        print()
        daily_totals.append((day_name, day_depot, day_route, day_total))
    
    # Give database time to process
    print("Waiting for database to process...")
    await asyncio.sleep(5)
    
    # Count passengers after spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("http://localhost:1337/api/active-passengers")
        if response.status_code == 200:
            after_data = response.json()
            passengers_after = after_data.get('meta', {}).get('pagination', {}).get('total', 0)
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
    print(f"{'Day':>9} | {'Depot':>5} | {'Route':>5} | {'Total':>5}")
    print("-" * 40)
    
    for day_name, day_depot, day_route, day_total in daily_totals:
        print(f"{day_name:>9} | {day_depot:>5} | {day_route:>5} | {day_total:>5}")
    
    print()
    print("-" * 80)
    print(f"Total Depot Passengers: {total_depot}")
    print(f"Total Route Passengers: {total_route}")
    print(f"Total Combined: {total_depot + total_route}")
    print()
    print(f"Database Before: {passengers_before}")
    print(f"Database After: {passengers_after}")
    print(f"Actual Created: {actual_created}")
    print()
    
    expected_total = total_depot + total_route
    if actual_created == expected_total:
        print(f"✅ SUCCESS: All {expected_total} passengers created in database!")
    else:
        print(f"⚠️  WARNING: Expected {expected_total}, but {actual_created} in database")
        print(f"  Difference: {expected_total - actual_created} passengers")
    
    print()
    print("=" * 80)
    print("Next Steps:")
    print("  - Query all: GET /api/active-passengers")
    print("  - Depot only: GET /api/active-passengers?filters[depot_id][$notnull]=true")
    print("  - Route only: GET /api/active-passengers?filters[depot_id][$null]=true")
    print("  - Analyze temporal patterns from spawned_at timestamps")
    print("  - Validate Poisson distribution from hourly counts")
    print("  - Run reset_passengers.py to clean up when done")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(spawn_full_week_combined())
