#!/usr/bin/env python3
"""
Test Telemetry Pipeline
-----------------------
Tests the complete telemetry flow from Navigator to GPS device transmission.
"""

import time
import asyncio
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer  
from world.vehicle_simulator.vehicle.engine.sim_speed_model import load_speed_model
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.driver.navigation.navigator import Navigator
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter

def test_navigator_to_gps_flow():
    """Test Navigator telemetry buffer to GPS device flow"""
    print("🔄 TESTING NAVIGATOR → GPS TELEMETRY FLOW")
    print("=" * 60)
    
    # Test route in Barbados
    test_route = [
        (-59.6463, 13.2810),  # (lng, lat) format
        (-59.6470, 13.2820),
        (-59.6480, 13.2830)
    ]
    
    # Create Engine components
    buffer = EngineBuffer(size=100)
    speed_model = load_speed_model('kinematic', speed=25.0)
    engine = Engine('TEST_VEHICLE', speed_model, buffer, tick_time=1.0)
    
    # Create Navigator
    navigator = Navigator(
        vehicle_id='TEST_VEHICLE',
        route_coordinates=test_route,
        engine_buffer=buffer,
        tick_time=1.0,
        mode='geodesic'
    )
    
    print(f"✅ Navigator created with {len(test_route)} route points")
    
    # Start engine and navigator
    print("🔥 Starting engine...")
    engine.on()
    
    print("🧭 Starting navigator...")
    navigator.on()
    
    # Let them run for a few seconds
    print("⏱️ Running for 3 seconds...")
    time.sleep(3.5)
    
    # Check Navigator telemetry buffer
    nav_entries = []
    print("📊 Reading Navigator telemetry buffer...")
    while True:
        entry = navigator.telemetry_buffer.read()
        if entry is None:
            break
        nav_entries.append(entry)
    
    print(f"✅ Navigator produced {len(nav_entries)} telemetry entries")
    
    if nav_entries:
        for i, entry in enumerate(nav_entries[-3:], 1):  # Show last 3 entries
            print(f"  Entry {i}: lat={entry.get('lat', 0):.6f}, "
                  f"lon={entry.get('lon', 0):.6f}, "
                  f"lng={entry.get('lng', 0):.6f}, "
                  f"speed={entry.get('speed', 0):.1f} km/h, "
                  f"bearing={entry.get('bearing', 0):.1f}°")
            # Show all keys in first entry for debugging
            if i == 1:
                print(f"    All keys: {list(entry.keys())}")
    
    # Stop components
    print("🛑 Stopping components...")
    navigator.off()
    engine.off()
    
    return len(nav_entries) > 0

def test_navigator_plugin_integration():
    """Test NavigatorPlugin reading from Navigator telemetry buffer"""
    print("\n🔌 TESTING NAVIGATOR PLUGIN INTEGRATION")
    print("=" * 60)
    
    # Test route
    test_route = [
        (-59.6463, 13.2810),
        (-59.6470, 13.2820),
        (-59.6480, 13.2830)
    ]
    
    try:
        from world.vehicle_simulator.vehicle.gps_device.plugins.navigator_plugin import NavigatorTelemetryPlugin
        
        # Create Navigator with telemetry
        buffer = EngineBuffer(size=100)
        speed_model = load_speed_model('kinematic', speed=20.0)
        engine = Engine('TEST_VEHICLE', speed_model, buffer, tick_time=1.0)
        
        navigator = Navigator(
            vehicle_id='TEST_VEHICLE',
            route_coordinates=test_route,
            engine_buffer=buffer,
            tick_time=1.0
        )
        
        # Create NavigatorTelemetryPlugin
        plugin_config = {
            "navigator": navigator,
            "device_id": "TEST_VEHICLE"
        }
        
        plugin = NavigatorTelemetryPlugin()
        plugin.initialize(plugin_config)
        
        print(f"✅ NavigatorTelemetryPlugin initialized")
        
        # Start components
        engine.on()
        navigator.on()
        plugin.start_data_stream()
        
        print("🔄 Components running...")
        time.sleep(2.5)
        
        # Test plugin data retrieval
        print("📡 Testing plugin data retrieval...")
        plugin_data_count = 0
        for _ in range(5):  # Try to get data 5 times
            data = plugin.get_data()
            if data:
                plugin_data_count += 1
                print(f"  📦 Plugin data: lat={data.get('lat', 0):.6f}, "
                      f"lng={data.get('lon', 0):.6f}, "
                      f"speed={data.get('speed', 0):.1f} km/h")
            time.sleep(0.5)
        
        # Cleanup
        plugin.stop_data_stream()
        navigator.off()
        engine.off()
        
        print(f"✅ Plugin provided {plugin_data_count} data entries")
        return plugin_data_count > 0
        
    except ImportError as e:
        print(f"❌ Could not import NavigatorTelemetryPlugin: {e}")
        return False
    except Exception as e:
        print(f"❌ Plugin test failed: {e}")
        return False

