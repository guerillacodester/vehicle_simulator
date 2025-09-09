# GPS Device Telemetry Interface Tutorial
## Connecting Data Sources to GPS Device RxTx Buffer

### 📋 **Overview**

This tutorial shows developers how to connect any telemetry data source to the GPS device's RxTx buffer using the source-agnostic telemetry interface. Whether you're working with simulation data, real GPS hardware, network streams, or file replay - this interface provides a clean, portable way to inject data into the GPS transmission pipeline.

### 🎯 **What You'll Learn**

- How the telemetry interface works
- Creating custom data sources
- Connecting sources to GPS devices
- Best practices for real-world deployment
- Troubleshooting common issues

---

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Data Source   │───▶│ Telemetry        │───▶│ GPS Device   │───▶│ WebSocket   │
│                 │    │ Injector         │    │ RxTx Buffer  │    │ Server      │
│ • Simulation    │    │                  │    │              │    │             │
│ • Real GPS      │    │ inject_single()  │    │ buffer.write │    │ Fleet Mgmt  │
│ • Network       │    │                  │    │              │    │             │
│ • File Replay   │    │                  │    │              │    │             │
└─────────────────┘    └──────────────────┘    └──────────────┘    └─────────────┘
```

### **Key Components:**

1. **`ITelemetryDataSource`** - Interface any data source must implement
2. **`TelemetryInjector`** - Bridges data sources to GPS devices
3. **`GPSDevice`** - Contains RxTx buffer and handles transmission
4. **`TelemetryPacket`** - Standard format for all telemetry data

---

## 🚀 **Quick Start Example**

Here's a complete example that connects a simple data source to a GPS device:

```python
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.telemetry_interface import (
    ITelemetryDataSource, TelemetryInjector
)
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet

# Step 1: Create your data source
class MyCustomDataSource(ITelemetryDataSource):
    def __init__(self, device_id):
        self.device_id = device_id
        self.counter = 0
    
    def get_telemetry_data(self):
        # Generate your telemetry data here
        self.counter += 1
        return make_packet(
            device_id=self.device_id,
            lat=13.2810 + (self.counter * 0.0001),  # Moving north
            lon=-59.6463,
            speed=45.0,
            heading=90.0,
            route="R001"
        )
    
    def is_available(self):
        return True

# Step 2: Create GPS device
gps_device = GPSDevice(
    device_id="DEV001",
    server_url="ws://localhost:8765",
    auth_token="your_token"
)

# Step 3: Connect source to GPS device
data_source = MyCustomDataSource("DEV001")
injector = TelemetryInjector(gps_device, data_source)

# Step 4: Start transmission
gps_device.on()                    # Start GPS device
injector.start_injection()         # Start data injection

# Step 5: Inject data
success = injector.inject_single() # Send one packet
print(f"Packet sent: {success}")

# Step 6: Cleanup
injector.stop_injection()
gps_device.off()
```

---

## 🔧 **Creating Custom Data Sources**

### **1. Implement the Interface**

Every data source must implement `ITelemetryDataSource`:

```python
from abc import ABC, abstractmethod
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
