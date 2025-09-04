from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base

class RouteShape(Base):
    __tablename__ = "route_shapes"

    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.route_id"), primary_key=True)
    shape_id = Column(UUID(as_uuid=True), ForeignKey("shapes.shape_id"), primary_key=True)
    variant_code = Column(String)
    is_default = Column(Boolean, default=False)

    route = relationship("Route", back_populates="shapes")
    shape = relationship("Shape")
