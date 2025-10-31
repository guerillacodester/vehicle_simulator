#!/usr/bin/env python3
"""
Calculate realistic depot spawn rates using hybrid model:
  terminal_population = buildings_near_depot × rate
  route_attractiveness = buildings_along_route / total_buildings_all_routes
  passengers_per_route = terminal_population × route_attractiveness
"""

import requests
import json

STRAPI_URL = "http://localhost:1337"
GEO_URL = "http://localhost:6000"

PASSENGERS_PER_BUILDING_PER_HOUR = 0.05
DEPOT_RADIUS = 800
ROUTE_BUFFER = 100  # meters buffer for route building queries

print("=" * 80)
print("HYBRID DEPOT SPAWN MODEL - REALISM CALCULATION")
print("=" * 80)
print(f"\nModel: terminal_pop × route_attractiveness")
print(f"  - Terminal population: buildings_near_depot × {PASSENGERS_PER_BUILDING_PER_HOUR}")
print(f"  - Route attractiveness: buildings_along_route / total_buildings_all_routes")
print()

# Focus on Speightstown since it has a route association
depot = {
    "id": 18,
    "name": "Speightstown Bus Terminal",
    "lat": 13.250128,
    "lon": -59.639525
}

print(f"\n{'=' * 80}")
print(f"DEPOT: {depot['name']}")
print('=' * 80)

# Step 1: Get buildings near depot (terminal population)
print(f"\nStep 1: Query buildings near depot ({DEPOT_RADIUS}m radius)")
geo_response = requests.get(
    f"{GEO_URL}/spatial/nearby-buildings",
    params={
        "lat": depot["lat"],
        "lon": depot["lon"],
        "radius_meters": DEPOT_RADIUS,
        "limit": 5000
    }
)
buildings_data = geo_response.json()
depot_building_count = len(buildings_data.get('buildings', []))
terminal_population = depot_building_count * PASSENGERS_PER_BUILDING_PER_HOUR

print(f"  Buildings near depot: {depot_building_count}")
print(f"  Terminal population: {depot_building_count} × {PASSENGERS_PER_BUILDING_PER_HOUR} = {terminal_population:.1f} pass/hr")

# Step 2: Get routes for this depot
print(f"\nStep 2: Get routes servicing this depot")
routes_response = requests.get(
    f"{STRAPI_URL}/api/routes?filters[depots][id][$eq]={depot['id']}&populate=*&pagination[pageSize]=100"
)
routes_data = routes_response.json()
routes = routes_data.get('data', []) if routes_data.get('data') is not None else []

print(f"  Routes found: {len(routes)}")

if len(routes) == 0:
    print("  ⚠️  NO ROUTES - Calculation stopped")
    exit()

# Step 3: Get buildings along each route
print(f"\nStep 3: Query buildings along each route ({ROUTE_BUFFER}m buffer)")

route_buildings = []
total_route_buildings = 0

for route in routes:
    route_attrs = route['attributes']
    route_id = route['id']
    route_name = route_attrs.get('route_long_name', 'Unknown')
    route_short = route_attrs.get('route_short_name', f'Route {route_id}')
    
    # Get route geometry
    route_geom = route_attrs.get('route_geometry')
    
    if not route_geom or not route_geom.get('coordinates'):
        print(f"  ⚠️  {route_short}: No geometry data")
        route_buildings.append({
            'id': route_id,
            'name': route_name,
            'short': route_short,
            'building_count': 0
        })
        continue
    
    # Query buildings along route
    route_coords = route_geom['coordinates']
    
    try:
        geo_response = requests.post(
            f"{GEO_URL}/spatial/buildings-along-route",
            json={
                "coordinates": route_coords,
                "buffer_meters": ROUTE_BUFFER,
                "limit": 5000
            }
        )
        route_buildings_data = geo_response.json()
        building_count = len(route_buildings_data.get('buildings', []))
    except Exception as e:
        print(f"  ⚠️  {route_short}: Error querying buildings - {e}")
        building_count = 0
    
    print(f"  {route_short}: {building_count} buildings along route")
    
    route_buildings.append({
        'id': route_id,
        'name': route_name,
        'short': route_short,
        'building_count': building_count
    })
    total_route_buildings += building_count

