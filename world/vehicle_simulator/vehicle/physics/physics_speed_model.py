"""Physics Speed Model Adapter

Internal canonical units:
    - Kernel state velocity (v) is meters/second (m/s)
    - Acceleration is meters/second^2

We now standardize the simulation INTERNALLY on SI units (m/s) and only
convert to km/h at the *telemetry emission* layer. The Engine previously
assumed km/h and integrated distance using (v * dt)/3600. After the unit
normalization patch, Engine integrates using m/s directly and stores
cruise_speed_mps in the buffer.

This adapter returns velocity in m/s under key `velocity_mps` (and for
legacy compatibility still provides `velocity` == m/s). Downstream code
should prefer `velocity_mps` when present.

Vehicle performance characteristics are now loaded from database by reg_code,
with fallback to environment variables and defaults.
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from .physics_kernel import PhysicsKernel, PhysicsState
from ...services.vehicle_performance import VehiclePerformanceService


class PhysicsSpeedModel:
    def __init__(
        self,
        route_coords: List[Tuple[float, float]],  # (lon, lat)
        target_speed_mps: float = 25/3.6,
        dt: float = 0.5,
        vehicle_reg_code: Optional[str] = None,
    ):
        # Load vehicle performance from database if reg_code provided
        if vehicle_reg_code:
            performance = VehiclePerformanceService.get_performance_by_reg_code(vehicle_reg_code)
            print(f"Loaded performance for {vehicle_reg_code}: {performance.max_speed_kmh} km/h, "
                  f"{performance.acceleration_mps2} m/s² accel, {performance.braking_mps2} m/s² brake")
            print(f"🌀 Curvature-aware speed limiting enabled with 1.5 m/s² lateral acceleration limit")
            
            self.kernel = PhysicsKernel(
                route_coords=route_coords,
                dt=dt,
                v_max=performance.max_speed_mps,
                a_max=performance.acceleration_mps2,
                d_max=performance.braking_mps2,
                enable_curvature=True,  # Enable realistic curve speed limiting
                a_lat_max=1.5  # 1.5 m/s² lateral acceleration limit for safety
            )
            self.performance = performance
            
            # Use database max speed as target speed (vehicle should operate at its rated max speed)
            actual_target_speed = performance.max_speed_mps
            print(f"Setting target speed to vehicle max: {performance.max_speed_kmh} km/h ({actual_target_speed:.2f} m/s)")
        else:
            # Fallback to legacy initialization
            self.kernel = PhysicsKernel(route_coords=route_coords, dt=dt)
            self.performance = None
            actual_target_speed = target_speed_mps
        
        self.kernel.set_target_speed(actual_target_speed)
        self._last: Optional[PhysicsState] = None

    def update(self):  # signature aligned with other speed models
        state = self.kernel.step()
        self._last = state
        return {
            "velocity": state.v,          # legacy (interpreted as m/s now)
            "velocity_mps": state.v,      # explicit unit key
            "acceleration": state.a,      # m/s^2
            "phase": state.phase,
            "heading": state.heading,
            "distance_along_route": state.s,  # meters along route
            "progress": state.progress,
            "segment_index": state.segment_index,
        }
