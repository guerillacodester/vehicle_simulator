# Vehicle Simulator - Comprehensive Repository Summary

## 🚗 Project Overview

The **Vehicle Simulator** is a sophisticated, real-time public transit simulation system designed for the Arknet Transit network in Barbados. It provides authentic physics-based vehicle movement with real-time GPS telemetry transmission, supporting both traditional scheduled operations and ZR van capacity-based dispatch systems.

## 🏗️ Architecture Overview

### Core Design Philosophy

- **Database-Driven Operations**: PostgreSQL-backed fleet management with real-time API integration
- **Physics-Based Simulation**: Authentic kinematic speed models with geodesic coordinate interpolation
- **Plugin Architecture**: Modular telemetry sources (simulation, ESP32 hardware, file replay, navigator)
- **Microservice Integration**: Seamless connection to Fleet Manager API via Socket.IO
- **Real-Time Telemetry**: WebSocket-based GPS transmission to external monitoring systems

### System Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Vehicle Simulator                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   Fleet Manager │  │   Socket.IO      │  │   Database      │ │
│  │   API Client    │◄─┤   Monitor        │◄─┤   Connection    │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  VehiclesDepot  │  │   Timetable      │  │   Route         │ │
│  │  (Core Engine)  │◄─┤   Scheduler      │◄─┤   Provider      │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│           Physics Engine & Navigation Layer                    │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   Engine        │  │   Navigator      │  │   GPS Device    │ │
│  │   (Kinematic)   │──┤   (Geodesic)     │──┤   (Telemetry)   │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│           External Interface Layer                              │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   WebSocket     │  │   Command Line   │  │   Configuration │ │
│  │   Transmitter   │  │   Interface      │  │   Management    │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Core Components

### VehiclesDepot (Core Engine)

**Location**: `world/vehicle_simulator/core/vehicles_depot.py`

The central orchestrator managing vehicle lifecycle and operations:

- **Fleet Management**: Creates and manages vehicle instances from database
- **Component Integration**: Coordinates Engine, Navigator, and GPS devices
- **Dual Scheduling**: Supports both time-based and capacity-based dispatch
- **Resource Tracking**: Real-time monitoring of vehicles, drivers, routes

**Key Features**:

- Database-driven vehicle instantiation
- Plugin-based GPS telemetry
- Navigator integration for route following
- Timetable scheduler coordination

### Physics Engine System

**Locations**:

- `world/vehicle_simulator/vehicle/engine/engine_block.py`
- `world/vehicle_simulator/speed_models/kinematic_speed.py`

Authentic vehicle physics simulation:

- **Kinematic Speed Models**: Realistic acceleration/deceleration patterns
- **Distance Calculation**: Precise distance accumulation over time
- **Engine Buffer**: Thread-safe circular buffer for diagnostics
- **Multi-threading**: Background engine simulation threads

**Physics Pipeline**:

```text
Speed Model → Engine Block → Distance Calculation → Engine Buffer
```

### Navigator & Geodesic System

**Location**: `world/vehicle_simulator/vehicle/driver/navigation/navigator.py`

Advanced geospatial navigation with Earth-accurate calculations:

- **Geodesic Interpolation**: Route following using proper Earth curvature mathematics
- **Haversine Distance**: Accurate distance calculations between coordinates
- **Bearing Calculation**: Realistic heading determination
- **Route Interpolation**: Smooth position updates along polyline routes

**Navigation Pipeline**:

```text
Engine Distance → Route Interpolation → Geodesic Calculation → GPS Coordinates
```

### GPS Telemetry System

**Location**: `world/vehicle_simulator/vehicle/gps_device/`

Plugin-based telemetry architecture:

- **NavigatorTelemetryPlugin**: Reads from Navigator's telemetry buffer
- **SimulationPlugin**: Generates synthetic movement data
- **ESP32Plugin**: Real hardware integration support
- **WebSocket Transmission**: Real-time data streaming

