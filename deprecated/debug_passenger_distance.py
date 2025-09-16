#!/usr/bin/env python3
"""
Debug Passenger Distance Issue
==============================

Investigate why passengers are being generated with trips shorter than 350m minimum.
"""

import asyncio
import math
import sys
import os

# Add the project to path
sys.path.append('world')
sys.path.append('world/arknet_transit_simulator')

from arknet_transit_simulator.passenger_modeler.passenger_service import DynamicPassengerService, haversine_distance


def debug_haversine():
    """Test the haversine distance function."""
    print("🧪 TESTING HAVERSINE DISTANCE FUNCTION")
    print("=" * 50)
    
    # Test cases from the sample data
    test_cases = [
        # PASS_1 - should be 90m but showing as too short
        ([13.270090, -59.642575], [13.269284, -59.642648], "PASS_1 trip"),
        # PASS_2 - should be 108m 
        ([13.272528, -59.641282], [13.272019, -59.642134], "PASS_2 trip"),
        # PASS_3 - should be 782m
        ([13.311450, -59.636820], [13.305126, -59.639983], "PASS_3 trip"),
        # Test a known distance for verification
        ([13.270090, -59.642575], [13.270090, -59.638575], "400m test (4km lon diff)"),
        ([13.270090, -59.642575], [13.274090, -59.642575], "350m test (0.004 lat diff)")
    ]
    
    for (lat1, lon1), (lat2, lon2), description in test_cases:
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        meets_min = "✅" if distance >= 350 else "❌"
        print(f"{meets_min} {description}: {distance:.1f}m")


async def debug_passenger_generation():
    """Debug the actual passenger generation logic."""
    print("\n🔍 DEBUGGING PASSENGER GENERATION")
    print("=" * 50)
    
    # Mock route data for testing
    mock_route_coords = [
        [-59.650000, 13.270000],  # Start
        [-59.645000, 13.272000],  # 500m away
        [-59.640000, 13.274000],  # Another 500m
        [-59.635000, 13.276000],  # Another 500m  
        [-59.630000, 13.278000],  # Another 500m
    ]
    
    print(f"📍 Testing with mock route of {len(mock_route_coords)} points")
    
    # Test distance calculation manually
    min_distance_m = 350.0
    max_attempts = 20
    valid_pairs = []
    
    for attempt in range(100):  # Test many attempts
        pickup_idx = 0  # Always start from beginning
        dest_idx = len(mock_route_coords) - 1  # Always end at end
        
        pickup_coord = mock_route_coords[pickup_idx]
        dest_coord = mock_route_coords[dest_idx]
        
        pickup_lat, pickup_lon = pickup_coord[1], pickup_coord[0]
        dest_lat, dest_lon = dest_coord[1], dest_coord[0]
        
        trip_distance = haversine_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)
        
        if trip_distance >= min_distance_m:
            valid_pairs.append((pickup_idx, dest_idx, trip_distance))
            
        if attempt < 5:  # Show first few attempts
            meets_min = "✅" if trip_distance >= min_distance_m else "❌"
            print(f"   Attempt {attempt+1}: idx {pickup_idx}→{dest_idx}, distance {trip_distance:.1f}m {meets_min}")
    
    print(f"\n📊 Results: {len(valid_pairs)}/100 attempts met minimum distance")
    
    if valid_pairs:
        avg_distance = sum(pair[2] for pair in valid_pairs) / len(valid_pairs)
        print(f"   Average valid distance: {avg_distance:.1f}m")
    else:
        print("   ❌ No valid pairs found!")


async def debug_actual_service():
    """Debug the actual passenger service."""
    print("\n🚀 TESTING ACTUAL PASSENGER SERVICE")
    print("=" * 50)
    
    try:
        # Create service
        service = DynamicPassengerService(['1B'], max_memory_mb=1)
        
        # Check configuration
        print(f"📋 Service configuration:")
        print(f"   Minimum destination distance: {service.config.get('destination_distance_meters', 'NOT SET')}m")
        print(f"   Max passengers: {service.max_passengers}")
        
        # Generate a test passenger manually
        print(f"\n🧪 Testing passenger generation logic...")
        # This would require mocking the route data
        
    except Exception as e:
        print(f"❌ Error testing service: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all debug tests."""
    debug_haversine()
    await debug_passenger_generation()
    await debug_actual_service()


if __name__ == "__main__":
    asyncio.run(main())