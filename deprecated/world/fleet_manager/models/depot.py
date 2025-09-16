"""
Depot model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from .base import Base
import uuid
from datetime import datetime

class Depot(Base):
    __tablename__ = 'depots'
    
    depot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    location = Column(Geometry('POINT', srid=4326))
    capacity = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="depots")
    vehicles = relationship("Vehicle", back_populates="home_depot")
    drivers = relationship("Driver", back_populates="home_depot")
    
    def __repr__(self):
        return f"<Depot(name='{self.name}', capacity={self.capacity})>"
