# Vehicle Simulator Project

A comprehensive vehicle simulation system for the Arknet Transit project.

## Project Structure

```text
vehicle_simulator/
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

1. Install dependencies: `pip install -r requirements.txt`
2. Configure the system using files in the `config/` directory
3. Run simulators from the `simulators/` directory
4. Execute tests from the `tests/` directory

## Main Entry Points

- `world_vehicles_simulator.py` - **PRIMARY ENTRY POINT** - Main vehicle simulation system
- `__main__.py` - Alternative application entry point
- `simulators/` - Individual vehicle simulators
- `src/` - Core application logic and utilities
