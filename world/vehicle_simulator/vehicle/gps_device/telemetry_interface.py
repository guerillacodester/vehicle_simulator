"""
Telemetry Data Source Interface
------------------------------
Source-agnostic interface for injecting telemetry data into GPS device.
Works with simulation, real hardware, files, network - any data source.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from .radio_module.packet import TelemetryPacket, make_packet


class ITelemetryDataSource(ABC):
    """
    Interface for any telemetry data source.
    Implementations can be simulation, serial GPS, network, file replay, etc.
    """
    
    @abstractmethod
    def get_telemetry_data(self) -> Optional[TelemetryPacket]:
        """
        Get the next telemetry packet from this data source.
        
        Returns:
            TelemetryPacket: Formatted packet ready for transmission
            None: No data available at this time
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if data source is available/connected"""
        pass
    
    def start(self):
        """Start the data source (optional)"""
        pass
    
    def stop(self):
        """Stop the data source (optional)"""
        pass


class TelemetryInjector:
    """
    Injects telemetry data from any source into GPS device buffer.
    This is the interface between data sources and the GPS device.
    """
    
    def __init__(self, gps_device, data_source: ITelemetryDataSource):
        """
        Args:
            gps_device: The GPS device with RxTx buffer
            data_source: Any implementation of ITelemetryDataSource
        """
        self.gps_device = gps_device
        self.data_source = data_source
        self.active = False
    
    def start_injection(self):
        """Start injecting data from source into GPS device buffer"""
        self.data_source.start()
        self.active = True
        print(f"📡 Telemetry injection started: {type(self.data_source).__name__}")
    
    def inject_single(self) -> bool:
        """
        Inject one telemetry packet into the buffer.
        
        Returns:
            bool: True if packet was injected, False if no data available
        """
        if not self.active or not self.data_source.is_available():
            return False
            
        packet = self.data_source.get_telemetry_data()
        if packet:
            # Convert TelemetryPacket to dict format expected by buffer
            packet_dict = {
                "lat": packet.lat,
                "lon": packet.lon,
                "speed": packet.speed,
                "heading": packet.heading,
                "route": packet.route,
                "vehicle_reg": packet.vehicleReg,
                "driver_id": packet.driverId,
                "driver_name": packet.driverName,
                "ts": packet.timestamp,
            }
            
            # Inject into GPS device buffer
            self.gps_device.buffer.write(packet_dict)
            return True
            
        return False
    
    def stop_injection(self):
        """Stop injecting data"""
        self.active = False
        self.data_source.stop()
        print("🛑 Telemetry injection stopped")


# Example implementations
class SimulatedTelemetrySource(ITelemetryDataSource):
    """Simulated telemetry data source (for testing)"""
    
    def __init__(self, device_id: str = "SIM001", route: str = "R001"):
        self.device_id = device_id
        self.route = route
        self.lat = 13.2810  # Barbados
        self.lon = -59.6463
        import random
        self.speed = random.uniform(30, 60)
        self.heading = random.uniform(0, 360)
    
    def get_telemetry_data(self) -> Optional[TelemetryPacket]:
        """Generate simulated telemetry packet"""
        import random
        
        # Simulate movement
        self.lat += random.uniform(-0.0001, 0.0001)
        self.lon += random.uniform(-0.0001, 0.0001)
        self.speed += random.uniform(-2, 2)
        self.speed = max(10, min(80, self.speed))
        
        return make_packet(
            device_id=self.device_id,
            lat=self.lat,
            lon=self.lon,
            speed=self.speed,
            heading=self.heading,
            route=self.route
        )
    
    def is_available(self) -> bool:
        return True


class SerialTelemetrySource(ITelemetryDataSource):
    """Real GPS data from serial port"""
    
    def __init__(self, port: str = "COM3", baudrate: int = 9600, device_id: str = "GPS001"):
        self.port = port
        self.baudrate = baudrate
        self.device_id = device_id
        self.serial_conn = None
        self._connected = False
    
    def start(self):
        """Connect to serial port"""
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self._connected = True
            print(f"🔌 Serial GPS connected: {self.port}")
        except Exception as e:
            print(f"❌ Serial connection failed: {e}")
            self._connected = False
    
    def get_telemetry_data(self) -> Optional[TelemetryPacket]:
        """Read GPS data from serial port"""
        if not self._connected or not self.serial_conn:
            return None
            
        try:
            line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
            if line:
                # Parse your specific GPS format here
                # This example assumes JSON format
                import json
                data = json.loads(line)
                
                return make_packet(
                    device_id=self.device_id,
                    lat=data.get("lat", 0.0),
                    lon=data.get("lon", 0.0),
                    speed=data.get("speed", 0.0),
                    heading=data.get("heading", 0.0),
                    route=data.get("route", "R001")
                )
        except Exception as e:
            print(f"⚠️ Serial read error: {e}")
            
        return None
    
    def is_available(self) -> bool:
        return self._connected
    
    def stop(self):
        """Close serial connection"""
        if self.serial_conn:
            self.serial_conn.close()
        self._connected = False


class FileTelemetrySource(ITelemetryDataSource):
    """Telemetry data from log file (for replay/testing)"""
    
    def __init__(self, file_path: str, device_id: str = "FILE001"):
        self.file_path = file_path
        self.device_id = device_id
        self.file_handle = None
        self._available = False
    
    def start(self):
        """Open file for reading"""
        try:
            self.file_handle = open(self.file_path, 'r')
            self._available = True
            print(f"📁 File telemetry source opened: {self.file_path}")
        except Exception as e:
            print(f"❌ File open failed: {e}")
            self._available = False
    
    def get_telemetry_data(self) -> Optional[TelemetryPacket]:
        """Read next line from file"""
        if not self._available or not self.file_handle:
            return None
            
        try:
            line = self.file_handle.readline()
            if line:
                import json
                data = json.loads(line.strip())
                
                return make_packet(
                    device_id=self.device_id,
                    lat=data.get("lat", 0.0),
                    lon=data.get("lon", 0.0),
                    speed=data.get("speed", 0.0),
                    heading=data.get("heading", 0.0),
                    route=data.get("route", "R001")
                )
            else:
                # End of file
                self._available = False
        except Exception as e:
            print(f"⚠️ File read error: {e}")
            
        return None
    
    def is_available(self) -> bool:
        return self._available
    
    def stop(self):
        """Close file"""
        if self.file_handle:
            self.file_handle.close()
        self._available = False
