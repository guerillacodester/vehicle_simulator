# GPS Device Plugin SDK Tutorial
## Building Custom Telemetry Plugins for Vehicle Simulator

### 📋 **Overview**

This comprehensive tutorial guides developers through creating custom telemetry plugins for the Vehicle Simulator's GPS device system. The plugin architecture provides a clean, extensible way to support any telemetry data source - from simulation data to real ESP32 hardware, network streams, or file replay systems.

### 🎯 **What You'll Learn**

- Understanding the plugin architecture
- Creating custom telemetry plugins
- Implementing ESP32 hardware plugins
- Plugin lifecycle management
- Best practices for production deployment
- Debugging and troubleshooting

---

## 🏗️ **Plugin Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Data Source   │───▶│ Telemetry        │───▶│ GPS Device   │───▶│ WebSocket   │
│                 │    │ Plugin           │    │ RxTx Buffer  │    │ Server      │
│ • Simulation    │    │                  │    │              │    │             │
│ • ESP32         │    │ get_data()       │    │ buffer.write │    │ Fleet Mgmt  │
│ • File Replay   │    │ start_stream()   │    │              │    │             │
│ • Custom HW     │    │ stop_stream()    │    │              │    │             │
└─────────────────┘    └──────────────────┘    └──────────────┘    └─────────────┘
```

### **Key Components:**

1. **`ITelemetryPlugin`** - Abstract interface all plugins must implement
2. **`PluginManager`** - Handles plugin discovery, loading, and lifecycle
3. **`GPSDevice`** - Contains plugin manager and coordinates data flow
4. **`TelemetryPacket`** - Standard format for all telemetry data

---

## 🚀 **Quick Start: Your First Plugin**

Let's create a simple custom plugin step by step:

### **Step 1: Create Plugin File**

Create a new file: `world/vehicle_simulator/vehicle/gps_device/plugins/my_custom_plugin.py`

```python
#!/usr/bin/env python3
"""
My Custom Telemetry Plugin
--------------------------
Example plugin showing how to implement ITelemetryPlugin interface.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)

class MyCustomTelemetryPlugin(ITelemetryPlugin):
    """
    Custom plugin example - generates mock GPS coordinates.
    Replace this with your actual data source logic.
    """
    
    def __init__(self):
        self.device_id = None
        self.latitude = 13.0975  # Barbados coordinates
        self.longitude = -59.6132
        self._connected = False
        self._config = {}
    
    @property
    def source_type(self) -> str:
        return "my_custom_source"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration."""
        try:
            self._config = config
            self.device_id = config.get("device_id", "CUSTOM001")
            
            # Add your initialization logic here
            # e.g., connect to hardware, open files, etc.
            
            logger.info(f"Custom plugin initialized for device: {self.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Custom plugin initialization failed: {e}")
            return False
    
    def start_data_stream(self) -> bool:
        """Start the data stream."""
        try:
            # Add your connection/startup logic here
            self._connected = True
            logger.info(f"Custom data stream started for {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start custom stream: {e}")
            return False
    
    def stop_data_stream(self) -> None:
        """Stop the data stream."""
        self._connected = False
        logger.info(f"Custom data stream stopped for {self.device_id}")
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get current telemetry data."""
        if not self._connected:
            return None
        
        try:
            # Generate your telemetry data here
            # This example creates moving coordinates
            self.latitude += 0.0001  # Move north slightly
            
            return {
                "lat": float(self.latitude),
                "lon": float(self.longitude),
                "speed": 35.0,
                "heading": 90.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "device_id": self.device_id,
                "route": "CUSTOM_ROUTE",
                "vehicle_reg": self.device_id,
                "driver_id": f"drv-{self.device_id}",
                "driver_name": {"first": "Custom", "last": "Driver"},
                "extras": {
                    "source": "my_custom_source",
                    "plugin_version": self.plugin_version
                }
            }
            
        except Exception as e:
            logger.warning(f"Custom data generation failed: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if data source is connected."""
        return self._connected
```

### **Step 2: Test Your Plugin**

```python
# Test script: test_my_plugin.py
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec

# Create WebSocket transmitter
transmitter = WebSocketTransmitter(
    server_url="ws://localhost:8080/gps",
    token="test-token",
    device_id="CUSTOM001",
    codec=PacketCodec()
)

# Configure your custom plugin
plugin_config = {
    "type": "my_custom_source",
    "device_id": "CUSTOM001",
    "update_interval": 2.0
}

# Create GPS device with your plugin
gps_device = GPSDevice(
    device_id="CUSTOM001",
    ws_transmitter=transmitter,
    plugin_config=plugin_config
)

