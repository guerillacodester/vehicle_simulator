"""
Country model for fleet management
"""
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class Country(Base):
    __tablename__ = 'countries'
    
    country_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iso_code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    routes = relationship("Route", back_populates="country")
    depots = relationship("Depot", back_populates="country")
    drivers = relationship("Driver", back_populates="country")
    stops = relationship("Stop", back_populates="country")
    vehicles = relationship("Vehicle", back_populates="country")
    services = relationship("Service", back_populates="country")
    blocks = relationship("Block", back_populates="country")
    
    def __repr__(self):
        return f"<Country(iso_code='{self.iso_code}', name='{self.name}')>"
