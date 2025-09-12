#!/usr/bin/env python3
"""
GPS Device Consumer Test
------------------------
Clean consumer test that demonstrates proper GPSDevice usage patterns.
Shows how to create, configure, and interact with GPSDevice instances
using the public API only.
"""

import asyncio
import time
import logging
from pathlib import Path
import sys

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# GPS Device imports
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GPSDeviceConsumer:
    """
    Clean consumer class that demonstrates GPSDevice usage patterns.
    
    This shows how external code should interact with GPSDevice instances
    using only the public API.
    """
    
    def __init__(self):
        self.devices = {}
        self.running = False
    
    def create_simulation_device(self, device_id: str, server_url: str = "localhost:5000") -> GPSDevice:
        """
        Create a GPS device with simulation plugin for testing.
        
        Args:
            device_id: Unique identifier for the device
            server_url: Server URL for telemetry transmission (without ws:// prefix)
            
        Returns:
            Configured GPSDevice instance
        """
        logger.info(f"Creating simulation GPS device: {device_id}")
        
        # Create WebSocket transmitter with codec
        codec = PacketCodec()
        transmitter = WebSocketTransmitter(
            server_url=server_url,
            token="test_token",
            device_id=device_id,
            codec=codec
        )
        
        # Create plugin configuration for simulation
        plugin_config = {
            "plugin": "simulation",
            "update_interval": 2.0,  # Update every 2 seconds
            "device_id": device_id,
            "start_lat": 13.0969,
            "start_lon": -59.6138,
            "speed": 30.0,  # km/h
            "heading": 45.0
        }
        
        # Create GPS device
        device = GPSDevice(
            device_id=device_id,
            ws_transmitter=transmitter,
            plugin_config=plugin_config
        )
        
        self.devices[device_id] = device
        return device
    
    def create_custom_data_device(self, device_id: str, custom_data: dict, server_url: str = "localhost:5000") -> GPSDevice:
        """
        Create a GPS device with custom telemetry data.
        
        Args:
            device_id: Unique identifier for the device
            custom_data: Custom telemetry data to transmit
            server_url: Server URL for telemetry transmission (without ws:// prefix)
            
        Returns:
            Configured GPSDevice instance
        """
        logger.info(f"Creating custom data GPS device: {device_id}")
        
        # Create WebSocket transmitter with codec
        codec = PacketCodec()
        transmitter = WebSocketTransmitter(
            server_url=server_url,
            token="test_token",
            device_id=device_id,
            codec=codec
        )
        
        # Create plugin configuration with custom data
        plugin_config = {
            "plugin": "simulation",
            "update_interval": 1.5,  # Update every 1.5 seconds
            "device_id": device_id,
            "custom_data": custom_data
        }
        
        # Create GPS device
        device = GPSDevice(
            device_id=device_id,
            ws_transmitter=transmitter,
            plugin_config=plugin_config
        )
        
        self.devices[device_id] = device
        return device
    
    def start_device(self, device_id: str) -> bool:
        """
        Start a GPS device by device ID.
        
        Args:
            device_id: ID of device to start
            
        Returns:
            True if started successfully, False otherwise
        """
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return False
        
        device = self.devices[device_id]
        
        try:
            device.on()  # GPSDevice uses on() method
            
            # Give it a moment to start up
            time.sleep(0.5)
            
            # Check if threads are running
            is_running = (
                (device.data_thread and device.data_thread.is_alive()) or
                (device.transmitter_thread and device.transmitter_thread.is_alive())
            )
            
            if is_running:
                logger.info(f"Device {device_id} started successfully")
            else:
                logger.warning(f"Device {device_id} started but threads may not be active")
            
            return True
        except Exception as e:
            logger.error(f"Exception starting device {device_id}: {e}")
            return False
    
    def stop_device(self, device_id: str) -> None:
        """
        Stop a GPS device by device ID.
        
        Args:
            device_id: ID of device to stop
        """
        if device_id not in self.devices:
            logger.warning(f"Device {device_id} not found for stopping")
            return
        
        device = self.devices[device_id]
        
        try:
            device.off()  # GPSDevice uses off() method
            logger.info(f"Device {device_id} stopped")
        except Exception as e:
            logger.error(f"Exception stopping device {device_id}: {e}")
    
    def get_device_status(self, device_id: str) -> dict:
        """
        Get status information for a device.
        
        Args:
            device_id: ID of device to check
            
        Returns:
            Dictionary with device status information
        """
        if device_id not in self.devices:
            return {"error": f"Device {device_id} not found"}
        
        device = self.devices[device_id]
        
        # Check if device is running by examining threads
        is_running = (
            (device.data_thread and device.data_thread.is_alive()) or
            (device.transmitter_thread and device.transmitter_thread.is_alive())
        )
        
        return {
            "device_id": device.device_id,
            "is_running": is_running,
            "data_thread_alive": device.data_thread and device.data_thread.is_alive(),
            "transmitter_thread_alive": device.transmitter_thread and device.transmitter_thread.is_alive(),
            "plugin_active": hasattr(device.plugin_manager, 'active_plugin') and device.plugin_manager.active_plugin is not None,
            "plugin_info": device.get_plugin_info() if hasattr(device, 'get_plugin_info') else None
        }
    
    def list_devices(self) -> list:
        """
        Get list of all device IDs.
        
        Returns:
            List of device IDs
        """
        return list(self.devices.keys())
    
    def inject_data_to_device(self, device_id: str, telemetry_data: dict) -> bool:
        """
        Inject custom telemetry data into a device's buffer.
        
        Args:
            device_id: ID of target device
            telemetry_data: Telemetry data to inject
            
        Returns:
            True if injection successful, False otherwise
        """
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found for injection")
            return False
        
        device = self.devices[device_id]
        
        try:
            # Inject data directly into the device's buffer
            device.rxtx_buffer.write(telemetry_data)
            logger.info(f"Injected data into device {device_id}: {telemetry_data}")
            return True
        except Exception as e:
            logger.error(f"Failed to inject data into device {device_id}: {e}")
            return False