**Telemetry Flow**:

```text
Navigator → Plugin → RxTx Buffer → WebSocket → External Systems
```

### Database Integration

**Location**: `world/vehicle_simulator/providers/data_provider.py`

Comprehensive fleet data management:

- **SQLAlchemy Integration**: Full ORM support for fleet entities
- **API Monitoring**: Socket.IO connection health tracking
- **Data Synchronization**: Real-time fleet state updates
- **SSH Tunneling**: Secure database connections

## 🚐 ZR Van Operations (Unique Feature)

### Capacity-Based Scheduling

Authentic Caribbean public transit simulation:

**ZR Van Logic**:

- **Passenger Simulation**: Automatic passenger arrival and boarding
- **Capacity Triggers**: Depart when full (11 passengers) OR after max wait time
- **Real-Time Monitoring**: Live passenger count and boarding status
- **Barbados-Specific**: Modeled after actual ZR van operations

**Sample Output**:

```text
🚐 ZR58 at Terminal (Capacity: 7/11, Wait: 45s/180s)
👥 Passenger boarding... (8/11)
🚀 ZR58 DEPARTING - Vehicle Full! (11/11 passengers)
```

## 📡 Real-Time Features

### WebSocket Telemetry

**Location**: `ws://localhost:5000/device`

Live GPS data transmission:

```json
{
  "deviceId": "ZR58",
  "lat": 13.281045,
  "lon": -59.646329,
  "speed": 45.3,
  "heading": 213.9,
  "route": "R001",
  "timestamp": "2025-09-11T08:43:18Z"
}
```

### Command Line Interface

**Entry Point**: `world/vehicle_simulator/main.py`

Comprehensive CLI with multiple operation modes:

```bash
# Basic operation
python main.py --duration 60 --tick-time 1.0

# Debug mode
python main.py --debug --duration 30

# System status
python main.py --status
python main.py --list-routes
```

**Available Arguments**:

- `--mode depot`: Database-driven operations with Navigator
- `--duration N`: Run for N seconds
- `--tick-time N`: Update interval in seconds
- `--debug`: Detailed logging
- `--list-routes`: Show available routes
- `--status`: System status display

## 🛠️ Technical Stack

### Core Dependencies

```python
# Real-time Communication
websockets>=12.0          # GPS telemetry transmission
python-socketio>=5.11     # Fleet Manager API integration

# Database & ORM  
sqlalchemy>=2.0.0         # Database ORM
psycopg2-binary>=2.9.0    # PostgreSQL driver
geoalchemy2>=0.14.0       # Geospatial extensions

# Geospatial & Physics
shapely>=2.0.0            # Geometric operations
# Custom geodesic mathematics for Earth-accurate calculations

# Security & Networking
paramiko>=4.0.0           # SSH tunneling
sshtunnel>=0.4.0          # Secure database connections

# Web Framework (Future API)
fastapi>=0.110.0          # REST API framework
uvicorn[standard]>=0.29.0 # ASGI server
```

### Development Tools

```python
# Configuration
python-dotenv>=1.0.0      # Environment management

# Testing & Validation
# Custom test suites for engine physics, telemetry pipeline

# Documentation
folium                    # Map visualization
```

## 📁 Directory Structure

