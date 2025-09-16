"""
GPS Device Management Service

Provides utilities for managing GPS device assignments to vehicles.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from world.fleet_manager.models import GPSDevice, Vehicle


class GPSDeviceService:
    """Service class for managing GPS device operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_device(self, device_name: str, serial_number: Optional[str] = None,
                     manufacturer: Optional[str] = None, model: Optional[str] = None,
                     firmware_version: Optional[str] = None, notes: Optional[str] = None) -> GPSDevice:
        """Create a new GPS device."""
        device = GPSDevice(
            device_name=device_name,
            serial_number=serial_number,
            manufacturer=manufacturer,
            model=model,
            firmware_version=firmware_version,
            notes=notes
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device
    
    def assign_device_to_vehicle(self, device_name: str, vehicle_reg_code: str) -> bool:
        """Assign a GPS device to a vehicle by their identifiers."""
        device = self.db.query(GPSDevice).filter(GPSDevice.device_name == device_name).first()
        vehicle = self.db.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg_code).first()
        
        if not device:
            raise ValueError(f"GPS device '{device_name}' not found")
        if not vehicle:
            raise ValueError(f"Vehicle '{vehicle_reg_code}' not found")
        if not device.is_active:
            raise ValueError(f"GPS device '{device_name}' is not active")
            
        # Check if device is already assigned to another vehicle
        if device.assigned_vehicle and device.assigned_vehicle.vehicle_id != vehicle.vehicle_id:
            raise ValueError(f"GPS device '{device_name}' is already assigned to vehicle '{device.assigned_vehicle.reg_code}'")
        
        # Check if vehicle already has a different GPS device assigned
        if vehicle.assigned_gps_device and vehicle.assigned_gps_device.device_id != device.device_id:
            raise ValueError(f"Vehicle '{vehicle_reg_code}' already has GPS device '{vehicle.assigned_gps_device.device_name}' assigned")
        
        # Make the assignment
        vehicle.assigned_gps_device_id = device.device_id
        self.db.commit()
        return True
    
    def unassign_device_from_vehicle(self, vehicle_reg_code: str) -> bool:
        """Remove GPS device assignment from a vehicle."""
        vehicle = self.db.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg_code).first()
        
        if not vehicle:
            raise ValueError(f"Vehicle '{vehicle_reg_code}' not found")
        
        if not vehicle.assigned_gps_device_id:
            return False  # No device assigned
            
        vehicle.assigned_gps_device_id = None
        self.db.commit()
        return True
    
    def list_available_devices(self) -> List[GPSDevice]:
        """Get list of active GPS devices not assigned to any vehicle."""
        return self.db.query(GPSDevice).filter(
            GPSDevice.is_active == True,
            GPSDevice.assigned_vehicle == None
        ).all()
    
    def list_assigned_devices(self) -> List[GPSDevice]:
        """Get list of GPS devices currently assigned to vehicles."""
        return self.db.query(GPSDevice).filter(
            GPSDevice.is_active == True,
            GPSDevice.assigned_vehicle != None
        ).all()
    
    def get_device_by_name(self, device_name: str) -> Optional[GPSDevice]:
        """Get a GPS device by its friendly name."""
        return self.db.query(GPSDevice).filter(GPSDevice.device_name == device_name).first()
    
    def get_vehicle_gps_device(self, vehicle_reg_code: str) -> Optional[GPSDevice]:
        """Get the GPS device assigned to a specific vehicle."""
        vehicle = self.db.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg_code).first()
        return vehicle.assigned_gps_device if vehicle else None