# Start the system
gps_device.on()
print("Custom plugin running... Press Ctrl+C to stop")

try:
    time.sleep(10)  # Run for 10 seconds
finally:
    gps_device.off()
    print("Plugin stopped")
```

---

---

## 🔌 **ESP32 Hardware Plugin Development**

The ESP32 plugin is designed for real GPS hardware integration. Here's how to implement and use it:

### **ESP32 Plugin Architecture**

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ ESP32 GPS   │───▶│ Serial      │───▶│ ESP32        │───▶│ GPS Device  │
│ Module      │    │ Connection  │    │ Plugin       │    │ RxTx Buffer │
│             │    │ (UART)      │    │              │    │             │
│ • NMEA      │    │ /dev/ttyUSB0│    │ parse_nmea() │    │ TelemetryPkt│
│ • Custom    │    │ COM3        │    │ validate()   │    │             │
│ • JSON      │    │ 9600 baud   │    │ convert()    │    │             │
└─────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
```

### **ESP32 Plugin Implementation**

Here's the current ESP32 plugin template that you can extend:

```python
#!/usr/bin/env python3
"""
ESP32 Hardware Telemetry Plugin
-------------------------------
Plugin for real ESP32 GPS hardware integration via serial communication.
"""

import serial
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)

class ESP32TelemetryPlugin(ITelemetryPlugin):
    """
    ESP32 hardware plugin for GPS device.
    
    Supports:
    - NMEA sentence parsing
    - Custom JSON protocols
    - Serial/UART communication
    - Hardware validation
    """
    
    def __init__(self):
        self.serial_port = None
        self.device_id = None
        self._connected = False
        self._config = {}
        self.port = "/dev/ttyUSB0"  # Default Linux
        self.baudrate = 9600
        self.timeout = 1.0
    
    @property
    def source_type(self) -> str:
        return "esp32_hardware"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize ESP32 connection."""
        try:
            self._config = config
            self.device_id = config.get("device_id", "ESP32_001")
            self.port = config.get("serial_port", "/dev/ttyUSB0")
            self.baudrate = config.get("baudrate", 9600)
            self.timeout = config.get("timeout", 1.0)
            
            logger.info(f"ESP32 plugin initialized for device: {self.device_id}")
            logger.info(f"Serial config: {self.port}@{self.baudrate}")
            return True
            
        except Exception as e:
            logger.error(f"ESP32 plugin initialization failed: {e}")
            return False
    
    def start_data_stream(self) -> bool:
        """Start ESP32 serial connection."""
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Wait for ESP32 to be ready
            time.sleep(2)
            
            # Test connection
            if self.serial_port.is_open:
                self._connected = True
                logger.info(f"ESP32 serial connection established: {self.port}")
                return True
            else:
                logger.error("Failed to open ESP32 serial port")
                return False
                
        except serial.SerialException as e:
            logger.error(f"ESP32 serial connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"ESP32 startup error: {e}")
            return False
    
    def stop_data_stream(self) -> None:
        """Stop ESP32 serial connection."""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self._connected = False
            logger.info("ESP32 serial connection closed")
        except Exception as e:
            logger.error(f"Error closing ESP32 connection: {e}")
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Read data from ESP32."""
        if not self._connected or not self.serial_port:
            return None
        
        try:
            # Read line from ESP32
            if self.serial_port.in_waiting > 0:
                line = self.serial_port.readline().decode('utf-8').strip()
                
                if line:
                    # Try to parse as JSON first
                    if line.startswith('{'):
                        return self._parse_json_data(line)
                    # Try NMEA parsing
                    elif line.startswith('$'):
                        return self._parse_nmea_data(line)
                    else:
                        logger.warning(f"Unknown data format: {line}")
            
            return None
            
        except Exception as e:
            logger.error(f"ESP32 data read error: {e}")
            return None
    
    def _parse_json_data(self, json_line: str) -> Optional[Dict[str, Any]]:
        """Parse custom JSON data from ESP32."""
        try:
            data = json.loads(json_line)
            
            # Validate required fields
            required_fields = ['lat', 'lon', 'speed', 'heading']
            if not all(field in data for field in required_fields):
                logger.warning("ESP32 JSON missing required fields")
                return None
            
            return {
                "lat": float(data["lat"]),
                "lon": float(data["lon"]),
                "speed": float(data.get("speed", 0.0)),
                "heading": float(data.get("heading", 0.0)),
                "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "device_id": self.device_id,
                "route": data.get("route", "ESP32_ROUTE"),
                "vehicle_reg": data.get("vehicle_reg", self.device_id),
                "driver_id": data.get("driver_id", f"esp32-{self.device_id}"),
                "driver_name": data.get("driver_name", {"first": "ESP32", "last": "Driver"}),
                "extras": {
                    "source": "esp32_hardware",
                    "plugin_version": self.plugin_version,
                    "raw_data": data
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"ESP32 JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"ESP32 JSON processing error: {e}")
            return None
    
    def _parse_nmea_data(self, nmea_line: str) -> Optional[Dict[str, Any]]:
        """Parse NMEA sentence from ESP32."""
        try:
            # This is a simplified NMEA parser
            # For production, use pynmea2 library
            
            if nmea_line.startswith('$GPGGA'):
                parts = nmea_line.split(',')
                if len(parts) >= 10:
                    lat_str = parts[2]
                    lat_dir = parts[3]
                    lon_str = parts[4]
                    lon_dir = parts[5]
                    
                    if lat_str and lon_str:
                        # Convert NMEA format to decimal degrees
                        lat = self._nmea_to_decimal(lat_str, lat_dir)
                        lon = self._nmea_to_decimal(lon_str, lon_dir)
                        
                        return {
                            "lat": lat,
                            "lon": lon,
                            "speed": 0.0,  # GPGGA doesn't include speed
                            "heading": 0.0,  # GPGGA doesn't include heading
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "device_id": self.device_id,
                            "route": "NMEA_ROUTE",
                            "vehicle_reg": self.device_id,
                            "driver_id": f"nmea-{self.device_id}",
                            "driver_name": {"first": "NMEA", "last": "Driver"},
                            "extras": {
                                "source": "esp32_nmea",
                                "plugin_version": self.plugin_version,
                                "sentence": nmea_line
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"NMEA parsing error: {e}")
            return None
    
    def _nmea_to_decimal(self, coord_str: str, direction: str) -> float:
        """Convert NMEA coordinate to decimal degrees."""
        if len(coord_str) < 4:
            return 0.0
        
        # NMEA format: DDMM.MMMM or DDDMM.MMMM
        degrees = int(coord_str[:2] if len(coord_str) == 9 else coord_str[:3])
        minutes = float(coord_str[2:] if len(coord_str) == 9 else coord_str[3:])
        
        decimal = degrees + minutes / 60.0
        
        if direction in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    
    def is_connected(self) -> bool:
        """Check if ESP32 is connected."""
        return self._connected and self.serial_port and self.serial_port.is_open
```

