"""
Test Depot-Route Connection Filtering

This script tests that depots are properly filtered by route connection,
ensuring only depots within 500m of a route's start/end points can spawn
passengers for that route.

Expected Results for Route 1A:
- Speightstown Bus Terminal: CONNECTED (at route start)
- Constitution River Terminal: NOT CONNECTED (22.6 km away)
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from production_api_data_source import ProductionApiDataSource
from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.socketio_client import SocketIOClient
from math import radians, sin, cos, sqrt, atan2


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points"""
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


async def test_depot_filtering():
    """Test that depot-route connection filtering works correctly"""
    
    print("=" * 80)
    print("TESTING DEPOT-ROUTE CONNECTION FILTERING")
    print("=" * 80)
    
    # Initialize API client
    api_client = ProductionApiDataSource()
    
    # Initialize minimal SocketIO client (for testing)
    socketio_client = SocketIOClient(
        server_url="http://localhost:3500",
        service_type="commuter",
        namespace="/commuter"
    )
    
    # Create depot reservoir
    print("\n[INIT] Creating DepotReservoir...")
    reservoir = DepotReservoir(
        api_client=api_client,
        client=socketio_client
    )
    
    # Initialize without starting background services
    print("[INIT] Initializing reservoir (loading depots and routes)...")
    await reservoir.initialize()
    
    print(f"\n[LOADED] {len(reservoir.depots)} depots")
    print(f"[LOADED] {len(reservoir.routes)} routes")
    
    # Find Route 1A
    route_1a = next((r for r in reservoir.routes if r.short_name == "1A"), None)
    
    if not route_1a:
        print("\n❌ ERROR: Route 1A not found!")
        return
    
    print(f"\n[ROUTE] Route 1A: {route_1a.long_name}")
    print(f"[ROUTE] Geometry points: {len(route_1a.geometry_coordinates)}")
    
    # Get route endpoints
    if route_1a.geometry_coordinates:
        start_coord = route_1a.geometry_coordinates[0]  # [lon, lat]
        end_coord = route_1a.geometry_coordinates[-1]
        start_point = (start_coord[1], start_coord[0])
        end_point = (end_coord[1], end_coord[0])
        
        print(f"[ROUTE] Start: ({start_point[0]:.4f}, {start_point[1]:.4f})")
        print(f"[ROUTE] End: ({end_point[0]:.4f}, {end_point[1]:.4f})")
    else:
        print("\n❌ ERROR: Route 1A has no geometry coordinates!")
        return
    
    print("\n" + "=" * 80)
    print("TESTING DEPOT CONNECTIONS TO ROUTE 1A")
    print("=" * 80)
    
    # Test each depot
    for depot in reservoir.depots:
        depot_lat = depot.latitude if depot.latitude is not None else depot.location.get('lat')
        depot_lon = depot.longitude if depot.longitude is not None else depot.location.get('lon')
        
        if not depot_lat or not depot_lon:
            print(f"\n⚠️  {depot.name} ({depot.depot_id}): No coordinates")
            continue
        
        # Ensure floats
        if isinstance(depot_lat, str):
            depot_lat = float(depot_lat)
        if isinstance(depot_lon, str):
            depot_lon = float(depot_lon)
        
        # Calculate distances
        dist_to_start = haversine_distance(depot_lat, depot_lon, start_point[0], start_point[1])
        dist_to_end = haversine_distance(depot_lat, depot_lon, end_point[0], end_point[1])
        min_dist = min(dist_to_start, dist_to_end)
        
        # Test connection check
        is_connected = reservoir._is_depot_connected_to_route(depot, "1A", max_distance_km=0.5)
        
        # Display results
        status = "✅ CONNECTED" if is_connected else "❌ NOT CONNECTED"
        print(f"\n{status}: {depot.name} ({depot.depot_id})")
        print(f"   Location: ({depot_lat:.4f}, {depot_lon:.4f})")
        print(f"   Distance to route start: {dist_to_start:.2f} km")
        print(f"   Distance to route end: {dist_to_end:.2f} km")
        print(f"   Minimum distance: {min_dist:.2f} km")
        
        # Validate logic
        expected_connected = min_dist <= 0.5
        if is_connected != expected_connected:
            print(f"   ⚠️  WARNING: Expected {expected_connected}, got {is_connected}")
    
    print("\n" + "=" * 80)
    print("EXPECTED RESULTS FOR ROUTE 1A:")
    print("=" * 80)
    print("✅ Speightstown Bus Terminal: CONNECTED (at route start)")
    print("❌ Constitution River Terminal: NOT CONNECTED (22+ km away)")
    print("=" * 80)
    
    # Test spawn filtering
    print("\n" + "=" * 80)
    print("TESTING SPAWN REQUEST FILTERING")
    print("=" * 80)
    
    # Get connected depots
    connected_depots = [d for d in reservoir.depots if reservoir._is_depot_connected_to_route(d, "1A")]
    
    print(f"\n[FILTER] Connected depots for Route 1A: {len(connected_depots)}")
    for depot in connected_depots:
        depot_lat = depot.latitude if depot.latitude is not None else depot.location.get('lat')
        depot_lon = depot.longitude if depot.longitude is not None else depot.location.get('lon')
        print(f"   ✅ {depot.name} ({depot.depot_id}) @ ({depot_lat:.4f}, {depot_lon:.4f})")
    
    # Verify only Speightstown is connected
    speightstown_connected = any(
        "Speightstown" in depot.name 
        for depot in connected_depots
    )
    constitution_connected = any(
        "Constitution" in depot.name 
        for depot in connected_depots
    )
    
    print("\n[VALIDATION]")
    if speightstown_connected and not constitution_connected:
        print("✅ SUCCESS: Only Speightstown is connected to Route 1A")
        print("✅ Constitution River Terminal is correctly filtered out")
    else:
        print(f"❌ FAILURE:")
        print(f"   Speightstown connected: {speightstown_connected} (expected: True)")
        print(f"   Constitution connected: {constitution_connected} (expected: False)")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_depot_filtering())
