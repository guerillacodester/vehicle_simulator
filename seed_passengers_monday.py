#!/usr/bin/env python3
"""
Seed passengers for a full Monday (24 hours)
This is NOT a real-time simulator - it generates all passengers at once
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from commuter_simulator.infrastructure.database.strapi_client import StrapiClient
from commuter_simulator.infrastructure.config.spawn_config_loader import SpawnConfigLoader
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from commuter_simulator.infrastructure.persistence.strapi.passenger_repository import PassengerRepository
from commuter_simulator.core.domain.spawner_engine.route_spawner import RouteSpawner
from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner


async def seed_monday_passengers():
    """Seed 24 hours of Monday passengers (00:00 to 23:59)"""
    
    print("=" * 80)
    print("PASSENGER SEEDING - MONDAY (24 hours)")
    print("=" * 80)
    
    # Initialize clients
    strapi_client = StrapiClient(base_url="http://localhost:1337")
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337")
    geo_client = GeospatialClient(base_url="http://localhost:6000")
    passenger_repo = PassengerRepository(api_base_url="http://localhost:1337")
    
    await passenger_repo.connect()
    
    # Get all active routes and depots
    routes = await strapi_client.get_active_routes()
    depots = await strapi_client.get_active_depots()
    
    print(f"\n📍 Found {len(routes)} active routes")
    print(f"📍 Found {len(depots)} active depots")
    
    # Create spawners
    route_spawners = []
    depot_spawners = []
    
    for route in routes:
        spawner = RouteSpawner(
            route_id=route['documentId'],
            config_loader=config_loader,
            geo_client=geo_client,
            passenger_repository=passenger_repo
        )
        route_spawners.append(spawner)
        print(f"  ✅ RouteSpawner created for route: {route.get('short_name', route['documentId'])}")
    
    for depot in depots:
        spawner = DepotSpawner(
            depot_id=depot['documentId'],
            depot_location=(depot['location']['coordinates'][1], depot['location']['coordinates'][0]),
            config_loader=config_loader,
            passenger_repository=passenger_repo,
            strapi_client=strapi_client
        )
        depot_spawners.append(spawner)
        print(f"  ✅ DepotSpawner created for depot: {depot.get('name', depot['documentId'])}")
    
    # Seed for Monday Nov 4, 2024 (00:00 to 23:00)
    base_date = datetime(2024, 11, 4, 0, 0, 0)  # Monday at midnight
    total_passengers = 0
    
    print(f"\n🌱 Seeding passengers for Monday {base_date.strftime('%Y-%m-%d')}...")
    print(f"   Time range: 00:00 - 23:59 (24 hours)\n")
    
    # Spawn for each hour of the day
    for hour in range(24):
        current_time = base_date + timedelta(hours=hour)
        hour_passengers = 0
        
        print(f"⏰ Hour {hour:02d}:00 - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Route spawners
        for spawner in route_spawners:
            try:
                spawn_requests = await spawner.spawn(current_time, time_window_minutes=60)
                hour_passengers += len(spawn_requests)
                if spawn_requests:
                    print(f"   🚌 Route {spawner.route_id}: {len(spawn_requests)} passengers")
            except Exception as e:
                print(f"   ❌ Route spawner error: {e}")
        
        # Depot spawners
        for spawner in depot_spawners:
            try:
                spawn_requests = await spawner.spawn(current_time, time_window_minutes=60)
                hour_passengers += len(spawn_requests)
                if spawn_requests:
                    print(f"   🏢 Depot {spawner.depot_id}: {len(spawn_requests)} passengers")
            except Exception as e:
                print(f"   ❌ Depot spawner error: {e}")
        
        total_passengers += hour_passengers
        if hour_passengers > 0:
            print(f"   📊 Hour total: {hour_passengers} passengers")
        print()
    
    await passenger_repo.disconnect()
    
    print("=" * 80)
    print(f"✅ SEEDING COMPLETE!")
    print(f"📊 Total passengers seeded: {total_passengers}")
    print(f"📅 Day: Monday {base_date.strftime('%Y-%m-%d')}")
    print(f"⏰ Time range: 00:00 - 23:59")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(seed_monday_passengers())
