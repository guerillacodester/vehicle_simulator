"""
Service Model
=============
Represents service calendars (weekday/weekend schedules)
"""

from .base import Base, Column, Text, Boolean, Date, DateTime, UUID, ForeignKey, func, relationship

class Service(Base):
    __tablename__ = 'services'
    
    service_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    mon = Column(Boolean, nullable=False, default=False)
    tue = Column(Boolean, nullable=False, default=False)
    wed = Column(Boolean, nullable=False, default=False)
    thu = Column(Boolean, nullable=False, default=False)
    fri = Column(Boolean, nullable=False, default=False)
    sat = Column(Boolean, nullable=False, default=False)
    sun = Column(Boolean, nullable=False, default=False)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="services")
    trips = relationship("Trip", back_populates="service")
    frequencies = relationship("Frequency", back_populates="service")
    timetables = relationship("Timetable", back_populates="service")
