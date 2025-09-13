"""
GPS Device Seeder

Seeds the database with sample GPS devices for testing and development.
"""
from world.fleet_manager.database import get_session
from world.fleet_manager.models import GPSDevice


def seed_gps_devices():
    """Seed the database with sample GPS devices."""
    db = get_session()
    
    try:
        # Check if devices already exist
        existing_count = db.query(GPSDevice).count()
        if existing_count > 0:
            print(f"GPS devices already exist ({existing_count} found). Skipping seeding.")
            return
        
        # Sample GPS devices
        devices = [
            {
                "device_name": "GPS-001",
                "serial_number": "QTL001234567",
                "manufacturer": "Quectel",
                "model": "EC25-AF",
                "firmware_version": "EC25AFAR06A08M4G",
                "notes": "Primary GPS device for Route 1 vehicles"
            },
            {
                "device_name": "GPS-002", 
                "serial_number": "QTL002345678",
                "manufacturer": "Quectel",
                "model": "EC25-AF",
                "firmware_version": "EC25AFAR06A08M4G",
                "notes": "Primary GPS device for Route 1A vehicles"
            },
            {
                "device_name": "GPS-003",
                "serial_number": "QTL003456789",
                "manufacturer": "Quectel", 
                "model": "EC25-AF",
                "firmware_version": "EC25AFAR06A08M4G",
                "notes": "Primary GPS device for Route 1B vehicles"
            },
            {
                "device_name": "TRK-ZR101",
                "serial_number": "UBX101234567",
                "manufacturer": "u-blox",
                "model": "NEO-8M",
                "firmware_version": "ROM 3.01",
                "notes": "High-precision tracker for ZR101"
            },
            {
                "device_name": "TRK-ZR102", 
                "serial_number": "UBX102345678",
                "manufacturer": "u-blox",
                "model": "NEO-8M",
                "firmware_version": "ROM 3.01",
                "notes": "High-precision tracker for ZR102"
            },
            {
                "device_name": "TRK-ZR103",
                "serial_number": "UBX103456789",
                "manufacturer": "u-blox",
                "model": "NEO-8M", 
                "firmware_version": "ROM 3.01",
                "notes": "High-precision tracker for ZR103"
            },
            {
                "device_name": "MOB-001",
                "serial_number": "SIM001234567",
                "manufacturer": "SIMCom",
                "model": "SIM7600G-H",
                "firmware_version": "SIM7600M22-A",
                "notes": "Mobile tracker with 4G connectivity"
            },
            {
                "device_name": "MOB-002",
                "serial_number": "SIM002345678", 
                "manufacturer": "SIMCom",
                "model": "SIM7600G-H",
                "firmware_version": "SIM7600M22-A",
                "notes": "Mobile tracker with 4G connectivity"
            },
            {
                "device_name": "ECO-001",
                "serial_number": "ECO001234567",
                "manufacturer": "Generic",
                "model": "GT06N",
                "firmware_version": "V1.2.3",
                "notes": "Economy GPS tracker - basic functionality"
            },
            {
                "device_name": "ECO-002",
                "serial_number": "ECO002345678",
                "manufacturer": "Generic", 
                "model": "GT06N",
                "firmware_version": "V1.2.3",
                "notes": "Economy GPS tracker - basic functionality"
            },
            {
                "device_name": "DEV-SIM001",
                "serial_number": None,
                "manufacturer": "Simulator",
                "model": "Virtual GPS",
                "firmware_version": "SIM-1.0",
                "notes": "Development/testing GPS device for simulator"
            },
            {
                "device_name": "DEV-SIM002",
                "serial_number": None,
                "manufacturer": "Simulator",
                "model": "Virtual GPS", 
                "firmware_version": "SIM-1.0",
                "notes": "Development/testing GPS device for simulator"
            }
        ]
        
        # Create and add devices
        created_devices = []
        for device_data in devices:
            device = GPSDevice(**device_data)
            db.add(device)
            created_devices.append(device)
        
        # Commit all devices
        db.commit()
        
        print(f"Successfully seeded {len(created_devices)} GPS devices:")
        for device in created_devices:
            print(f"  - {device.device_name} ({device.manufacturer} {device.model})")
            
    except Exception as e:
        db.rollback()
        print(f"Error seeding GPS devices: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Seeding GPS devices...")
    seed_gps_devices()
    print("✅ GPS device seeding complete!")