# Vehicle Simulator Project

A comprehensive vehicle simulation system for the Arknet Transit project.

## Project Structure

```text
vehicle_simulator/
├── api/                    # 🌐 FastAPI Remote Interface
│   ├── main.py            # Main FastAPI application
│   ├── fleet_management/   # Fleet data upload & management
│   │   ├── routes.py      # Upload routes, vehicles, timetables
│   │   ├── services.py    # Business logic
│   │   └── models.py      # Data models
│   ├── simulator_control/ # Simulation control & monitoring  
│   │   ├── routes.py      # Start/stop simulation
│   │   ├── services.py    # Simulation management
│   │   └── models.py      # Status models
│   └── requirements.txt   # API dependencies
├── src/                    # Core application source code
│   ├── config_loader.py    # Configuration management
│   ├── database_*.py       # Database utilities and diagnostics
│   ├── gps_*.py           # GPS server and monitoring
│   ├── route_*.py         # Route conversion and visualization
│   ├── sim_*.py           # Simulation models and logic
│   └── world_*.py         # World simulation components
├── simulators/             # Vehicle simulator implementations
│   ├── database_vehicles_simulator.py
│   ├── enhanced_vehicle_simulator.py
│   ├── gps_device_simulator.py
│   ├── simple_vehicle_simulator.py
│   └── world_vehicles_simulator.py
├── tests/                  # Test files
│   ├── test_db_connection.py
│   ├── test_gps_device.py
│   └── ...
├── config/                 # Configuration files
│   ├── alembic.ini
│   ├── config.ini
│   └── database.py
├── docs/                   # Documentation
│   ├── Vehicle_Simulator_Manual_and_Project_Summary.docx
│   ├── Telemetry Pipeline Doc.docx
│   └── COMMIT_SUMMARY.md
├── logs/                   # Log files
├── uploads/                # 📁 Uploaded files storage
│   ├── routes/            # GeoJSON route files by country
│   ├── vehicles/          # Vehicle JSON files by country
│   └── timetables/        # Timetable JSON files by country
├── data/                   # Data files (routes, stops, etc.)
├── migrations/             # Database migrations
├── models/                 # Data models
├── scripts/                # Utility scripts
├── utils/                  # Utility modules
├── world/                  # World simulation components
├── common/                 # Common utilities
└── unused/                 # Deprecated files

```

## Getting Started

### Local Simulation
1. Install dependencies: `pip install -r requirements.txt`
2. Configure the system using files in the `config/` directory
3. Run simulators from the `simulators/` directory
4. Execute tests from the `tests/` directory

### Remote API Interface  
1. Install API dependencies: `pip install -r api/requirements.txt`
2. Start the API server: `python start_api.py`
3. Access the dashboard at: http://localhost:8000
4. Use the API documentation at: http://localhost:8000/docs

## API Features

### 🗂️ Fleet Management Wing
- **Upload Routes**: POST `/fleet/upload/routes` - Upload GeoJSON route files by country
- **Upload Vehicles**: POST `/fleet/upload/vehicles` - Upload vehicle JSON files by country  
- **Upload Timetables**: POST `/fleet/upload/timetables` - Upload timetable JSON files by country
- **Manage Countries**: GET `/fleet/countries` - List all countries with fleet data
- **View Data**: GET `/fleet/countries/{country}/routes` - View country-specific data

### 🎮 Simulator Control Wing
- **Start Simulation**: POST `/simulator/start` - Start vehicle simulation remotely
- **Stop Simulation**: POST `/simulator/stop` - Stop running simulation
- **Monitor Status**: GET `/simulator/status` - Get real-time simulation status
- **Vehicle Control**: GET `/simulator/vehicles` - List active vehicles
- **Performance Metrics**: GET `/simulator/metrics` - Get performance statistics

## Main Entry Points

- `world_vehicles_simulator.py` - **PRIMARY ENTRY POINT** - Main vehicle simulation system
- `__main__.py` - Alternative application entry point
- `simulators/` - Individual vehicle simulators
- `src/` - Core application logic and utilities
