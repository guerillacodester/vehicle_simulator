"""
Vehicle Model
=============
Represents vehicles in the fleet
"""

from .base import Base, Column, Text, DateTime, UUID, ForeignKey, func, relationship
from .enums import VehicleStatus

class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    vehicle_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    reg_code = Column(Text, nullable=False)
    home_depot_id = Column(UUID(as_uuid=True), ForeignKey('depots.depot_id'))
    preferred_route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'))
    status = Column(VehicleStatus, nullable=False, default='available')
    profile_id = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="vehicles")
    home_depot = relationship("Depot", back_populates="vehicles")
    preferred_route = relationship("Route")
    assignments = relationship("VehicleAssignment", back_populates="vehicle")
    status_events = relationship("VehicleStatusEvent", back_populates="vehicle")
    timetables = relationship("Timetable", back_populates="vehicle")
