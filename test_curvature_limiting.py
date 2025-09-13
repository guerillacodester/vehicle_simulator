#!/usr/bin/env python3
"""
Test curvature-based speed limiting functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from world.arknet_transit_simulator.vehicle.physics.physics_kernel import PhysicsKernel
import math

def test_curvature_calculations():
    """Test curvature radius calculations and speed limiting."""
    
    print("🧪 Testing Curvature-Based Speed Limiting")
    print("=" * 50)
    
    # Test route with a sharp curve
    # Straight section, then 90-degree turn, then straight again
    route_coords = [
        (-59.63690, 13.31944),   # Start (straight)
        (-59.63700, 13.31944),   # Straight segment  
        (-59.63710, 13.31944),   # Before curve
        (-59.63720, 13.31954),   # Sharp turn point
        (-59.63720, 13.31964),   # After curve
        (-59.63720, 13.31974),   # Straight again
    ]
    
    # Create physics kernel with curvature enabled
    kernel = PhysicsKernel(
        route_coords=route_coords,
        dt=0.5,
        v_max=80.0/3.6,  # 80 km/h max speed
        a_max=1.5,
        d_max=1.8,
        enable_curvature=True,
        a_lat_max=1.5  # 1.5 m/s² lateral acceleration limit
    )
    
    print(f"📊 Route Analysis:")
    print(f"   Total route length: {kernel.route_length_m:.1f} meters")
    print(f"   Vehicle max speed: {kernel.v_max * 3.6:.1f} km/h")
    print(f"   Lateral accel limit: {kernel.a_lat_max:.1f} m/s²")
    print()
    
    # Analyze each segment
    for i in range(len(route_coords)):
        radius = kernel._calculate_curvature_radius(i)
        speed_limit = kernel._get_curvature_speed_limit(i) * 3.6  # Convert to km/h
        
        if radius == float('inf'):
            curve_type = "STRAIGHT"
            radius_str = "∞"
        elif radius > 500:
            curve_type = "GENTLE"
            radius_str = f"{radius:.0f}m"
        elif radius > 100:
            curve_type = "MODERATE"
            radius_str = f"{radius:.0f}m"
        else:
            curve_type = "SHARP"
            radius_str = f"{radius:.0f}m"
        
        print(f"📍 Segment {i}: {curve_type:8} | Radius: {radius_str:>6} | Speed Limit: {speed_limit:.1f} km/h")
    
    print()
    print("🚗 Simulating vehicle movement...")
    
    # Set target speed to max and simulate movement
    kernel.set_target_speed(kernel.v_max)
    
    # Simulate for 20 steps to see speed variations
    for step in range(20):
        state = kernel.step()
        
        current_seg = kernel._find_segment(state.s)
        curve_limit = kernel._get_curvature_speed_limit(current_seg)
        
        print(f"Step {step:2d}: "
              f"Speed: {state.v * 3.6:5.1f} km/h | "
              f"Segment: {current_seg} | "
              f"Curve Limit: {curve_limit * 3.6:5.1f} km/h | "
              f"Position: {state.s:6.1f}m | "
              f"Phase: {state.phase}")
        
        # Stop if we've completed the route
        if state.progress >= 1.0:
            print("🏁 Route completed!")
            break
    
    print("=" * 50)
    print("✅ Curvature limiting test completed!")

if __name__ == "__main__":
    test_curvature_calculations()