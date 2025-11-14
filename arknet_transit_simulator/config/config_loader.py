"""
Configuration Loader
-------------------
Centralized configuration loader for the vehicle simulator.
Reads configuration from config.ini and environment variables.
Located in config/ folder alongside config.ini for better organization.
"""

import os
import configparser
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False


class ConfigLoader:
    """
    Configuration loader that reads from config.ini and environment variables.
    Provides all configuration data needed for vehicle simulation.
    """
    
    def __init__(self, config_file: str = None):
        # Default to config.ini in same directory as this file
        if config_file is None:
            config_file = Path(__file__).parent / "config.ini"
        
        self.config_file = Path(config_file)
        self._config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if not self.config_file.exists():
            # Try alternative locations
            alternatives = [
                Path(__file__).parent / "config.ini",
                Path("config/config.ini"),
                Path("world/vehicle_simulator/config/config.ini")
            ]
            
            for alt_config in alternatives:
                if alt_config.exists():
                    self.config_file = alt_config
                    break
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
        # Load defaults from ConfigProvider if available
        server_url = 'ws://localhost:5000/'
        auth_token = 'supersecrettoken'
        
        if _config_available:
            try:
                config_provider = get_config()
                server_url = config_provider.infrastructure.gpscentcom_ws_url
                if not server_url.endswith('/'):
                    server_url += '/'
            except Exception as e:
                logger.warning(f"Could not load GPS config from ConfigProvider: {e}")
        
        config = {
            'server_url': server_url,
            'auth_token': auth_token,  # Will be overridden by AUTH_TOKEN env var
            'method': 'ws',
            'interval': 1.0
        }
        
        # From config file
        if self._config.has_section('server'):
            config.update(dict(self._config.items('server')))
        
        # Override with environment variables (highest priority)
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
        """
        Get simulation parameters.
        
        DEPRECATED: This method returns hardcoded defaults only.
        For runtime simulation configuration, use ConfigurationService to query database:
            from arknet_transit_simulator.services.config_service import ConfigurationService
            config_service = ConfigurationService()
            await config_service.initialize()
            tick_time = await config_service.get("vehicle_simulator.simulation.tick_time", default=1.0)
        
        Database sections:
            - vehicle_simulator.simulation.tick_time
            - vehicle_simulator.simulation.default_speed
            - vehicle_simulator.engine.speed_model
            - vehicle_simulator.engine.accel_limit
            - vehicle_simulator.engine.decel_limit
            - vehicle_simulator.engine.corner_slowdown
        """
        # Return minimal fallback defaults
        # These are ONLY used if database is unavailable
        config = {
            'tick_time': 1.0,
            'default_speed': 60.0,
            'max_speed': 120.0,
            'min_speed': 10.0,
            'vehicle_capacity': 40,
            'enable_timetable': True,
            'schedule_precision_seconds': 30
        }
        
        # Environment variables override (highest priority)
        env_mappings = {
            'SIM_TICK_TIME': 'tick_time',
            'SIM_DEFAULT_SPEED': 'default_speed',
            'SIM_MAX_SPEED': 'max_speed',
            'SIM_MIN_SPEED': 'min_speed',
            'SIM_VEHICLE_CAPACITY': 'vehicle_capacity',
            'SIM_ENABLE_TIMETABLE': 'enable_timetable',
            'SIM_SCHEDULE_PRECISION': 'schedule_precision_seconds'
        }
        
        for env_var, config_key in env_mappings.items():
            if os.getenv(env_var):
                value = os.getenv(env_var)
                # Try to convert to appropriate type
                try:
                    if config_key == 'enable_timetable':
                        config[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                    elif '.' in value:
                        config[config_key] = float(value)
                    else:
                        config[config_key] = int(value)
                except ValueError:
                    config[config_key] = value
        
        return config
    
    def get_fleet_config(self) -> Dict[str, Any]:
        """Get fleet management configuration"""
        # Load API URL from ConfigProvider
        api_url = 'http://localhost:1337'  # Fallback to Strapi
        
        if _config_available:
            try:
                config_provider = get_config()
                api_url = config_provider.infrastructure.strapi_url
            except Exception as e:
                logger.warning(f"Could not load fleet API URL from ConfigProvider: {e}")
        
        config = {
            'api_url': api_url,
            'default_depot_id': 'DEPOT_001',
            'auto_assign_vehicles': True,
            'schedule_lookahead_minutes': 30,
            'vehicle_warmup_minutes': 5,
            'enable_driver_assignments': True,
            'api_timeout_seconds': 5,
            'api_retry_attempts': 3
        }
        
        # From config file
        if self._config.has_section('fleet'):
            config.update(dict(self._config.items('fleet')))
        
        # Override with environment variables
        env_mappings = {
            'FLEET_API_URL': 'api_url',
            'FLEET_DEFAULT_DEPOT': 'default_depot_id',
            'FLEET_AUTO_ASSIGN': 'auto_assign_vehicles',
            'FLEET_LOOKAHEAD_MIN': 'schedule_lookahead_minutes',
            'FLEET_WARMUP_MIN': 'vehicle_warmup_minutes',
            'FLEET_ENABLE_DRIVERS': 'enable_driver_assignments',
            'FLEET_API_TIMEOUT': 'api_timeout_seconds',
            'FLEET_API_RETRY': 'api_retry_attempts'
        }
        
        for env_var, config_key in env_mappings.items():
            if os.getenv(env_var):
                value = os.getenv(env_var)
                try:
                    if config_key in ['auto_assign_vehicles', 'enable_driver_assignments']:
                        config[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                    elif config_key in ['schedule_lookahead_minutes', 'vehicle_warmup_minutes', 'api_timeout_seconds', 'api_retry_attempts']:
                        config[config_key] = int(value)
                    else:
                        config[config_key] = value
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
    
    def get_all_config(self) -> Dict[str, Dict[str, Any]]:
        """Get all configuration sections"""
        return {
            'database': self.get_database_config(),
            'gps': self.get_gps_config(),
            'simulation': self.get_simulation_config(),
            'fleet': self.get_fleet_config()
        }
