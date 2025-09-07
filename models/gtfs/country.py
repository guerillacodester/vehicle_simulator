"""
Country Model
=============
Represents countries in the transit system
"""

from .base import Base, Column, Text, DateTime, UUID, func, relationship

class Country(Base):
    __tablename__ = 'countries'
    
    country_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    iso_code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    routes = relationship("Route", back_populates="country")
    vehicles = relationship("Vehicle", back_populates="country")
    depots = relationship("Depot", back_populates="country")
    drivers = relationship("Driver", back_populates="country")
    services = relationship("Service", back_populates="country")
    blocks = relationship("Block", back_populates="country")
    stops = relationship("Stop", back_populates="country")
