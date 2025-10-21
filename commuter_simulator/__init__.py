"""
Commuter Simulator - Modern Architecture
=========================================

A redesigned passenger spawning and management system with clear subsystem separation.

Structure:
----------
commuter_simulator/
├── __init__.py              # Package initialization
├── main.py                  # Main entry point
├── config/                  # Configuration management
├── core/                    # Core business logic
│   ├── models/             # Data models (Passenger, Depot, Route)
│   ├── repositories/       # Data access layer (Strapi API)
│   └── domain/             # Domain services (spawn algorithms)
├── services/               # Application services
│   ├── depot_reservoir/   # Depot-based spawning service
│   ├── route_reservoir/   # Route-based spawning service
│   └── socketio/          # Socket.IO communication layer
├── infrastructure/         # External integrations
│   ├── database/          # Database clients (Strapi)
│   ├── geospatial/        # GIS utilities (geodesic, zones)
│   └── events/            # Event bus / message queue
└── utils/                  # Shared utilities
    ├── logging/           # Logging configuration
    └── validation/        # Data validation
"""

__version__ = "2.0.0"
__author__ = "ArkNet Transit Systems"
