"""
Depot Model
===========
Represents vehicle depots
"""

from .base import Base, Column, Text, Integer, DateTime, UUID, ForeignKey, func, relationship, Geometry

class Depot(Base):
    __tablename__ = 'depots'
    
    depot_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    location = Column(Geometry('POINT', srid=4326))
    capacity = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="depots")
    vehicles = relationship("Vehicle", back_populates="home_depot")
    drivers = relationship("Driver", back_populates="home_depot")
