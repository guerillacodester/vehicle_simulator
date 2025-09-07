"""
Stop Model
==========
Represents transit stops
"""

from .base import Base, Column, Text, DateTime, UUID, ForeignKey, func, relationship, Geometry

class Stop(Base):
    __tablename__ = 'stops'
    
    stop_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    code = Column(Text)
    name = Column(Text, nullable=False)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    zone_id = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="stops")
    stop_times = relationship("StopTime", back_populates="stop")