async def main():
    """
    Main test function demonstrating GPSDevice consumer patterns.
    """
    logger.info("=== GPS Device Consumer Test ===")
    
    # Create consumer instance
    consumer = GPSDeviceConsumer()
    
    try:
        # Test 1: Create and start a simulation device
        logger.info("\n--- Test 1: Simulation Device ---")
        sim_device = consumer.create_simulation_device("SIM_GPS_001")
        
        # Check initial status
        status = consumer.get_device_status("SIM_GPS_001")
        logger.info(f"Initial status: {status}")
        
        # Start the device
        started = consumer.start_device("SIM_GPS_001")
        if started:
            logger.info("Simulation device started, transmitting for 10 seconds...")
            await asyncio.sleep(10)
        
        # Test 2: Create device with custom data
        logger.info("\n--- Test 2: Custom Data Device ---")
        custom_data = {
            "lat": 13.1000,
            "lon": -59.6200,
            "speed": 45.0,
            "heading": 90.0,
            "route": "CUSTOM_ROUTE_1",
            "vehicle_reg": "CUSTOM_001"
        }
        
        custom_device = consumer.create_custom_data_device("CUSTOM_GPS_001", custom_data)
        started = consumer.start_device("CUSTOM_GPS_001")
        
        if started:
            logger.info("Custom device started, transmitting for 5 seconds...")
            await asyncio.sleep(5)
        
        # Test 3: Direct data injection
        logger.info("\n--- Test 3: Data Injection ---")
        from datetime import datetime, timezone
        
        # Create data using snake_case format (device will convert to TelemetryPacket)
        injection_data = {
            "device_id": "CUSTOM_GPS_001",         # snake_case, gets converted to deviceId
            "route": "INJECTION_ROUTE",            # string
            "vehicle_reg": "CUSTOM_GPS_001",       # snake_case, gets converted to vehicleReg
            "driver_id": "drv-CUSTOM_GPS_001",     # snake_case, gets converted to driverId
            "driver_name": {"first": "Test", "last": "Driver"},  # snake_case, gets converted to driverName
            "timestamp": datetime.now(timezone.utc).isoformat(),  # ISO8601 string
            "lat": 13.1050,                       # float, will be rounded to 6 decimal places
            "lon": -59.6250,                      # float, will be rounded to 6 decimal places
            "speed": 60.0,                        # float, will be rounded to 2 decimal places
            "heading": 180.0                      # float, will be rounded to 1 decimal place
        }
        
        injected = consumer.inject_data_to_device("CUSTOM_GPS_001", injection_data)
        if injected:
            logger.info("Data injected, waiting for transmission...")
            await asyncio.sleep(3)
        
        # Test 4: Status monitoring
        logger.info("\n--- Test 4: Status Monitoring ---")
        devices = consumer.list_devices()
        logger.info(f"Active devices: {devices}")
        
        for device_id in devices:
            status = consumer.get_device_status(device_id)
            logger.info(f"Device {device_id} status: {status}")
        
    except Exception as e:
        logger.error(f"Test error: {e}")
    
    finally:
        # Clean shutdown
        logger.info("\n--- Shutdown ---")
        devices = consumer.list_devices()
        for device_id in devices:
            consumer.stop_device(device_id)
        
        logger.info("GPS Device Consumer Test completed")


if __name__ == "__main__":
    asyncio.run(main())