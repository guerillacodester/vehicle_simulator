"""
Example Usage of Telemetry Interface
-----------------------------------
Demonstrates how to use the telemetry interface with different data sources.
"""

import time
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice


def example_simulated_telemetry():
    """Example: Using simulated telemetry data source"""
    print("🎭 Example: Simulated Telemetry Source")
    
    # Create GPS device
    gps_device = GPSDevice(
        device_id="EXAMPLE001",
        server_url="ws://localhost:8765",
        auth_token="test_token"
    )
    
    # Create simulated data source
    sim_source = SimulatedTelemetrySource(device_id="EXAMPLE001", route="R999")
    
    # Create injector
    injector = TelemetryInjector(gps_device, sim_source)
    
    try:
        # Start GPS device and injection
        gps_device.on()
        injector.start_injection()
        
        # Inject some packets
        for i in range(5):
            success = injector.inject_single()
            print(f"   Packet {i+1}: {'✅ Sent' if success else '❌ Failed'}")
            time.sleep(1)
            
    finally:
        # Cleanup
        injector.stop_injection()
        gps_device.off()
    
    print("✅ Simulated example complete\n")


def example_serial_telemetry():
    """Example: Using serial GPS telemetry (requires real hardware)"""
    print("📡 Example: Serial GPS Telemetry")
    
    # Create GPS device
    gps_device = GPSDevice(
        device_id="SERIAL001",
        server_url="ws://localhost:8765",
        auth_token="test_token"
    )
    
    # Create serial data source (will fail without real hardware)
    serial_source = SerialTelemetrySource(port="COM3", baudrate=9600, device_id="SERIAL001")
    
    # Create injector
    injector = TelemetryInjector(gps_device, serial_source)
    
    try:
        # Start GPS device and injection
        gps_device.on()
        injector.start_injection()
        
        if serial_source.is_available():
            print("   📡 Serial GPS connected - injecting data...")
            for i in range(5):
                success = injector.inject_single()
                print(f"   Packet {i+1}: {'✅ Sent' if success else '❌ No data'}")
                time.sleep(1)
        else:
            print("   ⚠️ Serial GPS not available (no hardware)")
            
    finally:
        # Cleanup
        injector.stop_injection()
        gps_device.off()
    
    print("✅ Serial example complete\n")


def example_file_telemetry():
    """Example: Using file-based telemetry replay"""
    print("📁 Example: File Telemetry Replay")
    
    # First, create a sample data file
    sample_data = [
        {"lat": 13.2810, "lon": -59.6463, "speed": 45.0, "heading": 90.0, "route": "R001"},
        {"lat": 13.2815, "lon": -59.6468, "speed": 47.0, "heading": 92.0, "route": "R001"},
        {"lat": 13.2820, "lon": -59.6473, "speed": 43.0, "heading": 95.0, "route": "R001"},
    ]
    
    import json
    sample_file = "sample_telemetry.json"
    with open(sample_file, 'w') as f:
        for data in sample_data:
            f.write(json.dumps(data) + "\n")
    
    # Create GPS device
    gps_device = GPSDevice(
        device_id="FILE001",
        server_url="ws://localhost:8765",
        auth_token="test_token"
    )
    
    # Create file data source
    file_source = FileTelemetrySource(file_path=sample_file, device_id="FILE001")
    
    # Create injector
    injector = TelemetryInjector(gps_device, file_source)
    
    try:
        # Start GPS device and injection
        gps_device.on()
        injector.start_injection()
        
        # Inject packets from file
        packet_count = 0
        while file_source.is_available() and packet_count < 10:
            success = injector.inject_single()
            if success:
                packet_count += 1
                print(f"   Packet {packet_count}: ✅ Sent from file")
            else:
                print(f"   Packet {packet_count + 1}: ❌ End of file")
                break
            time.sleep(1)
            
    finally:
        # Cleanup
        injector.stop_injection()
        gps_device.off()
        
        # Remove sample file
        import os
        try:
            os.remove(sample_file)
        except:
            pass
    
    print("✅ File example complete\n")


def main():
    """Run all examples"""
    print("=" * 60)
    print("🚌 Telemetry Interface Examples")
    print("=" * 60)
    print("This demonstrates how the telemetry interface works")
    print("with different data sources (simulation, serial, file).")
    print("-" * 60)
    
    # Run examples
    example_simulated_telemetry()
    example_serial_telemetry()
    example_file_telemetry()
    
    print("=" * 60)
    print("✅ All examples complete!")
    print("=" * 60)
    print("\n📋 Key Points:")
    print("• The interface is source-agnostic")
    print("• GPS device only sees TelemetryPacket objects")
    print("• Different sources can be swapped without changing GPS code")
    print("• Perfect for testing with simulation then deploying with real hardware")


if __name__ == "__main__":
    main()
