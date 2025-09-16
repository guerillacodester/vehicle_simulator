"""
Search result schemas with human-readable information for Fleet Management API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VehicleSearchResult(BaseModel):
    """Vehicle search result with human-readable information (no UUIDs)"""
    registration: str
    status: str
    capacity: Optional[int] = None
    
    # Driver information
    assigned_driver_name: Optional[str] = None
    assigned_driver_license: Optional[str] = None
    
    # Route information
    assigned_route_code: Optional[str] = None
    assigned_route_name: Optional[str] = None
    
    # Depot information
    home_depot_name: Optional[str] = None
    
    # Additional vehicle details
    profile_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class DriverSearchResult(BaseModel):
    """Driver search result with human-readable information (no UUIDs)"""
    name: str
    license_number: str
    employment_status: str
    
    # Vehicle information
    assigned_vehicles: Optional[list[str]] = []  # List of registration codes
    
    # Depot information
    home_depot_name: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class VehicleDriverPair(BaseModel):
    """Combined vehicle and driver information for relationship queries"""
    # Vehicle info
    registration: str
    vehicle_status: str
    vehicle_capacity: Optional[int] = None
    
    # Driver info
    driver_name: str
    driver_license: str
    driver_employment_status: str
    
    # Route info
    route_code: Optional[str] = None
    route_name: Optional[str] = None
    
    # Depot info
    depot_name: Optional[str] = None
    
    assignment_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True