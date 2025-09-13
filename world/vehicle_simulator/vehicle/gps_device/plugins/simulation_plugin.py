#!/usr/bin/env python3
"""
Simulation Telemetry Plugin
---------------------------
Plugin for simulated telemetry data sources.
Used for development, testing, and vehicle simulation scenarios.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)


class SimulationTelemetryPlugin(ITelemetryPlugin):
    """
    Simulation plugin for GPS device.
    
    Provides telemetry data from vehicle simulation, navigator,
    or other simulated sources for development and testing.
    """
    
    def __init__(self):
        self.vehicle_state = None
        self.route_data = None
        self.device_id = None
        self._connected = False
        self._config = {}
    
    @property
    def source_type(self) -> str:
        return "simulation"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize simulation plugin.
        
        Config format:
        {
            "vehicle_state": VehicleState object or dict (optional - can be set later),
            "device_id": str,
            "route_data": optional route information,
            "update_interval": float (seconds, default 1.0)
        }
        """
        try:
            self._config = config
            self.vehicle_state = config.get("vehicle_state")
            self.device_id = config.get("device_id", "SIM001")
            self.route_data = config.get("route_data")
            self.update_interval = config.get("update_interval", 1.0)
            
            # Vehicle state can be optional for delayed initialization
            if self.vehicle_state is None:
                logger.info("Simulation plugin initialized without vehicle_state (can be set later)")
            else:
                logger.info(f"Simulation plugin initialized with vehicle_state for device: {self.device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Simulation plugin initialization failed: {e}")
            return False
    
    def set_vehicle_state(self, vehicle_state):
        """Set vehicle state after plugin initialization."""
        self.vehicle_state = vehicle_state
        logger.info(f"Vehicle state set for simulation plugin: {self.device_id}")
    
    def start_data_stream(self) -> bool:
        """Start simulation data stream."""
        try:
            if self.vehicle_state is None:
                logger.debug(f"GPS device {self.device_id} starting without initial position data")
                # Still return True to allow the plugin to start, it will just return None data
            
            self._connected = True
            logger.info(f"Simulation data stream started for {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start simulation stream: {e}")
            return False
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current simulated telemetry data.
        
        Returns telemetry in standard GPS device format.
        """
        if not self._connected or not self.vehicle_state:
            return None
        
        try:
            # Handle both object and dict vehicle state
            if hasattr(self.vehicle_state, 'lat'):
                # Object-style access
                lat = getattr(self.vehicle_state, 'lat', 0.0)
                lon = getattr(self.vehicle_state, 'lng', 0.0)  # Note: lng not lon
                speed = getattr(self.vehicle_state, 'speed', 0.0)
                heading = getattr(self.vehicle_state, 'heading', 0.0)
                route_id = getattr(self.vehicle_state, 'route_id', 'SIM_ROUTE')
            else:
                # Dict-style access
                lat = self.vehicle_state.get('lat', 0.0)
                lon = self.vehicle_state.get('lon', 0.0)
                speed = self.vehicle_state.get('speed', 0.0)
                heading = self.vehicle_state.get('heading', 0.0)
                route_id = self.vehicle_state.get('route_id', 'SIM_ROUTE')
            
            # Get driver information from vehicle state
            if hasattr(self.vehicle_state, 'driver_id'):
                driver_id = getattr(self.vehicle_state, 'driver_id', f"drv-{self.device_id}")
                driver_name_full = getattr(self.vehicle_state, 'driver_name', f"Sim {self.device_id}")
                # Check both vehicle_reg and vehicle_id for compatibility
                vehicle_reg = getattr(self.vehicle_state, 'vehicle_reg', 
                                    getattr(self.vehicle_state, 'vehicle_id', self.device_id))
            else:
                driver_id = self.vehicle_state.get('driver_id', f"drv-{self.device_id}")
                driver_name_full = self.vehicle_state.get('driver_name', f"Sim {self.device_id}")
                # Check both vehicle_reg and vehicle_id for compatibility
                vehicle_reg = self.vehicle_state.get('vehicle_reg', 
                                                   self.vehicle_state.get('vehicle_id', self.device_id))
            
            # Parse driver name into first/last
            if isinstance(driver_name_full, str):
                name_parts = driver_name_full.split()
                driver_first = name_parts[0] if name_parts else "Sim"
                driver_last = name_parts[-1] if len(name_parts) > 1 else self.device_id
            else:
                driver_first = "Sim"
                driver_last = self.device_id
            
            # Return standardized telemetry format
            return {
                "lat": float(lat),
                "lon": float(lon),
                "speed": float(speed),
                "heading": float(heading),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "device_id": self.device_id,
                "route": str(route_id),
                "vehicle_reg": vehicle_reg,
                "driver_id": driver_id,
                "driver_name": {"first": driver_first, "last": driver_last},
                "extras": self._build_extras(self.vehicle_state)
            }
            
        except Exception as e:
            logger.warning(f"Simulation data generation failed: {e}")
            return None
    
    def stop_data_stream(self) -> None:
        """Stop simulation data stream."""
        self._connected = False
        logger.info(f"Simulation data stream stopped for {self.device_id}")

    def _build_extras(self, vehicle_state) -> Dict[str, Any]:
        base = {
            "source": "simulation",
            "plugin_version": self.plugin_version
        }
        try:
            if vehicle_state and hasattr(vehicle_state, 'accel'):
                physics_block = {
                    "accel": getattr(vehicle_state, 'accel', None),
                    "phase": getattr(vehicle_state, 'motion_phase', None),
                    "progress": getattr(vehicle_state, 'route_progress', None),
                    "segment_index": getattr(vehicle_state, 'segment_index', None)
                }
                base["physics"] = physics_block
        except Exception:
            pass
        return base
    
    def is_connected(self) -> bool:
        """Check if simulation is active."""
        return self._connected and self.vehicle_state is not None
