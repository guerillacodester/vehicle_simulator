"""
Vehicle schemas for Fleet Management API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema, VehicleStatusEnum

class VehicleBase(BaseModel):
    country_id: UUID
    reg_code: str
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None
    assigned_driver_id: Optional[UUID] = None
    status: VehicleStatusEnum = VehicleStatusEnum.available
    profile_id: Optional[str] = None
    notes: Optional[str] = None
    
    # Performance characteristics
    max_speed_kmh: float = Field(default=25.0, ge=5.0, le=100.0, description="Maximum speed in km/h")
    acceleration_mps2: float = Field(default=1.2, ge=0.1, le=5.0, description="Acceleration in m/s²")
    braking_mps2: float = Field(default=1.8, ge=0.1, le=10.0, description="Braking deceleration in m/s²")
    eco_mode: bool = Field(default=False, description="Eco-friendly driving mode")
    performance_profile: Optional[str] = Field(default=None, description="Performance profile: standard, eco, performance, express")

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    country_id: Optional[UUID] = None
    reg_code: Optional[str] = None
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None
    assigned_driver_id: Optional[UUID] = None
    status: Optional[VehicleStatusEnum] = None
    profile_id: Optional[str] = None
    notes: Optional[str] = None
    
    # Performance characteristics
    max_speed_kmh: Optional[float] = Field(None, ge=5.0, le=100.0, description="Maximum speed in km/h")
    acceleration_mps2: Optional[float] = Field(None, ge=0.1, le=5.0, description="Acceleration in m/s²")
    braking_mps2: Optional[float] = Field(None, ge=0.1, le=10.0, description="Braking deceleration in m/s²")
    eco_mode: Optional[bool] = Field(None, description="Eco-friendly driving mode")
    performance_profile: Optional[str] = Field(None, description="Performance profile: standard, eco, performance, express")

class Vehicle(VehicleBase, BaseSchema):
    vehicle_id: UUID
    created_at: datetime
    updated_at: datetime

class VehiclePublic(BaseModel):
    """Public vehicle schema without UUIDs for enhanced security"""
    reg_code: str
    status: VehicleStatusEnum = VehicleStatusEnum.available
    profile_id: Optional[str] = None
    notes: Optional[str] = None
    
    # Performance characteristics
    max_speed_kmh: float = Field(default=25.0, ge=5.0, le=100.0, description="Maximum speed in km/h")
    acceleration_mps2: float = Field(default=1.2, ge=0.1, le=5.0, description="Acceleration in m/s²")
    braking_mps2: float = Field(default=1.8, ge=0.1, le=10.0, description="Braking deceleration in m/s²")
    eco_mode: bool = Field(default=False, description="Eco-friendly driving mode")
    performance_profile: Optional[str] = Field(default=None, description="Performance profile: standard, eco, performance, express")

class VehiclePublicCreate(BaseModel):
    """Create vehicle using public API with business identifiers only"""
    reg_code: str
    status: VehicleStatusEnum = VehicleStatusEnum.available
    capacity: Optional[int] = None
    profile_id: Optional[str] = None
    notes: Optional[str] = None
    # Business identifiers instead of UUIDs
    country_code: Optional[str] = None      # e.g., "BB" for Barbados
    depot_name: Optional[str] = None        # e.g., "Bridgetown"
    preferred_route_code: Optional[str] = None  # e.g., "1A"

class VehiclePublicUpdate(BaseModel):
    """Update vehicle using public API with business identifiers only"""
    status: Optional[VehicleStatusEnum] = None
    capacity: Optional[int] = None
    profile_id: Optional[str] = None
    notes: Optional[str] = None
    # Business identifiers instead of UUIDs
    depot_name: Optional[str] = None
    preferred_route_code: Optional[str] = None

# Performance-specific schemas
class VehiclePerformance(BaseModel):
    """Vehicle performance characteristics"""
    max_speed_kmh: float = Field(ge=5.0, le=100.0, description="Maximum speed in km/h")
    acceleration_mps2: float = Field(ge=0.1, le=5.0, description="Acceleration in m/s²")
    braking_mps2: float = Field(ge=0.1, le=10.0, description="Braking deceleration in m/s²")
    eco_mode: bool = Field(description="Eco-friendly driving mode")
    performance_profile: Optional[str] = Field(description="Performance profile: standard, eco, performance, express")

class VehiclePerformanceUpdate(BaseModel):
    """Update vehicle performance characteristics"""
    max_speed_kmh: Optional[float] = Field(None, ge=5.0, le=100.0, description="Maximum speed in km/h")
    acceleration_mps2: Optional[float] = Field(None, ge=0.1, le=5.0, description="Acceleration in m/s²")
    braking_mps2: Optional[float] = Field(None, ge=0.1, le=10.0, description="Braking deceleration in m/s²")
    eco_mode: Optional[bool] = Field(None, description="Eco-friendly driving mode")
    performance_profile: Optional[str] = Field(None, description="Performance profile: standard, eco, performance, express")

class PerformanceProfile(BaseModel):
    """Pre-defined performance profile"""
    name: str = Field(description="Profile name: standard, eco, performance, express")
    max_speed_kmh: float = Field(ge=5.0, le=100.0, description="Maximum speed in km/h")
    acceleration_mps2: float = Field(ge=0.1, le=5.0, description="Acceleration in m/s²")
    braking_mps2: float = Field(ge=0.1, le=10.0, description="Braking deceleration in m/s²")
    eco_mode: bool = Field(description="Eco-friendly driving mode")
    description: str = Field(description="Profile description")
