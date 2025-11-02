"""
Configuration management for the launcher.

Handles loading and validation of launcher configuration from config.ini.
"""

import configparser
from pathlib import Path
from dataclasses import dataclass
from typing import Dict


@dataclass
class LauncherConfig:
    """Launcher timing and behavior configuration."""
    monitor_port: int
    strapi_startup_wait: int
    gpscentcom_startup_wait: int
    simulator_delay: int
    service_startup_wait: int
    
    # Subsystem enable flags
    enable_gpscentcom: bool
    enable_geospatial: bool
    enable_vehicle_simulator: bool
    enable_commuter_service: bool
    
    # Console spawning flags
    spawn_console_strapi: bool
    spawn_console_gpscentcom: bool
    spawn_console_geospatial: bool
    spawn_console_vehicle_simulator: bool
    spawn_console_commuter_service: bool


@dataclass
class InfrastructureConfig:
    """Infrastructure ports and URLs."""
    strapi_url: str
    strapi_port: int
    gpscentcom_port: int
    geospatial_port: int
    commuter_service_port: int


class ConfigurationManager:
    """
    Manages launcher configuration.
    
    Single Responsibility: Configuration loading and validation.
    """
    
    def __init__(self, config_path: Path):
        """Initialize configuration manager."""
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Read with UTF-8 encoding to handle special characters
        self.config.read(config_path, encoding='utf-8')
    
    def get_launcher_config(self) -> LauncherConfig:
        """Get launcher-specific configuration."""
        launcher = self.config['launcher']
        
        return LauncherConfig(
            monitor_port=launcher.getint('monitor_port', 8000),
            strapi_startup_wait=launcher.getint('strapi_startup_wait', 15),
            gpscentcom_startup_wait=launcher.getint('gpscentcom_startup_wait', 10),
            simulator_delay=launcher.getint('simulator_delay', 5),
            service_startup_wait=launcher.getint('service_startup_wait', 8),
            enable_gpscentcom=launcher.getboolean('enable_gpscentcom', True),
            enable_geospatial=launcher.getboolean('enable_geospatial', True),
            enable_vehicle_simulator=launcher.getboolean('enable_vehicle_simulator', False),
            enable_commuter_service=launcher.getboolean('enable_commuter_service', False),
            spawn_console_strapi=launcher.getboolean('spawn_console_strapi', False),
            spawn_console_gpscentcom=launcher.getboolean('spawn_console_gpscentcom', False),
            spawn_console_geospatial=launcher.getboolean('spawn_console_geospatial', False),
            spawn_console_vehicle_simulator=launcher.getboolean('spawn_console_vehicle_simulator', False),
            spawn_console_commuter_service=launcher.getboolean('spawn_console_commuter_service', False)
        )
    
    def get_infrastructure_config(self) -> InfrastructureConfig:
        """Get infrastructure configuration."""
        infra = self.config['infrastructure']
        
        return InfrastructureConfig(
            strapi_url=infra.get('strapi_url', 'http://localhost:1337'),
            strapi_port=infra.getint('strapi_port', 1337),
            gpscentcom_port=infra.getint('gpscentcom_port', 5000),
            geospatial_port=infra.getint('geospatial_port', 6000),
            commuter_service_port=infra.getint('commuter_service_port', 4000)
        )
