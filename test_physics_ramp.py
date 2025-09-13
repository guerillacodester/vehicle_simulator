#!/usr/bin/env python3
"""
Physics Kernel Unit Tests

Tests for physics-based acceleration ramp, target speed convergence,
and distance integration accuracy.
"""

import unittest
import time
from world.vehicle_simulator.vehicle.physics.physics_kernel import PhysicsKernel, PhysicsState
from world.vehicle_simulator.vehicle.physics.physics_speed_model import PhysicsSpeedModel


class TestPhysicsRamp(unittest.TestCase):
    
    def setUp(self):
        # Simple 1km straight route for predictable testing
        self.route_coords = [
            (-59.636900, 13.319443),  # start
            (-59.626900, 13.319443),  # 1km east
        ]
        self.target_speed_mps = 25.0 / 3.6  # 25 km/h -> m/s
        
    def test_acceleration_ramp_profile(self):
        """Test that physics model accelerates monotonically to target speed."""
        model = PhysicsSpeedModel(
            route_coords=self.route_coords,
            target_speed_mps=self.target_speed_mps,
            dt=0.5
        )
        
        speeds = []
        accelerations = []
        times = []
        
        # Step through first 8 seconds (should reach target by ~6s)
        for step in range(16):  # 16 * 0.5s = 8s
            result = model.update()
            speed_mps = result["velocity_mps"]
            accel_mps2 = result["acceleration"]
            
            speeds.append(speed_mps)
            accelerations.append(accel_mps2)
            times.append(step * 0.5)
            
            # Early ramp: acceleration should be positive (proportional control is gentler than bang-bang)
            if step < 10:  # first 5 seconds
                self.assertGreater(accel_mps2, 0.2, f"Low acceleration at t={step*0.5}s")
                self.assertLess(accel_mps2, 1.5, f"Excessive acceleration at t={step*0.5}s")
        
        # Check monotonic increase during ramp (allow tiny float tolerance)
        for i in range(1, 12):  # first 6 seconds
            speed_increase = speeds[i] - speeds[i-1]
            self.assertGreater(speed_increase, -0.05, 
                f"Speed decreased significantly at step {i}: {speeds[i-1]:.3f} -> {speeds[i]:.3f}")
        
        # Check target speed reached within tolerance by end
        final_speed_kmh = speeds[-1] * 3.6
        self.assertGreater(final_speed_kmh, 23.5, "Target speed not reached")
        self.assertLess(final_speed_kmh, 27.5, "Excessive overshoot")
        
        # Check time to target (should be around 5.8s = target_v / a_max)
        target_reached_step = None
        for i, speed in enumerate(speeds):
            if speed * 3.6 >= 24.0:  # within 1 km/h of target
                target_reached_step = i
                break
        
        self.assertIsNotNone(target_reached_step, "Target speed never reached")
        target_time = target_reached_step * 0.5
        self.assertGreater(target_time, 4.5, "Reached target too quickly")
        self.assertLess(target_time, 8.5, "Took too long to reach target")
    
    def test_distance_integration_accuracy(self):
        """Test that distance accumulation matches kinematic expectations."""
        model = PhysicsSpeedModel(
            route_coords=self.route_coords,
            target_speed_mps=self.target_speed_mps,
            dt=0.5
        )
        
        total_distance = 0.0
        dt = 0.5
        
        # Run for 10 seconds
        for step in range(20):
            result = model.update()
            speed_mps = result["velocity_mps"]
            
            # Integrate distance manually using trapezoidal rule
            if step > 0:
                avg_speed = (speed_mps + prev_speed) / 2
                total_distance += avg_speed * dt
            
            prev_speed = speed_mps
        
        # After 10s with target ~25 km/h, expect roughly:
        # - 6s ramp: distance ≈ 0.5 * a * t^2 ≈ 0.5 * 1.2 * 6^2 / 2 = 21.6m (rough)
        # - 4s cruise: distance ≈ 25 km/h * 4s = 25000/3600*4 ≈ 27.8m
        # Total expected: ~50-80m
        
        self.assertGreater(total_distance, 45, "Distance too low - integration error")
        self.assertLess(total_distance, 85, "Distance too high - integration error")
    
    def test_phase_transitions(self):
        """Test that physics model reports correct motion phases."""
        model = PhysicsSpeedModel(
            route_coords=self.route_coords,
            target_speed_mps=self.target_speed_mps,
            dt=0.5
        )
        
        phases_seen = set()
        
        # Step through and collect phases
        for step in range(15):  # 7.5 seconds
            result = model.update()
            phase = result["phase"]
            phases_seen.add(phase)
        
        # Should see LAUNCH during initial acceleration
        self.assertIn("LAUNCH", phases_seen, "LAUNCH phase not observed")
        
        # Should eventually see CRUISE as speed stabilizes
        # Note: with bang-bang control, might not see pure CRUISE, but should see non-LAUNCH
        non_launch_phases = phases_seen - {"LAUNCH", "STOPPED"}
        self.assertTrue(len(non_launch_phases) > 0, "No cruise/stable phase observed")


if __name__ == "__main__":
    unittest.main()