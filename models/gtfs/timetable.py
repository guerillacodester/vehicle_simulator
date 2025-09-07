"""
Timetable Model
===============
Represents schedule timetable data
"""

from .base import Base, Column, Text, DateTime, UUID, ForeignKey, func, relationship

class Timetable(Base):
    __tablename__ = 'timetables'
    
    timetable_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="timetables")
    route = relationship("Route", back_populates="timetables")
    service = relationship("Service", back_populates="timetables")