```text
vehicle_simulator/
├── world/vehicle_simulator/           # Main application
│   ├── main.py                       # CLI entry point
│   ├── config/                       # Configuration management
│   ├── core/                         # Core business logic
│   │   ├── vehicles_depot.py         # Central fleet orchestrator
│   │   ├── timetable_scheduler.py    # Dual-mode scheduling
│   │   └── standalone_manager.py     # Fleet management
│   ├── providers/                    # Data access layer
│   │   ├── data_provider.py          # Database integration
│   │   ├── api_monitor.py            # Socket.IO monitoring
│   │   └── file_route_provider.py    # Route data management
│   ├── simulators/                   # Simulation engines
│   │   └── simulator.py              # Basic fallback simulator
│   ├── vehicle/                      # Vehicle components
│   │   ├── engine/                   # Physics engine
│   │   │   ├── engine_block.py       # Multi-threaded engine
│   │   │   ├── engine_buffer.py      # Diagnostics buffer
│   │   │   └── sim_speed_model.py    # Speed model loader
│   │   ├── driver/navigation/        # Navigation system
│   │   │   ├── navigator.py          # Geodesic navigation
│   │   │   ├── math.py               # Geospatial mathematics
│   │   │   └── telemetry_buffer.py   # Navigation telemetry
│   │   └── gps_device/               # Telemetry system
│   │       ├── device.py             # GPS device orchestrator
│   │       ├── rxtx_buffer.py        # Transmission buffer
│   │       ├── plugins/              # Telemetry plugins
│   │       └── radio_module/         # WebSocket transmission
│   ├── speed_models/                 # Physics models
│   │   ├── kinematic_speed.py        # Realistic acceleration
│   │   ├── fixed_speed.py            # Constant speed
│   │   └── aggressive_speed.py       # High-performance driving
│   └── utils/                        # Utilities
├── data/                             # Route and geographic data
│   ├── routes/                       # GeoJSON route files
│   ├── stops/                        # Transit stop data
│   └── roads/                        # Road network data
├── docs/                             # Documentation
├── tests/                            # Test suites
│   ├── test_engine_pipeline.py       # Physics validation
│   ├── test_telemetry_pipeline.py    # Telemetry flow tests
│   ├── test_capacity_scheduling.py   # ZR van operations
│   └── test_complete_zr_cycle.py     # End-to-end testing
└── examples/                         # Usage examples
```

## 🧪 Testing & Validation

### Comprehensive Test Suite

**1. Engine Physics Validation** (`test_engine_pipeline.py`)

- Kinematic speed model accuracy
- Distance calculation verification
- Engine buffer threading safety

**2. Telemetry Pipeline Testing** (`test_telemetry_pipeline.py`)

- Navigator → GPS device data flow
- Plugin integration verification
- WebSocket transmission validation

**3. ZR Van Operations** (`test_capacity_scheduling.py`)

- Passenger boarding simulation
- Capacity-based departure triggers
- Real-time status monitoring

**4. End-to-End Validation** (`test_complete_zr_cycle.py`)

- Complete system integration
- Database → Engine → GPS → WebSocket flow
- Multi-vehicle coordination

### Test Results

```text
✅ Engine Physics: PASS - Authentic kinematic calculations
✅ Geodesic Math: PASS - Earth-accurate coordinate interpolation  
✅ Vehicle Simulation: PASS - Realistic movement patterns
✅ GPS Transmission: PASS - WebSocket telemetry confirmed
✅ ZR Van Operations: PASS - Capacity-based scheduling working
```

## 🚀 Current Capabilities

### Fully Operational

- **Real-Time Simulation**: 4 vehicles with authentic physics
- **GPS Telemetry**: WebSocket transmission to external systems
- **Database Integration**: 6 vehicles, 4 drivers from PostgreSQL
- **ZR Van Operations**: Capacity-based passenger scheduling
- **Geodesic Navigation**: Earth-accurate route following
- **API Monitoring**: Socket.IO Fleet Manager integration
- **Multi-Threading**: Concurrent engine, navigation, and GPS operations

### Performance Metrics

- **Tick Rate**: Configurable (default 1.0 seconds)
- **GPS Accuracy**: Geodesic precision for Barbados coordinates
- **Telemetry Rate**: 1Hz real-time transmission
- **Database Response**: ~2-3 second API connection time
- **Vehicle Count**: 4 active (BUS001, BUS002, BUS003, ZR1001)

## 🔄 Data Flow Summary

### Complete System Pipeline

