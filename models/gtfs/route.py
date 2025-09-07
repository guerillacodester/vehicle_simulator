"""
Route Model
===========
Represents transit routes
"""

from .base import Base, Column, Text, Boolean, Date, DateTime, UUID, ForeignKey, func, relationship

class Route(Base):
    __tablename__ = 'routes'
    
    route_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    short_name = Column(Text, nullable=False)
    long_name = Column(Text)
    parishes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    valid_from = Column(Date, server_default=func.current_date())
    valid_to = Column(Date)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="routes")
    trips = relationship("Trip", back_populates="route")
    route_shapes = relationship("RouteShape", back_populates="route")
    blocks = relationship("Block", back_populates="route")
    frequencies = relationship("Frequency", back_populates="route")
    timetables = relationship("Timetable", back_populates="route")
