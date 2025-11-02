#!/usr/bin/env python3
"""
Passenger Seeder - Generate static passenger manifest for simulation

Seeds database with passengers for a specific day and route(s).
This is NOT a real-time simulator - generates all passengers in one pass.

Usage:
    python commuter_simulator/seed_passengers.py --day monday --route all
    python commuter_simulator/seed_passengers.py --day monday --route 1
    python commuter_simulator/seed_passengers.py --day monday --route 1 --depot-spawning
"""

import asyncio
import argparse
import sys
import logging
import httpx
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from commuter_simulator.core.domain.spawner_engine.route_spawner import RouteSpawner
from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner
from commuter_simulator.domain.services.reservoirs.route_reservoir import RouteReservoir
from commuter_simulator.domain.services.reservoirs.depot_reservoir import DepotReservoir
from commuter_simulator.infrastructure.config.spawn_config_loader import SpawnConfigLoader
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from commuter_simulator.infrastructure.persistence.strapi.passenger_repository import PassengerRepository
from commuter_simulator.infrastructure.database.strapi_client import StrapiApiClient


# Day of week to date mapping (using Nov 2024)
DAY_TO_DATE = {
    'monday': datetime(2024, 11, 4),     # Monday Nov 4
    'tuesday': datetime(2024, 11, 5),    # Tuesday Nov 5
    'wednesday': datetime(2024, 11, 6),  # Wednesday Nov 6
    'thursday': datetime(2024, 11, 7),   # Thursday Nov 7
    'friday': datetime(2024, 11, 8),     # Friday Nov 8
    'saturday': datetime(2024, 11, 2),   # Saturday Nov 2
    'sunday': datetime(2024, 11, 3),     # Sunday Nov 3
}


