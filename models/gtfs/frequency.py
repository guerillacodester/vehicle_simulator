"""
Frequency Model
===============
Represents service frequency definitions
"""

from .base import Base, Column, Time, Integer, UUID, ForeignKey, func, relationship

class Frequency(Base):
    __tablename__ = 'frequencies'
    
    frequency_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    headway_s = Column(Integer, nullable=False)
    
    # Relationships
    service = relationship("Service", back_populates="frequencies")
    route = relationship("Route", back_populates="frequencies")
