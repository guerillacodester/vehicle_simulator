"""
Geospatial Service Client
=========================

GUI-agnostic client for consuming the Geospatial Service API.
Can be used from any interface (Next.js, console, desktop, mobile, etc.).

Usage:
    from clients.geospatial import GeospatialClient
    
    client = GeospatialClient("http://localhost:6000")
    address = client.reverse_geocode(13.0969, -59.6137)
    print(address)
"""

from .client import GeospatialClient
from .models import (
    Address,
    RouteGeometry,
    Building,
    DepotInfo,
    SpawnPoint,
    HealthResponse
)

__all__ = [
    "GeospatialClient",
    "Address",
    "RouteGeometry",
    "Building",
    "DepotInfo",
    "SpawnPoint",
    "HealthResponse"
]
