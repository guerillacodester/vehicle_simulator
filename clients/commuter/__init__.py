"""
Commuter Service Client
=======================

GUI-agnostic client for consuming the Commuter Service API.
Can be used from any interface (Next.js, console, desktop, mobile, etc.).

Usage:
    from clients.commuter import CommuterClient
    
    client = CommuterClient("http://localhost:4000")
    
    # Query manifest
    passengers = client.get_manifest(route="1", limit=100)
    
    # Get visualization
    barchart = client.get_barchart(date="2024-11-04", route="1")
    
    # Seed passengers (if endpoint exists)
    result = client.seed_passengers(route="1", day="monday")
"""

from .client import CommuterClient
from .models import (
    Passenger,
    ManifestResponse,
    BarchartResponse,
    TableResponse,
    RouteMetrics,
    SeedRequest,
    SeedResponse,
    HealthResponse
)

__all__ = [
    "CommuterClient",
    "Passenger",
    "ManifestResponse",
    "BarchartResponse",
    "TableResponse",
    "RouteMetrics",
    "SeedRequest",
    "SeedResponse",
    "HealthResponse"
]