```text
PostgreSQL Database
       ↓
Fleet Manager API (Socket.IO)
       ↓
VehiclesDepot (Fleet Orchestration)
       ↓
┌─────────────┬─────────────┬─────────────┐
│   Engine    │  Navigator  │ GPS Device  │
│ (Physics)   │ (Geodesic)  │ (Telemetry) │
└─────────────┴─────────────┴─────────────┘
       ↓
WebSocket Transmission (ws://localhost:5000)
       ↓
External Monitoring Systems
```

### Real-Time Operations

1. **Database Sync**: Fleet data loaded via API
2. **Physics Simulation**: Kinematic engine calculates movement
3. **Route Following**: Navigator interpolates GPS coordinates
4. **Telemetry Generation**: GPS devices format transmission data
5. **WebSocket Broadcast**: Real-time position streaming
6. **Status Monitoring**: Live system health tracking

## 🎯 Use Cases

### Transit Operations Simulation

- **Fleet Management Testing**: Validate scheduling algorithms
- **Route Optimization**: Analyze vehicle movement patterns
- **Capacity Planning**: ZR van passenger flow analysis
- **Performance Monitoring**: Real-time fleet tracking

### Development & Testing

- **GPS Device Integration**: Test telemetry systems
- **API Development**: Fleet Manager interface validation
- **Algorithm Validation**: Physics and navigation accuracy
- **Load Testing**: Multi-vehicle coordination stress testing

### Research & Analysis

- **Transit Behavior**: Caribbean public transit modeling
- **Geospatial Accuracy**: Geodesic calculation validation
- **Real-Time Systems**: WebSocket performance analysis
- **Database Operations**: Large-scale fleet data management

## 🔮 Future Roadmap

### Immediate Priorities

- **Route Database Seeding**: Add complete Barbados route network
- **Timetable Implementation**: Scheduled departure times
- **Driver Assignment System**: Shift patterns and rotations
- **Enhanced Monitoring**: Real-time dashboard development

### Advanced Features

- **Traffic Simulation**: Dynamic speed adjustments
- **Weather Integration**: Environmental impact modeling
- **Passenger Analytics**: Detailed boarding pattern analysis
- **Mobile Integration**: Real-time passenger information systems

## 📞 Getting Started

### Quick Start

```bash
# Clone and setup
git clone <repository>
cd vehicle_simulator
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with database credentials

# Run basic simulation
python world/vehicle_simulator/main.py --duration 60

# Monitor telemetry (separate terminal)
# WebSocket server should be running on localhost:5000

# Debug mode
python world/vehicle_simulator/main.py --debug --duration 30
```

### System Requirements

- **Python**: 3.11+
- **Database**: PostgreSQL with PostGIS
- **Network**: Access to Fleet Manager API
- **Memory**: 512MB+ for multi-vehicle operations
- **Platform**: Cross-platform (Windows, Linux, macOS)

## 📋 Summary

The **Vehicle Simulator** represents a sophisticated, production-ready transit simulation platform with authentic physics modeling, real-time telemetry transmission, and comprehensive database integration. Its unique ZR van capacity-based scheduling system provides accurate modeling of Caribbean public transit operations, while the modular plugin architecture ensures extensibility for future enhancements.

**Key Strengths**:

- ✅ **Authentic Physics**: Real kinematic calculations with geodesic accuracy
- ✅ **Real-Time Operations**: WebSocket telemetry with 1Hz transmission
- ✅ **Database Integration**: PostgreSQL-backed fleet management
- ✅ **Caribbean Focus**: ZR van passenger boarding simulation
- ✅ **Extensible Architecture**: Plugin-based telemetry system
- ✅ **Production Ready**: Comprehensive CLI with debug capabilities

The system successfully bridges the gap between theoretical transit modeling and practical real-world operations, providing a robust foundation for both development and operational deployment in the Arknet Transit ecosystem.
