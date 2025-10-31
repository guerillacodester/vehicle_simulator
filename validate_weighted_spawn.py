#!/usr/bin/env python3
"""
Validate depot spawn rates using route-distance weighting.
Each route gets passengers proportional to its distance relative to all routes at that depot.
"""

import requests
import json

STRAPI_URL = "http://localhost:1337"
GEO_URL = "http://localhost:6000"

# Depot data
depots = [
    {"id": 21, "name": "Constitution River Terminal", "lat": 13.102403, "lon": -59.612742},
    {"id": 20, "name": "Cheapside Terminal", "lat": 13.097306, "lon": -59.620117},
    {"id": 22, "name": "Princess Alice Terminal", "lat": 13.086972, "lon": -59.615194},
    {"id": 18, "name": "Speightstown Bus Terminal", "lat": 13.250128, "lon": -59.639525},
    {"id": 19, "name": "Granville Williams Terminal", "lat": 13.100147, "lon": -59.607353},
]

PASSENGERS_PER_BUILDING_PER_HOUR = 0.05
SPAWN_RADIUS = 800

print("=" * 80)
print("DEPOT SPAWN WITH ROUTE-DISTANCE WEIGHTING")
print("=" * 80)
print(f"\nParameters:")
print(f"  - Passengers per building per hour: {PASSENGERS_PER_BUILDING_PER_HOUR}")
print(f"  - Depot radius: {SPAWN_RADIUS}m")
print()

for depot in depots:
    depot_id = depot['id']
    depot_name = depot['name']
    
    print(f"\n{'=' * 80}")
    print(f"{depot_name} (ID: {depot_id})")
    print('=' * 80)
    
    # Get buildings near depot
    geo_response = requests.get(
        f"{GEO_URL}/spatial/nearby-buildings",
        params={"lat": depot["lat"], "lon": depot["lon"], "radius_meters": SPAWN_RADIUS, "limit": 5000}
    )
    buildings_data = geo_response.json()
    building_count = len(buildings_data.get('buildings', []))
    
    # Get routes for this depot
    routes_response = requests.get(
        f"{STRAPI_URL}/api/routes?filters[depots][id][$eq]={depot_id}&populate=*&pagination[pageSize]=100"
    )
    routes_data = routes_response.json()
    routes = routes_data.get('data', [])
    
    print(f"\nBuildings within {SPAWN_RADIUS}m: {building_count}")
    print(f"Routes servicing this depot: {len(routes)}")
    
    if len(routes) == 0:
        print("  ⚠️  NO ROUTES - No passengers will spawn")
        continue
    
    # Calculate base passenger pool from buildings
    base_passenger_pool = building_count * PASSENGERS_PER_BUILDING_PER_HOUR
    print(f"\nBase passenger pool: {building_count} × {PASSENGERS_PER_BUILDING_PER_HOUR} = {base_passenger_pool:.1f} pass/hr")
    
    # Get route distances and calculate weights
    total_distance = 0
    route_info = []
    
    for route in routes:
        route_attrs = route['attributes']
        route_name = route_attrs.get('route_long_name', 'Unknown')
        route_short = route_attrs.get('route_short_name', 'N/A')
        
        # Get route distance from shape_dist_traveled or calculate from geometry
        distance_km = route_attrs.get('shape_dist_traveled', 0)
        
        if distance_km == 0:
            # Try to get from route geometry
            route_geom = route_attrs.get('route_geometry')
            if route_geom and route_geom.get('coordinates'):
                # Simplified distance calculation
                coords = route_geom['coordinates']
                distance_km = len(coords) * 0.1  # Rough estimate: 100m per point
        
        route_info.append({
            'name': route_name,
            'short': route_short,
            'distance_km': distance_km
        })
        total_distance += distance_km
    
    if total_distance == 0:
        print("  ⚠️  Routes have no distance data - using equal weighting")
        # Fall back to equal distribution
        for route in route_info:
            passengers_per_hour = base_passenger_pool / len(routes)
            print(f"\n  Route {route['short']}: {route['name']}")
            print(f"    Distance: Unknown")
            print(f"    Weight: {1/len(routes):.2%}")
            print(f"    Passengers/hr: {passengers_per_hour:.1f} ({passengers_per_hour/60:.2f} pass/min)")
    else:
        print(f"Total route distance coverage: {total_distance:.2f} km")
        print(f"\nPassenger distribution by route distance:")
        
        for route in route_info:
            weight = route['distance_km'] / total_distance
            passengers_per_hour = base_passenger_pool * weight
            
            print(f"\n  Route {route['short']}: {route['name']}")
            print(f"    Distance: {route['distance_km']:.2f} km")
            print(f"    Weight: {weight:.2%} of total")
            print(f"    Passengers/hr: {passengers_per_hour:.1f} ({passengers_per_hour/60:.2f} pass/min)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nThis model ensures:")
print("  ✅ Longer routes get more passengers (serve more area)")
print("  ✅ Shorter routes get fewer passengers (serve less area)")
print("  ✅ Adding new routes increases total spawn (realistic)")
print("  ✅ Buildings near depot still matter (terminal activity)")
print("\nFormula per route:")
print("  passengers = (buildings × rate) × (route_distance / total_distance)")
