"""
Driver Model
============
Represents drivers in the system
"""

from .base import Base, Column, Text, DateTime, UUID, ForeignKey, func, relationship

class Driver(Base):
    __tablename__ = 'drivers'
    
    driver_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    license_no = Column(Text, nullable=False)
    home_depot_id = Column(UUID(as_uuid=True), ForeignKey('depots.depot_id'))
    employment_status = Column(Text, nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="drivers")
    home_depot = relationship("Depot", back_populates="drivers")
    assignments = relationship("DriverAssignment", back_populates="driver")
