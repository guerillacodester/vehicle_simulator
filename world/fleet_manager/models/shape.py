from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from ..database import Base

class Shape(Base):
    __tablename__ = "shapes"

    shape_id = Column(UUID(as_uuid=True), primary_key=True)
    geom = Column(Geometry("LINESTRING", srid=4326))
