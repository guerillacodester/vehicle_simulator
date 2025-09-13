"""
GPS Device model for fleet management

Represents physical GPS devices that can be installed in vehicles.
Each device has a unique friendly name/identifier that is used in telemetry.
"""
from sqlalchemy import Column, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime


class GPSDevice(Base):
    __tablename__ = 'gps_devices'
    
    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name = Column(Text, nullable=False, unique=True)  # Friendly name like "GPS-001", "TRK-ZR101", etc.
    serial_number = Column(Text, nullable=True, unique=True)  # Hardware serial number
    manufacturer = Column(Text, nullable=True)  # e.g., "Quectel", "u-blox", etc.
    model = Column(Text, nullable=True)  # e.g., "EC25", "NEO-8M", etc.
    firmware_version = Column(Text, nullable=True)  # Firmware version
    is_active = Column(Boolean, nullable=False, default=True)  # Is device active/operational
    notes = Column(Text, nullable=True)  # Additional notes about the device
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    assigned_vehicle = relationship("Vehicle", back_populates="assigned_gps_device")
    
    def __repr__(self):
        vehicle_reg = self.assigned_vehicle.reg_code if self.assigned_vehicle else "unassigned"
        return f"<GPSDevice(device_name='{self.device_name}', vehicle='{vehicle_reg}', active={self.is_active})>"

    @property
    def is_assigned(self) -> bool:
        """Check if device is currently assigned to a vehicle."""
        return self.assigned_vehicle is not None and self.is_active