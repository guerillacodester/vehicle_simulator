"""
Driver model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class Driver(Base):
    __tablename__ = 'drivers'
    
    driver_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    license_no = Column(Text, nullable=False)
    home_depot_id = Column(UUID(as_uuid=True), ForeignKey('depots.depot_id'))
    employment_status = Column(Text, nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="drivers")
    home_depot = relationship("Depot", back_populates="drivers")
    assigned_vehicles = relationship("Vehicle", back_populates="assigned_driver", foreign_keys="Vehicle.assigned_driver_id")
    assignments = relationship("DriverAssignment", back_populates="driver")
    
    def __repr__(self):
        return f"<Driver(name='{self.name}', license_no='{self.license_no}')>"
