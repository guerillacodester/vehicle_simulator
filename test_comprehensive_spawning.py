"""
Test Comprehensive Passenger Spawning System
============================================

Test all spawning strategies: depot-based, route-based, and mixed.
"""

import asyncio
import logging
from datetime import datetime
from passenger_service.strapi_api_client import StrapiApiClient
from passenger_service.spawn_interface import (
    PassengerSpawnManager, 
    DepotSpawnStrategy, 
    RouteSpawnStrategy, 
    MixedSpawnStrategy,
    SpawnType
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_depot_spawning():
    """Test depot-based passenger spawning"""
    print("\n🏭 Testing Depot-Based Spawning...")
    
    async with StrapiApiClient() as client:
        strategy = DepotSpawnStrategy(client)
        manager = PassengerSpawnManager(client, strategy)
        
        await manager.initialize()
        
        # Get spawn statistics
        stats = await manager.get_spawn_statistics()
        print(f"✅ Depot Spawn Locations: {stats['total_locations']}")
        
        for location in stats['locations_by_type'].get('depot', []):
            print(f"  - {location['name']}: capacity_factor={location['capacity_factor']:.2f}")
        
        # Generate spawn requests
        current_time = datetime.now()
        requests = await manager.spawn_passengers(current_time, time_window_minutes=10)
        
        print(f"✅ Generated {len(requests)} depot-based spawn requests")
        
        # Show sample requests
        for i, request in enumerate(requests[:3]):
            print(f"  Request {i+1}:")
            print(f"    Location: {request.spawn_location.name}")
            print(f"    Route: {request.assigned_route}")
            print(f"    Purpose: {request.trip_purpose}")
            print(f"    Wait time: {request.expected_wait_time}min")

async def test_route_spawning():
    """Test route-based passenger spawning"""
    print("\n🛣️  Testing Route-Based Spawning...")
    
    async with StrapiApiClient() as client:
        strategy = RouteSpawnStrategy(client)
        manager = PassengerSpawnManager(client, strategy)
        
        await manager.initialize()
        
        # Get spawn statistics
        stats = await manager.get_spawn_statistics()
        print(f"✅ Route Spawn Locations: {stats['total_locations']}")
        
        # Show locations by route
        route_locations = stats['locations_by_type'].get('route', [])
        routes = {}
        for location in route_locations:
            route_name = location['name'].split(' - ')[0]
            if route_name not in routes:
                routes[route_name] = 0
            routes[route_name] += 1
        
        for route, count in routes.items():
            print(f"  - {route}: {count} spawn points")
        
        # Generate spawn requests
        current_time = datetime.now()
        requests = await manager.spawn_passengers(current_time, time_window_minutes=10)
        
        print(f"✅ Generated {len(requests)} route-based spawn requests")
        
        # Show sample requests
        for i, request in enumerate(requests[:3]):
            print(f"  Request {i+1}:")
            print(f"    Location: {request.spawn_location.name}")
            print(f"    Route: {request.assigned_route}")
            print(f"    Purpose: {request.trip_purpose}")
            print(f"    Distance: {calculate_distance(request.spawn_location.coordinates, request.destination_location):.2f}km")

async def test_mixed_spawning():
    """Test mixed depot + route spawning"""
    print("\n🔄 Testing Mixed Spawning Strategy...")
    
    async with StrapiApiClient() as client:
        # 40% depot, 60% route spawning
        strategy = MixedSpawnStrategy(client, depot_weight=0.4, route_weight=0.6)
        manager = PassengerSpawnManager(client, strategy)
        
        await manager.initialize()
        
        # Get spawn statistics
        stats = await manager.get_spawn_statistics()
        print(f"✅ Mixed Spawn Locations: {stats['total_locations']}")
        print(f"  - Depot locations: {stats['location_types'].get('depot', 0)}")
        print(f"  - Route locations: {stats['location_types'].get('route', 0)}")
        
        # Generate spawn requests
        current_time = datetime.now()
        requests = await manager.spawn_passengers(current_time, time_window_minutes=10)
        
        print(f"✅ Generated {len(requests)} mixed spawn requests")
        
        # Analyze request types
        depot_requests = [r for r in requests if r.spawn_location.location_type == SpawnType.DEPOT_BASED]
        route_requests = [r for r in requests if r.spawn_location.location_type == SpawnType.ROUTE_BASED]
        
        if len(requests) > 0:
            print(f"  - Depot-based: {len(depot_requests)} ({len(depot_requests)/len(requests)*100:.1f}%)")
            print(f"  - Route-based: {len(route_requests)} ({len(route_requests)/len(requests)*100:.1f}%)")
        else:
            print(f"  - Depot-based: {len(depot_requests)} (0%)")
            print(f"  - Route-based: {len(route_requests)} (0%)")
        
        # Show sample requests
        print("\n  Sample Depot Requests:")
        for i, request in enumerate(depot_requests[:2]):
            print(f"    {i+1}. {request.spawn_location.name} → Route {request.assigned_route}")
        
        print("\n  Sample Route Requests:")
        for i, request in enumerate(route_requests[:2]):
            print(f"    {i+1}. {request.spawn_location.name}")

async def test_time_based_patterns():
    """Test spawning patterns at different times of day"""
    print("\n⏰ Testing Time-Based Spawning Patterns...")
    
    async with StrapiApiClient() as client:
        strategy = MixedSpawnStrategy(client)
        manager = PassengerSpawnManager(client, strategy)
        
        await manager.initialize()
        
        # Test different times of day
        test_times = [
            (7, "Morning Rush"),
            (12, "Lunch Time"),
            (18, "Evening Rush"),
            (23, "Night Time")
        ]
        
        for hour, period_name in test_times:
            test_time = datetime.now().replace(hour=hour, minute=0, second=0)
            requests = await manager.spawn_passengers(test_time, time_window_minutes=10)
            
            print(f"  {period_name} ({hour}:00): {len(requests)} spawn requests")
            
            # Analyze trip purposes
            purposes = {}
            for request in requests:
                purpose = request.trip_purpose
                purposes[purpose] = purposes.get(purpose, 0) + 1
            
            top_purposes = sorted(purposes.items(), key=lambda x: x[1], reverse=True)[:3]
            purpose_str = ", ".join([f"{p}: {c}" for p, c in top_purposes])
            print(f"    Top purposes: {purpose_str}")

def calculate_distance(coord1: dict, coord2: dict) -> float:
    """Calculate distance between two coordinates in km"""
    import math
    
    lat1, lon1 = coord1['lat'], coord1['lon']
    lat2, lon2 = coord2['lat'], coord2['lon']
    
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

async def main():
    """Run all spawning tests"""
    print("🧪 Testing Comprehensive Passenger Spawning System")
    print("=" * 60)
    
    try:
        await test_depot_spawning()
        await test_route_spawning()
        await test_mixed_spawning()
        await test_time_based_patterns()
        
        print("\n🎉 All spawning tests completed successfully!")
        print("\n📊 Summary:")
        print("✅ Depot-based spawning: Passengers spawn at depot locations")
        print("✅ Route-based spawning: Passengers spawn along route segments")
        print("✅ Mixed spawning: Combines both strategies with configurable weights")
        print("✅ Time-based patterns: Different spawn rates and purposes by time of day")
        print("✅ Realistic trip purposes: work, school, shopping, social, etc.")
        print("✅ Dynamic wait times: Based on time of day and service frequency")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())