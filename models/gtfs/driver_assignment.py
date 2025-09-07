"""
DriverAssignment Model
======================
Represents driver-to-block assignments
"""

from .base import Base, Column, DateTime, UUID, ForeignKey, func, relationship

class DriverAssignment(Base):
    __tablename__ = 'driver_assignments'
    
    assignment_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.driver_id'), nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    driver = relationship("Driver", back_populates="assignments")
    block = relationship("Block", back_populates="driver_assignments")
