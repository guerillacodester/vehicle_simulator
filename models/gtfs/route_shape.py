"""
RouteShape Model
================
Links routes to their geographic shapes
"""

from .base import Base, Column, Text, Boolean, UUID, ForeignKey, relationship

class RouteShape(Base):
    __tablename__ = 'route_shapes'
    
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), primary_key=True)
    shape_id = Column(UUID(as_uuid=True), ForeignKey('shapes.shape_id'), primary_key=True)
    variant_code = Column(Text)
    is_default = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    route = relationship("Route", back_populates="route_shapes")
    shape = relationship("Shape", back_populates="route_shapes")
