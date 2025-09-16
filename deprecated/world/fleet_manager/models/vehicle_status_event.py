"""
VehicleStatusEvent model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, VehicleStatus
from sqlalchemy import Enum as SQLEnum
import uuid
from datetime import datetime

class VehicleStatusEvent(Base):
    __tablename__ = 'vehicle_status_events'
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    status = Column(SQLEnum(VehicleStatus), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="status_events")
    
    def __repr__(self):
        return f"<VehicleStatusEvent(vehicle_id='{self.vehicle_id}', status='{self.status}')>"
