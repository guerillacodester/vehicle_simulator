"""
Fleet Management Client Models
===============================

Type-safe Pydantic models for fleet management API responses.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PositionData(BaseModel):
    """GPS position"""
    latitude: float
    longitude: float


class VehicleState(BaseModel):
    """Vehicle state response"""
    vehicle_id: str
    driver_name: Optional[str] = None
    route_id: Optional[int] = None
    current_position: Optional[PositionData] = None
    driver_state: Optional[str] = None
    engine_running: bool = False
    gps_running: bool = False
    passenger_count: int = 0
    capacity: int = 0
    boarding_active: bool = False


class VehicleListResponse(BaseModel):
    """List of vehicles response"""
    vehicles: list[VehicleState]
    count: int


class ConductorState(BaseModel):
    """Conductor state response"""
    conductor_id: str
    vehicle_id: str
    conductor_name: Optional[str] = None
    conductor_state: Optional[str] = None
    passengers_on_board: int = 0
    capacity: int = 0
    boarding_active: bool = False
    depot_boarding_active: bool = False


class ConductorListResponse(BaseModel):
    """List of conductors response"""
    conductors: list[ConductorState]
    count: int


class CommandResult(BaseModel):
    """Command execution result"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    timestamp: datetime
    simulator_running: bool
    active_vehicles: int
    event_bus_stats: Dict[str, Any]


class FleetEvent(BaseModel):
    """Real-time fleet event"""
    event_type: str
    vehicle_id: str
    timestamp: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None
