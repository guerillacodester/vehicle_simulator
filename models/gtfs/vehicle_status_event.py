"""
VehicleStatusEvent Model
========================
Represents vehicle status change events
"""

from .base import Base, Column, Text, DateTime, UUID, ForeignKey, func, relationship
from .enums import VehicleStatus

class VehicleStatusEvent(Base):
    __tablename__ = 'vehicle_status_events'
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    status = Column(VehicleStatus, nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes = Column(Text)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="status_events")
