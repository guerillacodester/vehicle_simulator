#!/usr/bin/env python3
"""
math.py
-------
Pure math helpers for navigation:
- haversine distance
- initial bearing
- interpolation along a polyline route
"""

import math
from typing import List, Tuple

# ---------------------------
# LEGACY FUNCTIONS
# ---------------------------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two points on Earth.
    Returns kilometers.
    """
    R = 6371.0  # Earth radius km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Initial bearing (forward azimuth) in degrees from point A to point B.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)

    brng = math.degrees(math.atan2(x, y))
    return (brng + 360.0) % 360.0


def interpolate_along_route(route: List[Tuple[float, float]], distance: float) -> Tuple[float, float, float]:
    """
    LEGACY: Interpolate a position along a polyline route (linear lat/lon).
    :param route: list of (lat, lon) tuples forming the route
    :param distance: distance travelled along the route (km)
    :return: (lat, lon, heading) at that distance
    """
    if len(route) < 2:
        raise ValueError("Route must contain at least two points")

    remaining = distance
    for i in range(len(route) - 1):
        lat1, lon1 = route[i]
        lat2, lon2 = route[i + 1]
        seg_len = haversine(lat1, lon1, lat2, lon2)

        if remaining <= seg_len:
            frac = remaining / seg_len if seg_len > 0 else 0.0
            lat = lat1 + frac * (lat2 - lat1)
            lon = lon1 + frac * (lon2 - lon1)
            head = bearing(lat1, lon1, lat2, lon2)
            return (lat, lon, head)

        remaining -= seg_len

    lat1, lon1 = route[-2]
    lat2, lon2 = route[-1]
    return (lat2, lon2, bearing(lat1, lon1, lat2, lon2))

# ---------------------------
# NEW FUNCTIONS
# ---------------------------

def forward_point(lat1: float, lon1: float, bearing_deg: float, distance_m: float) -> Tuple[float, float]:
    """
    Compute destination point given start (lat1, lon1), bearing (degrees), and distance (m).
    Uses a spherical Earth model.
    """
    R = 6371000.0  # Earth radius (m)
    phi1 = math.radians(lat1)
    lam1 = math.radians(lon1)
    brng = math.radians(bearing_deg)

    d_div_R = distance_m / R

    phi2 = math.asin(math.sin(phi1) * math.cos(d_div_R) +
                     math.cos(phi1) * math.sin(d_div_R) * math.cos(brng))

    lam2 = lam1 + math.atan2(math.sin(brng) * math.sin(d_div_R) * math.cos(phi1),
                             math.cos(d_div_R) - math.sin(phi1) * math.sin(phi2))

    return math.degrees(phi2), math.degrees(lam2)


def interpolate_along_route_geodesic(route: List[Tuple[float, float]], distance_km: float) -> Tuple[float, float, float]:
    """
    NEW: Interpolate a position along a polyline route using geodesic forward projection.
    :param route: list of (lat, lon) tuples forming the route
    :param distance_km: distance travelled along the route (km)
    :return: (lat, lon, heading)
    """
    if len(route) < 2:
        raise ValueError("Route must contain at least two points")

    remaining = distance_km
    for i in range(len(route) - 1):
        lat1, lon1 = route[i]
        lat2, lon2 = route[i + 1]
        seg_len_km = haversine(lat1, lon1, lat2, lon2)

        if remaining <= seg_len_km:
            dist_m = remaining * 1000.0
            head = bearing(lat1, lon1, lat2, lon2)
            lat, lon = forward_point(lat1, lon1, head, dist_m)
            return (lat, lon, head)

        remaining -= seg_len_km

    lat1, lon1 = route[-2]
    lat2, lon2 = route[-1]
    return (lat2, lon2, bearing(lat1, lon1, lat2, lon2))
