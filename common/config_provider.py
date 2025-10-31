"""
Centralized configuration provider for the vehicle simulator system.

Provides a singleton ConfigProvider that reads infrastructure settings from config.ini
and provides a single source of truth for all URLs, ports, and connection settings.

Usage:
    from common.config_provider import ConfigProvider, get_config
    
    # Get singleton instance
    config = ConfigProvider.get_instance()
    
    # Access infrastructure settings
    gps_url = config.infrastructure.gpscentcom_http_url
    ws_url = config.infrastructure.gpscentcom_ws_url
    
    # Or use the convenience function
    config = get_config()
"""

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class InfrastructureConfig:
    """Infrastructure configuration settings loaded from config.ini [infrastructure] section."""
    
    # GPS Telemetry Service
    gpscentcom_http_url: str
    gpscentcom_ws_url: str
    
    # Strapi CMS API
    strapi_url: str
    
    # Geospatial Service
    geospatial_url: str
    
    # Manifest API
    manifest_url: str
    
    # Database Connection
    database_host: str
    database_port: int
    
    # Derived URLs (constructed automatically)
    strapi_api_url: str
    routes_endpoint: str
    depots_endpoint: str
    operational_config_endpoint: str
    

class ConfigProvider:
    """
    Singleton configuration provider that loads settings from config.ini.
    
    This class ensures a single source of truth for all infrastructure configuration
    and provides typed access to configuration values throughout the application.
    """
    
    _instance: Optional['ConfigProvider'] = None
    _config_path: Path = Path(__file__).parent.parent / "config.ini"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the ConfigProvider.
        
        Args:
            config_path: Optional path to config.ini. If not provided, uses default location.
            
        Note: Use get_instance() instead of direct instantiation to ensure singleton behavior.
        """
        if config_path:
            self._config_path = config_path
            
        self._parser = configparser.ConfigParser()
        
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self._config_path}\n"
                f"Please ensure config.ini exists in the project root."
            )
        
        # Read with UTF-8 encoding to handle special characters
        self._parser.read(self._config_path, encoding='utf-8')
        self._infrastructure = self._load_infrastructure_config()
    
    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> 'ConfigProvider':
        """
        Get the singleton instance of ConfigProvider.
        
        Args:
            config_path: Optional path to config.ini (only used on first call)
            
        Returns:
            The singleton ConfigProvider instance
        """
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (primarily for testing)."""
        cls._instance = None
    
    @property
    def infrastructure(self) -> InfrastructureConfig:
        """Get infrastructure configuration settings."""
        return self._infrastructure
    
    def _load_infrastructure_config(self) -> InfrastructureConfig:
        """Load and parse infrastructure configuration from config.ini."""
        section = 'infrastructure'
        
        if not self._parser.has_section(section):
            raise ValueError(
                f"Missing [{section}] section in {self._config_path}\n"
                f"Please ensure config.ini contains infrastructure settings."
            )
        
        infra = self._parser[section]
        
        # Load base URLs and connection settings
        strapi_url = infra.get('strapi_url', 'http://localhost:1337')
        gpscentcom_http_url = infra.get('gpscentcom_http_url', 'http://localhost:5000')
        gpscentcom_ws_url = infra.get('gpscentcom_ws_url', 'ws://localhost:5000')
        geospatial_url = infra.get('geospatial_url', 'http://localhost:6000')
        manifest_url = infra.get('manifest_url', 'http://localhost:4000')
        database_host = infra.get('database_host', 'localhost')
        database_port = infra.getint('database_port', 5432)
        
        # Construct derived URLs
        strapi_api_url = f"{strapi_url}/api"
        routes_endpoint = f"{strapi_api_url}/routes"
        depots_endpoint = f"{strapi_api_url}/depots"
        operational_config_endpoint = f"{strapi_api_url}/operational-configurations"
        
        return InfrastructureConfig(
            gpscentcom_http_url=gpscentcom_http_url,
            gpscentcom_ws_url=gpscentcom_ws_url,
            strapi_url=strapi_url,
            geospatial_url=geospatial_url,
            manifest_url=manifest_url,
            database_host=database_host,
            database_port=database_port,
            strapi_api_url=strapi_api_url,
            routes_endpoint=routes_endpoint,
            depots_endpoint=depots_endpoint,
            operational_config_endpoint=operational_config_endpoint,
        )


def get_config() -> ConfigProvider:
    """
    Convenience function to get the ConfigProvider singleton instance.
    
    Returns:
        The singleton ConfigProvider instance
        
    Example:
        from common.config_provider import get_config
        
        config = get_config()
        print(config.infrastructure.strapi_url)
    """
    return ConfigProvider.get_instance()
