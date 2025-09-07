"""
Route model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime, date

class Route(Base):
    __tablename__ = 'routes'
    
    route_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    short_name = Column(Text, nullable=False)
    long_name = Column(Text)
    parishes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    valid_from = Column(Date, default=date.today)
    valid_to = Column(Date)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="routes")
    trips = relationship("Trip", back_populates="route")
    blocks = relationship("Block", back_populates="route")
    frequencies = relationship("Frequency", back_populates="route")
    timetables = relationship("Timetable", back_populates="route")
    vehicles = relationship("Vehicle", back_populates="preferred_route")
    route_shapes = relationship("RouteShape", back_populates="route")
    
    def __repr__(self):
        return f"<Route(short_name='{self.short_name}', long_name='{self.long_name}')>"
