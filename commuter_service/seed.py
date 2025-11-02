"""
Commuter Simulator - Passenger Seeding Tool

Production-grade entrypoint for seeding passengers into the database.
Seeds static passenger manifests for testing/MVP demonstrations.

Usage:
    python commuter_service/seed.py --day monday --route 1
    python commuter_service/seed.py --day tuesday --route all
    python commuter_service/seed.py --day wednesday --route 5 --depot-spawning

Arguments:
    --day: Day of week to seed (monday, tuesday, wednesday, thursday, friday, saturday, sunday)
    --route: Route short_name to seed (e.g., "1", "5", "all")
    --depot-spawning: Enable depot spawning (optional, default: route spawning only)

Security:
    - Uses human-readable route short_name (e.g., "1") not documentId
    - DocumentIds used internally for API queries only, never displayed

For production:
    - Real mobile app users (no seeded passengers needed)
    - Lightweight operation (~2GB RAM sufficient)
    - This tool is for MVP/testing only
"""

import asyncio
import httpx
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
from commuter_service.core.domain.spawner_engine.depot_spawner import DepotSpawner
from commuter_service.core.domain.reservoirs.route_reservoir import RouteReservoir
from commuter_service.core.domain.reservoirs.depot_reservoir import DepotReservoir
from commuter_service.infrastructure.spawn.config_loader import SpawnConfigLoader
from commuter_service.infrastructure.geospatial.client import GeospatialClient
from commuter_service.infrastructure.database.passenger_repository import PassengerRepository


# Day of week mapping
DAYS_OF_WEEK = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6
}


async def fetch_routes(strapi_url: str):
    """Fetch all routes from Strapi"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{strapi_url}/api/routes")
        data = response.json()
        return data.get('data', [])


async def fetch_depot_for_route(route_doc_id: str, geospatial_url: str):
    """Fetch depot information for a specific route"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{geospatial_url}/routes/by-document-id/{route_doc_id}/depot")
        depot_info = response.json().get('depot')
        return depot_info


