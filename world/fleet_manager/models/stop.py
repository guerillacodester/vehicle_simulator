"""
Stop model for fleet management
"""
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_X, ST_Y
from .base import Base
import uuid
from datetime import datetime

class Stop(Base):
    __tablename__ = 'stops'
    
    stop_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    code = Column(Text)
    name = Column(Text, nullable=False)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    zone_id = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="stops")
    stop_times = relationship("StopTime", back_populates="stop")
    
    @property
    def latitude(self):
        """Extract latitude from PostGIS geometry"""
        if self.location:
            from sqlalchemy import func
            # This would need to be computed in a query, for now return None
            return None
    
    @property 
    def longitude(self):
        """Extract longitude from PostGIS geometry"""
        if self.location:
            from sqlalchemy import func
            # This would need to be computed in a query, for now return None
            return None
    
    def __repr__(self):
        return f"<Stop(name='{self.name}', code='{self.code}')>"
