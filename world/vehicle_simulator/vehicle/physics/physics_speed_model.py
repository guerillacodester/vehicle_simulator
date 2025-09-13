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
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from .physics_kernel import PhysicsKernel, PhysicsState


class PhysicsSpeedModel:
    def __init__(
        self,
        route_coords: List[Tuple[float, float]],  # (lon, lat)
        target_speed_mps: float = 25/3.6,
        dt: float = 0.5,
    ):
        self.kernel = PhysicsKernel(route_coords=route_coords, dt=dt)
        self.kernel.set_target_speed(target_speed_mps)
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
