"""
Self-Contained Configuration Provider
------------------------------------
Configuration provider that doesn't depend on scripts/config_loader.py
Reads directly from config files or environment variables.
"""

import os
import configparser
from pathlib import Path
from typing import Dict, Any
import logging

from world.vehicle_simulator.interfaces.route_provider import IConfigProvider

logger = logging.getLogger(__name__)


class SelfContainedConfigProvider(IConfigProvider):
    """
    Configuration provider that reads directly from config.ini and environment.
    No dependencies on scripts/config_loader.py
    """
    
    def __init__(self, config_file: str = "config/config.ini"):
        self.config_file = Path(config_file)
        self._config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if not self.config_file.exists():
            # Try relative to project root
            project_root = Path(__file__).parent.parent
            alt_config = project_root / "config" / "config.ini"
            if alt_config.exists():
                self.config_file = alt_config
            else:
                logger.warning(f"Config file not found: {self.config_file}")
                return
        
        try:
            self._config.read(self.config_file, encoding="utf-8")
            logger.info(f"Loaded configuration from: {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        config = {}
        
        # From config file
        if self._config.has_section('database'):
            config.update(dict(self._config.items('database')))
        
        # Override with environment variables
        env_mappings = {
            'DB_HOST': 'host',
            'DB_PORT': 'port',
            'DB_NAME': 'database',
            'DB_USER': 'user',
            'DB_PASSWORD': 'password',
            'SSH_HOST': 'ssh_host',
            'SSH_PORT': 'ssh_port',
            'SSH_USER': 'ssh_user',
            'SSH_PASSWORD': 'ssh_password'
        }
        
        for env_var, config_key in env_mappings.items():
            if os.getenv(env_var):
                config[config_key] = os.getenv(env_var)
        
        return config
    
    def get_gps_config(self) -> Dict[str, Any]:
        """Get GPS server configuration"""
        config = {
            'server_url': 'ws://localhost:5000/',
            'auth_token': 'supersecrettoken',
            'method': 'ws',
            'interval': 1.0
        }
        
        # From config file
        if self._config.has_section('server'):
            config.update(dict(self._config.items('server')))
        
        # Override with environment variables
        env_mappings = {
            'GPS_SERVER_URL': 'server_url',
            'GPS_WS_URL': 'ws_url',
            'AUTH_TOKEN': 'auth_token',
            'GPS_METHOD': 'method',
            'GPS_INTERVAL': 'interval'
        }
        
        for env_var, config_key in env_mappings.items():
            if os.getenv(env_var):
                config[config_key] = os.getenv(env_var)
        
        return config
    
    def get_simulation_config(self) -> Dict[str, Any]:
        """Get simulation parameters"""
        config = {
            'tick_time': 1.0,
            'default_speed': 60.0,
            'max_speed': 120.0,
            'min_speed': 10.0,
            'vehicle_capacity': 40
        }
        
        # From config file
        if self._config.has_section('simulation'):
            config.update(dict(self._config.items('simulation')))
        
        # Override with environment variables
        env_mappings = {
            'SIM_TICK_TIME': 'tick_time',
            'SIM_DEFAULT_SPEED': 'default_speed',
            'SIM_MAX_SPEED': 'max_speed',
            'SIM_MIN_SPEED': 'min_speed',
            'SIM_VEHICLE_CAPACITY': 'vehicle_capacity'
        }
        
        for env_var, config_key in env_mappings.items():
            if os.getenv(env_var):
                value = os.getenv(env_var)
                # Try to convert to appropriate type
                try:
                    if '.' in value:
                        config[config_key] = float(value)
                    else:
                        config[config_key] = int(value)
                except ValueError:
                    config[config_key] = value
        
        return config
    
    def get_config_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        if self._config.has_section(section):
            return dict(self._config.items(section))
        return {}
    
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get specific configuration value"""
        try:
            return self._config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
