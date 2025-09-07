"""
StopTime Model
==============
Represents stop timing information for trips
"""

from .base import Base, Column, Time, Integer, UUID, ForeignKey, relationship

class StopTime(Base):
    __tablename__ = 'stop_times'
    
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), primary_key=True)
    stop_id = Column(UUID(as_uuid=True), ForeignKey('stops.stop_id'), primary_key=True)
    arrival_time = Column(Time, nullable=False)
    departure_time = Column(Time, nullable=False)
    stop_sequence = Column(Integer, primary_key=True)
    
    # Relationships
    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")
