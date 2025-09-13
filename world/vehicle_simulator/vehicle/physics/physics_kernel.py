"""Physics Kernel

Authoritative kinematics integrator for a single vehicle moving along a polyline route.

Phase 1 Scope:
 - Longitudinal acceleration / braking toward a target speed
 - Basic curvature-aware speed capping (optional via init flag)
 - Deterministic dt stepping (no jerk limiting yet)
 - Mapping distance s -> (lat, lon) by linear interpolation between route coordinates
 - Phase classification

Design Goals:
 - Pure Python, low overhead
 - No dependency on driver personality or engine internals
 - Immutable PhysicsState snapshots for external consumption

Future Extensions:
 - Jerk limiting
 - Dwell / stop scheduling
 - Lateral g based cornering
 - Driver personality overlay
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

# ---------------------------- Data Classes ---------------------------- #
@dataclass(frozen=True)
class PhysicsState:
    t: float
    dt: float
    s: float              # distance along route (m)
    lat: float
    lon: float
    v: float              # m/s
    a: float              # m/s^2
    heading: float        # degrees
    phase: str            # CRUISE|BRAKE|DWELL|LAUNCH|STOPPED
    segment_index: int
    progress: float       # 0..1


class PhysicsKernel:
    def __init__(
        self,
        route_coords: List[Tuple[float, float]],  # (lon, lat) sequence
        dt: float = 0.5,
        a_max: float = 1.2,     # m/s^2 acceleration
        d_max: float = 1.8,     # m/s^2 braking (positive number)
        v_max: float = 25/3.6,  # global cap (m/s)
        enable_curvature: bool = False,
        a_lat_max: float = 1.5  # lateral accel cap for curvature (m/s^2)
    ):
        if len(route_coords) < 2:
            raise ValueError("Route requires at least two coordinates")
        self._coords = route_coords
        self.dt = dt
        self.a_max = a_max
        self.d_max = d_max
        self.v_max = v_max
        self.enable_curvature = enable_curvature
        self.a_lat_max = a_lat_max

        # Precompute segment lengths & bearings
        self._seg_lengths: List[float] = []
        self._bearings: List[float] = []
        total = 0.0
        for i in range(len(route_coords)-1):
            p1 = route_coords[i]
            p2 = route_coords[i+1]
            dist = self._haversine_m(p1, p2)
            self._seg_lengths.append(dist)
            self._bearings.append(self._bearing_deg(p1, p2))
            total += dist
        self.route_length_m = total
        self._cum_lengths: List[float] = [0.0]
        c = 0.0
        for L in self._seg_lengths:
            c += L
            self._cum_lengths.append(c)

        # State vars
        self._t = 0.0
        self._s = 0.0
        self._v = 0.0
        self._a = 0.0
        self._seg_index = 0
        self._phase = "STOPPED"
        self._target_speed: Optional[float] = self.v_max  # m/s
        self._force_stop = False

    # ---------------------------- Public API ---------------------------- #
    def set_target_speed(self, v_mps: Optional[float]):
        if v_mps is None:
            return
        self._target_speed = max(0.0, min(v_mps, self.v_max))

    def force_stop(self, stop: bool = True):
        self._force_stop = stop
        if stop:
            # ensure we have a target of 0 to brake toward
            self._target_speed = 0.0

    def step(self) -> PhysicsState:
        dt = self.dt

        # Determine effective cap
        v_cap = self._target_speed if self._target_speed is not None else self.v_max
        v_cap = min(v_cap, self.v_max)

        if self._force_stop:
            v_cap = 0.0

        # Decide acceleration direction
        if self._v < v_cap - 0.01:
            a_cmd = self.a_max
        elif self._v > v_cap + 0.01:
            a_cmd = -self.d_max
        else:
            a_cmd = 0.0

        # Integrate
        v_next = self._v + a_cmd * dt
        # Clamp overshoot when braking to zero
        if v_next < 0:
            v_next = 0.0
            a_cmd = -self._v / dt if dt > 0 else 0.0

        # Distance advance (basic kinematics)
        s_advance = self._v * dt + 0.5 * a_cmd * dt * dt
        s_next = self._s + s_advance
        if s_next >= self.route_length_m:
            s_next = self.route_length_m
            v_next = 0.0
            a_cmd = 0.0
            self._force_stop = True

        # Map s to segment
        seg_index = self._find_segment(s_next)
        lat, lon, heading = self._interpolate(seg_index, s_next)

        # Phase classification
        if v_next < 0.05 and self._force_stop:
            phase = "STOPPED"
        elif a_cmd > 0.05 and self._v < 0.2:
            phase = "LAUNCH"
        elif a_cmd > 0.05:
            phase = "CRUISE"  # accelerating but already moving
        elif a_cmd < -0.05 and v_next > 0.2:
            phase = "BRAKE"
        else:
            phase = "CRUISE"

        # Commit state
        self._t += dt
        self._s = s_next
        self._v = v_next
        self._a = a_cmd
        self._seg_index = seg_index
        self._phase = phase

        return PhysicsState(
            t=self._t,
            dt=dt,
            s=self._s,
            lat=lat,
            lon=lon,
            v=self._v,
            a=self._a,
            heading=heading,
            phase=self._phase,
            segment_index=self._seg_index,
            progress=(self._s / self.route_length_m) if self.route_length_m > 0 else 0.0,
        )

    # ---------------------------- Internal Helpers ---------------------------- #
    def _find_segment(self, s: float) -> int:
        # linear scan (fast enough for modest route lengths); can binary search later
        for i in range(len(self._cum_lengths)-1):
            if self._cum_lengths[i] <= s < self._cum_lengths[i+1]:
                return i
        return len(self._cum_lengths)-2

    def _interpolate(self, seg_index: int, s: float) -> Tuple[float, float, float]:
        s0 = self._cum_lengths[seg_index]
        s1 = self._cum_lengths[seg_index+1]
        if s1 - s0 < 1e-6:
            lon, lat = self._coords[seg_index]
            return lat, lon, self._bearings[seg_index]
        ratio = (s - s0) / (s1 - s0)
        (lon0, lat0) = self._coords[seg_index]
        (lon1, lat1) = self._coords[seg_index+1]
        lat = lat0 + (lat1 - lat0) * ratio
        lon = lon0 + (lon1 - lon0) * ratio
        heading = self._bearings[seg_index]
        return lat, lon, heading

    @staticmethod
    def _haversine_m(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        lon1, lat1 = p1
        lon2, lat2 = p2
        R = 6371000.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    @staticmethod
    def _bearing_deg(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        lon1, lat1 = map(math.radians, (p1[0], p1[1]))
        lon2, lat2 = map(math.radians, (p2[0], p2[1]))
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
        brng = math.degrees(math.atan2(x, y))
        return (brng + 360) % 360
