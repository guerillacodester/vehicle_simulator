# Vehicle Simulator User Manual

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Plugin System](#plugin-system)
5. [GPS Device Integration](#gps-device-integration)
6. [Operating Modes](#operating-modes)
7. [Configuration Guide](#configuration-guide)
8. [Command Line Interface](#command-line-interface)
9. [Real Data Integration](#real-data-integration)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Usage](#advanced-usage)

---

## Overview

e.g. execute: python -m arknet_transit_simulator --mode depot --duration 60 --debug

The Vehicle Simulator is a comprehensive system designed to simulate vehicle operations, GPS telemetry transmission, and fleet management scenarios. Built with a modern **plugin architecture**, it provides realistic vehicle behavior simulation with real-time GPS data transmission capabilities, making it ideal for testing, development, and demonstration of transportation management systems.

### Core Capabilities

- **Plugin-Based Architecture** - Extensible telemetry data sources
- **Realistic Vehicle Simulation** - Physics-based movement and behavior  
- **Multiple Data Sources** - Simulation, ESP32 hardware, file replay, custom plugins
- **GPS Telemetry Transmission** - Real-time data via WebSocket
- **Multiple Operating Modes** - Standalone, enhanced, and depot modes
- **Database Integration** - PostgreSQL support with SSH tunneling
- **Route Management** - File-based and database route providers
- **Flexible Deployment** - Portable GPS device architecture

### System Requirements

- **Python 3.8+**
- **PostgreSQL** (optional, for database mode)
- **WebSocket Server** (for GPS transmission)
- **Minimum 4GB RAM** (for multiple vehicle simulation)
- **Network Access** (for remote database/WebSocket connections)
- **Serial Port Access** (for ESP32 hardware plugins)

---

## System Architecture

### Component Overview

```text
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Vehicle Simulator  │───▶│   GPS Device     │───▶│  WebSocket      │
│                     │    │   Plugin System  │    │  Transmission   │
│ • Route Provider    │    │   RxTx Buffer    │    │                 │
│ • Physics Engine    │    └──────────────────┘    └─────────────────┘
│ • Speed Model       │             │
└─────────────────────┘             │
                                    ▼
                            ┌──────────────────┐
                            │ Telemetry Plugin │
                            │                  │
                            │ • Simulation     │
                            │ • ESP32          │
                            │ • File Replay    │
                            │ • Custom         │
                            └──────────────────┘
```

### Key Components

1. **Vehicle Simulator** - Core simulation engine with physics and route following
2. **GPS Device** - Hardware abstraction layer with plugin system
3. **Plugin System** - Extensible telemetry data source architecture
4. **WebSocket Transmission** - Real-time data streaming to fleet management
5. **Route Provider** - File-based or database route data access

### Directory Structure

```text
world/vehicle_simulator/
├── main.py                      # Main application entry point
├── config/
│   ├── config.ini              # Configuration settings
│   └── vehicles.json           # Vehicle fleet configuration
├── core/
│   ├── standalone_manager.py   # Standalone simulation manager
│   └── vehicles_depot.py       # Vehicle depot management
├── interfaces/
│   ├── route_provider.py       # Route data interface
│   └── telemetry_source.py     # Telemetry source interface (deprecated)
├── providers/
│   ├── config_provider.py      # Configuration management
│   ├── database_route_provider.py  # Database route access
│   └── file_route_provider.py  # File-based route access
├── models/
│   ├── people.py               # People simulator with passenger generation
│   ├── people_models/          # Plugin models for passenger distribution
│   └── speed_models/           # Vehicle physics and speed models
├── utils/
│   └── telemetry_utils.py      # Telemetry helper functions
├── vehicle/
│   ├── driver/                 # Driver behavior simulation
│   └── gps_device/            # GPS transmission system with plugins
│       ├── device.py          # Main GPS device controller
│       ├── plugins/           # Telemetry plugin system
│       │   ├── interface.py   # Plugin interface definition
│       │   ├── manager.py     # Plugin management
│       │   ├── simulation.py  # Simulation data plugin
│       │   ├── esp32.py       # ESP32 hardware plugin
│       │   └── file_replay.py # File replay plugin
│       └── radio_module/      # WebSocket communication
└── docs/                       # Documentation
    ├── USER_MANUAL.md         # This manual
    └── PLUGIN_INTERFACE_TUTORIAL.md  # Plugin development guide
```

---

## Installation & Setup

### Prerequisites

1. **Python Environment**

   ```bash
   python --version  # Ensure Python 3.8+
   pip install --upgrade pip
   ```

2. **Install Dependencies**

   ```bash
   cd e:\projects\arknettransit\vehicle_simulator
   pip install -r requirements.txt
   ```

3. **Configuration Setup**

   The simulator uses `world/vehicle_simulator/config/config.ini` for configuration:

   ```ini
   [routes]
   provider = file
   file_path = data/routes/
   
   [database]
   host = localhost
   port = 5432
   user = fleet_user
   password = secure_password
   database = fleet_manager
   
   [simulation]
   default_tick_time = 1.0
   max_vehicles = 50
   physics_enabled = true
   
   [gps]
   server_url = ws://localhost:8765
   auth_token = supersecrettoken
   transmission_interval = 1.0
   ```

### Quick Start

1. **Basic Simulation**

   ```bash
   python world\vehicle_simulator\main.py --mode enhanced --duration 60
   ```

2. **Custom Configuration**

   ```bash
   python world\vehicle_simulator\main.py --mode enhanced --duration 120 --tick-time 0.5
   ```

3. **Verify GPS Transmission**

   Check WebSocket server logs for incoming telemetry data.

---

## Operating Modes

### 1. Enhanced Mode (Recommended)

**Description:** Full-featured simulation with GPS transmission and database integration.

**Features:**

- Real-time vehicle simulation
- GPS telemetry transmission
- Database route loading (with fallback to dummy data)
- WebSocket communication
- Complete fleet management

**Usage:**

```bash
python world\vehicle_simulator\main.py --mode enhanced --duration 300 --tick-time 1.0
```

**Parameters:**

- `--duration`: Simulation time in seconds
- `--tick-time`: Update interval in seconds (default: 1.0)
- `--debug`: Enable debug logging

### 2. Standalone Mode

**Description:** Independent operation without external dependencies.

**Features:**

- File-based route loading
- Local vehicle simulation
- No database requirements
- Minimal resource usage

**Usage:**

```bash
python world\vehicle_simulator\main.py --mode standalone --duration 180
```

### 3. Depot Mode

**Description:** Specialized mode for depot operations and vehicle maintenance scenarios.

**Features:**

- Depot-specific vehicle behaviors
- Maintenance scheduling simulation
- Parking and storage operations
- Fleet staging scenarios

**Usage:**

```bash
python world\vehicle_simulator\main.py --mode depot --duration 240
```

### Mode Comparison

| Feature | Enhanced | Standalone | Depot |
|---------|----------|------------|-------|
| GPS Transmission | ✅ | ✅ | ✅ |
| Database Integration | ✅ | ❌ | ✅ |
| Route Management | ✅ | ✅ | ✅ |
| Real-time Updates | ✅ | ✅ | ✅ |
| External Dependencies | High | Low | Medium |
| Resource Usage | High | Low | Medium |

---

## GPS Device Integration

### GPS Device Architecture

The GPS device system is completely self-contained and portable:

```text
┌─────────────────────┐
│    GPS Device       │
├─────────────────────┤
│ • Device ID         │
│ • Server URL        │
│ • Auth Token        │
│ • Method (WebSocket)│
└─────────────────────┘
          │
┌─────────────────────┐
│   RxTx Buffer       │
├─────────────────────┤
│ • Queue System      │
│ • Thread-Safe       │
│ • Auto-Flush        │
└─────────────────────┘
          │
┌─────────────────────┐
│  Radio Modules      │
├─────────────────────┤
│ • WebSocket Trans.  │
│ • Packet Codecs     │
│ • Error Handling    │
└─────────────────────┘
```

### Configuration

GPS devices are automatically configured per vehicle:

```python
# Automatic GPS device creation
gps_device = GPSDevice(
    device_id=vehicle_id,
    server_url="ws://localhost:8765",  # From config
    auth_token="supersecrettoken",     # From config
    method="ws",
    interval=1.0
)
```

### Data Format

GPS telemetry packets include:

```json
{
    "lat": 13.2810,
    "lon": -59.6463,
    "speed": 45.0,
    "heading": 90.0,
    "route": "R001",
    "vehicle_reg": "BUS001",
    "driver_id": "drv-BUS001",
    "driver_name": {"first": "Sim", "last": "BUS001"},
    "ts": "2025-09-09T20:00:00Z"
}
```

---

## Plugin System

### Modern Plugin Architecture

The Vehicle Simulator uses a modern plugin system that provides clean separation between the GPS device and telemetry data sources. This architecture allows for easy extension and switching between different data sources.

```python
from world.vehicle_simulator.vehicle.gps_device.plugins.manager import PluginManager
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice

# Configure plugin
plugin_config = {
    "type": "simulation",  # or "esp32_hardware", "file_replay"
    "device_id": "VEHICLE_001",
    "update_interval": 1.0
}

# Create GPS device with plugin
gps_device = GPSDevice(
    device_id="VEHICLE_001",
    ws_transmitter=transmitter,
    plugin_config=plugin_config
)
```

### Available Plugins

#### 1. Simulation Plugin (Default)

Used for development and testing with simulated GPS data:

```python
plugin_config = {
    "type": "simulation",
    "device_id": "BUS001",
    "route": "R001",
    "update_interval": 1.0
}
```

**Features:**

- Realistic GPS coordinate generation
- Configurable movement patterns
- Variable speed simulation
- No external dependencies

#### 2. ESP32 Hardware Plugin

For real GPS hardware connected via ESP32:

```python
plugin_config = {
    "type": "esp32_hardware", 
    "device_id": "GPS001",
    "serial_port": "COM3",        # Windows
    # "serial_port": "/dev/ttyUSB0",  # Linux
    "baud_rate": 115200,
    "timeout": 2.0
}
```

**Features:**

- Real GPS data from ESP32 device
- Serial communication protocol
- Hardware status monitoring
- Automatic error recovery

#### 3. File Replay Plugin

For testing with recorded GPS data:

```python
plugin_config = {
    "type": "file_replay",
    "device_id": "REPLAY001", 
    "file_path": "gps_data.json",
    "loop": True,
    "speed_multiplier": 1.0
}
```

**Features:**

- Replay recorded GPS traces
- Support for various file formats
- Configurable playback speed
- Loop functionality for continuous testing

### Plugin Development

To create custom plugins, implement the `ITelemetryPlugin` interface:

```python
from world.vehicle_simulator.vehicle.gps_device.plugins.interface import ITelemetryPlugin

class MyCustomPlugin(ITelemetryPlugin):
    @property
    def source_type(self) -> str:
        return "my_custom"
    
    def initialize(self, config: dict) -> bool:
        # Initialize your plugin
        return True
    
    def start_data_stream(self) -> bool:
        # Start data collection
        return True
    
    def get_data(self) -> Optional[dict]:
        # Return GPS data in standard format
        return {
            "lat": 13.2810,
            "lon": -59.6463,
            "speed": 45.0,
            "heading": 90.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # ... other required fields
        }
    
    def stop_data_stream(self) -> None:
        # Stop data collection
        pass
    
    def is_connected(self) -> bool:
        # Return connection status
        return True
```

For complete plugin development instructions, see the [Plugin Interface Tutorial](PLUGIN_INTERFACE_TUTORIAL.md).

### Runtime Plugin Management

#### Switch Plugins at Runtime

```python
# Switch to ESP32 hardware
new_config = {
    "type": "esp32_hardware",
    "device_id": "VEHICLE_001", 
    "serial_port": "/dev/ttyUSB0"
}

gps_device.switch_plugin(new_config)
```

#### Get Plugin Information

```python
# Check current plugin
plugin_info = gps_device.get_plugin_info()
print(f"Active plugin: {plugin_info['type']}")
print(f"Plugin version: {plugin_info['version']}")
print(f"Connection status: {plugin_info['connected']}")
```

#### Plugin Discovery

```python
from world.vehicle_simulator.vehicle.gps_device.plugins.manager import PluginManager

manager = PluginManager()
available_plugins = manager.list_available_plugins()
print("Available plugins:", available_plugins)
```

---

## Configuration Guide

### Configuration File Structure

The main configuration file is `world/vehicle_simulator/config/config.ini`:

```ini
[routes]
# Route data provider: file or database
provider = file
file_path = data/routes/
database_fallback = true

[database]
# PostgreSQL connection settings
host = localhost
port = 5432
user = fleet_user
password = secure_password
database = fleet_manager
ssh_tunnel = false

# SSH tunnel settings (if ssh_tunnel = true)
ssh_host = remote-server.com
ssh_port = 22
ssh_user = ssh_user
ssh_key_path = /path/to/ssh/key

[simulation]
# Simulation behavior settings
default_tick_time = 1.0
max_vehicles = 50
physics_enabled = true
collision_detection = false
realistic_acceleration = true

[gps]
# GPS transmission settings
server_url = ws://localhost:8765
auth_token = supersecrettoken
transmission_interval = 1.0
retry_attempts = 3
timeout_seconds = 10

[logging]
# Logging configuration
level = INFO
file_output = false
console_output = true
format = %(asctime)s - %(levelname)s - %(message)s
```

### Environment Variables

Override configuration with environment variables:

```bash
# Database settings
export DB_HOST=production-db.com
export DB_USER=prod_user
export DB_PASSWORD=secure_prod_password

# GPS settings
export GPS_SERVER_URL=wss://production-gps.com
export GPS_AUTH_TOKEN=production_token

# Simulation settings
export SIM_TICK_TIME=0.5
export SIM_MAX_VEHICLES=100
```

### Route Configuration

#### File-based Routes

Place GeoJSON route files in `data/routes/`:

```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "route_id": "R001",
                "route_name": "Main Line",
                "direction": "inbound"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-59.6463, 13.2810],
                    [-59.6470, 13.2820],
                    [-59.6480, 13.2830]
                ]
            }
        }
    ]
}
```

#### Database Routes

Configure database connection for dynamic route loading:

```python
# Routes loaded from database tables:
# - routes: route definitions
# - route_shapes: geometry data
# - stops: stop locations
# - schedules: timing information
```

---

## Command Line Interface

### Basic Commands

#### Start Simulation

```bash
# Basic enhanced mode
python world\vehicle_simulator\main.py --mode enhanced

# With custom duration and tick time
python world\vehicle_simulator\main.py --mode enhanced --duration 300 --tick-time 0.5

# Standalone mode
python world\vehicle_simulator\main.py --mode standalone --duration 180

# Debug mode
python world\vehicle_simulator\main.py --mode enhanced --debug
```

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--mode` | string | enhanced | Operating mode (enhanced/standalone/depot) |
| `--duration` | int | 60 | Simulation duration in seconds |
| `--tick-time` | float | 1.0 | Update interval in seconds |
| `--debug` | flag | false | Enable debug logging |
| `--no-gps` | flag | false | Disable GPS transmission |
| `--config` | string | config/config.ini | Configuration file path |

### Advanced Options

#### Custom Configuration

```bash
python world\vehicle_simulator\main.py --mode enhanced --config custom_config.ini
```

#### Disable GPS Transmission

```bash
python world\vehicle_simulator\main.py --mode enhanced --no-gps --duration 120
```

#### High-Frequency Simulation

```bash
python world\vehicle_simulator\main.py --mode enhanced --tick-time 0.1 --duration 60
```

### Batch Operations

#### Multiple Simulations

Create a batch script for multiple runs:

```bash
# batch_simulation.bat (Windows)
@echo off
for /l %%i in (1,1,5) do (
    echo Running simulation %%i
    python world\vehicle_simulator\main.py --mode enhanced --duration 120
    timeout /t 30
)
```

```bash
# batch_simulation.sh (Linux)
#!/bin/bash
for i in {1..5}; do
    echo "Running simulation $i"
    python world/vehicle_simulator/main.py --mode enhanced --duration 120
    sleep 30
done
```

---

## Real Data Integration

### Replacing Simulated Data

The vehicle simulator can work with real telemetry data instead of simulation:

#### Option 1: Custom Data Source

```python
class RealGPSSource(ITelemetryDataSource):
    def __init__(self, device_connection):
        self.device = device_connection
    
    def get_telemetry_data(self):
        # Read from real GPS device
        raw_data = self.device.read_nmea()
        return self.parse_to_telemetry_packet(raw_data)
    
    def is_available(self):
        return self.device.is_connected()

# Use in simulator
real_source = RealGPSSource(gps_device_connection)
injector = TelemetryInjector(gps_device, real_source)
```

#### Option 2: Network Data Stream

```python
class NetworkTelemetrySource(ITelemetryDataSource):
    def __init__(self, api_endpoint, vehicle_id):
        self.api_endpoint = api_endpoint
        self.vehicle_id = vehicle_id
    
    def get_telemetry_data(self):
        response = requests.get(f"{self.api_endpoint}/vehicles/{self.vehicle_id}/location")
        if response.status_code == 200:
            data = response.json()
            return make_packet(
                device_id=self.vehicle_id,
                lat=data['latitude'],
                lon=data['longitude'],
                speed=data['speed'],
                heading=data['bearing']
            )
        return None
```

#### Option 3: File Replay

```python
# Use existing FileTelemetrySource
file_source = FileTelemetrySource(
    file_path="recorded_gps_data.json",
    device_id="BUS001"
)

# Integrate with simulator
injector = TelemetryInjector(gps_device, file_source)
injector.start_injection()
```

### Data Format Requirements

#### Input Data Format

Real data should be converted to the standard telemetry packet format:

```python
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet

packet = make_packet(
    device_id="BUS001",        # Required: unique device identifier
    lat=13.2810,               # Required: latitude (WGS84)
    lon=-59.6463,              # Required: longitude (WGS84)  
    speed=45.0,                # Required: speed in km/h
    heading=90.0,              # Required: heading in degrees (0-360)
    route="R001",              # Optional: route identifier
    driver_id="driver123",     # Optional: driver identifier
    driver_name={"first": "John", "last": "Doe"}  # Optional: driver name
)
```

#### NMEA Sentence Parsing

For GPS devices outputting NMEA sentences:

```python
import pynmea2

def parse_nmea_to_packet(nmea_sentence, device_id):
    try:
        msg = pynmea2.parse(nmea_sentence)
        
        if msg.sentence_type == 'GGA':  # GPS fix data
            return make_packet(
                device_id=device_id,
                lat=float(msg.latitude),
                lon=float(msg.longitude),
                speed=0.0,  # GGA doesn't include speed
                heading=0.0  # GGA doesn't include heading
            )
        
        elif msg.sentence_type == 'RMC':  # Recommended minimum
            return make_packet(
                device_id=device_id,
                lat=float(msg.latitude),
                lon=float(msg.longitude),
                speed=float(msg.spd_over_grnd) * 1.852,  # Convert knots to km/h
                heading=float(msg.true_course) if msg.true_course else 0.0
            )
    
    except Exception as e:
        print(f"NMEA parsing error: {e}")
        return None
```

---

## Troubleshooting

### Common Issues

#### Simulation Won't Start

**Symptoms:**

- Application exits immediately
- "Configuration not found" errors
- Import errors

**Solutions:**

1. **Check Python Environment**

   ```bash
   python --version  # Should be 3.8+
   pip list | grep -E "fastapi|socketio|psycopg2"
   ```

2. **Verify Configuration File**

   ```bash
   # Check if config file exists
   ls world\vehicle_simulator\config\config.ini
   
   # Validate configuration
   python -c "import configparser; c=configparser.ConfigParser(); c.read('world/vehicle_simulator/config/config.ini'); print(c.sections())"
   ```

3. **Install Missing Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

#### GPS Transmission Issues

**Symptoms:**

- No telemetry data received at WebSocket server
- "Connection refused" errors
- GPS device startup failures

**Solutions:**

1. **Check WebSocket Server**

   ```bash
   # Test WebSocket server availability
   curl -I http://localhost:8765
   
   # Or use telnet
   telnet localhost 8765
   ```

2. **Verify GPS Configuration**

   ```python
   # Test GPS device manually
   from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
   
   device = GPSDevice("TEST001", "ws://localhost:8765", "test_token")
   device.on()
   print(f"Device active: {device.thread is not None}")
   ```

3. **Check Network Connectivity**

   ```bash
   # Test network connection
   ping localhost
   netstat -an | findstr 8765  # Windows
   netstat -an | grep 8765     # Linux
   ```

#### Database Connection Problems

**Symptoms:**

- "Database unavailable" warnings
- Fallback to dummy data
- SSH tunnel failures

**Solutions:**

1. **Test Database Connection**

   ```python
   import psycopg2
   try:
       conn = psycopg2.connect(
           host="localhost",
           port=5432,
           user="fleet_user",
           password="password",
           database="fleet_manager"
       )
       print("Database connection successful")
       conn.close()
   except Exception as e:
       print(f"Database connection failed: {e}")
   ```

2. **SSH Tunnel Debugging**

   ```bash
   # Test SSH connection manually
   ssh -L 5433:localhost:5432 user@remote-server
   
   # Check if tunnel is working
   psql -h localhost -p 5433 -U fleet_user -d fleet_manager
   ```

3. **Use Standalone Mode**

   ```bash
   # Bypass database issues
   python world\vehicle_simulator\main.py --mode standalone
   ```

#### Performance Issues

**Symptoms:**

- High CPU usage
- Memory leaks
- Slow simulation updates

**Solutions:**

1. **Optimize Tick Time**

   ```bash
   # Reduce update frequency
   python world\vehicle_simulator\main.py --tick-time 2.0
   ```

2. **Limit Vehicle Count**

   ```ini
   # In config.ini
   [simulation]
   max_vehicles = 10  # Reduce from default
   ```

3. **Monitor Resource Usage**

   ```python
   import psutil
   import os
   
   def monitor_resources():
       process = psutil.Process(os.getpid())
       print(f"CPU: {process.cpu_percent()}%")
       print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

### Debug Mode

Enable comprehensive debugging:

```bash
python world\vehicle_simulator\main.py --mode enhanced --debug --duration 60
```

Debug output includes:

- Configuration loading details
- Database connection attempts
- GPS device initialization
- Vehicle state updates
- Telemetry transmission logs

### Log Analysis

Check log output for common patterns:

```text
# Successful startup
INFO - Loaded configuration from: config/config.ini
INFO - Vehicle Simulator initialized in enhanced mode
INFO - GPS devices initialized for 4 vehicles
INFO - Enhanced vehicle simulation started

# Database issues
WARNING - Database unavailable (connection refused), using dummy data
INFO - Created 4 dummy vehicles

# GPS transmission
INFO - GPS device for BUS001 turned ON
INFO - Telemetry injection started: VehicleTelemetrySource
```

---

## Advanced Usage

### Custom Vehicle Behaviors

#### Implement Custom Speed Models

```python
# In models/speed_models/custom_speed_model.py
class CustomSpeedModel:
    def __init__(self, max_speed=60.0, acceleration=2.0):
        self.max_speed = max_speed
        self.acceleration = acceleration
    
    def calculate_speed(self, current_speed, target_speed, time_delta):
        speed_diff = target_speed - current_speed
        
        if abs(speed_diff) < 0.1:
            return target_speed
        
        if speed_diff > 0:
            # Accelerating
            return min(current_speed + self.acceleration * time_delta, target_speed)
        else:
            # Decelerating
            return max(current_speed - self.acceleration * 2 * time_delta, target_speed)
```

#### Custom Route Following

```python
# Custom route behavior
class AdvancedRouteFollower:
    def __init__(self, route_data):
        self.route_points = route_data['coordinates']
        self.current_segment = 0
        self.progress = 0.0
    
    def update_position(self, time_delta, speed):
        # Calculate distance traveled
        distance = speed * time_delta / 3600  # Convert km/h to km
        
        # Update progress along route
        self.progress += distance / self.get_segment_length()
        
        if self.progress >= 1.0:
            self.next_segment()
        
        return self.interpolate_position()
```

### Multi-Vehicle Coordination

#### Fleet Formation

```python
class FleetFormation:
    def __init__(self, lead_vehicle, follow_vehicles, spacing=50):
        self.lead_vehicle = lead_vehicle
        self.follow_vehicles = follow_vehicles
        self.spacing = spacing  # meters
    
    def update_formation(self):
        lead_pos = self.lead_vehicle.get_position()
        
        for i, vehicle in enumerate(self.follow_vehicles):
            target_pos = self.calculate_follow_position(lead_pos, i + 1)
            vehicle.set_target_position(target_pos)
```

#### Traffic Simulation

```python
class TrafficManager:
    def __init__(self, vehicles):
        self.vehicles = vehicles
        self.traffic_lights = []
        self.congestion_areas = []
    
    def update_traffic_conditions(self):
        for vehicle in self.vehicles:
            # Check for traffic lights
            if self.is_at_traffic_light(vehicle):
                vehicle.set_speed(0 if self.light_is_red() else vehicle.max_speed)
            
            # Check for congestion
            nearby_vehicles = self.get_nearby_vehicles(vehicle, radius=100)
            if len(nearby_vehicles) > 3:
                vehicle.reduce_speed(0.5)
```

### Integration with External Systems

#### Real-time Fleet Management

```python
class ExternalFleetInterface:
    def __init__(self, api_endpoint):
        self.api_endpoint = api_endpoint
    
    def send_vehicle_status(self, vehicle_data):
        response = requests.post(
            f"{self.api_endpoint}/vehicles/status",
            json=vehicle_data,
            headers={"Authorization": "Bearer token"}
        )
        return response.status_code == 200
    
    def receive_dispatch_commands(self):
        response = requests.get(f"{self.api_endpoint}/dispatch/pending")
        if response.status_code == 200:
            return response.json()
        return []
```

#### IoT Device Integration

```python
class IoTDeviceManager:
    def __init__(self, mqtt_broker):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(mqtt_broker, 1883, 60)
    
    def publish_vehicle_data(self, vehicle_id, data):
        topic = f"fleet/vehicles/{vehicle_id}/telemetry"
        self.mqtt_client.publish(topic, json.dumps(data))
    
    def subscribe_to_commands(self, vehicle_id, callback):
        topic = f"fleet/vehicles/{vehicle_id}/commands"
        self.mqtt_client.subscribe(topic)
        self.mqtt_client.on_message = callback
```

### Performance Optimization

#### Efficient Data Structures

```python
# Use spatial indexing for large fleets
from rtree import index

class SpatialVehicleIndex:
    def __init__(self):
        self.idx = index.Index()
        self.vehicles = {}
    
    def add_vehicle(self, vehicle_id, lat, lon):
        self.idx.insert(hash(vehicle_id), (lon, lat, lon, lat))
        self.vehicles[vehicle_id] = (lat, lon)
    
    def find_nearby_vehicles(self, lat, lon, radius_km):
        # Convert radius to degrees (approximate)
        radius_deg = radius_km / 111.0
        bbox = (lon - radius_deg, lat - radius_deg, 
                lon + radius_deg, lat + radius_deg)
        
        return list(self.idx.intersection(bbox))
```

#### Parallel Processing

```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

def simulate_vehicle_batch(vehicle_batch, duration):
    """Simulate a batch of vehicles in parallel"""
    results = []
    for vehicle in vehicle_batch:
        result = vehicle.simulate(duration)
        results.append(result)
    return results

def run_parallel_simulation(vehicles, duration, num_processes=4):
    # Split vehicles into batches
    batch_size = len(vehicles) // num_processes
    batches = [vehicles[i:i+batch_size] for i in range(0, len(vehicles), batch_size)]
    
    # Run simulation in parallel
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = [executor.submit(simulate_vehicle_batch, batch, duration) 
                  for batch in batches]
        
        results = []
        for future in futures:
            results.extend(future.result())
    
    return results
```

### Deployment Strategies

#### Docker Containerization

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV SIM_MODE=enhanced
ENV SIM_DURATION=3600

CMD ["python", "world/vehicle_simulator/main.py", "--mode", "${SIM_MODE}", "--duration", "${SIM_DURATION}"]
```

#### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vehicle-simulator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vehicle-simulator
  template:
    metadata:
      labels:
        app: vehicle-simulator
    spec:
      containers:
      - name: simulator
        image: vehicle-simulator:latest
        env:
        - name: SIM_MODE
          value: "enhanced"
        - name: GPS_SERVER_URL
          value: "ws://fleet-manager:8765"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

#### Monitoring & Alerting

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
VEHICLES_ACTIVE = Gauge('vehicles_active_total', 'Number of active vehicles')
TELEMETRY_SENT = Counter('telemetry_packets_sent_total', 'Total telemetry packets sent')
SIMULATION_DURATION = Histogram('simulation_duration_seconds', 'Simulation duration')

def update_metrics(simulator):
    VEHICLES_ACTIVE.set(len(simulator.vehicles))
    # Update other metrics...

# Start metrics server
start_http_server(8000)
```

---

**For additional documentation, examples, and support, see:**

- **GPS Device Documentation**: `world/vehicle_simulator/vehicle/gps_device/docs/`
- **API Examples**: `world/vehicle_simulator/vehicle/gps_device/example_usage.py`
- **Configuration Reference**: `world/vehicle_simulator/config/config.ini`