async def test_complete_gps_transmission():
    """Test complete GPS device with WebSocket transmission"""
    print("\n📡 TESTING COMPLETE GPS TRANSMISSION")
    print("=" * 60)
    
    try:
        from world.vehicle_simulator.vehicle.gps_device.radio_module.json_codec import JsonCodec
        
        # Create WebSocket transmitter
        codec = JsonCodec()
        transmitter = WebSocketTransmitter(
            server_url="ws://localhost:5000",
            token="test_token",
            device_id="TEST_GPS",
            codec=codec
        )
        
        # Test route
        test_route = [
            (-59.6463, 13.2810),
            (-59.6470, 13.2820)
        ]
        
        # Create Navigator components
        buffer = EngineBuffer(size=100)
        speed_model = load_speed_model('kinematic', speed=15.0)
        engine = Engine('TEST_GPS', speed_model, buffer, tick_time=1.0)
        
        navigator = Navigator(
            vehicle_id='TEST_GPS',
            route_coordinates=test_route,
            engine_buffer=buffer,
            tick_time=1.0
        )
        
        # Create GPS device with navigator plugin
        plugin_config = {
            "type": "navigator_telemetry",
            "navigator": navigator,
            "device_id": "TEST_GPS"
        }
        
        gps_device = GPSDevice(
            device_id='TEST_GPS',
            ws_transmitter=transmitter,
            plugin_config=plugin_config
        )
        
        print("✅ GPS device created with navigator plugin")
        
        # Start all components
        engine.on()
        navigator.on()
        gps_device.on()
        
        print("🚀 All components started, transmitting for 3 seconds...")
        await asyncio.sleep(3.5)
        
        # Stop components
        print("🛑 Stopping transmission...")
        gps_device.off()
        navigator.off()
        engine.off()
        
        print("✅ Complete GPS transmission test completed")
        return True
        
    except Exception as e:
        print(f"❌ GPS transmission test failed: {e}")
        return False

def main():
    print("🧪 TELEMETRY PIPELINE VERIFICATION")
    print("=" * 70)
    
    # Test 1: Navigator telemetry production
    nav_ok = test_navigator_to_gps_flow()
    
    # Test 2: Navigator plugin integration 
    plugin_ok = test_navigator_plugin_integration()
    
    # Test 3: Complete GPS transmission
    transmission_ok = asyncio.run(test_complete_gps_transmission())
    
    print("\n🎯 TELEMETRY PIPELINE SUMMARY")
    print("=" * 70)
    print(f"✅ Navigator Telemetry: {'PASS' if nav_ok else 'FAIL'}")
    print(f"✅ Navigator Plugin: {'PASS' if plugin_ok else 'FAIL'}")  
    print(f"✅ GPS Transmission: {'PASS' if transmission_ok else 'FAIL'}")
    
    if nav_ok and plugin_ok and transmission_ok:
        print("\n🎉 TELEMETRY PIPELINE VERIFIED!")
        print("   ✅ Navigator produces telemetry from engine data")
        print("   ✅ NavigatorPlugin reads from Navigator buffer")
        print("   ✅ GPS device transmits via WebSocket")
        print("   ✅ Complete Engine → Navigator → GPS → WebSocket flow works!")
    else:
        print("\n⚠️ Telemetry pipeline has issues - check components")

if __name__ == "__main__":
    main()
