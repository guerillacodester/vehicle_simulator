"""
Configuration Loader
--------------------

Centralized configuration loader for commuter simulator.
Reads from config.ini and .env files following the architectural pattern.

Config.ini: Infrastructure settings (URLs, ports, operational flags)
.env: Secrets only (API tokens, credentials)
Database: Operational/business settings (spawn rates, routes, etc.)
"""
import os
import configparser
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class InfrastructureConfig:
    """Infrastructure service URLs and ports"""
    strapi_url: str
    strapi_port: int
    gpscentcom_http_url: str
    gpscentcom_ws_url: str
    gpscentcom_port: int
    geospatial_url: str
    geospatial_port: int
    commuter_service_url: str
    commuter_service_port: int
    database_host: str
    database_port: int


@dataclass
class CommuterSimulatorConfig:
    """Commuter simulator infrastructure settings"""
    enable_redis_cache: bool


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str
    format: str


@dataclass
class AppConfig:
    """Complete application configuration"""
    infrastructure: InfrastructureConfig
    commuter_service: CommuterSimulatorConfig
    logging: LoggingConfig
    strapi_api_token: Optional[str] = None


def find_config_file() -> Path:
    """Find config.ini file (search from current file up to project root)"""
    current = Path(__file__).resolve()
    
    # Search up the directory tree
    for parent in [current.parent] + list(current.parents):
        config_path = parent / "config.ini"
        if config_path.exists():
            return config_path
    
    # Fallback to project root
    project_root = Path(__file__).resolve().parents[3]  # commuter_service/infrastructure/config -> root
    return project_root / "config.ini"


def load_config() -> AppConfig:
    """
    Load configuration from config.ini and .env
    
    Returns:
        AppConfig object with all settings
    """
    # Load environment variables from .env
    env_path = find_config_file().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    # Load config.ini
    config = configparser.ConfigParser(interpolation=None)  # Disable interpolation for % signs
    config_path = find_config_file()
    
    if not config_path.exists():
        raise FileNotFoundError(f"config.ini not found at {config_path}")
    
    config.read(config_path, encoding='utf-8')
    
    # Parse infrastructure section
    infrastructure = InfrastructureConfig(
        strapi_url=config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337'),
        strapi_port=config.getint('infrastructure', 'strapi_port', fallback=1337),
        gpscentcom_http_url=config.get('infrastructure', 'gpscentcom_http_url', fallback='http://localhost:5000'),
        gpscentcom_ws_url=config.get('infrastructure', 'gpscentcom_ws_url', fallback='ws://localhost:5000'),
        gpscentcom_port=config.getint('infrastructure', 'gpscentcom_port', fallback=5000),
        geospatial_url=config.get('infrastructure', 'geospatial_url', fallback='http://localhost:6000'),
        geospatial_port=config.getint('infrastructure', 'geospatial_port', fallback=6000),
        commuter_service_url=config.get('infrastructure', 'commuter_service_url', fallback='http://localhost:4000'),
        commuter_service_port=config.getint('infrastructure', 'commuter_service_port', fallback=4000),
        database_host=config.get('infrastructure', 'database_host', fallback='localhost'),
        database_port=config.getint('infrastructure', 'database_port', fallback=5432)
    )
    
    # Parse commuter_service section
    commuter_sim = CommuterSimulatorConfig(
        enable_redis_cache=config.getboolean('commuter_service', 'enable_redis_cache', fallback=False)
    )
    
    # Parse logging section
    logging_config = LoggingConfig(
        level=config.get('logging', 'level', fallback='INFO'),
        format=config.get('logging', 'format', fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Get API token from environment
    strapi_api_token = os.getenv('STRAPI_API_TOKEN')
    
    return AppConfig(
        infrastructure=infrastructure,
        commuter_service=commuter_sim,
        logging=logging_config,
        strapi_api_token=strapi_api_token
    )


# Singleton instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get cached configuration instance.
    Loads config on first call, returns cached instance on subsequent calls.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> AppConfig:
    """
    Force reload configuration from files.
    Use when config.ini or .env has changed.
    """
    global _config
    _config = load_config()
    return _config
