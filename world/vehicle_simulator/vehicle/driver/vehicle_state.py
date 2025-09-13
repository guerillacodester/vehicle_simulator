"""
Vehicle State Module

Provides the VehicleState class used for GPS plugin data transmission.
Contains all vehicle telemetry data including position, speed, heading, 
driver information, and engine status.
"""

from datetime import datetime, timezone
from typing import Optional


class VehicleState:
    """Vehicle state object for GPS plugin system."""
    
    def __init__(self, driver_id: str, driver_name: str, vehicle_id: str, route_name: str = ""):
        """
        Initialize vehicle state.
        
        Args:
            driver_id: Driver license ID (e.g., "LIC002")
            driver_name: Driver's human-readable name (e.g., "Jane Doe")
            vehicle_id: Vehicle registration (e.g., "ZR101")
            route_name: Route identifier (e.g., "1A")
        """
        self.lat = 0.0
        self.lng = 0.0
        self.speed = 0.0
        self.heading = 0.0
        self.route_id = route_name
        self.driver_id = driver_id
        self.driver_name = driver_name
        self.vehicle_reg = vehicle_id
        self.engine_status = "OFF"
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def update_position(self, lat: float, lon: float, speed: float, heading: float):
        """
        Update vehicle position and motion data.
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            speed: Speed in km/h
            heading: Heading/bearing in degrees (0-360)
        """
        self.lat = lat
        self.lng = lon
        self.speed = speed
        self.heading = heading
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def set_engine_status(self, status: str):
        """
        Set engine status.
        
        Args:
            status: Engine status ("ON" or "OFF")
        """
        self.engine_status = status
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def set_position(self, lat: float, lon: float):
        """
        Set position without affecting speed/heading.
        
        Args:
            lat: Latitude in decimal degrees  
            lon: Longitude in decimal degrees
        """
        self.lat = lat
        self.lng = lon
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def __repr__(self):
        return (f"VehicleState(driver={self.driver_name}, vehicle={self.vehicle_reg}, "
                f"position=({self.lat:.6f}, {self.lng:.6f}), speed={self.speed}, "
                f"engine={self.engine_status})")