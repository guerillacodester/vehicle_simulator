#!/usr/bin/env python3
"""
math.py
-------
Navigation math helpers for the vehicle driver.
Uses shared geospatial utilities.
"""

import math
import sys
import os
from typing import List, Tuple

# Add project root to path for absolute imports
if __name__ != "__main__":
    try:
        from arknet_transit_simulator.utils.geospatial import haversine, bearing, forward_point
    except ImportError:
        # Fallback for direct execution or testing
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
        from arknet_transit_simulator.utils.geospatial import haversine, bearing, forward_point
else:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
    from arknet_transit_simulator.utils.geospatial import haversine, bearing, forward_point

# ---------------------------
# ROUTE INTERPOLATION
# ---------------------------


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
