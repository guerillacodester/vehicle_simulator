"""
Frequency model for fleet management
"""
from sqlalchemy import Column, Time, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid

class Frequency(Base):
    __tablename__ = 'frequencies'
    
    frequency_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    headway_s = Column(Integer, nullable=False)
    
    # Relationships
    service = relationship("Service", back_populates="frequencies")
    route = relationship("Route", back_populates="frequencies")
    
    def __repr__(self):
        return f"<Frequency(route_id='{self.route_id}', headway_s={self.headway_s})>"