### **ESP32 Configuration Example**

```python
# ESP32 plugin configuration
esp32_config = {
    "type": "esp32_hardware",
    "device_id": "ESP32_BUS001",
    "serial_port": "/dev/ttyUSB0",  # Linux
    # "serial_port": "COM3",        # Windows
    "baudrate": 9600,
    "timeout": 1.0,
    "update_interval": 1.0
}

# Create GPS device with ESP32 plugin
gps_device = GPSDevice(
    device_id="ESP32_BUS001",
    ws_transmitter=transmitter,
    plugin_config=esp32_config
)
```

### **ESP32 Hardware Setup**

**ESP32 Code Example (Arduino IDE):**

```cpp
#include "WiFi.h"
#include "SoftwareSerial.h"

// GPS module pins
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17

SoftwareSerial gpsSerial(GPS_RX_PIN, GPS_TX_PIN);

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);
  
  Serial.println("ESP32 GPS Bridge Started");
}

void loop() {
  // Read from GPS module
  if (gpsSerial.available()) {
    String gpsData = gpsSerial.readStringUntil('\n');
    
    // Option 1: Forward raw NMEA
    Serial.println(gpsData);
    
    // Option 2: Parse and send as JSON
    // parseAndSendJSON(gpsData);
  }
  
  delay(100);
}

void parseAndSendJSON(String nmea) {
  // Parse NMEA and create JSON
  // Example JSON output:
  // {"lat": 13.0975, "lon": -59.6132, "speed": 25.5, "heading": 90.0}
  
  // Implementation depends on your GPS module and requirements
}
```

**Wiring Diagram:**
```
ESP32          GPS Module
--------------------------
3.3V    ───────> VCC
GND     ───────> GND
GPIO16  ───────> TX
GPIO17  ───────> RX
```

---

## 📁 **File Replay Plugin Development**

For testing and demo purposes, you can create file-based plugins:

### **File Replay Plugin Example**

