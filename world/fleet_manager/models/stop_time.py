"""
StopTime model for fleet management
"""
from sqlalchemy import Column, Time, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class StopTime(Base):
    __tablename__ = 'stop_times'
    
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), primary_key=True)
    stop_id = Column(UUID(as_uuid=True), ForeignKey('stops.stop_id'), primary_key=True)
    arrival_time = Column(Time, nullable=False)
    departure_time = Column(Time, nullable=False)
    stop_sequence = Column(Integer, nullable=False, primary_key=True)
    
    # Relationships
    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")
    
    def __repr__(self):
        return f"<StopTime(trip_id='{self.trip_id}', stop_sequence={self.stop_sequence})>"
