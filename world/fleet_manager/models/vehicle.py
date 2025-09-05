from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(UUID(as_uuid=True), primary_key=True)
    label = Column(String, nullable=False)       # registration number or display label
    capacity = Column(Integer, nullable=True)    # passenger capacity (optional)
    active = Column(Boolean, default=True)       # whether the vehicle is in service
