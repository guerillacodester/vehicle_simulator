"""
Test the new StrapiApiClient and DepotPassengerSpawner integration
"""

import asyncio
import logging
from commuter_service.strapi_api_client import StrapiApiClient
from commuter_service.depot_commuter_spawner import DepotCommuterSpawner
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_api_client():
    """Test the StrapiApiClient directly"""
    print("🧪 Testing StrapiApiClient...")
    
    async with StrapiApiClient() as client:
        # Test health check
        health = await client.health_check()
        print(f"Health check: {health}")
        
        # Test depot loading
        depots = await client.get_all_depots()
        print(f"✅ Loaded {len(depots)} depots:")
        for depot in depots:
            print(f"  - {depot.name} (ID: {depot.depot_id}, Capacity: {depot.capacity})")
        
        # Test route loading
        routes = await client.get_all_routes()
        print(f"✅ Loaded {len(routes)} routes:")
        for route in routes:
            print(f"  - {route.short_name}: {route.long_name} ({route.coordinate_count} coordinates, {route.route_length_km:.1f}km)")

async def test_depot_spawner():
    """Test the DepotPassengerSpawner with API client"""
    print("\n🏭 Testing DepotPassengerSpawner...")
    
    spawner = DepotCommuterSpawner()
    
    try:
        # Initialize spawner
        if await spawner.initialize():
            print(f"✅ Spawner initialized with {len(spawner.depots)} depots and {len(spawner.routes)} routes")
            
            # Generate some spawn requests
            current_time = datetime.now()
            spawn_requests = await spawner.generate_passenger_spawn_requests(current_time, time_window_minutes=5)
            
            print(f"✅ Generated {len(spawn_requests)} passenger spawn requests")
            
            # Show first few requests
            for i, request in enumerate(spawn_requests[:3]):
                print(f"  Request {i+1}:")
                print(f"    Depot: {request.depot_info.name}")
                print(f"    Route: {request.route_info.short_name}")
                print(f"    Purpose: {request.trip_purpose}")
                print(f"    Priority: {request.priority:.2f}")
                print(f"    Wait time: {request.expected_wait_time}min")
                
        else:
            print("❌ Failed to initialize spawner")
            
    finally:
        await spawner.close()

async def main():
    """Run all tests"""
    try:
        await test_api_client()
        await test_depot_spawner()
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())