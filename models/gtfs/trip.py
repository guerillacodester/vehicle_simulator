"""
Trip Model
==========
Represents individual trip instances
"""

from sqlalchemy import SmallInteger
from .base import Base, Column, Text, DateTime, UUID, ForeignKey, func, relationship

class Trip(Base):
    __tablename__ = 'trips'
    
    trip_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    shape_id = Column(UUID(as_uuid=True), ForeignKey('shapes.shape_id'))
    trip_headsign = Column(Text)
    direction_id = Column(SmallInteger)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    route = relationship("Route", back_populates="trips")
    service = relationship("Service", back_populates="trips")
    shape = relationship("Shape", back_populates="trips")
    block = relationship("Block", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip")
    block_trips = relationship("BlockTrip", back_populates="trip")
