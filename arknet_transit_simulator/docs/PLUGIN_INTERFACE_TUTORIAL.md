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

```text
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
    Custom telemetry plugin example.
    
    This plugin demonstrates the basic structure and required methods
    for creating your own telemetry data source.
    """
    
    def __init__(self):
        self.device_id = None
        self.custom_config = {}
        self._connected = False
        self.counter = 0
    
    @property
    def source_type(self) -> str:
        return "my_custom"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration."""
        try:
            self.device_id = config.get("device_id", "CUSTOM001")
            self.custom_config = config
            
            logger.info(f"My custom plugin initialized for device: {self.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Custom plugin initialization failed: {e}")
            return False
    
    def start_data_stream(self) -> bool:
        """Start data collection."""
        try:
            self._connected = True
            logger.info(f"Custom data stream started for {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start custom stream: {e}")
            return False
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get telemetry data."""
        if not self._connected:
            return None
        
        try:
            # Generate custom telemetry data
            self.counter += 1
            
            return {
                "lat": 13.2810 + (self.counter * 0.0001),  # Moving north
                "lon": -59.6463,
                "speed": 45.0 + (self.counter % 10),  # Varying speed
                "heading": 90.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "device_id": self.device_id,
                "route": "CUSTOM_ROUTE",
                "vehicle_reg": self.device_id,
                "driver_id": f"driver-{self.device_id}",
                "driver_name": {"first": "Custom", "last": "Driver"},
                "extras": {
                    "source": "my_custom",
                    "counter": self.counter,
                    "plugin_version": self.plugin_version
                }
            }
            
        except Exception as e:
            logger.warning(f"Custom data generation failed: {e}")
            return None
    
    def stop_data_stream(self) -> None:
        """Stop data collection."""
        self._connected = False
        logger.info(f"Custom data stream stopped for {self.device_id}")
    
    def is_connected(self) -> bool:
        """Check if data source is connected."""
        return self._connected
```

### **Step 2: Test Your Plugin**

Create a test script to verify your plugin works:

```python
#!/usr/bin/env python3
"""Test script for custom plugin"""

from world.vehicle_simulator.vehicle.gps_device.plugins.my_custom_plugin import MyCustomTelemetryPlugin

# Create and test plugin
plugin = MyCustomTelemetryPlugin()

# Initialize with test config
config = {
    "device_id": "TEST001",
    "custom_setting": "test_value"
}

if plugin.initialize(config):
    print("✅ Plugin initialized successfully")
    
    # Start data stream
    if plugin.start_data_stream():
        print("✅ Data stream started")
        
        # Get some test data
        for i in range(3):
            data = plugin.get_data()
            print(f"📡 Data {i+1}: {data}")
        
        # Stop stream
        plugin.stop_data_stream()
        print("✅ Data stream stopped")
    else:
        print("❌ Failed to start data stream")
else:
    print("❌ Plugin initialization failed")
```

### **Step 3: Use in Vehicle Simulator**

```python
from world.vehicle_simulator.simulator import CleanVehicleSimulator
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec

# Create transmitter
transmitter = WebSocketTransmitter(
    server_url="ws://localhost:8080/gps",
    token="your_token",
    device_id="CUSTOM001",
    codec=PacketCodec()
)

# Configure your custom plugin
plugin_config = {
    "type": "my_custom",
    "device_id": "CUSTOM001",
    "custom_setting": "production_value"
}

# Create GPS device with your plugin
gps_device = GPSDevice(
    device_id="CUSTOM001",
    ws_transmitter=transmitter,
    plugin_config=plugin_config
)

# Start GPS device
gps_device.on()
print("🚀 GPS device with custom plugin started!")

# Plugin will automatically provide data to GPS device
# GPS device will transmit to WebSocket server
```

---

## 🔌 **ESP32 Hardware Plugin Implementation**

For real-world deployment with ESP32 hardware, here's how to implement the ESP32 plugin:

### **ESP32 Arduino Code**

First, prepare your ESP32 with this Arduino sketch:

