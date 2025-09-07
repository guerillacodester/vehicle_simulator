"""
BlockBreak model for fleet management
"""
from sqlalchemy import Column, Time, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid

class BlockBreak(Base):
    __tablename__ = 'block_breaks'
    
    break_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), nullable=False)
    break_start = Column(Time, nullable=False)
    break_end = Column(Time, nullable=False)
    break_duration = Column(Integer, nullable=False)
    
    # Relationships
    block = relationship("Block", back_populates="breaks")
    
    def __repr__(self):
        return f"<BlockBreak(block_id='{self.block_id}', duration={self.break_duration})>"
