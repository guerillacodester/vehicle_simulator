"""
Pydantic schemas for Fleet Management API
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID
from enum import Enum

# Enum for vehicle status
class VehicleStatusEnum(str, Enum):
    available = "available"
    in_service = "in_service"
    maintenance = "maintenance"
    retired = "retired"

# Base schemas
class CountryBase(BaseModel):
    iso_code: str
    name: str

class CountryCreate(CountryBase):
    pass

class CountryUpdate(BaseModel):
    iso_code: Optional[str] = None
    name: Optional[str] = None

class Country(CountryBase):
    model_config = ConfigDict(from_attributes=True)
    
    country_id: UUID
    created_at: datetime

# Depot schemas
class DepotBase(BaseModel):
    country_id: UUID
    name: str
    capacity: Optional[int] = None
    notes: Optional[str] = None

class DepotCreate(DepotBase):
    pass

class DepotUpdate(BaseModel):
    country_id: Optional[UUID] = None
    name: Optional[str] = None
    capacity: Optional[int] = None
    notes: Optional[str] = None

class Depot(DepotBase):
    model_config = ConfigDict(from_attributes=True)
    
    depot_id: UUID
    created_at: datetime
    updated_at: datetime

# Route schemas
class RouteBase(BaseModel):
    country_id: UUID
    short_name: str
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    country_id: Optional[UUID] = None
    short_name: Optional[str] = None
    long_name: Optional[str] = None
    parishes: Optional[str] = None
    is_active: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class Route(RouteBase):
    model_config = ConfigDict(from_attributes=True)
    
    route_id: UUID
    created_at: datetime
    updated_at: datetime

# Vehicle schemas
class VehicleBase(BaseModel):
    country_id: UUID
    reg_code: str
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None
    status: VehicleStatusEnum = VehicleStatusEnum.available
    profile_id: Optional[str] = None
    notes: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    country_id: Optional[UUID] = None
    reg_code: Optional[str] = None
    home_depot_id: Optional[UUID] = None
    preferred_route_id: Optional[UUID] = None
    status: Optional[VehicleStatusEnum] = None
    profile_id: Optional[str] = None
    notes: Optional[str] = None

class Vehicle(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    
    vehicle_id: UUID
    created_at: datetime
    updated_at: datetime

# Service schemas
class ServiceBase(BaseModel):
    country_id: UUID
    name: str
    mon: bool = False
    tue: bool = False
    wed: bool = False
    thu: bool = False
    fri: bool = False
    sat: bool = False
    sun: bool = False
    date_start: date
    date_end: date

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    country_id: Optional[UUID] = None
    name: Optional[str] = None
    mon: Optional[bool] = None
    tue: Optional[bool] = None
    wed: Optional[bool] = None
    thu: Optional[bool] = None
    fri: Optional[bool] = None
    sat: Optional[bool] = None
    sun: Optional[bool] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None

class Service(ServiceBase):
    model_config = ConfigDict(from_attributes=True)
    
    service_id: UUID
    created_at: datetime
    updated_at: datetime

# Shape schemas
class ShapeBase(BaseModel):
    pass  # Geometry field will be handled separately

class ShapeCreate(ShapeBase):
    pass

class ShapeUpdate(ShapeBase):
    pass

class Shape(ShapeBase):
    model_config = ConfigDict(from_attributes=True)
    
    shape_id: UUID

# Stop schemas
class StopBase(BaseModel):
    country_id: UUID
    code: Optional[str] = None
    name: str
    zone_id: Optional[str] = None

class StopCreate(StopBase):
    pass

class StopUpdate(BaseModel):
    country_id: Optional[UUID] = None
    code: Optional[str] = None
    name: Optional[str] = None
    zone_id: Optional[str] = None

class Stop(StopBase):
    model_config = ConfigDict(from_attributes=True)
    
    stop_id: UUID
    created_at: datetime

# Trip schemas
class TripBase(BaseModel):
    route_id: UUID
    service_id: UUID
    shape_id: Optional[UUID] = None
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None
    block_id: Optional[UUID] = None

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    route_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    shape_id: Optional[UUID] = None
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None
    block_id: Optional[UUID] = None

class Trip(TripBase):
    model_config = ConfigDict(from_attributes=True)
    
    trip_id: UUID
    created_at: datetime

# Driver schemas
class DriverBase(BaseModel):
    country_id: UUID
    name: str
    license_no: str
    home_depot_id: Optional[UUID] = None
    employment_status: str = "active"

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    country_id: Optional[UUID] = None
    name: Optional[str] = None
    license_no: Optional[str] = None
    home_depot_id: Optional[UUID] = None
    employment_status: Optional[str] = None

class Driver(DriverBase):
    model_config = ConfigDict(from_attributes=True)
    
    driver_id: UUID
    created_at: datetime
    updated_at: datetime

# Block schemas
class BlockBase(BaseModel):
    country_id: UUID
    route_id: UUID
    service_id: UUID
    start_time: time
    end_time: time

class BlockCreate(BlockBase):
    pass

class BlockUpdate(BaseModel):
    country_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class Block(BlockBase):
    model_config = ConfigDict(from_attributes=True)
    
    block_id: UUID
    created_at: datetime

# Timetable schemas
class TimetableBase(BaseModel):
    vehicle_id: UUID
    route_id: UUID
    departure_time: datetime
    arrival_time: Optional[datetime] = None
    notes: Optional[str] = None

class TimetableCreate(TimetableBase):
    pass

class TimetableUpdate(BaseModel):
    vehicle_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    notes: Optional[str] = None

class Timetable(TimetableBase):
    model_config = ConfigDict(from_attributes=True)
    
    timetable_id: UUID
    created_at: datetime
    updated_at: datetime