```cpp
#include <WiFi.h>
#include <ArduinoJson.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// GPS module on Serial2
TinyGPSPlus gps;
HardwareSerial ss(2);

// Device configuration
String deviceId = "ESP32_001";
unsigned long lastTransmission = 0;
const unsigned long transmissionInterval = 1000; // 1 second

void setup() {
    Serial.begin(115200);
    ss.begin(9600, SERIAL_8N1, 16, 17); // RX=16, TX=17
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("WiFi connected!");
    Serial.println("ESP32 GPS Device Ready");
}

void loop() {
    // Read GPS data
    while (ss.available() > 0) {
        if (gps.encode(ss.read())) {
            if (gps.location.isValid()) {
                // Check if it's time to transmit
                if (millis() - lastTransmission >= transmissionInterval) {
                    sendGPSData();
                    lastTransmission = millis();
                }
            }
        }
    }
    
    // Handle serial commands from Python
    if (Serial.available()) {
        String command = Serial.readString();
        command.trim();
        handleCommand(command);
    }
}

void sendGPSData() {
    // Create JSON with GPS data
    DynamicJsonDocument doc(1024);
    doc["device_id"] = deviceId;
    doc["lat"] = gps.location.lat();
    doc["lon"] = gps.location.lng();
    doc["speed"] = gps.speed.kmph();
    doc["heading"] = gps.course.deg();
    doc["timestamp"] = millis();
    doc["satellites"] = gps.satellites.value();
    doc["hdop"] = gps.hdop.hdop();
    
    // Send to serial
    serializeJson(doc, Serial);
    Serial.println();
}

void handleCommand(String command) {
    if (command == "STATUS") {
        Serial.println("ESP32_READY");
    } else if (command == "GET_DATA") {
        if (gps.location.isValid()) {
            sendGPSData();
        } else {
            Serial.println("NO_GPS_FIX");
        }
    } else if (command.startsWith("SET_DEVICE_ID:")) {
        deviceId = command.substring(14);
        Serial.println("DEVICE_ID_SET");
    }
}
```

### **Python ESP32 Plugin Implementation**

Update the ESP32 plugin with complete functionality:

```python
#!/usr/bin/env python3
"""
ESP32 Hardware Telemetry Plugin
-------------------------------
Production plugin for ESP32 GPS hardware via serial communication.
"""

import json
import time
import serial
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)

class ESP32TelemetryPlugin(ITelemetryPlugin):
    """
    ESP32 hardware plugin for real GPS data via serial communication.
    
    This plugin communicates with an ESP32 device over serial to get
    real GPS coordinates and telemetry data.
    """
    
    def __init__(self):
        self.device_id = None
        self.serial_port = None
        self.baud_rate = 115200
        self.timeout = 1.0
        self.serial_connection = None
        self._connected = False
        self._latest_data = None
        self._data_lock = threading.Lock()
        self._reader_thread = None
        self._stop_reading = threading.Event()
    
    @property
    def source_type(self) -> str:
        return "esp32_hardware"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize ESP32 plugin.
        
        Config format:
        {
            "device_id": str,
            "serial_port": str (e.g., "COM3" or "/dev/ttyUSB0"),
            "baud_rate": int (default: 115200),
            "timeout": float (default: 1.0)
        }
        """
        try:
            self.device_id = config.get("device_id", "ESP32_001")
            self.serial_port = config.get("serial_port", "COM3")  # Windows default
            self.baud_rate = config.get("baud_rate", 115200)
            self.timeout = config.get("timeout", 1.0)
            
            logger.info(f"ESP32 plugin initialized - Device: {self.device_id}, Port: {self.serial_port}")
            return True
            
        except Exception as e:
            logger.error(f"ESP32 plugin initialization failed: {e}")
            return False
    
    def start_data_stream(self) -> bool:
        """Start ESP32 serial communication."""
        try:
            # Open serial connection
            self.serial_connection = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            
            # Wait for connection
            time.sleep(2)
            
            # Test connection
            self.serial_connection.write(b"STATUS\n")
            response = self.serial_connection.readline().decode().strip()
            
            if response == "ESP32_READY":
                # Set device ID on ESP32
                command = f"SET_DEVICE_ID:{self.device_id}\n"
                self.serial_connection.write(command.encode())
                
                # Start data reader thread
                self._stop_reading.clear()
                self._reader_thread = threading.Thread(target=self._read_serial_data, daemon=True)
                self._reader_thread.start()
                
                self._connected = True
                logger.info(f"ESP32 data stream started for {self.device_id}")
                return True
            else:
                logger.error(f"ESP32 not responding properly: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start ESP32 stream: {e}")
            return False
    
    def _read_serial_data(self):
        """Background thread to read serial data from ESP32."""
        while not self._stop_reading.is_set():
            try:
                if self.serial_connection and self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode().strip()
                    
                    if line:
                        try:
                            # Parse JSON data from ESP32
                            data = json.loads(line)
                            
                            # Convert to standard format
                            standardized_data = {
                                "lat": float(data.get("lat", 0.0)),
                                "lon": float(data.get("lon", 0.0)),
                                "speed": float(data.get("speed", 0.0)),
                                "heading": float(data.get("heading", 0.0)),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "device_id": self.device_id,
                                "route": "HARDWARE_ROUTE",
                                "vehicle_reg": self.device_id,
                                "driver_id": f"driver-{self.device_id}",
                                "driver_name": {"first": "Hardware", "last": "Driver"},
                                "extras": {
                                    "source": "esp32_hardware",
                                    "satellites": data.get("satellites", 0),
                                    "hdop": data.get("hdop", 0.0),
                                    "esp32_timestamp": data.get("timestamp", 0),
                                    "plugin_version": self.plugin_version
                                }
                            }
                            
                            # Store latest data thread-safely
                            with self._data_lock:
                                self._latest_data = standardized_data
                                
                        except json.JSONDecodeError:
                            # Ignore non-JSON lines (status messages, etc.)
                            pass
                            
                time.sleep(0.01)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error reading ESP32 data: {e}")
                time.sleep(1.0)
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get latest GPS data from ESP32."""
        if not self._connected:
            return None
        
        try:
            with self._data_lock:
                return self._latest_data.copy() if self._latest_data else None
                
        except Exception as e:
            logger.warning(f"ESP32 data retrieval failed: {e}")
            return None
    
    def stop_data_stream(self) -> None:
        """Stop ESP32 communication."""
        self._connected = False
        self._stop_reading.set()
        
        # Wait for reader thread to stop
        if self._reader_thread:
            self._reader_thread.join(timeout=2.0)
        
        # Close serial connection
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except Exception as e:
                logger.warning(f"Error closing ESP32 serial connection: {e}")
        
        logger.info(f"ESP32 data stream stopped for {self.device_id}")
    
    def is_connected(self) -> bool:
        """Check if ESP32 is connected."""
        return self._connected and (
            self.serial_connection is not None and 
            self.serial_connection.is_open
        )
```

