"""
Block Model
===========
Represents vehicle service blocks
"""

from .base import Base, Column, Time, DateTime, UUID, ForeignKey, func, relationship

class Block(Base):
    __tablename__ = 'blocks'
    
    block_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="blocks")
    route = relationship("Route", back_populates="blocks")
    service = relationship("Service")
    trips = relationship("Trip", back_populates="block")
    vehicle_assignments = relationship("VehicleAssignment", back_populates="block")
    driver_assignments = relationship("DriverAssignment", back_populates="block")
    block_trips = relationship("BlockTrip", back_populates="block")
    block_breaks = relationship("BlockBreak", back_populates="block")
