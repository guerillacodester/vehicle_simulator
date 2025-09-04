from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base

class Route(Base):
    __tablename__ = "routes"

    route_id = Column(UUID(as_uuid=True), primary_key=True)
    short_name = Column(String, nullable=False)
    long_name = Column(String)
    parishes = Column(String)
    is_active = Column(Boolean, default=True)

    shapes = relationship("RouteShape", back_populates="route")
