"""
BlockTrip Model
===============
Represents trip assignments within blocks
"""

from .base import Base, Column, Integer, UUID, ForeignKey, relationship

class BlockTrip(Base):
    __tablename__ = 'block_trips'
    
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), primary_key=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), primary_key=True)
    layover_minutes = Column(Integer, default=0)
    
    # Relationships
    block = relationship("Block", back_populates="block_trips")
    trip = relationship("Trip", back_populates="block_trips")
