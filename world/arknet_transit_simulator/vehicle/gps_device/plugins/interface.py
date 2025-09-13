#!/usr/bin/env python3
"""
ITelemetryPlugin Interface
--------------------------
100% agnostic interface for telemetry data sources.
Supports simulation, ESP32 hardware, file replay, and any future sources.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class ITelemetryPlugin(ABC):
    """
    Plugin interface for telemetry data sources.
    
    This interface ensures complete decoupling between GPS device firmware
    and data sources, allowing seamless swapping between:
    - Simulation data
    - Real ESP32 hardware with secure boot
    - File replay
    - Network streams
    - Any future telemetry sources
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin-specific configuration dictionary
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod 
    def start_data_stream(self) -> bool:
        """
        Start receiving data from the source.
        
        Returns:
            bool: True if stream started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get standardized telemetry data.
        
        Returns:
            Optional[Dict]: Telemetry data in standard format or None if unavailable
            
        Standard format:
            {
                "lat": float,           # GPS latitude
                "lon": float,           # GPS longitude  
                "speed": float,         # Speed in km/h
                "heading": float,       # Bearing/heading in degrees
                "timestamp": str,       # ISO8601 UTC timestamp
                "device_id": str,       # Device identifier
                "extras": Dict          # Optional additional data
            }
        """
        pass
    
    @abstractmethod
    def stop_data_stream(self) -> None:
        """Stop data stream and cleanup resources."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if plugin is connected and operational.
        
        Returns:
            bool: True if connected and data available, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """
        Unique source type identifier.
        
        Returns:
            str: Plugin identifier (e.g., "simulation", "esp32_hardware", "file_replay")
        """
        pass
    
    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """
        Plugin version for compatibility checking.
        
        Returns:
            str: Semantic version string (e.g., "1.0.0")
        """
        pass