```python
#!/usr/bin/env python3
"""
File Replay Telemetry Plugin
----------------------------
Plugin for replaying recorded GPS data from files.
"""

import json
import csv
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)

class FileReplayTelemetryPlugin(ITelemetryPlugin):
    """
    File replay plugin for GPS device.
    
    Supports:
    - JSON file replay
    - CSV file replay
    - Looped playback
    - Timestamp preservation
    """
    
    def __init__(self):
        self.device_id = None
        self.file_path = None
        self.data_records = []
        self.current_index = 0
        self.loop_playback = True
        self._connected = False
        self._config = {}
    
    @property
    def source_type(self) -> str:
        return "file_replay"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize file replay."""
        try:
            self._config = config
            self.device_id = config.get("device_id", "REPLAY001")
            self.file_path = config.get("file_path")
            self.loop_playback = config.get("loop_playback", True)
            
            if not self.file_path:
                logger.error("File replay plugin requires 'file_path' in config")
                return False
            
            # Load data from file
            self._load_data_file()
            
            logger.info(f"File replay plugin initialized: {len(self.data_records)} records")
            return True
            
        except Exception as e:
            logger.error(f"File replay plugin initialization failed: {e}")
            return False
    
    def _load_data_file(self):
        """Load GPS data from file."""
        try:
            if self.file_path.endswith('.json'):
                self._load_json_file()
            elif self.file_path.endswith('.csv'):
                self._load_csv_file()
            else:
                raise ValueError("Unsupported file format. Use .json or .csv")
                
        except Exception as e:
            logger.error(f"Failed to load data file: {e}")
            raise
    
    def _load_json_file(self):
        """Load JSON format GPS data."""
        with open(self.file_path, 'r') as f:
            data = json.load(f)
            
            if isinstance(data, list):
                self.data_records = data
            else:
                self.data_records = [data]
    
    def _load_csv_file(self):
        """Load CSV format GPS data."""
        with open(self.file_path, 'r') as f:
            reader = csv.DictReader(f)
            self.data_records = list(reader)
    
    def start_data_stream(self) -> bool:
        """Start file replay."""
        try:
            if not self.data_records:
                logger.error("No data records loaded for replay")
                return False
            
            self.current_index = 0
            self._connected = True
            logger.info(f"File replay started: {self.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start file replay: {e}")
            return False
    
    def stop_data_stream(self) -> None:
        """Stop file replay."""
        self._connected = False
        logger.info("File replay stopped")
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get next record from file."""
        if not self._connected or not self.data_records:
            return None
        
        try:
            # Get current record
            if self.current_index >= len(self.data_records):
                if self.loop_playback:
                    self.current_index = 0
                else:
                    logger.info("File replay completed")
                    return None
            
            record = self.data_records[self.current_index]
            self.current_index += 1
            
            # Convert to standard format
            return {
                "lat": float(record.get("lat", 0.0)),
                "lon": float(record.get("lon", 0.0)),
                "speed": float(record.get("speed", 0.0)),
                "heading": float(record.get("heading", 0.0)),
                "timestamp": record.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "device_id": self.device_id,
                "route": record.get("route", "REPLAY_ROUTE"),
                "vehicle_reg": record.get("vehicle_reg", self.device_id),
                "driver_id": record.get("driver_id", f"replay-{self.device_id}"),
                "driver_name": record.get("driver_name", {"first": "Replay", "last": "Driver"}),
                "extras": {
                    "source": "file_replay",
                    "plugin_version": self.plugin_version,
                    "record_index": self.current_index - 1
                }
            }
            
        except Exception as e:
            logger.error(f"File replay data error: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if file replay is active."""
        return self._connected
```

---
from world.vehicle_simulator.vehicle.gps_device.telemetry_interface import ITelemetryDataSource
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet

class MyDataSource(ITelemetryDataSource):
    def __init__(self, device_id, **kwargs):
        self.device_id = device_id
        # Your initialization here
    
    @abstractmethod
    def get_telemetry_data(self):
        """
        Returns: TelemetryPacket or None
        
        This method is called every time the injector needs data.
        Return None if no data is available.
        """
        # Your data generation/reading logic here
        return make_packet(
            device_id=self.device_id,
            lat=your_latitude,
            lon=your_longitude,
            speed=your_speed,
            heading=your_heading,
            route=your_route_id,
            driver_id=your_driver_id,      # Optional
            driver_name=your_driver_name   # Optional
        )
    
    @abstractmethod
    def is_available(self):
        """
        Returns: bool
        
        True if data source is ready/connected, False otherwise.
        """
        return your_connection_status
    
    def start(self):
        """Optional: Initialize connections, open files, etc."""
        pass
    
    def stop(self):
        """Optional: Cleanup connections, close files, etc."""
        pass
