#!/usr/bin/env python3
"""
Test GPS Device Assignment Constraints

Tests that the database properly prevents assigning the same GPS device to multiple vehicles.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from world.fleet_manager.database import get_session
from world.fleet_manager.models import Vehicle, GPSDevice


def test_unique_gps_assignment():
    """Test that GPS devices can only be assigned to one vehicle at a time."""
    db = get_session()
    
    try:
        print("🧪 Testing GPS Device Assignment Constraints")
        print("=" * 50)
        
        # Get first few vehicles and GPS devices
        vehicles = db.query(Vehicle).limit(3).all()
        devices = db.query(GPSDevice).limit(2).all()
        
        if len(vehicles) < 2:
            print("❌ Need at least 2 vehicles in database for test")
            return False
            
        if len(devices) < 1:
            print("❌ Need at least 1 GPS device in database for test")
            return False
        
        vehicle1 = vehicles[0]
        vehicle2 = vehicles[1]
        device = devices[0]
        
        print(f"📍 Vehicle 1: {vehicle1.reg_code}")
        print(f"📍 Vehicle 2: {vehicle2.reg_code}")
        print(f"📡 GPS Device: {device.device_name}")
        print()
        
        # Test 1: Assign GPS device to first vehicle
        print("Test 1: Assigning GPS device to first vehicle...")
        vehicle1.assigned_gps_device_id = device.device_id
        db.commit()
        print(f"✅ Successfully assigned {device.device_name} to {vehicle1.reg_code}")
        
        # Test 2: Try to assign the same GPS device to second vehicle (should fail)
        print("\nTest 2: Trying to assign same GPS device to second vehicle...")
        try:
            vehicle2.assigned_gps_device_id = device.device_id
            db.commit()
            print("❌ ERROR: Should have failed due to unique constraint!")
            return False
        except Exception as e:
            print(f"✅ Correctly prevented duplicate assignment: {str(e)[:100]}...")
            db.rollback()
        
        # Test 3: Unassign from first vehicle, then assign to second vehicle
        print("\nTest 3: Unassigning from first vehicle, then assigning to second...")
        vehicle1.assigned_gps_device_id = None
        db.commit()
        print(f"✅ Unassigned GPS device from {vehicle1.reg_code}")
        
        vehicle2.assigned_gps_device_id = device.device_id
        db.commit()
        print(f"✅ Successfully assigned {device.device_name} to {vehicle2.reg_code}")
        
        # Cleanup
        vehicle2.assigned_gps_device_id = None
        db.commit()
        
        print("\n🎉 All GPS device assignment constraint tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_unique_gps_assignment()
    sys.exit(0 if success else 1)