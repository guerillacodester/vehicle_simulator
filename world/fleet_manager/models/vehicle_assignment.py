"""
VehicleAssignment model for fleet management
"""
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class VehicleAssignment(Base):
    __tablename__ = 'vehicle_assignments'
    
    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="assignments")
    block = relationship("Block", back_populates="vehicle_assignments")
    
    def __repr__(self):
        return f"<VehicleAssignment(vehicle_id='{self.vehicle_id}', block_id='{self.block_id}')>"
