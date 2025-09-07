"""
Service model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class Service(Base):
    __tablename__ = 'services'
    
    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    mon = Column(Boolean, nullable=False, default=False)
    tue = Column(Boolean, nullable=False, default=False)
    wed = Column(Boolean, nullable=False, default=False)
    thu = Column(Boolean, nullable=False, default=False)
    fri = Column(Boolean, nullable=False, default=False)
    sat = Column(Boolean, nullable=False, default=False)
    sun = Column(Boolean, nullable=False, default=False)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="services")
    trips = relationship("Trip", back_populates="service")
    blocks = relationship("Block", back_populates="service")
    frequencies = relationship("Frequency", back_populates="service")
    
    def __repr__(self):
        return f"<Service(name='{self.name}', date_start='{self.date_start}')>"
