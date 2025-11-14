#!/usr/bin/env python3
"""
Logging Configuration for Vehicle Simulator
--------------------------------------------
Configuration management for the logging system.
Integrates with the main config system and provides logging-specific settings.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum

from arknet_transit_simulator.config.config_loader import ConfigLoader
from arknet_transit_simulator.utils.logging_system import LogLevel


class LoggingConfig:
    """Configuration manager for logging system."""
    
    DEFAULT_CONFIG = {
        'logging': {
            'level': 'INFO',
            'verbose': False,
            'console': {
                'enabled': True,
                'level': 'INFO'
            },
            'file': {
                'enabled': True,
                'directory': 'logs',
                'main_file': 'vehicle_simulator.log',
                'error_file': 'vehicle_simulator_errors.log',
                'max_size_mb': 10,
                'backup_count': 5
            },
            'structured': {
                'enabled': False,
                'format': 'json'
            },
            'components': {
                'main': 'INFO',
                'depot': 'INFO',
                'vehicle': 'INFO',
                'gps': 'WARNING',
                'engine': 'WARNING',
                'navigation': 'INFO',
                'telemetry': 'INFO',
                'api': 'INFO',
                'database': 'WARNING',
                'simulator': 'INFO',
                'fleet': 'INFO',
                'dispatcher': 'INFO'
            }
        }
    }
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """
        Initialize logging configuration.
        
        Args:
            config_loader: Optional config loader instance
        """
        self.config_loader = config_loader or ConfigLoader()
        self._logging_config = None
        self._load_config()
    
    def _load_config(self):
        """Load logging configuration from config system."""
        try:
            # Get full configuration
            full_config = self.config_loader.get_all_config()
            
            # Extract logging section or use defaults
            self._logging_config = full_config.get('logging', self.DEFAULT_CONFIG['logging'])
            
            # Ensure all required keys exist
            self._validate_and_fill_defaults()
            
        except Exception as e:
            print(f"Warning: Failed to load logging config, using defaults: {e}")
            self._logging_config = self.DEFAULT_CONFIG['logging']
    
    def _validate_and_fill_defaults(self):
        """Ensure all required configuration keys exist."""
        default_logging = self.DEFAULT_CONFIG['logging']
        
        # Fill missing top-level keys
        for key, default_value in default_logging.items():
            if key not in self._logging_config:
                self._logging_config[key] = default_value
        
        # Fill missing nested keys
        for section in ['console', 'file', 'structured', 'components']:
            if section not in self._logging_config:
                self._logging_config[section] = default_logging[section]
            else:
                # Fill missing nested keys
                for key, default_value in default_logging[section].items():
                    if key not in self._logging_config[section]:
                        self._logging_config[section][key] = default_value
    
    def get_log_level(self) -> LogLevel:
        """Get the main log level."""
        level_str = self._logging_config.get('level', 'INFO').upper()
        try:
            return LogLevel[level_str]
        except KeyError:
            return LogLevel.INFO
    
    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled."""
        return self._logging_config.get('verbose', False)
    
    def is_console_enabled(self) -> bool:
        """Check if console logging is enabled."""
        return self._logging_config.get('console', {}).get('enabled', True)
    
    def get_console_level(self) -> LogLevel:
        """Get console logging level."""
        level_str = self._logging_config.get('console', {}).get('level', 'INFO').upper()
        try:
            return LogLevel[level_str]
        except KeyError:
            return LogLevel.INFO
    
    def is_file_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return self._logging_config.get('file', {}).get('enabled', True)
    
    def get_log_directory(self) -> str:
        """Get the log directory path."""
        return self._logging_config.get('file', {}).get('directory', 'logs')
    
    def get_main_log_file(self) -> str:
        """Get the main log file name."""
        return self._logging_config.get('file', {}).get('main_file', 'vehicle_simulator.log')
    
    def get_error_log_file(self) -> str:
        """Get the error log file name."""
        return self._logging_config.get('file', {}).get('error_file', 'vehicle_simulator_errors.log')
    
    def get_max_file_size_mb(self) -> int:
        """Get the maximum log file size in MB."""
        return self._logging_config.get('file', {}).get('max_size_mb', 10)
    
    def get_backup_count(self) -> int:
        """Get the number of backup files to keep."""
        return self._logging_config.get('file', {}).get('backup_count', 5)
    
    def is_structured_enabled(self) -> bool:
        """Check if structured logging is enabled."""
        return self._logging_config.get('structured', {}).get('enabled', False)
    
    def get_structured_format(self) -> str:
        """Get the structured logging format."""
        return self._logging_config.get('structured', {}).get('format', 'json')
    
    def get_component_level(self, component: str) -> LogLevel:
        """
        Get the log level for a specific component.
        
        Args:
            component: Component name
            
        Returns:
            Log level for the component
        """
        level_str = self._logging_config.get('components', {}).get(component, 'INFO').upper()
        try:
            return LogLevel[level_str]
        except KeyError:
            return LogLevel.INFO
    
    def get_all_component_levels(self) -> Dict[str, LogLevel]:
        """Get log levels for all components."""
        components = self._logging_config.get('components', {})
        return {
            component: self.get_component_level(component)
            for component in components.keys()
        }
    
    def update_level(self, level: LogLevel):
        """Update the main log level."""
        self._logging_config['level'] = level.name
    
    def update_verbose(self, verbose: bool):
        """Update verbose mode setting."""
        self._logging_config['verbose'] = verbose
    
    def update_component_level(self, component: str, level: LogLevel):
        """Update log level for a specific component."""
        if 'components' not in self._logging_config:
            self._logging_config['components'] = {}
        self._logging_config['components'][component] = level.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Get the full logging configuration as a dictionary."""
        return self._logging_config.copy()
    
    def print_config(self):
        """Print the current logging configuration."""
        print("Current Logging Configuration:")
        print(f"  Level: {self.get_log_level().name}")
        print(f"  Verbose: {self.is_verbose()}")
        print(f"  Console: {self.is_console_enabled()} (level: {self.get_console_level().name})")
        print(f"  File: {self.is_file_enabled()} (dir: {self.get_log_directory()})")
        print(f"  Structured: {self.is_structured_enabled()}")
        print("  Component Levels:")
        for component, level in self.get_all_component_levels().items():
            print(f"    {component}: {level.name}")


# Example usage
if __name__ == "__main__":
    config = LoggingConfig()
    config.print_config()