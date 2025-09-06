# world/fleet_manager/models/timetable.py

from sqlalchemy import Column, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Timetable(Base):
    __tablename__ = "timetables"

    timetable_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )

    route_id = Column(
        UUID(as_uuid=True),
        ForeignKey("routes.route_id", ondelete="CASCADE"),
        nullable=False,
    )

    departure_time = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    arrival_time = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<Timetable(vehicle_id={self.vehicle_id}, route_id={self.route_id}, "
            f"departure={self.departure_time}, arrival={self.arrival_time})>"
        )
