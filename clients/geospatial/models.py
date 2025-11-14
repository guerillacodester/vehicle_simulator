"""
Pydantic models for Geospatial Service responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Address(BaseModel):
    """Reverse geocoded address"""
    formatted: str = Field(..., description="Full formatted address")
    street: Optional[str] = Field(None, description="Street name")
    amenity: Optional[str] = Field(None, description="Nearby amenity")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class RouteGeometry(BaseModel):
    """Route geometry with LineString"""
    route_id: str = Field(..., description="Route document ID")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON LineString")
    total_distance_meters: float = Field(..., description="Total route length in meters")


class Building(BaseModel):
    """Building near a route"""
    osm_id: str = Field(..., description="OpenStreetMap ID")
    name: Optional[str] = Field(None, description="Building name")
    amenity: Optional[str] = Field(None, description="Building type/amenity")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    distance_from_route: float = Field(..., description="Distance from route in meters")


class DepotInfo(BaseModel):
    """Depot information"""
    documentId: str = Field(..., description="Depot document ID")
    name: str = Field(..., description="Depot name")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")


class SpawnPoint(BaseModel):
    """Potential spawn point along a route"""
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    distance_from_start: float = Field(..., description="Distance from route start in meters")
    segment_index: int = Field(..., description="Route segment index")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    database: str = Field(..., description="Database connection status")
    latency_ms: float = Field(..., description="Database query latency in milliseconds")
    timestamp: str = Field(..., description="ISO8601 timestamp")
