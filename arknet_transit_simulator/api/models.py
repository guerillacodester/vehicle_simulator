"""Pydantic models for API responses."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    simulator_running: bool
    active_vehicles: int
    event_bus_stats: Dict[str, Any]


class VehicleResponse(BaseModel):
    """Vehicle state response."""
    vehicle_id: str
    driver_id: str
    driver_name: str
    route_id: Optional[str] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    driver_state: str
    engine_running: bool
    gps_running: bool
    passenger_count: int = 0
    capacity: int = 0
    boarding_active: bool = False


class DriverListResponse(BaseModel):
    """List of drivers."""
    drivers: List[VehicleResponse]
    total: int


class ConductorResponse(BaseModel):
    """Conductor state response."""
    conductor_id: str
    vehicle_id: str
    conductor_name: str
    conductor_state: str
    passengers_on_board: int
    capacity: int
    boarding_active: bool
    depot_boarding_active: bool = False


class ConductorListResponse(BaseModel):
    """List of conductors."""
    conductors: List[ConductorResponse]
    total: int


class EventResponse(BaseModel):
    """Event data response."""
    event_type: str
    data: Dict[str, Any]
    timestamp: str


class CommandResponse(BaseModel):
    """Generic command response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
