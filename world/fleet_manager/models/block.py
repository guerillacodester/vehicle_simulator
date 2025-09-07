"""
Block model for fleet management
"""
from sqlalchemy import Column, Time, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class Block(Base):
    __tablename__ = 'blocks'
    
    block_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="blocks")
    route = relationship("Route", back_populates="blocks")
    service = relationship("Service", back_populates="blocks")
    trips = relationship("Trip", back_populates="block")
    breaks = relationship("BlockBreak", back_populates="block")
    block_trips = relationship("BlockTrip", back_populates="block")
    driver_assignments = relationship("DriverAssignment", back_populates="block")
    vehicle_assignments = relationship("VehicleAssignment", back_populates="block")
    
    def __repr__(self):
        return f"<Block(block_id='{self.block_id}', start_time='{self.start_time}')>"
