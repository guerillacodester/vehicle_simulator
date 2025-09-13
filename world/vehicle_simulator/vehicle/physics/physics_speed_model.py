"""Physics Speed Model Adapter

Adapts the PhysicsKernel to the existing Engine speed model interface.
The Engine expects an object with an update() method returning:
  {"velocity": <m/s>, "acceleration": <m/s^2>, ...}

We preserve backward compatibility by only filling required fields.
Additional diagnostic fields (phase, heading, progress) are included for future use.
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
            "velocity": state.v,            # required by Engine loop
            "acceleration": state.a,
            "phase": state.phase,
            "heading": state.heading,
            "distance_along_route": state.s,
            "progress": state.progress,
            "segment_index": state.segment_index,
        }
