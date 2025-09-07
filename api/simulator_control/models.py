"""
Simulator Control Data Models
============================
Pydantic models for simulator control API
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class SimulationRequest(BaseModel):
    """Request to start a simulation"""
    country: Optional[str] = None
    duration_seconds: int = 60
    update_interval: float = 1.0
    gps_enabled: bool = True

class SimulationStatus(BaseModel):
    """Current simulation status"""
    is_running: bool
    country: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    elapsed_seconds: Optional[float] = None
    update_interval: Optional[float] = None
    gps_enabled: bool = True
    active_vehicles: int = 0
    message: str = ""

class VehicleStatus(BaseModel):
    """Individual vehicle status"""
    vehicle_id: str
    is_active: bool
    route_id: Optional[str] = None
    route_name: Optional[str] = None
    current_location: Optional[Dict[str, float]] = None  # {"lat": 13.123, "lon": -59.456}
    speed_kmh: Optional[float] = None
    last_update: Optional[datetime] = None
    gps_enabled: bool = True
    country: Optional[str] = None

class SimulationMetrics(BaseModel):
    """Simulation performance metrics"""
    total_updates: int = 0
    updates_per_second: float = 0.0
    average_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    gps_messages_sent: int = 0
    errors_count: int = 0
    uptime_seconds: float = 0.0

class LogEntry(BaseModel):
    """Log entry"""
    timestamp: datetime
    level: str
    message: str
    vehicle_id: Optional[str] = None
