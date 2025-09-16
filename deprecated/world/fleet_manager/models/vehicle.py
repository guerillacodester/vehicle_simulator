"""
Vehicle model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, VehicleStatus
from sqlalchemy import Enum as SQLEnum
import uuid
from datetime import datetime

class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    vehicle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    reg_code = Column(Text, nullable=False)
    home_depot_id = Column(UUID(as_uuid=True), ForeignKey('depots.depot_id'))
    preferred_route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'))
    assigned_driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.driver_id'), nullable=True)  # Direct driver assignment
    assigned_gps_device_id = Column(UUID(as_uuid=True), ForeignKey('gps_devices.device_id'), nullable=True)  # Assigned GPS device
    status = Column(SQLEnum(VehicleStatus), nullable=False, default=VehicleStatus.available)
    capacity = Column(Integer, nullable=True, default=11)  # Passenger capacity (ZR van default)
    profile_id = Column(Text)
    notes = Column(Text)
    
    # Performance characteristics
    max_speed_kmh = Column(Float, nullable=False, default=25.0)  # Maximum speed in km/h
    acceleration_mps2 = Column(Float, nullable=False, default=1.2)  # Acceleration in m/s²
    braking_mps2 = Column(Float, nullable=False, default=1.8)  # Braking deceleration in m/s²
    eco_mode = Column(Boolean, nullable=False, default=False)  # Eco-friendly driving mode
    performance_profile = Column(Text, nullable=True)  # "standard", "eco", "performance", "express"
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="vehicles")
    home_depot = relationship("Depot", back_populates="vehicles")
    preferred_route = relationship("Route", back_populates="vehicles")
    assigned_driver = relationship("Driver", back_populates="assigned_vehicles", foreign_keys=[assigned_driver_id])
    assigned_gps_device = relationship("GPSDevice", back_populates="assigned_vehicle", foreign_keys=[assigned_gps_device_id])
    timetables = relationship("Timetable", back_populates="vehicle")
    assignments = relationship("VehicleAssignment", back_populates="vehicle")
    status_events = relationship("VehicleStatusEvent", back_populates="vehicle")
    
    def __repr__(self):
        return f"<Vehicle(reg_code='{self.reg_code}', status='{self.status}')>"
