"""
VehicleAssignment Model
=======================
Represents vehicle-to-block assignments
"""

from .base import Base, Column, DateTime, UUID, ForeignKey, func, relationship

class VehicleAssignment(Base):
    __tablename__ = 'vehicle_assignments'
    
    assignment_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="assignments")
    block = relationship("Block", back_populates="vehicle_assignments")
