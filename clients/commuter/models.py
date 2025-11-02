"""
Pydantic models for Commuter Service responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Passenger(BaseModel):
    """Individual passenger data"""
    documentId: str = Field(..., description="Passenger document ID")
    status: str = Field(..., description="Passenger status (WAITING, BOARDED, etc.)")
    route_id: Optional[str] = Field(None, description="Assigned route ID")
    depot_id: Optional[str] = Field(None, description="Origin depot ID")
    start_lat: float = Field(..., description="Start location latitude")
    start_lon: float = Field(..., description="Start location longitude")
    stop_lat: float = Field(..., description="Destination latitude")
    stop_lon: float = Field(..., description="Destination longitude")
    spawned_at: str = Field(..., description="Spawn timestamp (ISO8601)")
    distance_from_route_start: Optional[float] = Field(None, description="Distance from route start in meters")
    start_address: Optional[str] = Field(None, description="Geocoded start address")
    stop_address: Optional[str] = Field(None, description="Geocoded stop address")
    commute_distance: Optional[float] = Field(None, description="Commute distance in km")


class ManifestResponse(BaseModel):
    """Response from /api/manifest endpoint"""
    count: int = Field(..., description="Number of passengers returned")
    route_id: Optional[str] = Field(None, description="Route filter applied")
    depot_id: Optional[str] = Field(None, description="Depot filter applied")
    passengers: List[Dict[str, Any]] = Field(..., description="Passenger data")
    ordered_by_route_position: bool = Field(..., description="Whether sorted by route position")


class BarchartResponse(BaseModel):
    """Response from /api/manifest/visualization/barchart"""
    hourly_counts: List[int] = Field(..., description="Passenger count per hour (0-23)")
    total: int = Field(..., description="Total passengers")
    max_count: int = Field(..., description="Maximum count in any hour")
    peak_hour: int = Field(..., description="Hour with most passengers (0-23)")
    route_passengers: int = Field(..., description="Count of route passengers")
    depot_passengers: int = Field(..., description="Count of depot passengers")
    date: str = Field(..., description="Target date (YYYY-MM-DD)")
    route_name: Optional[str] = Field(None, description="Route name if filtered")


class RouteMetrics(BaseModel):
    """Route metrics summary"""
    total_passengers: int = Field(..., description="Total passengers")
    route_passengers: int = Field(..., description="Route passengers")
    depot_passengers: int = Field(..., description="Depot passengers")
    avg_commute_distance: float = Field(..., description="Average commute distance in km")
    avg_depot_distance: float = Field(..., description="Average distance from depot in km")
    total_route_distance: Optional[float] = Field(None, description="Total route distance in km")
    date: str = Field(..., description="Target date (YYYY-MM-DD)")
    route_name: Optional[str] = Field(None, description="Route name if filtered")


class TableResponse(BaseModel):
    """Response from /api/manifest/visualization/table"""
    passengers: List[Dict[str, Any]] = Field(..., description="Enriched passenger data with addresses")
    metrics: RouteMetrics = Field(..., description="Summary metrics")
    date: str = Field(..., description="Target date (YYYY-MM-DD)")
    route_name: Optional[str] = Field(None, description="Route name if filtered")


class SeedRequest(BaseModel):
    """Request to seed passengers"""
    route: str = Field(..., description="Route short name (e.g., '1')")
    day: Optional[str] = Field(None, description="Day of week (monday, tuesday, etc.)")
    date: Optional[str] = Field(None, description="Specific date (YYYY-MM-DD)")
    start_hour: int = Field(0, ge=0, le=23, description="Start hour (0-23)")
    end_hour: int = Field(23, ge=0, le=23, description="End hour (0-23)")
    spawn_type: str = Field("route", description="Spawn type: route, depot, or both")


class SeedResponse(BaseModel):
    """Response from seeding operation"""
    success: bool = Field(..., description="Whether seeding succeeded")
    route: str = Field(..., description="Route seeded")
    date: str = Field(..., description="Date seeded (YYYY-MM-DD)")
    passengers_created: int = Field(..., description="Number of passengers created")
    route_passengers: int = Field(..., description="Route passengers created")
    depot_passengers: int = Field(..., description="Depot passengers created")
    message: str = Field(..., description="Success/error message")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    timestamp: str = Field(..., description="ISO8601 timestamp")
