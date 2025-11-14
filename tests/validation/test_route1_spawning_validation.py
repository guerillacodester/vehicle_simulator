"""
Route 1 Spawning Validation Test - Bar Charts WITHOUT Database Insertion

Shows expected spawn counts with bar charts for visual validation.
Does NOT create any database records.
Reads spawn config AND building counts from database/geospatial service.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from datetime import datetime
import numpy as np
import httpx

# Strapi configuration
STRAPI_URL = "http://localhost:1337"
ROUTE_SHORT_NAME = "1"


async def fetch_spawn_config_and_buildings():
    """Fetch spawn config and building counts from geospatial service (NOT HARDCODED)."""
    from commuter_service.infrastructure.geospatial.client import GeospatialClient
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get route documentId
        response = await client.get(
            f"{STRAPI_URL}/api/routes",
            params={"filters[short_name][$eq]": ROUTE_SHORT_NAME}
        )
        route_data = response.json().get('data', [])[0]
        route_doc_id = route_data['documentId']
        
        # Get spawn config
        response = await client.get(
            f"{STRAPI_URL}/api/spawn-configs",
            params={
                "filters[route][short_name][$eq]": ROUTE_SHORT_NAME,
                "populate": "*"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch spawn config: {response.status_code}")
        
        data = response.json().get('data', [])
        if not data:
            raise Exception(f"No spawn config found for route {ROUTE_SHORT_NAME}")
        
        record = data[0]
        config = record.get('config', {})
        
        # Extract from nested structure
        hourly_rates = config.get('hourly_rates')
        day_multipliers = config.get('day_multipliers')
        dist_params = config.get('distribution_params', {})
        depot_base_rate = dist_params.get('depot_passengers_per_building_per_hour')
        route_base_rate = dist_params.get('route_passengers_per_building_per_hour')
        
        # Validate required fields
        if not depot_base_rate:
            raise Exception("spawn_config.config.distribution_params.depot_passengers_per_building_per_hour is empty in database!")
        if not route_base_rate:
            raise Exception("spawn_config.config.distribution_params.route_passengers_per_building_per_hour is empty in database!")
        if not hourly_rates:
            raise Exception("spawn_config.config.hourly_rates is empty in database!")
        if not day_multipliers:
            raise Exception("spawn_config.config.day_multipliers is empty in database!")
        
        # Convert string-keyed dicts to arrays for easier indexing
        hourly_rates_array = [float(hourly_rates.get(str(i), 0.0)) for i in range(24)]
        day_multipliers_array = [float(day_multipliers.get(str(i), 1.0)) for i in range(7)]
        
        # Get Route 1 to query buildings
        r = await client.get(f"{STRAPI_URL}/api/routes?filters[short_name][$eq]={ROUTE_SHORT_NAME}")
        route = r.json()['data'][0]
        route_doc_id = route['documentId']
        
        # Get route geometry
        r = await client.get(f"http://localhost:6000/spatial/route-geometry/{route_doc_id}")
        route_geom = r.json()
        route_coords = route_geom.get('coordinates', [])
        
        # Query ACTUAL building counts from geospatial service (same as spawners use)
        geo_client = GeospatialClient(base_url="http://localhost:6000")
        
        # Route buildings
        route_buildings_result = geo_client.buildings_along_route(
            route_coordinates=route_coords,
            buffer_meters=500,
            limit=5000
        )
        route_building_count = len(route_buildings_result.get('buildings', []))
        
        # Depot buildings (get depot location first)
        r = await client.get(f"http://localhost:6000/routes/by-document-id/{route_doc_id}/depot")
        depot_info = r.json().get('depot')
        depot_lat = depot_info['latitude']
        depot_lon = depot_info['longitude']
        
        depot_buildings_result = geo_client.depot_catchment_area(
            depot_latitude=depot_lat,
            depot_longitude=depot_lon,
            catchment_radius_meters=800
        )
        depot_building_count = len(depot_buildings_result.get('buildings', []))
        
        # Return config with BOTH depot and route rates
        spawn_config = {
            'distribution_params': {
                'depot_passengers_per_building_per_hour': float(depot_base_rate),
                'route_passengers_per_building_per_hour': float(route_base_rate)
            },
            'hourly_rates': {str(i): v for i, v in enumerate(hourly_rates_array)},
            'day_multipliers': {str(i): v for i, v in enumerate(day_multipliers_array)}
        }
        
        building_counts = {
            'depot': depot_building_count,
            'route': route_building_count
        }
        
        return spawn_config, building_counts


def calculate_spawn_count(hour: int, day_of_week: int, depot_buildings: int, route_buildings: int, spawn_config: dict) -> tuple:
    """
    Calculate expected spawn count using the spawn formula.
    
    NOTE: RouteSpawner and DepotSpawner work independently:
    - RouteSpawner: Creates passengers along route (uses route_buildings)
    - DepotSpawner: Creates passengers at depot (uses depot_buildings)
    
    This function calculates both for visualization purposes.
    """
    # Use the simulator's SpawnCalculator to perform temporal extraction
    # and effective-rate calculation. This keeps the test aligned with
    # the production calculation kernel instead of re-implementing logic.
    from datetime import datetime, timedelta
    from commuter_service.core.domain.spawner_engine.spawn_calculator import SpawnCalculator

    # Build a current_time that matches requested weekday and hour.
    # Use Monday 2024-11-04 as base (weekday=0) and offset by day_of_week.
    base_monday = datetime(2024, 11, 4)
    day_date = base_monday + timedelta(days=day_of_week)
    current_time = datetime(day_date.year, day_date.month, day_date.day, hour, 0)

    # Extract temporal multipliers for DEPOT spawner
    depot_base_rate, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
        spawn_config=spawn_config,
        current_time=current_time,
        spawner_type='depot'
    )

    # Extract temporal multipliers for ROUTE spawner
    route_base_rate, _, _ = SpawnCalculator.extract_temporal_multipliers(
        spawn_config=spawn_config,
        current_time=current_time,
        spawner_type='route'
    )

    # Calculate effective rates
    depot_effective_rate = SpawnCalculator.calculate_effective_rate(
        base_rate=depot_base_rate,
        hourly_multiplier=hourly_mult,
        day_multiplier=day_mult
    )
    
    route_effective_rate = SpawnCalculator.calculate_effective_rate(
        base_rate=route_base_rate,
        hourly_multiplier=hourly_mult,
        day_multiplier=day_mult
    )

    # Independent spawners:
    # - DepotSpawner creates: depot_buildings × depot_effective_rate passengers at depot
    # - RouteSpawner creates: route_buildings × route_effective_rate passengers along route
    depot_passengers_per_hour = depot_buildings * depot_effective_rate
    route_passengers_per_hour = route_buildings * route_effective_rate

    # For deterministic validation bars we return the expected hourly counts
    depot_count = int(round(depot_passengers_per_hour))
    route_count = int(round(route_passengers_per_hour))
    total_count = depot_count + route_count

    return depot_count, route_count, total_count


def print_bar(hour: int, count: int, max_count: int, label: str):
    """Print a horizontal bar chart."""
    if max_count == 0:
        bar_length = 0
    else:
        bar_length = int((count / max_count) * 40)
    
    bar = '█' * bar_length
    print(f"  {hour:02d}:00 {label:6s} {count:>3} |{bar}")


def run_validation():
    """Run validation showing bar charts for Saturday, Sunday, Monday."""
    
    # Fetch spawn config AND building counts from database/geospatial
    print("📡 Fetching spawn config and building counts...")
    spawn_config, building_counts = asyncio.run(fetch_spawn_config_and_buildings())
    print(f"   ✅ Loaded spawn config for Route {ROUTE_SHORT_NAME}")
    print()
    
    print("=" * 80)
    print("ROUTE 1 SPAWNING VALIDATION - BAR CHARTS")
    print("=" * 80)
    print(f"Configuration:")
    
    # Extract BOTH depot and route base rates from distribution_params
    dist_params = spawn_config.get('distribution_params', {})
    depot_base_rate = dist_params.get('depot_passengers_per_building_per_hour', 0.0)
    route_base_rate = dist_params.get('route_passengers_per_building_per_hour', 0.0)
    
    print(f"  Depot Base Rate: {depot_base_rate}")
    print(f"  Route Base Rate: {route_base_rate}")
    print(f"  Depot Buildings: {building_counts['depot']} (from geospatial service)")
    print(f"  Route Buildings: {building_counts['route']} (from geospatial service)")
    
    # Get peak hour rate
    hourly_rates_map = spawn_config.get('hourly_rates', {})
    peak_rate = float(hourly_rates_map.get('8', 0.0))
    print(f"  Peak Hour (8 AM): rate={peak_rate}")
    print()
    
    days = [
        (5, "Saturday", datetime(2024, 11, 2)),  # Day 5 = Saturday
        (6, "Sunday", datetime(2024, 11, 3)),    # Day 6 = Sunday
        (0, "Monday", datetime(2024, 11, 4))     # Day 0 = Monday
    ]
    
    for day_idx, day_name, day_date in days:
        print("=" * 80)
        print(f"{day_name} {day_date.strftime('%Y-%m-%d')}")
        
        # Get day multiplier from spawn config
        day_mults_map = spawn_config.get('day_multipliers', {})
        day_mult = float(day_mults_map.get(str(day_idx), 1.0))
        print(f"Day Multiplier: {day_mult}")
        print("=" * 80)
        
        hourly_depot = []
        hourly_route = []
        hourly_total = []
        
        # Calculate for each hour using ACTUAL building counts
        for hour in range(24):
            depot, route, total = calculate_spawn_count(
                hour, day_idx,
                building_counts['depot'],
                building_counts['route'],
                spawn_config
            )
            hourly_depot.append(depot)
            hourly_route.append(route)
            hourly_total.append(total)
        
        # Print bar charts
        max_total = max(hourly_total) if hourly_total else 1
        
        print("\nDEPOT PASSENGERS:")
        for hour in range(24):
            if hourly_depot[hour] > 0:
                print_bar(hour, hourly_depot[hour], max_total, "Depot")
        
        print("\nROUTE PASSENGERS:")
        for hour in range(24):
            if hourly_route[hour] > 0:
                print_bar(hour, hourly_route[hour], max_total, "Route")
        
        print("\nTOTAL PASSENGERS:")
        for hour in range(24):
            if hourly_total[hour] > 0:
                print_bar(hour, hourly_total[hour], max_total, "Total")
        
        daily_total = sum(hourly_total)
        daily_depot = sum(hourly_depot)
        daily_route = sum(hourly_route)
        
        print()
        print(f"Daily Summary:")
        print(f"  Depot Passengers: {daily_depot:>4}")
        print(f"  Route Passengers: {daily_route:>4}")
        print(f"  Total Passengers: {daily_total:>4}")
        print()
    
    print("=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print("This shows expected spawn patterns with current configuration.")
    print("NO database records were created.")
    print("=" * 80)


if __name__ == "__main__":
    run_validation()