### **Using ESP32 Plugin in Production**

```python
# ESP32 plugin configuration
esp32_config = {
    "type": "esp32_hardware",
    "device_id": "VEHICLE_001",
    "serial_port": "/dev/ttyUSB0",  # Linux
    # "serial_port": "COM3",        # Windows
    "baud_rate": 115200,
    "timeout": 2.0
}

# Create GPS device with ESP32 plugin
gps_device = GPSDevice(
    device_id="VEHICLE_001",
    ws_transmitter=transmitter,
    plugin_config=esp32_config
)

# Start GPS device
gps_device.on()
print("🛰️ ESP32 GPS device started!")
```

---

## 📁 **File Replay Plugin**

The file replay plugin is perfect for testing and demo scenarios:

```python
# File replay configuration
file_config = {
    "type": "file_replay",
    "device_id": "REPLAY_001",
    "file_path": "/path/to/gps_data.json",
    "loop": True,
    "speed_multiplier": 1.0
}

# Each line in gps_data.json should be:
# {"lat": 13.2810, "lon": -59.6463, "speed": 45.0, "heading": 90.0, "timestamp": "2025-09-09T10:00:00Z"}
```

---

## 🔧 **Plugin Manager Advanced Features**

### **Runtime Plugin Switching**

```python
# Switch between plugins at runtime
gps_device.switch_plugin({
    "type": "esp32_hardware",
    "device_id": "VEHICLE_001",
    "serial_port": "/dev/ttyUSB0"
})

# Check current plugin
plugin_info = gps_device.get_plugin_info()
print(f"Active plugin: {plugin_info}")
```

### **Plugin Discovery**

```python
from world.vehicle_simulator.vehicle.gps_device.plugins.manager import PluginManager

# Get available plugins
manager = PluginManager()
available_plugins = manager.list_available_plugins()
print("Available plugins:", available_plugins)
```

