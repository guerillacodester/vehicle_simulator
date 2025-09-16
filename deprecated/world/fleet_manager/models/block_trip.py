"""
BlockTrip model for fleet management
"""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class BlockTrip(Base):
    __tablename__ = 'block_trips'
    
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), primary_key=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), primary_key=True)
    layover_minutes = Column(Integer, default=0)
    
    # Relationships
    block = relationship("Block", back_populates="block_trips")
    trip = relationship("Trip")
    
    def __repr__(self):
        return f"<BlockTrip(block_id='{self.block_id}', trip_id='{self.trip_id}')>"
