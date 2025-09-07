"""
RouteShape model for fleet management
"""
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class RouteShape(Base):
    __tablename__ = "route_shapes"

    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.route_id"), primary_key=True)
    shape_id = Column(UUID(as_uuid=True), ForeignKey("shapes.shape_id"), primary_key=True)
    variant_code = Column(String)
    is_default = Column(Boolean, default=False)

    route = relationship("Route", back_populates="route_shapes")
    shape = relationship("Shape", back_populates="route_shapes")

    def __repr__(self):
        return f"<RouteShape(route_id='{self.route_id}', shape_id='{self.shape_id}')>"
