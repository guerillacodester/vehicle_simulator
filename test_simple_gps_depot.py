#!/usr/bin/env python3
"""
Simple GPS Connection Test for Depot

Shows GPS devices connecting to telemetry server when drivers board vehicles.
NO ENGINES - just GPS device connections!
"""
import asyncio
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.fleet_manager.database import get_session
from world.fleet_manager.utils.gps_device_lookup import get_vehicle_gps_device_name
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec, make_packet
from world.vehicle_simulator.core.states import DeviceState


async def test_simple_gps_connections():
    """Simple test: drivers board, GPS connects, send test packets."""
    print("🧪 Simple GPS Connection Test")
    print("=" * 40)
    print("📋 Test flow:")
    print("   1. Look up GPS devices assigned to vehicles")
    print("   2. Create GPS device components")
    print("   3. 'Driver boards' → GPS turns ON → connects to server")
    print("   4. Send test telemetry packets")
    print("   5. 'Driver leaves' → GPS turns OFF → disconnects")
    print()
    
    # Get database session
    db = get_session()
    gps_devices = {}
    
    try:
        # Test vehicles
        test_vehicles = ["ZR101", "ZR400"]
        
        print("🔍 Looking up GPS devices for vehicles...")
        for vehicle_reg in test_vehicles:
            gps_device_name = get_vehicle_gps_device_name(db, vehicle_reg)
            
            if not gps_device_name:
                print(f"   ❌ No GPS device assigned to {vehicle_reg}")
                # Quick assignment for testing
                await assign_test_gps_device(db, vehicle_reg)
                gps_device_name = get_vehicle_gps_device_name(db, vehicle_reg)
            
            if gps_device_name:
                print(f"   📡 {vehicle_reg} → {gps_device_name}")
                
                # Create GPS device component
                transmitter = WebSocketTransmitter(
                    server_url="ws://localhost:5000",
                    token="depot_test",
                    device_id=gps_device_name,
                    codec=PacketCodec()
                )
                
                gps_device = GPSDevice(gps_device_name, transmitter)
                
                gps_devices[vehicle_reg] = {
                    'device': gps_device,
                    'device_name': gps_device_name,
                    'driver_name': f"Driver of {vehicle_reg}"
                }
        
        if not gps_devices:
            print("❌ No GPS devices available for testing")
            return False
            
        print(f"\n✅ Created {len(gps_devices)} GPS device components")
        
        # Simulate drivers boarding (GPS devices turn ON)
        print(f"\n🚌 Simulating Driver Boarding...")
        for vehicle_reg, components in gps_devices.items():
            device = components['device']
            device_name = components['device_name']
            driver_name = components['driver_name']
            
            print(f"\n👨‍💼 {driver_name} boarding {vehicle_reg}")
            print(f"   📡 GPS Device: {device_name}")
            print(f"   Initial state: {device.current_state}")
            
            # Driver boards → GPS turns ON
            success = await device.start()
            
            if success:
                print(f"   ✅ GPS device turned ON: {device.current_state}")
                
                if device.current_state == DeviceState.ON:
                    print(f"   🎉 {device_name} connected to telemetry server!")
                else:
                    print(f"   ⚠️  GPS device state: {device.current_state}")
            else:
                print(f"   ❌ Failed to turn on GPS device")
        
        # Send test packets
        print(f"\n📡 Sending test telemetry packets...")
        for vehicle_reg, components in gps_devices.items():
            device = components['device']
            device_name = components['device_name']
            
            if device.current_state == DeviceState.ON:
                # Create test packet
                test_packet = make_packet(
                    device_id=device_name,
                    lat=13.1 + (hash(vehicle_reg) % 100) / 1000.0,  # Slight variation
                    lon=-59.6 + (hash(vehicle_reg) % 100) / 1000.0,
                    speed=35.0,
                    heading=90.0,
                    route="TEST",
                    vehicle_reg=vehicle_reg,
                    driver_id=f"DRV_{vehicle_reg[-3:]}",
                    driver_name={"first": "Test", "last": f"Driver{vehicle_reg[-3:]}"}
                )
                
                try:
                    # Send packet directly via transmitter
                    await device.transmitter.send(test_packet)
                    print(f"   📤 Sent test packet from {device_name}")
                except Exception as e:
                    print(f"   ❌ Failed to send packet from {device_name}: {e}")
        
        # Let GPS devices run for a few seconds
        print(f"\n⏱️  GPS devices active for 5 seconds...")
        await asyncio.sleep(5)
        
        # Simulate drivers leaving (GPS devices turn OFF)
        print(f"\n🚪 Simulating Driver Departure...")
        for vehicle_reg, components in gps_devices.items():
            device = components['device']
            device_name = components['device_name']
            driver_name = components['driver_name']
            
            print(f"\n👨‍💼 {driver_name} leaving {vehicle_reg}")
            
            # Driver leaves → GPS turns OFF
            success = await device.stop()
            
            if success:
                print(f"   ✅ GPS device turned OFF: {device.current_state}")
                
                if device.current_state == DeviceState.OFF:
                    print(f"   🔌 {device_name} disconnected from server")
                else:
                    print(f"   ⚠️  GPS device state: {device.current_state}")
            else:
                print(f"   ❌ Failed to turn off GPS device")
        
        print(f"\n🎉 GPS connection test completed!")
        print(f"📋 Check telemetry server logs to see:")
        print(f"   • GPS device connections when drivers boarded")
        print(f"   • Test telemetry packets received")  
        print(f"   • GPS device disconnections when drivers left")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        for components in gps_devices.values():
            try:
                await components['device'].stop()
            except:
                pass
        db.close()


async def assign_test_gps_device(db, vehicle_reg: str):
    """Quick GPS device assignment for testing."""
    try:
        from world.fleet_manager.models import Vehicle, GPSDevice as DBGPSDevice
        
        vehicle = db.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg).first()
        available_device = db.query(DBGPSDevice).filter(
            DBGPSDevice.is_active == True,
            DBGPSDevice.assigned_vehicle == None
        ).first()
        
        if vehicle and available_device:
            vehicle.assigned_gps_device_id = available_device.device_id
            db.commit()
            print(f"   📡 Auto-assigned {available_device.device_name} to {vehicle_reg}")
            
    except Exception as e:
        print(f"   ⚠️  Could not auto-assign GPS device: {e}")


if __name__ == "__main__":
    success = asyncio.run(test_simple_gps_connections())
    print(f"\n{'🎉 Test completed successfully!' if success else '❌ Test failed'}")
    sys.exit(0 if success else 1)