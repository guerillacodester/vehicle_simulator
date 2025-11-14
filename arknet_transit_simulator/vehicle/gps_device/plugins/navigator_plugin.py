#!/usr/bin/env python3
"""
Navigator Telemetry Plugin
--------------------------
Reads real telemetry data from Navigator's TelemetryBuffer for realistic
route-following vehicle simulation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)


class NavigatorTelemetryPlugin(ITelemetryPlugin):
    """
    Navigator plugin for GPS device.
    
    Reads telemetry data from Navigator's TelemetryBuffer to provide
    realistic route-following vehicle movement data.
    """
    
    def __init__(self):
        self.navigator = None
        self.device_id = None
        self._connected = False
        self._config = {}
    
    @property
    def source_type(self) -> str:
        return "navigator_telemetry"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize navigator plugin.
        
        Config format:
        {
            "navigator": Navigator instance,
            "device_id": str,
            "update_interval": float (seconds, default 1.0)
        }
        """
        try:
            self.device_id = config.get("device_id", "NAVIGATOR_001")
            self.navigator = config.get("navigator")
            self._config = config
            
            if not self.navigator:
                logger.error("Navigator instance required for navigator plugin")
                return False
                
            if not hasattr(self.navigator, 'telemetry_buffer'):
                logger.error("Navigator must have telemetry_buffer attribute")
                return False
            
            logger.info(f"Navigator plugin initialized for device: {self.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Navigator plugin initialization failed: {e}")
            return False
    
    def start_data_stream(self) -> bool:
        """Start plugin-controlled Navigator integration."""
        try:
            if not self.navigator:
                logger.error("No navigator available")
                return False
                
            self._connected = True
            logger.info(f"Navigator plugin-controlled integration started for {self.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start navigator plugin integration: {e}")
            return False
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get telemetry data from Navigator's buffer (VehiclesDepot orchestrates Navigator).
        
        Returns telemetry in standard GPS device format.
        """
        if not self._connected or not self.navigator:
            return None
        
        try:
            # Read from Navigator's telemetry buffer (Navigator worker writes to this)
            telemetry_entry = self.navigator.telemetry_buffer.read()
            
            if not telemetry_entry:
                return None
            
            # Convert Navigator telemetry to standard GPS format
            return {
                "lat": float(telemetry_entry.get("lat", 0.0)),
                "lon": float(telemetry_entry.get("lon", 0.0)),
                "speed": float(telemetry_entry.get("speed", 0.0)),
                "heading": float(telemetry_entry.get("bearing", 0.0)),  # Navigator uses 'bearing'
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "device_id": self.device_id,
                "route": telemetry_entry.get("route", "NAVIGATOR_ROUTE"),
                "vehicle_reg": self.device_id,
                "driver_id": f"drv-{self.device_id}",
                "driver_name": {"first": "Navigator", "last": self.device_id},
                "extras": {
                    "source": "navigator_telemetry",
                    "plugin_version": self.plugin_version,
                    "engine_rpm": telemetry_entry.get("engine_rpm", 0),
                    "engine_load": telemetry_entry.get("engine_load", 0.0),
                    "navigator_mode": getattr(self.navigator, 'mode', 'unknown')
                }
            }
            
        except Exception as e:
            logger.warning(f"Navigator data retrieval failed: {e}")
            return None
    
    def stop_data_stream(self) -> None:
        """Stop reading from Navigator."""
        self._connected = False
        logger.info(f"Navigator data stream stopped for {self.device_id}")
    
    def is_connected(self) -> bool:
        """Check if Navigator is available and active."""
        return (
            self._connected and 
            self.navigator is not None and
            hasattr(self.navigator, 'telemetry_buffer')
        )
