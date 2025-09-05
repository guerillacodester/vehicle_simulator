from sqlalchemy import Column, Text, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from .base import Base


class Depot(Base):
    __tablename__ = "depots"

    depot_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.country_id", ondelete="CASCADE"),
        nullable=False
    )
    name = Column(Text, nullable=False)
    location = Column(Geometry("POINT", srid=4326))   # GIS geometry point
    capacity = Column(Integer)                        # must be >=0 if not null
    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<Depot(id={self.depot_id}, name={self.name}, capacity={self.capacity})>"
