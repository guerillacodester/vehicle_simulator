"""
Data models for GPS telemetry.

Pure Pydantic models with no dependencies on transport or UI.
Can be serialized/deserialized to/from JSON, dict, or any format.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union
from datetime import datetime


class PersonName(BaseModel):
    """Driver or conductor name."""
    first: str
    last: str
    
    def __str__(self) -> str:
        return f"{self.first} {self.last}"


class Vehicle(BaseModel):
    """
    GPS telemetry data for a single vehicle.
    
    Represents the latest known state of a GPS device.
    Matches the DeviceState model from GPSCentCom server.
    """
    
    # Identity
    deviceId: str = Field(..., description="Unique GPS device identifier")
    route: str = Field(..., description="Route code (e.g., '1', '2A')")
    vehicleReg: str = Field(..., description="Vehicle registration number")
    
    # Location (validated)
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    speed: float = Field(..., ge=0, description="Speed in km/h")
    heading: float = Field(..., ge=0, le=360, description="Heading in degrees (0=North)")
    
    # Crew
    driverId: Optional[str] = Field(None, description="Driver ID")
    driverName: Optional[Union[str, PersonName]] = Field(None, description="Driver name")
    conductorId: Optional[str] = Field(None, description="Conductor ID")
    conductorName: Optional[PersonName] = Field(None, description="Conductor name")
    
    # Timestamps
    timestamp: str = Field(..., description="Device-reported timestamp (ISO format)")
    lastSeen: str = Field(..., description="Server-received timestamp (ISO format)")
    
    # Shift times
    startTime: Optional[str] = Field(None, description="Shift start time (ISO format)")
    logoutTime: Optional[str] = Field(None, description="Shift end time (ISO format)")
    
    # Extensions
    extras: Optional[Dict[str, Any]] = Field(None, description="Custom extension fields")
    
    def get_driver_display_name(self) -> str:
        """Get formatted driver name for display."""
        if isinstance(self.driverName, PersonName):
            return str(self.driverName)
        elif isinstance(self.driverName, str):
            return self.driverName
        return f"Driver {self.driverId or 'Unknown'}"
    
    def get_age_seconds(self) -> float:
        """Calculate how old this telemetry data is in seconds."""
        try:
            last_seen = datetime.fromisoformat(self.lastSeen.replace('Z', '+00:00'))
            now = datetime.now(last_seen.tzinfo or None)
            return (now - last_seen).total_seconds()
        except Exception:
            return -1.0
    
    def is_stale(self, threshold_seconds: int = 120) -> bool:
        """Check if telemetry is stale (older than threshold)."""
        age = self.get_age_seconds()
        return age < 0 or age > threshold_seconds


class RouteAnalytics(BaseModel):
    """Analytics data for a specific route."""
    count: int = Field(..., description="Number of active devices on route")
    avgSpeed: float = Field(..., description="Average speed of devices on route")


class AnalyticsResponse(BaseModel):
    """Server analytics response."""
    routes: Dict[str, RouteAnalytics] = Field(..., description="Per-route analytics")
    totalDevices: int = Field(..., description="Total number of active devices")


class HealthResponse(BaseModel):
    """Server health check response."""
    status: str = Field(..., description="Health status (ok, degraded, down)")
    uptime_sec: float = Field(..., description="Server uptime in seconds")
    devices: int = Field(..., description="Number of active devices")
