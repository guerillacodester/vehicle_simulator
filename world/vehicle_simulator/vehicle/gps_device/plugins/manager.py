#!/usr/bin/env python3
"""
Plugin Manager
--------------
Manages dynamic loading, registration, and lifecycle of telemetry plugins.
Provides plugin discovery and source switching capabilities.
"""

import importlib
import logging
from typing import Dict, Type, Optional, List, Any
from .interface import ITelemetryPlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages telemetry plugins for GPS device.
    
    Handles plugin discovery, registration, loading, and lifecycle management.
    Supports runtime source switching for development to production transitions.
    """
    
    def __init__(self):
        self.registered_plugins: Dict[str, Type[ITelemetryPlugin]] = {}
        self.active_plugin: Optional[ITelemetryPlugin] = None
        self._discover_builtin_plugins()
    
    def _discover_builtin_plugins(self):
        """Auto-discover and register built-in plugins."""
        try:
            # Import built-in plugins
            from .simulation_plugin import SimulationTelemetryPlugin
            from .esp32_plugin import ESP32TelemetryPlugin
            from .file_replay_plugin import FileReplayTelemetryPlugin
            
            self.register_plugin(SimulationTelemetryPlugin)
            self.register_plugin(ESP32TelemetryPlugin)
            self.register_plugin(FileReplayTelemetryPlugin)
            
            logger.info("Built-in plugins discovered and registered")
            
        except ImportError as e:
            logger.warning(f"Some built-in plugins not available: {e}")
    
    def register_plugin(self, plugin_class: Type[ITelemetryPlugin]):
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class implementing ITelemetryPlugin
        """
        try:
            # Validate plugin implements interface
            if not issubclass(plugin_class, ITelemetryPlugin):
                raise ValueError(f"Plugin {plugin_class.__name__} does not implement ITelemetryPlugin")
            
            # Get plugin identifier
            plugin_instance = plugin_class()
            source_type = plugin_instance.source_type
            
            self.registered_plugins[source_type] = plugin_class
            logger.info(f"Registered plugin: {source_type} v{plugin_instance.plugin_version}")
            
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")
    
    def list_available_plugins(self) -> List[str]:
        """
        Get list of available plugin source types.
        
        Returns:
            List[str]: Available plugin identifiers
        """
        return list(self.registered_plugins.keys())
    
    def load_plugin(self, source_type: str, config: Dict[str, Any]) -> bool:
        """
        Load and initialize a specific plugin.
        
        Args:
            source_type: Plugin identifier (e.g., "simulation", "esp32_hardware")
            config: Plugin-specific configuration
            
        Returns:
            bool: True if plugin loaded successfully, False otherwise
        """
        try:
            # Unload current plugin if active
            if self.active_plugin:
                self.unload_current_plugin()
            
            # Check if plugin is registered
            if source_type not in self.registered_plugins:
                logger.error(f"Plugin '{source_type}' not registered. Available: {self.list_available_plugins()}")
                return False
            
            # Instantiate and initialize plugin
            plugin_class = self.registered_plugins[source_type]
            plugin_instance = plugin_class()
            
            if plugin_instance.initialize(config):
                self.active_plugin = plugin_instance
                logger.info(f"Successfully loaded plugin: {source_type}")
                return True
            else:
                logger.error(f"Plugin '{source_type}' initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load plugin '{source_type}': {e}")
            return False
    
    def unload_current_plugin(self):
        """Unload the currently active plugin."""
        if self.active_plugin:
            try:
                self.active_plugin.stop_data_stream()
                source_type = self.active_plugin.source_type
                self.active_plugin = None
                logger.info(f"Unloaded plugin: {source_type}")
            except Exception as e:
                logger.warning(f"Error unloading plugin: {e}")
    
    def start_data_stream(self) -> bool:
        """
        Start data stream from active plugin.
        
        Returns:
            bool: True if stream started, False otherwise
        """
        if self.active_plugin:
            return self.active_plugin.start_data_stream()
        return False
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get telemetry data from active plugin.
        
        Returns:
            Optional[Dict]: Standardized telemetry data or None
        """
        if self.active_plugin and self.active_plugin.is_connected():
            return self.active_plugin.get_data()
        return None
    
    def is_connected(self) -> bool:
        """
        Check if active plugin is connected and operational.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.active_plugin and self.active_plugin.is_connected()
    
    def get_active_plugin_info(self) -> Optional[Dict[str, str]]:
        """
        Get information about the currently active plugin.
        
        Returns:
            Optional[Dict]: Plugin info or None if no active plugin
        """
        if self.active_plugin:
            return {
                "source_type": self.active_plugin.source_type,
                "version": self.active_plugin.plugin_version,
                "connected": self.active_plugin.is_connected()
            }
        return None
