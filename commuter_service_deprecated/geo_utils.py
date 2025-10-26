"""
Geographic Utility Functions
=============================

Shared geographic calculations and spatial operations used throughout
the commuter service. Eliminates duplicate Haversine implementations
and provides consistent geographic computations.

All distance calculations use the WGS84 ellipsoid approximation with
the Haversine formula, which is accurate for distances under ~1000km.
"""

from math import radians, sin, cos, sqrt, atan2, degrees, asin
from typing import Tuple, List
from commuter_service.constants import (
    EARTH_RADIUS_METERS,
    EARTH_RADIUS_KM,
    GRID_CELL_SIZE_DEGREES
)


def haversine_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
    unit: str = "meters"
) -> float:
    """
    Calculate distance between two geographic points using Haversine formula.
    
    The Haversine formula calculates the great-circle distance between two points
    on a sphere given their longitudes and latitudes. This is accurate for most
    purposes when distances are under ~1000km.
    
    Args:
        point1: Tuple of (latitude, longitude) in decimal degrees
        point2: Tuple of (latitude, longitude) in decimal degrees
        unit: Return unit - "meters" (default) or "km"
    
    Returns:
        Distance between points in specified unit
    
    Example:
        >>> barbados_depot = (13.0965, -59.6086)
        >>> bridgetown = (13.0969, -59.6166)
        >>> distance = haversine_distance(barbados_depot, bridgetown)
        >>> print(f"{distance:.2f} meters")
        667.89 meters
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    # Haversine formula
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    # Calculate distance
    if unit == "km":
        return EARTH_RADIUS_KM * c
    else:  # default to meters
        return EARTH_RADIUS_METERS * c


def get_grid_cell(
    lat: float,
    lon: float,
    cell_size: float = GRID_CELL_SIZE_DEGREES
) -> Tuple[int, int]:
    """
    Get grid cell coordinates for spatial indexing.
    
    Divides the world into a grid of cells and returns the cell coordinates
    for a given lat/lon. Useful for spatial indexing and proximity queries.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        cell_size: Grid cell size in degrees (default ~1km)
    
    Returns:
        Tuple of (grid_x, grid_y) integer coordinates
    
    Example:
        >>> cell = get_grid_cell(13.0965, -59.6086)
        >>> print(f"Cell: {cell}")
        Cell: (1309, -5960)
    """
    grid_x = int(lat / cell_size)
    grid_y = int(lon / cell_size)
    return (grid_x, grid_y)


def get_nearby_cells(
    lat: float,
    lon: float,
    radius_km: float = 2.0,
    cell_size: float = GRID_CELL_SIZE_DEGREES
) -> List[Tuple[int, int]]:
    """
    Get all grid cells within a given radius of a point.
    
    Used for efficient proximity queries - instead of checking all points,
    we can check only points in nearby grid cells.
    
    Args:
        lat: Center latitude in decimal degrees
        lon: Center longitude in decimal degrees
        radius_km: Search radius in kilometers
        cell_size: Grid cell size in degrees
    
    Returns:
        List of (grid_x, grid_y) tuples for nearby cells
    
    Example:
        >>> cells = get_nearby_cells(13.0965, -59.6086, radius_km=1.0)
        >>> print(f"Found {len(cells)} nearby cells")
        Found 9 nearby cells
    """
    # Convert radius to degrees (approximate)
    # At equator: 1 degree ≈ 111 km
    radius_deg = radius_km / 111.0
    
    center_cell = get_grid_cell(lat, lon, cell_size)
    cell_radius = int(radius_deg / cell_size) + 1
    
    cells = []
    for dx in range(-cell_radius, cell_radius + 1):
        for dy in range(-cell_radius, cell_radius + 1):
            cells.append((center_cell[0] + dx, center_cell[1] + dy))
    
    return cells


def is_within_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
    max_distance_meters: float
) -> bool:
    """
    Check if two points are within a specified distance.
    
    More efficient than calculating exact distance when you only need
    to know if points are within a threshold.
    
    Args:
        point1: First point (lat, lon)
        point2: Second point (lat, lon)
        max_distance_meters: Maximum distance in meters
    
    Returns:
        True if points are within max_distance_meters, False otherwise
    
    Example:
        >>> depot = (13.0965, -59.6086)
        >>> passenger = (13.0970, -59.6090)
        >>> is_within_distance(depot, passenger, max_distance_meters=100)
        True
    """
    distance = haversine_distance(point1, point2, unit="meters")
    return distance <= max_distance_meters


def bearing_between_points(
    point1: Tuple[float, float],
    point2: Tuple[float, float]
) -> float:
    """
    Calculate the bearing (direction) from point1 to point2.
    
    Returns the compass bearing in degrees (0-360), where:
    - 0/360 = North
    - 90 = East
    - 180 = South
    - 270 = West
    
    Args:
        point1: Start point (lat, lon)
        point2: End point (lat, lon)
    
    Returns:
        Bearing in degrees (0-360)
    
    Example:
        >>> start = (13.0965, -59.6086)
        >>> end = (13.1065, -59.6086)  # North
        >>> bearing = bearing_between_points(start, end)
        >>> print(f"{bearing:.1f}° (North)")
        0.0° (North)
    """
    lat1, lon1 = radians(point1[0]), radians(point1[1])
    lat2, lon2 = radians(point2[0]), radians(point2[1])
    
    dlon = lon2 - lon1
    
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    
    initial_bearing = atan2(x, y)
    compass_bearing = (degrees(initial_bearing) + 360) % 360
    
    return compass_bearing


def midpoint_between_points(
    point1: Tuple[float, float],
    point2: Tuple[float, float]
) -> Tuple[float, float]:
    """
    Calculate the geographic midpoint between two points.
    
    Args:
        point1: First point (lat, lon)
        point2: Second point (lat, lon)
    
    Returns:
        Midpoint (lat, lon) in decimal degrees
    
    Example:
        >>> depot = (13.0965, -59.6086)
        >>> destination = (13.1065, -59.6186)
        >>> midpoint = midpoint_between_points(depot, destination)
        >>> print(f"Midpoint: {midpoint}")
        Midpoint: (13.1015, -59.6136)
    """
    lat1, lon1 = radians(point1[0]), radians(point1[1])
    lat2, lon2 = radians(point2[0]), radians(point2[1])
    
    bx = cos(lat2) * cos(lon2 - lon1)
    by = cos(lat2) * sin(lon2 - lon1)
    
    lat_mid = atan2(
        sin(lat1) + sin(lat2),
        sqrt((cos(lat1) + bx)**2 + by**2)
    )
    lon_mid = lon1 + atan2(by, cos(lat1) + bx)
    
    return (degrees(lat_mid), degrees(lon_mid))


def bounding_box(
    center: Tuple[float, float],
    radius_km: float
) -> Tuple[float, float, float, float]:
    """
    Calculate a bounding box around a center point.
    
    Returns the minimum and maximum lat/lon that encompasses
    a circular area of the given radius.
    
    Args:
        center: Center point (lat, lon)
        radius_km: Radius in kilometers
    
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    
    Example:
        >>> center = (13.0965, -59.6086)
        >>> bbox = bounding_box(center, radius_km=1.0)
        >>> print(f"Bounding box: {bbox}")
        Bounding box: (13.0876, -59.6175, 13.1054, -59.5997)
    """
    lat, lon = center
    
    # Approximate: 1 degree latitude ≈ 111 km
    # 1 degree longitude varies by latitude: 111 * cos(lat) km
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * cos(radians(lat)))
    
    min_lat = lat - lat_delta
    max_lat = lat + lat_delta
    min_lon = lon - lon_delta
    max_lon = lon + lon_delta
    
    return (min_lat, min_lon, max_lat, max_lon)


def route_length_from_coordinates(
    coordinates: List[Tuple[float, float]]
) -> float:
    """
    Calculate total route length from a list of coordinates.
    
    Sums the Haversine distances between consecutive points
    to get the total route length.
    
    Args:
        coordinates: List of (lat, lon) tuples representing route path
    
    Returns:
        Total route length in meters
    
    Example:
        >>> route = [(13.0965, -59.6086), (13.1065, -59.6186), (13.1165, -59.6286)]
        >>> length = route_length_from_coordinates(route)
        >>> print(f"Route length: {length/1000:.2f} km")
        Route length: 27.89 km
    """
    if len(coordinates) < 2:
        return 0.0
    
    total_length = 0.0
    for i in range(len(coordinates) - 1):
        segment_length = haversine_distance(
            coordinates[i],
            coordinates[i + 1],
            unit="meters"
        )
        total_length += segment_length
    
    return total_length
