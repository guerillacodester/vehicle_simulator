#!/usr/bin/env python3
"""
GPS Device Seeder

Seeds the database with sample GPS devices for testing and development.
Run this script to populate the gps_devices table with realistic test data.
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from world.fleet_manager.database import get_session
from world.fleet_manager.models import GPSDevice, Vehicle


def seed_gps_devices():
    """Seed GPS devices into the database."""
    db = get_session()
    
    # Sample GPS devices with realistic specifications
    devices = [
        {
            "device_name": "GPS-001",
            "serial_number": "QC8150-001",
            "manufacturer": "Quectel",
            "model": "EC25-E",
            "firmware_version": "EC25EFAR06A02E4G",
            "notes": "Primary fleet GPS device - high accuracy"
        },
        {
            "device_name": "GPS-002", 
            "serial_number": "QC8150-002",
            "manufacturer": "Quectel",
            "model": "EC25-E",
            "firmware_version": "EC25EFAR06A02E4G",
            "notes": "Secondary fleet GPS device"
        },
        {
            "device_name": "TRK-ZR101",
            "serial_number": "UB7020-101",
            "manufacturer": "u-blox",
            "model": "NEO-8M",
            "firmware_version": "ROM CORE 3.01",
            "notes": "Dedicated tracker for ZR101 vehicle"
        },
        {
            "device_name": "TRK-ZR102",
            "serial_number": "UB7020-102", 
            "manufacturer": "u-blox",
            "model": "NEO-8M",
            "firmware_version": "ROM CORE 3.01",
            "notes": "Dedicated tracker for ZR102 vehicle"
        },
        {
            "device_name": "TRK-ZR103",
            "serial_number": "UB7020-103",
            "manufacturer": "u-blox", 
            "model": "NEO-8M",
            "firmware_version": "ROM CORE 3.01",
            "notes": "Dedicated tracker for ZR103 vehicle"
        },
        {
            "device_name": "GPS-BACKUP-01",
            "serial_number": "ST9540-B01",
            "manufacturer": "STMicroelectronics",
            "model": "Teseo-LIV3F",
            "firmware_version": "LIV3F_2.0.6",
            "notes": "Backup GPS device for emergencies"
        },
        {
            "device_name": "GPS-MOBILE-01",
            "serial_number": "SIM7600-M01",
            "manufacturer": "SIMCom",
            "model": "SIM7600E-H",
            "firmware_version": "SIM7600E22_V1.0",
            "notes": "Mobile GPS unit for temporary assignments"
        },
        {
            "device_name": "GPS-MOBILE-02",
            "serial_number": "SIM7600-M02",
            "manufacturer": "SIMCom", 
            "model": "SIM7600E-H",
            "firmware_version": "SIM7600E22_V1.0",
            "notes": "Mobile GPS unit for temporary assignments"
        },
        {
            "device_name": "GPS-TEST-DEV",
            "serial_number": "TEST-001",
            "manufacturer": "Generic",
            "model": "TestGPS-V1",
            "firmware_version": "1.0.0-beta",
            "notes": "Development and testing GPS device"
        },
        {
            "device_name": "GPS-PREMIUM-01",
            "serial_number": "GA6T-PRE01",
            "manufacturer": "GlobalTop",
            "model": "PA6H",
            "firmware_version": "AXN_5.1.6_3333",
            "notes": "High-precision GPS for route optimization testing"
        }
    ]
    
    try:
        print("🔧 Seeding GPS devices...")
        created_count = 0
        
        for device_data in devices:
            # Check if device already exists
            existing = db.query(GPSDevice).filter(
                GPSDevice.device_name == device_data["device_name"]
            ).first()
            
            if existing:
                print(f"⚠️  Device '{device_data['device_name']}' already exists, skipping")
                continue
                
            # Create new device
            device = GPSDevice(**device_data)
            db.add(device)
            created_count += 1
            print(f"✅ Created GPS device: {device_data['device_name']} ({device_data['manufacturer']} {device_data['model']})")
        
        # Commit all changes
        db.commit()
        
        print(f"\n🎉 Successfully seeded {created_count} GPS devices!")
        
        # Show summary
        total_devices = db.query(GPSDevice).count()
        active_devices = db.query(GPSDevice).filter(GPSDevice.is_active == True).count()
        assigned_devices = db.query(GPSDevice).filter(GPSDevice.assigned_vehicle != None).count()
        
        print(f"📊 Database summary:")
        print(f"   Total GPS devices: {total_devices}")
        print(f"   Active devices: {active_devices}")
        print(f"   Assigned to vehicles: {assigned_devices}")
        print(f"   Available for assignment: {active_devices - assigned_devices}")
        
    except Exception as e:
        print(f"❌ Error seeding GPS devices: {e}")
        db.rollback()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    print("🚀 GPS Device Seeder")
    print("=" * 40)
    exit_code = seed_gps_devices()
    sys.exit(exit_code)