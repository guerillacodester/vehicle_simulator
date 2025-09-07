"""
BlockBreak Model
=================
Represents break periods within blocks
"""

from .base import Base, Column, Time, Integer, UUID, ForeignKey, func, relationship

class BlockBreak(Base):
    __tablename__ = 'block_breaks'
    
    break_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), nullable=False)
    break_start = Column(Time, nullable=False)
    break_end = Column(Time, nullable=False)
    break_duration = Column(Integer, nullable=False)
    
    # Relationships
    block = relationship("Block", back_populates="block_breaks")
