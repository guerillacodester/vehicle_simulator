#!/usr/bin/env python3
"""
Test Route Reservoir Functionality in Isolation
This script tests the route passenger spawning system independently.
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_spawning_api import DatabaseSpawningAPI

def test_route_reservoir():
    """Test route reservoir functionality with detailed output"""
    print("🚌 ROUTE RESERVOIR TEST")
    print("=" * 50)
    
    # Test parameters
    test_hour = 8  # Peak morning hour
    time_window = 5  # 5-minute window
    
    print(f"📅 Testing Hour: {test_hour}")
    print(f"⏱️  Time Window: {time_window} minutes")
    print()
    
    # Generate passengers using database API and filter for route only
    print("🔄 Generating route passengers...")
    import asyncio
    from database_spawning_api import handle_spawn_request
    
    result = asyncio.run(handle_spawn_request(test_hour, time_window))
    all_passengers = result.get('spawn_requests', [])
    passengers = [p for p in all_passengers if p.get('spawn_type') == 'route']
    
    # Analyze results
    print(f"✅ Generated {len(passengers)} route passengers")
    print()
    
    if passengers:
        # Show sample passengers
        print("📋 Sample Passengers (first 5):")
        for i, passenger in enumerate(passengers[:5]):
            print(f"  {i+1}. Route ID: {passenger.get('route_id', 'N/A')}")
            print(f"     Location: ({passenger['latitude']:.6f}, {passenger['longitude']:.6f})")
            print(f"     Spawn Type: {passenger['spawn_type']}")
            print(f"     Location Name: {passenger.get('location_name', 'N/A')}")
            print(f"     Zone Type: {passenger.get('zone_type', 'N/A')}")
            print(f"     Spawn Rate: {passenger.get('spawn_rate', 'N/A')}")
            print(f"     Minute: {passenger.get('minute', 'N/A')}")
            print()
        
        # Statistics
        route_ids = set(p.get('route_id') for p in passengers if p.get('route_id'))
        spawn_rates = [p.get('spawn_rate', 0) for p in passengers]
        minutes = [p.get('minute', 0) for p in passengers]
        
        print("📊 ROUTE STATISTICS:")
        print(f"   • Total Passengers: {len(passengers)}")
        print(f"   • Unique Routes: {len(route_ids)}")
        print(f"   • Route IDs: {sorted(route_ids) if route_ids else 'None'}")
        print(f"   • Average Spawn Rate: {sum(spawn_rates)/len(spawn_rates):.2f}" if spawn_rates else "   • Average Spawn Rate: N/A")
        print(f"   • Minute Range: {min(minutes)}-{max(minutes)}" if minutes else "   • Minute Range: N/A")
        
        # Verify data integrity
        print("\n🔍 DATA VALIDATION:")
        valid_passengers = 0
        for passenger in passengers:
            has_coords = 'latitude' in passenger and 'longitude' in passenger
            has_spawn_type = passenger.get('spawn_type') == 'route'
            has_route_id = 'route_id' in passenger and passenger['route_id'] is not None
            
            if has_coords and has_spawn_type and has_route_id:
                valid_passengers += 1
        
        print(f"   • Valid Passengers: {valid_passengers}/{len(passengers)} ({100*valid_passengers/len(passengers):.1f}%)")
        
        # Peak hour multiplier check
        peak_multipliers = [p.get('spawn_rate', 0) for p in passengers]
        expected_multiplier = 2.5  # Hour 8 should have 2.5x multiplier
        
        if peak_multipliers:
            avg_multiplier = sum(peak_multipliers) / len(peak_multipliers)
            print(f"   • Peak Hour Multiplier: {avg_multiplier:.2f} (expected: {expected_multiplier})")
            
            multiplier_match = abs(avg_multiplier - expected_multiplier) < 0.1
            print(f"   • Multiplier Correct: {'✅' if multiplier_match else '❌'}")
        
    else:
        print("❌ NO PASSENGERS GENERATED!")
        print("   This indicates a problem with route data or configuration.")
    
    print("\n" + "=" * 50)
    print("🚌 ROUTE RESERVOIR TEST COMPLETE")
    
    return len(passengers) > 0, passengers

def test_route_data_source():
    """Test the underlying route data source"""
    print("\n🔧 ROUTE DATA SOURCE TEST")
    print("=" * 30)
    
    try:
        # Test database connection by getting route data through API
        import asyncio
        from database_spawning_api import DatabaseSpawningAPI
        
        db_api = DatabaseSpawningAPI()
        data = asyncio.run(db_api.get_database_data())
        routes = data.get('routes', [])
        
        if routes:
            print(f"✅ Route data loaded: {len(routes)} routes")
            
            # Show sample route data
            print("\n📋 Sample Route Data (first 3):")
            for i, route in enumerate(routes[:3]):
                print(f"  {i+1}. ID: {route.get('id', 'N/A')}")
                print(f"     Name: {route.get('short_name', 'N/A')}")
                print(f"     Long Name: {route.get('long_name', 'N/A')}")
                print(f"     Shape ID: {route.get('shape_id', 'N/A')}")
                print()
        else:
            print("❌ No route data found!")
            print("   Check database connection and routes table.")
            
        # Check shapes data
        shapes = data.get('shapes', [])
        if shapes:
            print(f"✅ Shape data loaded: {len(shapes)} shape points")
            
            # Group by shape_id to count unique shapes
            unique_shapes = set(s.get('shape_id') for s in shapes if s.get('shape_id'))
            print(f"✅ Unique shapes: {len(unique_shapes)}")
            
            # Show sample shape data
            print("\n📋 Sample Shape Data (first 3):")
            for i, shape in enumerate(shapes[:3]):
                print(f"  {i+1}. Shape ID: {shape.get('shape_id', 'N/A')}")
                print(f"     Sequence: {shape.get('shape_pt_sequence', 'N/A')}")
                print(f"     Location: ({shape.get('shape_pt_lat', 'N/A')}, {shape.get('shape_pt_lon', 'N/A')})")
                print()
        else:
            print("❌ No shape data found!")
            print("   Check database connection and shapes table.")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("   Check PostgreSQL connection and credentials.")

if __name__ == "__main__":
    print("🚀 STARTING ROUTE RESERVOIR ISOLATION TEST")
    print("=" * 60)
    
    try:
        # Test data source first
        test_route_data_source()
        
        # Test passenger generation
        success, passengers = test_route_reservoir()
        
        if success:
            print(f"\n🎉 ROUTE TEST PASSED! Generated {len(passengers)} passengers")
        else:
            print(f"\n❌ ROUTE TEST FAILED! No passengers generated")
            
    except Exception as e:
        print(f"\n💥 ROUTE TEST ERROR: {e}")
        import traceback
        traceback.print_exc()