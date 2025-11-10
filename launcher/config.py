"""
Configuration management for the launcher.

Handles loading and validation of launcher configuration from config.ini.
"""

import configparser
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class ServiceConfig:
    """Configuration for a single service plugin."""
    name: str
    enabled: bool
    port: Optional[int]
    url: Optional[str]
    health_url: Optional[str]
    spawn_console: bool
    startup_wait: int
    category: str
    display_name: str
    description: str
    icon: str
    dependencies: List[str]
    extra_config: Dict[str, str]  # Service-specific settings


@dataclass
class LauncherConfig:
    """Global launcher configuration."""
    api_port: int
    cors_origins: List[str]
    monitor_port: int
    startup_wait_default: int
    strapi_startup_wait: int
    simulator_delay: int


@dataclass
class InfrastructureConfig:
    """Global infrastructure settings."""
    database_host: str
    database_port: int


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
        """Get global launcher configuration."""
        launcher = self.config['launcher']
        
        # Parse CORS origins
        cors_origins_str = launcher.get('cors_origins', 'http://localhost:3000')
        cors_origins = [origin.strip() for origin in cors_origins_str.split(',')]
        
        return LauncherConfig(
            api_port=launcher.getint('api_port', 7000),
            cors_origins=cors_origins,
            monitor_port=launcher.getint('monitor_port', 8000),
            startup_wait_default=launcher.getint('startup_wait_default', 10),
            strapi_startup_wait=launcher.getint('strapi_startup_wait', 15),
            simulator_delay=launcher.getint('simulator_delay', 5)
        )
    
    def get_infrastructure_config(self) -> InfrastructureConfig:
        """Get global infrastructure configuration."""
        infra = self.config['infrastructure']
        
        return InfrastructureConfig(
            database_host=infra.get('database_host', 'localhost'),
            database_port=infra.getint('database_port', 5432)
        )
    
    def get_service_configs(self) -> Dict[str, ServiceConfig]:
        """Get all service configurations from plugin sections."""
        services = {}
        
        # Known service sections (could be made dynamic in the future)
        # Add 'redis' to allow the launcher to register and present Redis as a managed service
        service_names = ['strapi', 'gpscentcom', 'geospatial', 'vehicle_simulator', 'commuter_service', 'redis']
        
        for service_name in service_names:
            if service_name in self.config:
                section = self.config[service_name]
                
                # Parse dependencies
                dependencies_str = section.get('dependencies', '')
                dependencies = [dep.strip() for dep in dependencies_str.split(',') if dep.strip()]
                
                # Collect extra config (all other settings in the section)
                extra_config = {}
                for key, value in section.items():
                    if key not in ['enabled', 'port', 'url', 'health_url', 'spawn_console', 
                                 'startup_wait', 'category', 'display_name', 'description', 'icon', 'dependencies']:
                        extra_config[key] = value
                
                services[service_name] = ServiceConfig(
                    name=service_name,
                    enabled=section.getboolean('enabled', False),
                    port=section.getint('port', None) if section.get('port') else None,
                    url=section.get('url'),
                    health_url=section.get('health_url'),
                    spawn_console=section.getboolean('spawn_console', False),
                    startup_wait=section.getint('startup_wait', 10),
                    category=section.get('category', 'unknown'),
                    display_name=section.get('display_name', service_name),
                    description=section.get('description', ''),
                    icon=section.get('icon', '⚙️'),
                    dependencies=dependencies,
                    extra_config=extra_config
                )
        
        return services
