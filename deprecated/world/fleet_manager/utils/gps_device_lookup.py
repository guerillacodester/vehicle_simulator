"""
GPS Device Query Helper

Simple utility for the simulator to query GPS device assignments.
No CRUD operations - devices must be managed manually in the database.
"""
from typing import Optional
from sqlalchemy.orm import Session
from world.fleet_manager.models import GPSDevice, Vehicle


def get_vehicle_gps_device_name(db_session: Session, vehicle_reg_code: str) -> Optional[str]:
    """
    Get the GPS device name assigned to a vehicle.
    
    Args:
        db_session: Database session
        vehicle_reg_code: Vehicle registration code (e.g., "ZR101")
        
    Returns:
        GPS device name (e.g., "GPS-001") or None if no device assigned
        
    Note:
        This is read-only. GPS device assignments must be managed manually in the database.
        The unique constraint ensures one device cannot be assigned to multiple vehicles.
    """
    vehicle = db_session.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg_code).first()
    
    if not vehicle or not vehicle.assigned_gps_device:
        return None
        
    return vehicle.assigned_gps_device.device_name


def get_gps_device_info(db_session: Session, vehicle_reg_code: str) -> Optional[dict]:
    """
    Get GPS device information for a vehicle.
    
    Args:
        db_session: Database session
        vehicle_reg_code: Vehicle registration code
        
    Returns:
        Dictionary with device info or None if no device assigned
    """
    vehicle = db_session.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg_code).first()
    
    if not vehicle or not vehicle.assigned_gps_device:
        return None
        
    device = vehicle.assigned_gps_device
    return {
        "device_name": device.device_name,
        "serial_number": device.serial_number,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "is_active": device.is_active
    }