async def seed_route(
    route,
    target_date: datetime,
    spawn_type: str,  # 'route', 'depot', or 'both'
    start_hour: int,
    end_hour: int,
    strapi_url: str,
    geospatial_url: str
):
    """Seed passengers for a single route for a specific date"""
    
    route_short_name = route.get('short_name', 'Unknown')
    route_doc_id = route.get('documentId')
    
    print(f"\n{'='*80}")
    print(f"SEEDING: Route {route_short_name} - {target_date.strftime('%A, %Y-%m-%d')} - Type: {spawn_type.upper()}")
    print(f"Time Range: {start_hour:02d}:00 - {end_hour:02d}:00")
    print(f"{'='*80}\n")
    
    # Initialize components
    passenger_repo = PassengerRepository(strapi_url=strapi_url)
    await passenger_repo.connect()
    
    config_loader = SpawnConfigLoader(api_base_url=f"{strapi_url}/api")
    geo_client = GeospatialClient(base_url=geospatial_url)
    
    # Create spawners based on type
    route_spawner = None
    route_reservoir = None
    depot_spawner = None
    depot_reservoir = None
    
    if spawn_type in ['route', 'both']:
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
        
        print(f"✅ RouteSpawner initialized for Route {route_short_name}")
    
    if spawn_type in ['depot', 'both']:
        depot_info = await fetch_depot_for_route(route_doc_id, geospatial_url)
        depot_doc_id = depot_info['documentId']
        depot_lat = depot_info['latitude']
        depot_lon = depot_info['longitude']
        
        depot_reservoir = DepotReservoir(
            depot_id=depot_doc_id,
            passenger_repository=passenger_repo,
            enable_redis_cache=False
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
        
        print(f"✅ DepotSpawner initialized at ({depot_lat}, {depot_lon})")
    
    # Count passengers before spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{strapi_url}/api/active-passengers")
        if response.status_code == 200:
            before_data = response.json()
            passengers_before = before_data.get('meta', {}).get('pagination', {}).get('total', 0)
        else:
            passengers_before = 0
    
    print(f"📊 Passengers in DB before seeding: {passengers_before}\n")
    
    print(f"📅 Target Date: {target_date.strftime('%A, %Y-%m-%d')}")
    print(f"{'='*80}\n")
    
    total_route = 0
    total_depot = 0
    
    # Spawn for specified hour range
    for hour in range(start_hour, end_hour + 1):
        spawn_time = target_date.replace(hour=hour, minute=0, second=0)
        
        try:
            if spawn_type == 'both' and depot_spawner and route_spawner:
                # Spawn both depot and route simultaneously
                depot_requests, route_requests = await asyncio.gather(
                    depot_spawner.spawn(current_time=spawn_time, time_window_minutes=60),
                    route_spawner.spawn(current_time=spawn_time, time_window_minutes=60)
                )
                
                depot_count = 0
                route_count = 0
                
                if depot_requests:
                    successful, failed = await depot_reservoir.push_batch(depot_requests)
                    depot_count = successful
                    if failed > 0:
                        print(f"  {hour:02d}:00 - ⚠️  DEPOT: {failed} failed insertions")
                
                if route_requests:
                    successful, failed = await route_reservoir.push_batch(route_requests)
                    route_count = successful
                    if failed > 0:
                        print(f"  {hour:02d}:00 - ⚠️  ROUTE: {failed} failed insertions")
                
                total_depot += depot_count
                total_route += route_count
                
                total_hour = depot_count + route_count
                if total_hour > 0:
                    print(f"  {hour:02d}:00 - Depot: {depot_count:>3}, Route: {route_count:>3}, Total: {total_hour:>3}")
                else:
                    print(f"  {hour:02d}:00 - No passengers spawned")
                    
            elif spawn_type == 'depot' and depot_spawner:
                # Depot spawning only
                depot_requests = await depot_spawner.spawn(current_time=spawn_time, time_window_minutes=60)
                
                if depot_requests:
                    successful, failed = await depot_reservoir.push_batch(depot_requests)
                    total_depot += successful
                    
                    if failed > 0:
                        print(f"  {hour:02d}:00 - Depot: {successful:>3} ⚠️  ({failed} failed)")
                    elif successful > 0:
                        print(f"  {hour:02d}:00 - Depot: {successful:>3}")
                    else:
                        print(f"  {hour:02d}:00 - No passengers spawned")
                else:
                    print(f"  {hour:02d}:00 - No passengers spawned")
                    
            elif spawn_type == 'route' and route_spawner:
                # Route spawning only
                route_requests = await route_spawner.spawn(current_time=spawn_time, time_window_minutes=60)
                
                if route_requests:
                    successful, failed = await route_reservoir.push_batch(route_requests)
                    total_route += successful
                    
                    if failed > 0:
                        print(f"  {hour:02d}:00 - Route: {successful:>3} ⚠️  ({failed} failed)")
                    elif successful > 0:
                        print(f"  {hour:02d}:00 - Route: {successful:>3}")
                    else:
                        print(f"  {hour:02d}:00 - No passengers spawned")
                else:
                    print(f"  {hour:02d}:00 - No passengers spawned")
            
            # Small delay to not overwhelm the API
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"  {hour:02d}:00 - ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Wait for database to process
    print("\n⏳ Waiting for database to process...")
    await asyncio.sleep(3)
    
    # Count passengers after spawning
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{strapi_url}/api/active-passengers")
        if response.status_code == 200:
            after_data = response.json()
            passengers_after = after_data.get('meta', {}).get('pagination', {}).get('total', 0)
        else:
            passengers_after = 0
    
    actual_created = passengers_after - passengers_before
    
    # Cleanup
    await passenger_repo.disconnect()
    
    # Results
    print(f"\n{'='*80}")
    print(f"SEEDING COMPLETE - Route {route_short_name} - {target_date.strftime('%A, %Y-%m-%d')} - {spawn_type.upper()}")
    print(f"{'='*80}\n")
    
    if spawn_type == 'both':
        print(f"Route Passengers:  {total_route}")
        print(f"Depot Passengers:  {total_depot}")
        print(f"Total Created:     {total_route + total_depot}")
    elif spawn_type == 'depot':
        print(f"Depot Passengers:  {total_depot}")
    else:  # route
        print(f"Route Passengers:  {total_route}")
    
    print(f"\nDatabase Before:   {passengers_before}")
    print(f"Database After:    {passengers_after}")
    print(f"Actual Created:    {actual_created}\n")
    
    expected_total = total_route + total_depot
    if actual_created == expected_total:
        print(f"✅ SUCCESS: All {expected_total} passengers created in database!")
    else:
        print(f"⚠️  WARNING: Expected {expected_total}, but {actual_created} in database")
        print(f"  Difference: {expected_total - actual_created} passengers")
    
    print(f"{'='*80}\n")


async def main():
    """Main entrypoint for passenger seeding"""
    
    parser = argparse.ArgumentParser(
        description="Seed passengers for testing/MVP demonstrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Route passengers only, full day, by day name
    python commuter_service/seed.py --day monday --route 1 --type route
    
    # Specific date instead of day name
    python commuter_service/seed.py --date 2024-12-25 --route 1 --type route
    
    # Depot passengers only, morning rush
    python commuter_service/seed.py --day monday --route 1 --type depot --start-hour 6 --end-hour 9
    
    # Both types, evening rush, specific date
    python commuter_service/seed.py --date 2024-11-15 --route 1 --type both --start-hour 16 --end-hour 19
    
    # All routes, route passengers only
    python commuter_service/seed.py --day wednesday --route all --type route

Security:
    Uses human-readable route short_name (e.g., "1") not documentId.
    DocumentIds used internally only, never displayed.
        """
    )
    
    parser.add_argument(
        '--day',
        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        help='Day of week to seed (alternative to --date)'
    )
    
    parser.add_argument(
        '--date',
        help='Specific date to seed (YYYY-MM-DD format, alternative to --day)'
    )
    
    parser.add_argument(
        '--route',
        required=True,
        help='Route short_name to seed (e.g., "1", "5", "all")'
    )
    
    parser.add_argument(
        '--type',
        required=True,
        choices=['route', 'depot', 'both'],
        help='Type of passengers to spawn: route (along corridor), depot (at terminal), or both'
    )
    
    parser.add_argument(
        '--start-hour',
        type=int,
        default=0,
        help='Start hour (0-23, default: 0)'
    )
    
    parser.add_argument(
        '--end-hour',
        type=int,
        default=23,
        help='End hour (0-23, default: 23)'
    )
    
    parser.add_argument(
        '--strapi-url',
        default='http://localhost:1337',
        help='Strapi API URL (default: http://localhost:1337)'
    )
    
    parser.add_argument(
        '--geospatial-url',
        default='http://localhost:6000',
        help='Geospatial API URL (default: http://localhost:6000)'
    )
    
    args = parser.parse_args()
    
    # Validate that either --day or --date is provided (but not both)
    if not args.day and not args.date:
        parser.error("Either --day or --date must be specified")
    
    if args.day and args.date:
        parser.error("Cannot specify both --day and --date")
    
    # Determine target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
            date_display = args.date
        except ValueError:
            print(f"❌ ERROR: Invalid date format '{args.date}'. Use YYYY-MM-DD")
            return
    else:
        # Use a fixed base week (first full week of November 2024)
        base_date = datetime(2024, 11, 4)  # Monday, Nov 4, 2024
        day_offset = DAYS_OF_WEEK[args.day.lower()]
        target_date = base_date + timedelta(days=day_offset)
        date_display = args.day.upper()
    
    print(f"\n{'='*80}")
    print("COMMUTER SIMULATOR - PASSENGER SEEDING TOOL")
    print(f"{'='*80}")
    print(f"Date:             {target_date.strftime('%A, %Y-%m-%d')}")
    print(f"Route:            {args.route}")
    print(f"Type:             {args.type.upper()}")
    print(f"Time Range:       {args.start_hour:02d}:00 - {args.end_hour:02d}:00")
    print(f"Strapi URL:       {args.strapi_url}")
    print(f"Geospatial URL:   {args.geospatial_url}")
    print(f"{'='*80}\n")
    
    # Fetch routes from database
    print("🔍 Fetching routes from database...")
    routes = await fetch_routes(args.strapi_url)
    
    if not routes:
        print("❌ ERROR: No routes found in database!")
        return
    
    print(f"✅ Found {len(routes)} routes in database\n")
    
    # Filter routes by short_name
    if args.route.lower() == 'all':
        target_routes = routes
        print(f"📋 Seeding ALL {len(routes)} routes\n")
    else:
        target_routes = [r for r in routes if r.get('short_name') == args.route]
        if not target_routes:
            print(f"❌ ERROR: Route '{args.route}' not found in database!")
            print(f"Available routes: {', '.join([r.get('short_name', '?') for r in routes])}")
            return
        print(f"📋 Seeding Route {args.route}\n")
    
    # Seed each route
    for route in target_routes:
        await seed_route(
            route=route,
            target_date=target_date,
            spawn_type=args.type,
            start_hour=args.start_hour,
            end_hour=args.end_hour,
            strapi_url=args.strapi_url,
            geospatial_url=args.geospatial_url
        )
    
    print(f"\n{'='*80}")
    print("ALL SEEDING OPERATIONS COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