async def seed_passengers(day: str, route_filter: str, enable_depot: bool = False):
    """
    Seed passengers for a specific day and route
    
    Args:
        day: Day of week (monday, tuesday, etc.)
        route_filter: 'all' for all routes, or route short_name (e.g., "1", "2")
        enable_depot: Whether to also spawn depot passengers
    """
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    print("=" * 80)
    print("PASSENGER SEEDING - STATIC MANIFEST GENERATOR")
    print("=" * 80)
    print(f"Day: {day.upper()}")
    print(f"Route filter: {route_filter}")
    print(f"Depot spawning: {'ENABLED' if enable_depot else 'DISABLED'}")
    print("=" * 80)
    print()
    
    # Get base date for the day
    if day.lower() not in DAY_TO_DATE:
        print(f"ERROR: Invalid day '{day}'. Must be one of: {', '.join(DAY_TO_DATE.keys())}")
        return
    
    base_date = DAY_TO_DATE[day.lower()]
    print(f"📅 Seeding for {day.title()} {base_date.strftime('%Y-%m-%d')} (00:00-23:59)")
    print()
    
    # Initialize infrastructure
    strapi_client = StrapiApiClient(base_url="http://localhost:1337")
    await strapi_client.connect()
    
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    geo_client = GeospatialClient(base_url="http://localhost:6000")
    passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")
    
    await passenger_repo.connect()
    logger.info("✅ Connected to database")
    
    # Get routes from database
    routes = await strapi_client.get_all_routes()
    
    # Filter routes by short_name (human-readable)
    if route_filter.lower() == 'all':
        selected_routes = routes
        print(f"📍 Seeding ALL {len(routes)} active routes")
    else:
        selected_routes = [r for r in routes if r.get('short_name') == route_filter]
        if not selected_routes:
            print(f"ERROR: Route '{route_filter}' not found!")
            print(f"Available routes: {', '.join([r.get('short_name', '?') for r in routes])}")
            await passenger_repo.disconnect()
            return
        print(f"📍 Seeding Route {selected_routes[0].get('short_name')} - {selected_routes[0].get('long_name', 'N/A')}")
    
    print()
    
    # Create route spawners
    route_spawners = []
    for route in selected_routes:
        route_reservoir = RouteReservoir(
            passenger_repository=passenger_repo,
            enable_redis_cache=False
        )
        
        spawner = RouteSpawner(
            reservoir=route_reservoir,
            config={},
            route_id=route['documentId'],
            config_loader=config_loader,
            geo_client=geo_client
        )
        route_spawners.append((route, spawner, route_reservoir))
        logger.info(f"✅ RouteSpawner created for Route {route.get('short_name')} - {route.get('long_name', 'N/A')}")
    
    # Create depot spawners if enabled
    depot_spawners = []
    if enable_depot:
        depots = await strapi_client.get_all_depots()
        print(f"\n📍 Found {len(depots)} active depots")
        
        for depot in depots:
            depot_reservoir = DepotReservoir(
                depot_id=depot['documentId'],
                passenger_repository=passenger_repo,
                enable_redis_cache=False
            )
            
            # Get depot location
            depot_coords = depot.get('location', {}).get('coordinates', [])
            if len(depot_coords) == 2:
                depot_location = (depot_coords[1], depot_coords[0])  # (lat, lon)
            else:
                logger.warning(f"Skipping depot {depot['documentId']} - no valid location")
                continue
            
            spawner = DepotSpawner(
                reservoir=depot_reservoir,
                config={},
                depot_id=depot['documentId'],
                depot_location=depot_location,
                available_routes=[r['documentId'] for r in selected_routes],
                depot_document_id=depot['documentId'],
                config_loader=config_loader,
                geo_client=geo_client
            )
            depot_spawners.append((depot, spawner, depot_reservoir))
            logger.info(f"✅ DepotSpawner created for: {depot.get('name', 'Unknown Depot')}")
    
    print()
    print("=" * 80)
    print("SEEDING IN PROGRESS...")
    print("=" * 80)
    print()
    
    # Seed for each hour of the day
    total_route_passengers = 0
    total_depot_passengers = 0
    hourly_breakdown = []
    
    for hour in range(24):
        current_time = base_date.replace(hour=hour, minute=0, second=0)
        hour_route = 0
        hour_depot = 0
        
        print(f"⏰ {current_time.strftime('%H:%M')} - ", end='', flush=True)
        
        # Spawn route passengers
        for route, spawner, reservoir in route_spawners:
            try:
                spawn_requests = await spawner.spawn(current_time=current_time, time_window_minutes=60)
                if spawn_requests:
                    successful, failed = await reservoir.push_batch(spawn_requests)
                    hour_route += successful
                    if failed > 0:
                        logger.warning(f"Route {route.get('short_name')} hour {hour}: {failed} failed")
            except Exception as e:
                logger.error(f"Route spawn error at hour {hour}: {e}")
        
        # Spawn depot passengers
        if enable_depot:
            for depot, spawner, reservoir in depot_spawners:
                try:
                    spawn_requests = await spawner.spawn(current_time=current_time, time_window_minutes=60)
                    if spawn_requests:
                        successful, failed = await reservoir.push_batch(spawn_requests)
                        hour_depot += successful
                        if failed > 0:
                            logger.warning(f"Depot {depot.get('name')} hour {hour}: {failed} failed")
                except Exception as e:
                    logger.error(f"Depot spawn error at hour {hour}: {e}")
        
        hour_total = hour_route + hour_depot
        total_route_passengers += hour_route
        total_depot_passengers += hour_depot
        
        if enable_depot:
            print(f"Route: {hour_route:>3}, Depot: {hour_depot:>3}, Total: {hour_total:>3}")
        else:
            print(f"Route: {hour_route:>3}")
        
        hourly_breakdown.append((hour, hour_route, hour_depot, hour_total))
        
        # Small delay to avoid overwhelming API
        await asyncio.sleep(0.1)
    
    # Cleanup
    await passenger_repo.disconnect()
    await strapi_client.disconnect()
    
    # Results
    print()
    print("=" * 80)
    print("SEEDING COMPLETE!")
    print("=" * 80)
    print()
    print(f"📊 Route passengers: {total_route_passengers}")
    if enable_depot:
        print(f"📊 Depot passengers: {total_depot_passengers}")
        print(f"📊 Total passengers: {total_route_passengers + total_depot_passengers}")
    print()
    print(f"📅 Day: {day.title()} {base_date.strftime('%Y-%m-%d')}")
    print(f"📍 Routes seeded: {len(route_spawners)}")
    if enable_depot:
        print(f"📍 Depots seeded: {len(depot_spawners)}")
    print()
    print("=" * 80)
    print("Next steps:")
    print("  - View manifest: python scripts/show_route_manifest.py")
    print("  - Analyze data: python scripts/check_spawn_data.py")
    print("  - Delete all: python delete_all_passengers_fast.py")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Seed passengers for simulation')
    parser.add_argument('--day', type=str, required=True,
                       choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                       help='Day of week to seed')
    parser.add_argument('--route', type=str, default='all',
                       help='Route short_name to seed (e.g., "1", "2"), or "all" for all routes')
    parser.add_argument('--depot-spawning', action='store_true',
                       help='Also spawn depot passengers')
    
    args = parser.parse_args()
    
    asyncio.run(seed_passengers(
        day=args.day,
        route_filter=args.route,
        enable_depot=args.depot_spawning
    ))


if __name__ == "__main__":
    main()
