"""
Shape Model
===========
Represents geographic shapes for routes
"""

from .base import Base, Column, UUID, func, relationship, Geometry

class Shape(Base):
    __tablename__ = 'shapes'
    
    shape_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    geom = Column(Geometry('LINESTRING', srid=4326), nullable=False)
    
    # Relationships
    route_shapes = relationship("RouteShape", back_populates="shape")
    trips = relationship("Trip", back_populates="shape")