print(f"\n  Total buildings across all routes: {total_route_buildings}")

# Step 4: Calculate passenger distribution
print(f"\nStep 4: Calculate passenger distribution by route attractiveness")
print("=" * 80)

if total_route_buildings == 0:
    print("  ⚠️  No buildings along any routes - using equal distribution")
    for route_info in route_buildings:
        passengers_per_hour = terminal_population / len(routes)
        print(f"\n  {route_info['short']}: {route_info['name']}")
        print(f"    Buildings along route: {route_info['building_count']}")
        print(f"    Attractiveness: {1/len(routes):.2%} (equal)")
        print(f"    Passengers/hr: {passengers_per_hour:.1f} ({passengers_per_hour/60:.3f} pass/min)")
else:
    total_passengers_check = 0
    
    for route_info in route_buildings:
        attractiveness = route_info['building_count'] / total_route_buildings
        passengers_per_hour = terminal_population * attractiveness
        total_passengers_check += passengers_per_hour
        
        print(f"\n  {route_info['short']}: {route_info['name']}")
        print(f"    Buildings along route: {route_info['building_count']}")
        print(f"    Attractiveness: {attractiveness:.2%}")
        print(f"    Passengers/hr: {passengers_per_hour:.1f} ({passengers_per_hour/60:.3f} pass/min)")
    
    print(f"\n  Total distributed: {total_passengers_check:.1f} pass/hr (should equal {terminal_population:.1f})")

# Step 5: Realism check
print(f"\n{'=' * 80}")
print("REALISM CHECK")
print('=' * 80)

print(f"\nTerminal: {depot['name']}")
print(f"  Population density (buildings near depot): {depot_building_count}")
print(f"  Total passengers spawning: {terminal_population:.1f} pass/hr")
print(f"  Routes serviced: {len(routes)}")

if len(routes) > 0:
    print(f"\nPer route breakdown:")
    for route_info in route_buildings:
        if total_route_buildings > 0:
            attractiveness = route_info['building_count'] / total_route_buildings
            passengers = terminal_population * attractiveness
        else:
            attractiveness = 1 / len(routes)
            passengers = terminal_population / len(routes)
        
        print(f"  {route_info['short']}:")
        print(f"    - {route_info['building_count']} buildings along route (destination density)")
        print(f"    - {attractiveness:.1%} of terminal passengers choose this route")
        print(f"    - {passengers:.1f} pass/hr ({passengers/60:.2f} pass/min)")

print(f"\n{'=' * 80}")
print("COMPARISON WITH ROUTE-ONLY SPAWNING")
print('=' * 80)
print("\nIf we ONLY used route spawning (current working model):")
for route_info in route_buildings:
    route_only_spawn = route_info['building_count'] * PASSENGERS_PER_BUILDING_PER_HOUR
    print(f"  {route_info['short']}: {route_only_spawn:.1f} pass/hr (buildings along route only)")

print(f"\n{'=' * 80}")
print("CONCLUSION")
print('=' * 80)
print("\nHybrid Model Benefits:")
print("  ✅ Terminal activity affects spawn rate (busy terminals = more passengers)")
print("  ✅ Route destination affects distribution (busy routes = more attractive)")
print("  ✅ Adding routes doesn't dilute unrealistically")
print("  ✅ Short route to busy area gets more than long route to nowhere")
print("\nHybrid Model vs Route-Only:")
print("  - Depot spawning adds terminal-originating passengers")
print("  - Route spawning adds stop-originating passengers")
print("  - Both are realistic and independent")
