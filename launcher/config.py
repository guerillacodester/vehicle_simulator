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
    enable_manifest: bool
    enable_vehicle_simulator: bool
    enable_commuter_simulator: bool


@dataclass
class InfrastructureConfig:
    """Infrastructure ports and URLs."""
    strapi_url: str
    strapi_port: int
    gpscentcom_port: int
    geospatial_port: int
    manifest_port: int


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
        
        self.config.read(config_path)
    
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
            enable_manifest=launcher.getboolean('enable_manifest', True),
            enable_vehicle_simulator=launcher.getboolean('enable_vehicle_simulator', False),
            enable_commuter_simulator=launcher.getboolean('enable_commuter_simulator', False)
        )
    
    def get_infrastructure_config(self) -> InfrastructureConfig:
        """Get infrastructure configuration."""
        infra = self.config['infrastructure']
        
        return InfrastructureConfig(
            strapi_url=infra.get('strapi_url', 'http://localhost:1337'),
            strapi_port=infra.getint('strapi_port', 1337),
            gpscentcom_port=infra.getint('gpscentcom_port', 5000),
            geospatial_port=infra.getint('geospatial_port', 6000),
            manifest_port=infra.getint('manifest_port', 4000)
        )
