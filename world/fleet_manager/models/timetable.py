"""
Timetable model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class Timetable(Base):
    __tablename__ = 'timetables'
    
    timetable_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="timetables")
    route = relationship("Route", back_populates="timetables")
    
    def __repr__(self):
        return f"<Timetable(vehicle_id='{self.vehicle_id}', departure_time='{self.departure_time}')>"
