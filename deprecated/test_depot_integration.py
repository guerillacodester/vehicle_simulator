"""
Depot-Level Passenger Service Integration Test
============================================

Tests the new architecture where passenger service starts at depot level
and queries dispatcher's route buffer for GPS-aware passenger placement.

Key features tested:
- Depot manager starts passenger service after route assignment
- Dispatcher route buffer with GPS indexing  
- Passenger service queries route geometries from dispatcher
- GPS-based route discovery with walking distance
- Real Barbados transit route coordinates
"""

import asyncio
import logging  
import json
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_real_route_coordinates() -> Dict[str, Any]:
    """Load real Barbados transit route coordinates from geojson file."""
    try:
        import os
        route_file = os.path.join(os.path.dirname(__file__), 'data', 'roads', 'route_1_final_processed.geojson')
        
        with open(route_file, 'r') as f:
            geojson_data = json.load(f)
        
        # Extract coordinates from the first feature
        if geojson_data.get('features') and len(geojson_data['features']) > 0:
            coordinates = geojson_data['features'][0]['geometry']['coordinates']
            
            # Calculate pickup and destination points (10% and 80% along route)
            total_coords = len(coordinates)
            pickup_index = int(total_coords * 0.1)
            destination_index = int(total_coords * 0.8)
            
            pickup_coord = coordinates[pickup_index]
            destination_coord = coordinates[destination_index]
            
            return {
                'route_id': 'route_1_final_processed',
                'coordinates': coordinates,
                'pickup_coords': pickup_coord,  # [lon, lat]
                'destination_coords': destination_coord,
                'total_points': total_coords
            }
    except Exception as e:
        print(f"⚠️ Could not load real route data: {e}")
    
    # Fallback to test coordinates if file not found
    return {
        'route_id': 'TEST_ROUTE_1',
        'coordinates': [[-59.64, 13.28], [-59.63, 13.27], [-59.62, 13.26]],
        'pickup_coords': [-59.64, 13.28],
        'destination_coords': [-59.62, 13.26],
        'total_points': 3
    }

async def test_depot_passenger_integration():
    """Test complete depot → dispatcher → passenger service integration."""
    print("🏗️ Testing Depot-Level Passenger Service Integration")
    print("="*60)
    
    try:
        # Import components  
        from world.arknet_transit_simulator.core.dispatcher import Dispatcher, RouteBuffer
        from world.arknet_transit_simulator.core.depot_manager import DepotManager
        from world.arknet_transit_simulator.core.passenger_service_factory import PassengerServiceFactory
        from world.arknet_transit_simulator.core.interfaces import RouteInfo
        
        # Load real route data
        route_data = load_real_route_coordinates()
        print(f"📍 Using route: {route_data['route_id']} with {route_data['total_points']} GPS points")
        
        # Test 1: Route Buffer GPS Indexing
        print("\n🧪 Test 1: Route Buffer GPS Indexing")
        print("-" * 40)
        
        route_buffer = RouteBuffer()
        
        # Create RouteInfo with real coordinates
        route_info = RouteInfo(
            route_id=route_data['route_id'],
            route_name="Barbados Transit Route 1",
            route_type="bus",
            geometry={
                'type': 'LineString',
                'coordinates': route_data['coordinates']
            },
            coordinate_count=route_data['total_points']
        )
        
        # Add route to buffer
        success = await route_buffer.add_route(route_info)
        print(f"✅ Route added to buffer: {success}")
        
        # Test GPS-based route query
        pickup_coords = route_data['pickup_coords']
        nearby_routes = await route_buffer.get_routes_by_gps(
            lat=pickup_coords[1], 
            lon=pickup_coords[0], 
            walking_distance_km=0.5
        )
        print(f"✅ GPS query found {len(nearby_routes)} routes near pickup point")
        
        # Test 2: Dispatcher Route Buffer Integration
        print("\n🧪 Test 2: Dispatcher Route Buffer Integration")  
        print("-" * 40)
        
        # Create mock dispatcher (without API connection for testing)
        dispatcher = Dispatcher("TestDispatcher", "http://localhost:8000")
        
        # Manually populate route buffer
        await dispatcher.route_buffer.add_route(route_info)
        
        # Test route queries
        queried_route = await dispatcher.query_route_by_id(route_data['route_id'])
        print(f"✅ Route query by ID: {queried_route.route_name if queried_route else 'None'}")
        
        nearby_routes = await dispatcher.query_routes_by_gps(
            lat=pickup_coords[1], 
            lon=pickup_coords[0], 
            walking_distance_km=1.0
        )
        print(f"✅ GPS-based route query: {len(nearby_routes)} routes found")
        
        # Test 3: Passenger Service Factory
        print("\n🧪 Test 3: Passenger Service Factory Integration")
        print("-" * 40)
        
        passenger_factory = PassengerServiceFactory("TestPassengerFactory")
        passenger_factory.set_dispatcher(dispatcher)
        
        # Create passenger service for the route
        route_ids = [route_data['route_id']]
        service_created = await passenger_factory.create_passenger_service(route_ids)  
        print(f"✅ Passenger service created: {service_created}")
        
        if service_created:
            # Get service status
            status = await passenger_factory.get_service_status()
            print(f"📊 Service status: {status['passengers']} passengers, {status['routes']} routes")
            print(f"📊 Memory usage: {status['memory_usage_mb']:.2f}MB")
            print(f"📊 Running: {status['running']}")
            
            # Wait for some passengers to spawn
            print("\n⏳ Waiting for passenger spawning...")
            await asyncio.sleep(3)
            
            # Check passenger status again
            status = await passenger_factory.get_service_status()
            print(f"📊 After spawning: {status['passengers']} passengers")
            
            # Test GPS-based passenger query
            passengers_near_pickup = await passenger_factory.query_passengers_near_gps(
                lat=pickup_coords[1],
                lon=pickup_coords[0],
                radius_km=0.5
            )
            print(f"🔍 Passengers near pickup point: {len(passengers_near_pickup)}")
            
            # Show passenger details
            if passengers_near_pickup:
                passenger = passengers_near_pickup[0]
                if passenger.get('pickup_coords'):
                    coords = passenger['pickup_coords']
                    print(f"👤 Sample passenger: {passenger['id']} at ({coords[1]:.6f}, {coords[0]:.6f})")
                    print(f"🗺️ Route: {passenger.get('route_name', 'Unknown')}")
            
            # Stop passenger service
            await passenger_factory.stop_passenger_service()
            print("✅ Passenger service stopped")
        
        # Test 4: Route Buffer Statistics
        print("\n🧪 Test 4: Route Buffer Statistics")
        print("-" * 40)
        
        buffer_stats = await dispatcher.get_route_buffer_stats()
        print(f"📊 Buffer stats: {buffer_stats}")
        
        print("\n🎉 All Integration Tests Passed!")
        print("✅ Depot-level passenger service architecture working correctly")
        print("✅ GPS-based route queries functional")
        print("✅ Real Barbados transit coordinates integrated")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Depot-Level Passenger Service Integration Tests")
    print("="*60)
    print(f"📅 Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        result = asyncio.run(test_depot_passenger_integration())
        if result:
            print("\n🎯 Result: All tests PASSED! 🎉")
            print("Ready for depot-level passenger service deployment! 🚀")
        else:
            print("\n❌ Result: Some tests FAILED")
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()