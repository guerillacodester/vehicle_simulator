"""
Trip model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, SmallInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class Trip(Base):
    __tablename__ = 'trips'
    
    trip_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    shape_id = Column(UUID(as_uuid=True), ForeignKey('shapes.shape_id'))
    trip_headsign = Column(Text)
    direction_id = Column(SmallInteger)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    route = relationship("Route", back_populates="trips")
    service = relationship("Service", back_populates="trips")
    shape = relationship("Shape", back_populates="trips")
    block = relationship("Block", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip")
    
    def __repr__(self):
        return f"<Trip(trip_headsign='{self.trip_headsign}', direction_id={self.direction_id})>"
