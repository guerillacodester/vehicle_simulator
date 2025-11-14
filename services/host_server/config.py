"""
Host Server Configuration
==========================

Configuration for the ArkNet host server.
Reads from root config.ini for infrastructure settings.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
import configparser


class HostServerConfig(BaseSettings):
    """Host server configuration"""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 6000
    
    # Service ports
    simulator_api_port: int = 5001
    gps_server_port: int = 5000
    commuter_service_port: int = 4000
    strapi_port: int = 1337
    strapi_url: str = "http://localhost:1337"  # Default, will be overridden from config.ini
    
    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    simulator_module: str = "arknet_transit_simulator"
    
    # Process management
    process_check_interval: float = 5.0  # seconds
    process_start_timeout: float = 30.0  # seconds
    process_stop_timeout: float = 10.0   # seconds
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "host_server.log"
    
    class Config:
        env_prefix = "ARKNET_HOST_"
        case_sensitive = False


def _load_config_from_ini() -> HostServerConfig:
    """Load configuration from root config.ini file"""
    config_obj = HostServerConfig()
    
    # Read root config.ini
    config_file = config_obj.project_root / "config.ini"
    if config_file.exists():
        parser = configparser.ConfigParser()
        try:
            parser.read(config_file, encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails
            parser.read(config_file, encoding='latin-1')
        
        # Load infrastructure settings
        if parser.has_section("infrastructure"):
            if parser.has_option("infrastructure", "strapi_url"):
                config_obj.strapi_url = parser.get("infrastructure", "strapi_url")
            if parser.has_option("infrastructure", "strapi_port"):
                config_obj.strapi_port = parser.getint("infrastructure", "strapi_port")
    
    return config_obj


# Global config instance
config = _load_config_from_ini()
