"""
Shape model for fleet management
"""
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from .base import Base
import uuid

class Shape(Base):
    __tablename__ = 'shapes'
    
    shape_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    geom = Column(Geometry('LINESTRING', srid=4326), nullable=False)
    
    # Relationships
    route_shapes = relationship("RouteShape", back_populates="shape")
    trips = relationship("Trip", back_populates="shape")
    
    def __repr__(self):
        return f"<Shape(shape_id='{self.shape_id}')>"
