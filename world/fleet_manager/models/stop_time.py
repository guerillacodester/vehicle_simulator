from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base

class StopTime(Base):
    __tablename__ = "stop_times"

    stop_time_id = Column(UUID(as_uuid=True), primary_key=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.trip_id"), nullable=False)
    stop_id = Column(String, nullable=False)          # placeholder until stops table exists
    arrival_time = Column(String, nullable=False)     # format: HH:MM:SS
    departure_time = Column(String, nullable=False)   # format: HH:MM:SS
    stop_sequence = Column(Integer, nullable=False)   # order in trip
