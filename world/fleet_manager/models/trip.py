from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base

class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(UUID(as_uuid=True), primary_key=True)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.route_id"), nullable=False)
    service_id = Column(String, nullable=False)       # e.g. weekday, weekend, holiday
    trip_headsign = Column(String, nullable=True)     # destination or headsign
    direction_id = Column(Boolean, default=True)      # True=outbound, False=inbound
