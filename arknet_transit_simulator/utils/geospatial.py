#!/usr/bin/env python3
"""
geospatial.py
-------------
Shared geospatial utility functions for the ArkNet Vehicle Simulator.

This module provides common geospatial calculations used throughout the simulator:
- Great-circle distance (Haversine formula)
- Initial bearing between two points
- Forward point projection along a bearing

All functions use the WGS84 Earth model with radius R = 6371 km.

Examples:
    >>> from arknet_transit_simulator.utils.geospatial import haversine, bearing, forward_point
    >>> 
    >>> # Calculate distance between two points
    >>> dist_km = haversine(13.0975, -59.6137, 13.1000, -59.6200)
    >>> print(f"Distance: {dist_km:.3f} km")
    >>> 
    >>> # Get bearing from point A to point B
    >>> heading = bearing(13.0975, -59.6137, 13.1000, -59.6200)
    >>> print(f"Bearing: {heading:.1f}°")
    >>> 
    >>> # Project a point 1000m at bearing 45°
    >>> new_lat, new_lon = forward_point(13.0975, -59.6137, 45.0, 1000.0)
"""

import math
from typing import Tuple

__all__ = ['haversine', 'bearing', 'forward_point']


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula to compute the shortest distance over the
    Earth's surface (assuming a spherical Earth with radius 6371 km).
    
    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees
    
    Returns:
        Distance between the two points in kilometers
    
    Example:
        >>> # Distance from Bridgetown to Speightstown, Barbados
        >>> dist = haversine(13.0975, -59.6137, 13.2381, -59.6431)
        >>> print(f"{dist:.2f} km")
        15.71 km
    """
    R = 6371.0  # Earth radius in kilometers
    
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(dphi / 2.0) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the initial bearing (forward azimuth) from point A to point B.
    
    The bearing is the compass direction you need to travel from the first
    point to reach the second point along a great circle path.
    
    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees
    
    Returns:
        Initial bearing in degrees (0-360), where:
        - 0° = North
        - 90° = East
        - 180° = South
        - 270° = West
    
    Example:
        >>> # Bearing from Bridgetown to Speightstown
        >>> heading = bearing(13.0975, -59.6137, 13.2381, -59.6431)
        >>> print(f"{heading:.1f}°")
        337.2°
    """
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    
    # Calculate bearing
    x = math.sin(dlambda) * math.cos(phi2)
    y = (math.cos(phi1) * math.sin(phi2) - 
         math.sin(phi1) * math.cos(phi2) * math.cos(dlambda))
    
    brng = math.degrees(math.atan2(x, y))
    
    # Normalize to 0-360
    return (brng + 360.0) % 360.0


def forward_point(lat1: float, lon1: float, bearing_deg: float, distance_m: float) -> Tuple[float, float]:
    """
    Project a point forward along a bearing for a given distance.
    
    Given a starting point, compass bearing, and distance, calculate the
    destination point using a spherical Earth model.
    
    Args:
        lat1: Latitude of starting point in decimal degrees
        lon1: Longitude of starting point in decimal degrees
        bearing_deg: Compass bearing in degrees (0-360)
        distance_m: Distance to travel in meters
    
    Returns:
        Tuple of (latitude, longitude) of the destination point in decimal degrees
    
    Example:
        >>> # Move 1000m north from Bridgetown
        >>> new_lat, new_lon = forward_point(13.0975, -59.6137, 0.0, 1000.0)
        >>> print(f"New position: {new_lat:.4f}, {new_lon:.4f}")
        New position: 13.1065, -59.6137
    """
    R = 6371000.0  # Earth radius in meters
    
    # Convert to radians
    phi1 = math.radians(lat1)
    lam1 = math.radians(lon1)
    brng = math.radians(bearing_deg)
    
    # Angular distance
    d_div_R = distance_m / R
    
    # Calculate destination point
    phi2 = math.asin(
        math.sin(phi1) * math.cos(d_div_R) +
        math.cos(phi1) * math.sin(d_div_R) * math.cos(brng)
    )
    
    lam2 = lam1 + math.atan2(
        math.sin(brng) * math.sin(d_div_R) * math.cos(phi1),
        math.cos(d_div_R) - math.sin(phi1) * math.sin(phi2)
    )
    
    return math.degrees(phi2), math.degrees(lam2)