```

### **2. Real-World Examples**

#### **Serial GPS Data Source**

```python
import serial
import json

class SerialGPSSource(ITelemetryDataSource):
    def __init__(self, device_id, port="COM3", baudrate=9600):
        self.device_id = device_id
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self._connected = False
    
    def start(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self._connected = True
            print(f"🔌 Serial GPS connected: {self.port}")
        except Exception as e:
            print(f"❌ Serial connection failed: {e}")
            self._connected = False
    
    def get_telemetry_data(self):
        if not self._connected:
            return None
        
        try:
            # Read NMEA sentence or JSON from GPS
            line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
            if line:
                # Parse your GPS format (NMEA, JSON, etc.)
                data = self._parse_gps_data(line)
                if data:
                    return make_packet(
                        device_id=self.device_id,
                        lat=data['lat'],
                        lon=data['lon'],
                        speed=data['speed'],
                        heading=data['heading'],
                        route=data.get('route', 'R001')
                    )
        except Exception as e:
            print(f"⚠️ Serial read error: {e}")
        
        return None
    
    def _parse_gps_data(self, line):
        # Your parsing logic here
        # Could be NMEA, JSON, or custom format
        try:
            return json.loads(line)  # Example for JSON format
        except:
            return None
    
    def is_available(self):
        return self._connected
    
    def stop(self):
        if self.serial_conn:
            self.serial_conn.close()
        self._connected = False
```

#### **Network Stream Data Source**

```python
import requests
import time

class NetworkStreamSource(ITelemetryDataSource):
    def __init__(self, device_id, api_url, api_key):
        self.device_id = device_id
        self.api_url = api_url
        self.api_key = api_key
        self.session = None
        self._connected = False
    
    def start(self):
        try:
            self.session = requests.Session()
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
            # Test connection
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            self._connected = response.status_code == 200
            print(f"🌐 Network source connected: {self.api_url}")
        except Exception as e:
            print(f"❌ Network connection failed: {e}")
            self._connected = False
    
    def get_telemetry_data(self):
        if not self._connected:
            return None
        
        try:
            # Fetch latest telemetry from API
            response = self.session.get(
                f"{self.api_url}/telemetry/{self.device_id}",
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                return make_packet(
                    device_id=self.device_id,
                    lat=data['latitude'],
                    lon=data['longitude'],
                    speed=data['speed_kmh'],
                    heading=data['bearing'],
                    route=data.get('route_id', 'R001')
                )
        except Exception as e:
            print(f"⚠️ Network fetch error: {e}")
        
        return None
    
    def is_available(self):
        return self._connected
    
    def stop(self):
        if self.session:
            self.session.close()
        self._connected = False
```

#### **Database Data Source**

```python
import sqlite3
from datetime import datetime, timedelta

class DatabaseSource(ITelemetryDataSource):
    def __init__(self, device_id, db_path, table_name="vehicle_positions"):
        self.device_id = device_id
        self.db_path = db_path
        self.table_name = table_name
        self.conn = None
        self.last_timestamp = None
    
    def start(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.last_timestamp = datetime.now()
            print(f"🗄️ Database source connected: {self.db_path}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    
    def get_telemetry_data(self):
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            
            # Get latest position for this device
            cursor.execute(f"""
                SELECT lat, lon, speed, heading, route_id, timestamp
                FROM {self.table_name}
                WHERE device_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (self.device_id, self.last_timestamp))
            
            row = cursor.fetchone()
            if row:
                lat, lon, speed, heading, route_id, timestamp = row
                self.last_timestamp = timestamp
                
                return make_packet(
                    device_id=self.device_id,
                    lat=lat,
                    lon=lon,
                    speed=speed,
                    heading=heading,
                    route=route_id
                )
        except Exception as e:
            print(f"⚠️ Database query error: {e}")
        
        return None
    
    def is_available(self):
        return self.conn is not None
    
    def stop(self):
        if self.conn:
            self.conn.close()
```

---

## 🔄 **Integration Patterns**

### **1. Continuous Injection Loop**

For real-time data sources that need continuous monitoring:

```python
import time
import threading

class ContinuousInjector:
    def __init__(self, gps_device, data_source, interval=1.0):
        self.injector = TelemetryInjector(gps_device, data_source)
        self.interval = interval
        self.running = False
        self.thread = None
    
    def start(self):
        self.injector.start_injection()
        self.running = True
        self.thread = threading.Thread(target=self._injection_loop)
        self.thread.start()
        print(f"🔄 Continuous injection started (interval: {self.interval}s)")
    
    def _injection_loop(self):
        while self.running:
            try:
                success = self.injector.inject_single()
                if not success:
                    print("⚠️ No data available")
                time.sleep(self.interval)
            except Exception as e:
                print(f"❌ Injection error: {e}")
                time.sleep(self.interval)
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.injector.stop_injection()
        print("🛑 Continuous injection stopped")

# Usage
continuous = ContinuousInjector(gps_device, your_data_source, interval=0.5)
continuous.start()
# ... let it run ...
continuous.stop()
```

### **2. Event-Driven Injection**

For data sources that provide callbacks or events:

```python
class EventDrivenInjector:
    def __init__(self, gps_device, data_source):
        self.injector = TelemetryInjector(gps_device, data_source)
        self.data_source = data_source
    
    def start(self):
        self.injector.start_injection()
        # Register callback with your data source
        self.data_source.on_data_received = self._on_new_data
    
    def _on_new_data(self, data):
        """Called when new data arrives"""
        success = self.injector.inject_single()
        if success:
            print(f"📡 Data injected: {data}")
    
    def stop(self):
        self.data_source.on_data_received = None
        self.injector.stop_injection()
```

### **3. Batch Processing**

For processing historical data or bulk uploads:

```python
def process_batch_data(gps_device, data_source, batch_size=100):
    injector = TelemetryInjector(gps_device, data_source)
    
    try:
        injector.start_injection()
        
        processed = 0
        while data_source.is_available() and processed < batch_size:
            success = injector.inject_single()
            if success:
                processed += 1
                print(f"📦 Processed {processed}/{batch_size}")
            else:
                break
        
        print(f"✅ Batch complete: {processed} packets processed")
        
    finally:
        injector.stop_injection()
```

---

## 🛠️ **Configuration and Deployment**

### **1. Configuration Management**

Create a configuration system for your data sources:

```python
import configparser

class TelemetryConfig:
    def __init__(self, config_file="telemetry.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
    
    def get_gps_config(self):
        return {
            'server_url': self.config.get('gps', 'server_url', fallback='ws://localhost:8765'),
            'auth_token': self.config.get('gps', 'auth_token', fallback='default_token'),
            'device_id': self.config.get('gps', 'device_id', fallback='GPS001')
        }
    
    def get_source_config(self, source_type):
        section = f'source_{source_type}'
        if section in self.config:
            return dict(self.config[section])
        return {}

# Example config file (telemetry.ini):
"""
[gps]
server_url = ws://your-server.com:8765
auth_token = your_production_token
device_id = BUS001

[source_serial]
port = COM3
baudrate = 9600
timeout = 1

[source_network]
api_url = https://api.example.com/v1
api_key = your_api_key
poll_interval = 2.0
"""
```

### **2. Factory Pattern for Sources**

Create a factory to manage different source types:

```python
class TelemetrySourceFactory:
    @staticmethod
    def create_source(source_type, device_id, config):
        if source_type == 'simulation':
            from .telemetry_interface import SimulatedTelemetrySource
            return SimulatedTelemetrySource(device_id, config.get('route', 'R001'))
        
        elif source_type == 'serial':
            return SerialGPSSource(
                device_id,
                port=config.get('port', 'COM3'),
                baudrate=int(config.get('baudrate', 9600))
            )
        
        elif source_type == 'network':
            return NetworkStreamSource(
                device_id,
                api_url=config['api_url'],
                api_key=config['api_key']
            )
        
        elif source_type == 'database':
            return DatabaseSource(
                device_id,
                db_path=config['db_path'],
                table_name=config.get('table_name', 'positions')
            )
        
        else:
            raise ValueError(f"Unknown source type: {source_type}")

# Usage
config = TelemetryConfig()
source = TelemetrySourceFactory.create_source(
    'serial',
    'BUS001',
    config.get_source_config('serial')
)
```

---

## 🔍 **Testing and Debugging**

### **1. Data Source Testing**

Test your data source independently:

```python
def test_data_source(source, num_packets=5):
    print(f"🧪 Testing {type(source).__name__}")
    
    # Test availability
    print(f"   Available: {source.is_available()}")
    
    # Test data generation
    source.start()
    for i in range(num_packets):
        packet = source.get_telemetry_data()
        if packet:
            print(f"   Packet {i+1}: ✅ lat={packet.lat:.6f}, lon={packet.lon:.6f}")
        else:
            print(f"   Packet {i+1}: ❌ No data")
    source.stop()

# Test your source
test_data_source(your_data_source)
```

### **2. Injection Monitoring**

Monitor injection success rates:

```python
class MonitoredInjector:
    def __init__(self, gps_device, data_source):
        self.injector = TelemetryInjector(gps_device, data_source)
        self.stats = {
            'total_attempts': 0,
            'successful_injections': 0,
            'failures': 0
        }
    
    def inject_single(self):
        self.stats['total_attempts'] += 1
        success = self.injector.inject_single()
        
        if success:
            self.stats['successful_injections'] += 1
        else:
            self.stats['failures'] += 1
        
        return success
    
    def get_stats(self):
        success_rate = (
            self.stats['successful_injections'] / self.stats['total_attempts'] * 100
            if self.stats['total_attempts'] > 0 else 0
        )
        return {
            **self.stats,
            'success_rate': success_rate
        }

# Usage
monitored = MonitoredInjector(gps_device, your_source)
# ... inject data ...
print(f"📊 Stats: {monitored.get_stats()}")
```

### **3. Logging and Debugging**

Add comprehensive logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LoggedDataSource(ITelemetryDataSource):
    def __init__(self, wrapped_source, logger_name):
        self.source = wrapped_source
        self.logger = logging.getLogger(logger_name)
    
    def get_telemetry_data(self):
        try:
            packet = self.source.get_telemetry_data()
            if packet:
                self.logger.debug(f"Generated packet: {packet.lat:.6f}, {packet.lon:.6f}")
            else:
                self.logger.warning("No data available")
            return packet
        except Exception as e:
            self.logger.error(f"Data generation failed: {e}")
            return None
    
    def is_available(self):
        return self.source.is_available()
    
    def start(self):
        self.logger.info("Starting data source")
        return self.source.start()
    
    def stop(self):
        self.logger.info("Stopping data source")
        return self.source.stop()

# Wrap your source with logging
logged_source = LoggedDataSource(your_source, 'telemetry.source')
```

---

## ⚠️ **Common Issues and Solutions**

### **1. Connection Issues**

```python
def robust_connection(create_source_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            source = create_source_func()
            source.start()
            if source.is_available():
                return source
            source.stop()
        except Exception as e:
            print(f"❌ Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    raise ConnectionError("Failed to establish connection after retries")
```

### **2. Data Validation**

```python
def validate_packet_data(packet):
    """Validate telemetry packet data"""
    if not packet:
        return False, "Packet is None"
    
    if not (-90 <= packet.lat <= 90):
        return False, f"Invalid latitude: {packet.lat}"
    
    if not (-180 <= packet.lon <= 180):
        return False, f"Invalid longitude: {packet.lon}"
    
    if packet.speed < 0:
        return False, f"Invalid speed: {packet.speed}"
    
    if not (0 <= packet.heading <= 360):
        return False, f"Invalid heading: {packet.heading}"
    
    return True, "Valid"

class ValidatedInjector:
    def __init__(self, gps_device, data_source):
        self.injector = TelemetryInjector(gps_device, data_source)
    
    def inject_single(self):
        packet = self.injector.data_source.get_telemetry_data()
        if packet:
            valid, message = validate_packet_data(packet)
            if valid:
                # Manually inject the validated packet
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
                self.injector.gps_device.buffer.write(packet_dict)
                return True
            else:
                print(f"⚠️ Invalid packet: {message}")
        return False
```

### **3. Performance Optimization**

```python
import time
from collections import deque

class BufferedInjector:
    def __init__(self, gps_device, data_source, buffer_size=10):
        self.injector = TelemetryInjector(gps_device, data_source)
        self.buffer = deque(maxlen=buffer_size)
        self.last_batch_time = 0
        self.batch_interval = 1.0  # Batch every second
    
    def inject_single(self):
        # Collect packets in buffer
        packet = self.injector.data_source.get_telemetry_data()
        if packet:
            self.buffer.append(packet)
        
        # Send batch if interval reached
        current_time = time.time()
        if current_time - self.last_batch_time >= self.batch_interval:
            return self._flush_buffer()
        
        return bool(packet)
    
    def _flush_buffer(self):
        sent_count = 0
        while self.buffer:
            packet = self.buffer.popleft()
            # Convert and send packet
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
            self.injector.gps_device.buffer.write(packet_dict)
            sent_count += 1
        
        self.last_batch_time = time.time()
        if sent_count > 0:
            print(f"📦 Sent batch of {sent_count} packets")
        
        return sent_count > 0
```

---

## 🎯 **Best Practices**

### **1. Error Handling**
- Always implement proper exception handling in your data sources
- Use timeouts for network/serial operations
- Implement retry logic for transient failures
- Log errors with sufficient detail for debugging

### **2. Resource Management**
- Always call `stop()` methods in finally blocks or use context managers
- Close connections, files, and other resources properly
- Monitor memory usage for long-running processes

### **3. Testing Strategy**
- Test data sources independently before integration
- Use simulation sources for development and testing
- Validate data before injection
- Monitor injection success rates in production

### **4. Configuration Management**
- Use configuration files for deployment-specific settings
- Support environment variables for sensitive data
- Implement configuration validation
- Document all configuration options

### **5. Performance Considerations**
- Use appropriate polling intervals for your use case
- Implement buffering for high-frequency data
- Consider async/await for I/O-bound operations
- Monitor CPU and memory usage

---

## 📚 **Complete Working Example**

Here's a complete, production-ready example:

```python
#!/usr/bin/env python3
"""
Production Telemetry System
--------------------------
Complete example showing how to connect various data sources
to GPS devices with proper error handling and monitoring.
"""

import time
import signal
import sys
import logging
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.telemetry_interface import (
    TelemetryInjector, SimulatedTelemetrySource
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionTelemetrySystem:
    def __init__(self, config):
        self.config = config
        self.gps_device = None
        self.data_source = None
        self.injector = None
        self.running = False
        
        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        try:
            # Create GPS device
            self.gps_device = GPSDevice(
                device_id=self.config['device_id'],
                server_url=self.config['server_url'],
                auth_token=self.config['auth_token']
            )
            
            # Create data source (using simulation for this example)
            self.data_source = SimulatedTelemetrySource(
                device_id=self.config['device_id'],
                route=self.config.get('route', 'R001')
            )
            
            # Create injector
            self.injector = TelemetryInjector(self.gps_device, self.data_source)
            
            # Start everything
            self.gps_device.on()
            self.injector.start_injection()
            self.running = True
            
            logger.info("✅ Telemetry system started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start telemetry system: {e}")
            self.stop()
            raise
    
    def run(self, duration=None):
        if not self.running:
            raise RuntimeError("System not started")
        
        start_time = time.time()
        injection_count = 0
        
        try:
            while self.running:
                # Inject telemetry data
                success = self.injector.inject_single()
                if success:
                    injection_count += 1
                
                # Log stats every 60 seconds
                elapsed = time.time() - start_time
                if elapsed > 0 and int(elapsed) % 60 == 0:
                    rate = injection_count / elapsed
                    logger.info(f"📊 Injected {injection_count} packets ({rate:.2f}/s)")
                
                # Check duration limit
                if duration and elapsed >= duration:
                    logger.info(f"⏰ Duration limit reached ({duration}s)")
                    break
                
                time.sleep(1.0)  # 1 second interval
                
        except Exception as e:
            logger.error(f"❌ Runtime error: {e}")
        finally:
            logger.info(f"📈 Final stats: {injection_count} packets in {elapsed:.1f}s")
    
    def stop(self):
        self.running = False
        
        if self.injector:
            try:
                self.injector.stop_injection()
                logger.info("🔌 Injector stopped")
            except Exception as e:
                logger.error(f"⚠️ Error stopping injector: {e}")
        
        if self.gps_device:
            try:
                self.gps_device.off()
                logger.info("📡 GPS device stopped")
            except Exception as e:
                logger.error(f"⚠️ Error stopping GPS device: {e}")
        
        logger.info("✅ Telemetry system stopped")

def main():
    # Configuration
    config = {
        'device_id': 'PROD001',
        'server_url': 'ws://localhost:8765',
        'auth_token': 'production_token',
        'route': 'R001'
    }
    
    # Create and run system
    system = ProductionTelemetrySystem(config)
    
    try:
        system.start()
        system.run(duration=300)  # Run for 5 minutes
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
    finally:
        system.stop()

if __name__ == "__main__":
    main()
```

---

## 🎉 **Conclusion**

You now have everything you need to connect any data source to the GPS device RxTx buffer! The telemetry interface provides:

- ✅ **Source Agnostic Design** - Works with any data type
- ✅ **Clean Separation** - GPS device doesn't know about data sources
- ✅ **Easy Testing** - Test with simulation, deploy with real data
- ✅ **Portable** - Take the GPS device anywhere
- ✅ **Extensible** - Add new source types easily

### **Next Steps:**
1. Implement your specific data source following the examples
2. Test thoroughly with the provided debugging tools
3. Deploy with proper error handling and monitoring
4. Scale as needed with performance optimizations

**Happy coding!** 🚀

---

*For more examples and the latest updates, check the source code in:*
- `world/vehicle_simulator/vehicle/gps_device/telemetry_interface.py`
- `world/vehicle_simulator/vehicle/gps_device/example_usage.py`
