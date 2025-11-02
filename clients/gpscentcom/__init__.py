"""
GPS Telemetry Client Library
=============================

Interface-agnostic Python library for consuming GPS telemetry from GPSCentCom server.

Can be used by:
- CLI applications (Python)
- GUI applications (Tkinter, Qt, .NET via pythonnet)
- Web dashboards (Flask, FastAPI)
- Monitoring tools
- Data pipelines

Core Components:
    - GPSTelemetryClient: Main client for HTTP/SSE operations
    - Vehicle: Pydantic model for telemetry data
    - TelemetryObserver: Observer pattern for event-driven updates

Usage:
    from gps_telemetry_client import GPSTelemetryClient, Vehicle
    
    client = GPSTelemetryClient()  # Auto-loads from config.ini
    vehicles = client.get_all_devices()
    for vehicle in vehicles:
        print(f"{vehicle.deviceId}: {vehicle.lat}, {vehicle.lon}")
"""

from .client import GPSTelemetryClient
from .models import Vehicle, PersonName
from .observers import TelemetryObserver, CallbackObserver

__version__ = "1.0.0"
__all__ = [
    "GPSTelemetryClient",
    "Vehicle",
    "PersonName",
    "TelemetryObserver",
    "CallbackObserver",
]
