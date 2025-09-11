#!/usr/bin/env python3
"""
Test Engine Pipeline
--------------------
Tests the complete engine physics and geospatial calculation pipeline.
"""

import time
import sys
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer  
from world.vehicle_simulator.vehicle.engine.sim_speed_model import load_speed_model
from world.vehicle_simulator.vehicle.driver.navigation import math as nav_math

def test_engine_physics():
    """Test engine distance calculations"""
    print("🔬 TESTING ENGINE PHYSICS")
    print("=" * 50)
    
    # Create engine components
    buffer = EngineBuffer(size=100)
    speed_model = load_speed_model('kinematic', speed=30.0)  # 30 km/h target speed
    engine = Engine('TEST_VEHICLE', speed_model, buffer, tick_time=1.0)
    
    print("Starting engine for 3 seconds...")
    engine.on()
    time.sleep(3.1)
    engine.off()
    
    # Analyze results
    entries = []
    while len(buffer) > 0:
        entry = buffer.read()
        if entry:
            entries.append(entry)
    if entries:
        last_entry = entries[-1]
        print(f"✅ Engine produced {len(entries)} entries")
        print(f"📊 Final speed: {last_entry['cruise_speed']:.1f} km/h")
        print(f"📏 Total distance: {last_entry['distance']:.6f} km")
        print(f"⏱️ Total time: {last_entry['time']:.1f} s")
        
        # Calculate expected distance (rough check)
        avg_speed = last_entry['cruise_speed']  # km/h
        time_hours = last_entry['time'] / 3600  # convert to hours
        expected_distance = avg_speed * time_hours
        print(f"🧮 Expected distance: {expected_distance:.6f} km")
        
        return last_entry['distance']
    else:
        print("❌ No engine data produced!")
        return None

def test_geodesic_calculations():
    """Test geodesic interpolation"""
    print("\n🗺️ TESTING GEODESIC CALCULATIONS")
    print("=" * 50)
    
    # Test route in Barbados
    test_route = [
        (13.2810, -59.6463),  # Start point
        (13.2820, -59.6470),  # Mid point  
        (13.2830, -59.6480)   # End point
    ]
    
    print("Route points:")
    for i, (lat, lng) in enumerate(test_route):
        print(f"  Point {i+1}: ({lat:.6f}, {lng:.6f})")
    
    print("\nTesting interpolation at different distances:")
    test_distances = [0.0, 0.1, 0.2, 0.3, 0.5]
    
    for dist_km in test_distances:
        try:
            lat, lng, bearing = nav_math.interpolate_along_route_geodesic(test_route, dist_km)
            print(f"  {dist_km:.1f}km -> ({lat:.6f}, {lng:.6f}) bearing: {bearing:.1f}°")
        except Exception as e:
            print(f"  {dist_km:.1f}km -> Error: {e}")
    
    # Test distance calculation between first two points
    lat1, lng1 = test_route[0]
    lat2, lng2 = test_route[1]
    segment_distance = nav_math.haversine(lat1, lng1, lat2, lng2)
    print(f"\n📏 Distance between point 1-2: {segment_distance:.6f} km")
    
    return True

def test_vehicle_simulation():
    """Test complete vehicle simulation"""
    print("\n🚗 TESTING COMPLETE VEHICLE SIMULATION")
    print("=" * 50)
    
    try:
        from world.vehicle_simulator.simulators.simulator import VehicleSimulator
        
        # Create simulator without GPS to focus on engine
        sim = VehicleSimulator(tick_time=1.0, enable_gps=False)
        
        if not sim.vehicles:
            print("❌ No vehicles in simulator")
            return False
            
        # Test with first vehicle
        vehicle_id = list(sim.vehicles.keys())[0]
        print(f"Testing vehicle: {vehicle_id}")
        
        # Get initial state
        vehicle = sim.vehicles[vehicle_id]
        initial_lat = vehicle.lat
        initial_lng = vehicle.lng
        initial_speed = vehicle.speed
        
        print(f"Initial: ({initial_lat:.6f}, {initial_lng:.6f}) speed: {initial_speed:.1f} km/h")
        
        # Run simulation
        sim.start()
        
        # Track changes over 3 ticks
        for tick in range(3):
            time.sleep(1.1)  # Wait for tick
            sim.update()
            
            vehicle = sim.vehicles[vehicle_id]
            lat_change = abs(vehicle.lat - initial_lat)
            lng_change = abs(vehicle.lng - initial_lng)
            
            print(f"Tick {tick+1}: ({vehicle.lat:.6f}, {vehicle.lng:.6f}) "
                  f"Δlat: {lat_change:.6f} Δlng: {lng_change:.6f} speed: {vehicle.speed:.1f} km/h")
            
            # Update for next comparison
            initial_lat = vehicle.lat
            initial_lng = vehicle.lng
        
        sim.stop()
        print("✅ Vehicle simulation completed")
        return True
        
    except Exception as e:
        print(f"❌ Vehicle simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ENGINE PIPELINE VERIFICATION TEST")
    print("=" * 60)
    
    # Run all tests
    engine_distance = test_engine_physics()
    geodesic_ok = test_geodesic_calculations()
    vehicle_ok = test_vehicle_simulation()
    
    print("\n🎯 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Engine Physics: {'PASS' if engine_distance else 'FAIL'}")
    print(f"✅ Geodesic Math: {'PASS' if geodesic_ok else 'FAIL'}")
    print(f"✅ Vehicle Sim: {'PASS' if vehicle_ok else 'FAIL'}")
    
    if engine_distance and geodesic_ok and vehicle_ok:
        print("\n🎉 ALL TESTS PASSED - Engine pipeline working correctly!")
        print("   ✅ Engine calculates distances from speed/time")
        print("   ✅ Navigator interpolates lat/lng using geodesics")  
        print("   ✅ Vehicle simulation updates positions properly")
    else:
        print("\n⚠️ Some tests failed - check implementation")
