# world/vehicle/driver/navigation/geodesy.py
import math

def haversine(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """
    Great-circle distance (km) between two points given as (lon, lat).
    """
    lon1, lat1 = p1
    lon2, lat2 = p2
    R = 6371.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """
    Bearing (degrees) from p1 to p2, inputs as (lon, lat).
    """
    lon1, lat1 = map(math.radians, p1)
    lon2, lat2 = map(math.radians, p2)

    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360
