"""
Fleet Management Data Models
===========================
Pydantic models for fleet management API
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class UploadResponse(BaseModel):
    """Response model for file uploads"""
    success: bool
    message: str
    files_processed: int
    country: str
    upload_type: str
    upload_id: Optional[str] = None
    timestamp: datetime = datetime.now()

class CountryData(BaseModel):
    """Country fleet data summary"""
    country: str
    routes_count: int
    vehicles_count: int
    timetables_count: int
    last_updated: Optional[datetime] = None

class VehicleData(BaseModel):
    """Vehicle information"""
    vehicle_id: str
    vehicle_type: str
    capacity: Optional[int] = None
    country: str
    route_id: Optional[str] = None
    status: str = "inactive"
    last_seen: Optional[datetime] = None

class RouteData(BaseModel):
    """Route information"""
    route_id: str
    route_name: str
    country: str
    stops_count: int
    distance_km: Optional[float] = None
    created_at: datetime

class TimetableData(BaseModel):
    """Timetable information"""
    timetable_id: str
    route_id: str
    vehicle_id: str
    country: str
    schedule: Dict[str, Any]
    created_at: datetime

class FleetStats(BaseModel):
    """Fleet statistics"""
    total_countries: int
    total_routes: int
    total_vehicles: int
    total_timetables: int
    active_simulations: int
