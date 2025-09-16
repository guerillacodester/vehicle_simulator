"""
DriverAssignment model for fleet management
"""
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class DriverAssignment(Base):
    __tablename__ = 'driver_assignments'
    
    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.driver_id'), nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    driver = relationship("Driver", back_populates="assignments")
    block = relationship("Block", back_populates="driver_assignments")
    
    def __repr__(self):
        return f"<DriverAssignment(driver_id='{self.driver_id}', block_id='{self.block_id}')>"