---

## 🛠️ **Best Practices**

### **1. Error Handling**

- Always implement proper exception handling
- Log errors with appropriate levels
- Gracefully handle connection failures
- Provide meaningful error messages

### **2. Threading Safety**

- Use locks for shared data access
- Implement proper thread cleanup
- Handle thread timeouts gracefully

### **3. Configuration Validation**

- Validate all configuration parameters
- Provide sensible defaults
- Document configuration options clearly

### **4. Testing**

- Create unit tests for your plugins
- Test with simulated and real data
- Verify thread safety and error conditions

### **5. Performance**

- Minimize data processing overhead
- Use appropriate sleep intervals
- Monitor memory usage for long-running plugins

---

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Plugin Not Loading**

   ```text
   Check plugin file location and naming
   Verify ITelemetryPlugin implementation
   Check import errors in plugin code
   ```

2. **Serial Communication Errors**

   ```text
   Verify correct serial port and baud rate
   Check cable connections and permissions
   Test with serial terminal first
   ```

3. **Data Format Issues**

   ```text
   Validate GPS coordinate ranges
   Check timestamp format (ISO 8601)
   Verify required fields are present
   ```

4. **Threading Problems**

   ```text
   Ensure proper thread cleanup
   Use appropriate timeouts
   Check for deadlocks with locks
   ```

### **Debug Mode**

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your plugin code
```

### **Plugin Testing Script**

```python
#!/usr/bin/env python3
"""Comprehensive plugin testing script"""

import time
import logging
from world.vehicle_simulator.vehicle.gps_device.plugins.manager import PluginManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_plugin(plugin_type: str, config: dict):
    """Test a specific plugin configuration."""
    manager = PluginManager()
    
    try:
        # Load plugin
        if manager.load_plugin(plugin_type, config):
            logger.info(f"✅ Plugin {plugin_type} loaded successfully")
            
            # Start data stream
            if manager.start_data_stream():
                logger.info("✅ Data stream started")
                
                # Get test data
                for i in range(5):
                    data = manager.get_data()
                    if data:
                        logger.info(f"📡 Sample {i+1}: {data}")
                    else:
                        logger.warning(f"⚠️ No data received (sample {i+1})")
                    time.sleep(1)
                
                # Stop stream
                manager.unload_current_plugin()
                logger.info("✅ Plugin test completed")
                return True
            else:
                logger.error("❌ Failed to start data stream")
                return False
        else:
            logger.error(f"❌ Failed to load plugin {plugin_type}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Plugin test failed: {e}")
        return False

# Test configurations
test_configs = [
    {
        "type": "simulation",
        "config": {
            "device_id": "TEST_SIM",
            "update_interval": 1.0
        }
    },
    {
        "type": "esp32_hardware",
        "config": {
            "device_id": "TEST_ESP32",
            "serial_port": "COM3",  # Change as needed
            "baud_rate": 115200
        }
    },
    {
        "type": "file_replay",
        "config": {
            "device_id": "TEST_FILE",
            "file_path": "sample_gps_data.json",
            "loop": True
        }
    }
]

# Run tests
print("🧪 Starting Plugin Tests...")
for test_config in test_configs:
    plugin_type = test_config["type"]
    config = test_config["config"]
    
    print(f"\n🔍 Testing {plugin_type} plugin...")
    success = test_plugin(plugin_type, config)
    
    if success:
        print(f"✅ {plugin_type} plugin test PASSED")
    else:
        print(f"❌ {plugin_type} plugin test FAILED")

print("\n🏁 Plugin testing completed!")
```

---

## 🎓 **Summary**

You now have everything needed to create custom telemetry plugins for the Vehicle Simulator:

1. **✅ Plugin Interface** - Implement `ITelemetryPlugin` methods
2. **✅ Plugin Manager** - Handles loading and lifecycle automatically  
3. **✅ ESP32 Integration** - Complete hardware implementation guide
4. **✅ Testing Framework** - Comprehensive testing and debugging tools
5. **✅ Best Practices** - Production-ready development guidelines

### **Next Steps:**

1. Create your first custom plugin using the template
2. Test with the simulation plugin first
3. Implement ESP32 hardware integration
4. Deploy to production with proper error handling
5. Contribute your plugins back to the community!

**Happy plugin development!** 🚀
