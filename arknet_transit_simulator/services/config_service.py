"""
Configuration Service Layer

Provides cached, auto-refreshing access to operational configuration parameters
stored in Strapi. Supports dot-notation queries, change callbacks, and hot-reload.

Example Usage:
    config = ConfigurationService()
    await config.initialize()
    
    # Get configuration values
    radius = await config.get("conductor.proximity.pickup_radius_km", default=0.2)
    interval = await config.get("driver.waypoints.broadcast_interval_seconds", default=5.0)
    
    # Get all configs in a section
    conductor_config = await config.get_section("conductor.proximity")
    
    # Register callback for config changes
    config.on_change("conductor.proximity.pickup_radius_km", my_callback)
"""

import asyncio
import aiohttp
import json
import logging

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConfigurationService:
    """
    Singleton service for accessing operational configuration parameters.
    
    Features:
    - Cached configuration data with auto-refresh
    - Dot-notation parameter access
    - Change callbacks for hot-reload
    - Section-based queries
    - Type conversion and validation
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Load Strapi URL from ConfigProvider
            strapi_url = "http://localhost:1337"  # Fallback
            if _config_available:
                try:
                    config = get_config()
                    strapi_url = config.infrastructure.strapi_url
                except Exception:
                    pass  # Use fallback
            
            self.strapi_url = strapi_url
            self.api_endpoint = f"{self.strapi_url}/api/operational-configurations"
            
            # Cache configuration data
            self._cache: Dict[str, Dict[str, Any]] = {}  # {section: {parameter: config_data}}
            self._flat_cache: Dict[str, Any] = {}  # {"section.parameter": value}
            
            # Change detection
            self._previous_values: Dict[str, Any] = {}
            self._change_callbacks: Dict[str, List[Callable]] = defaultdict(list)
            
            # Auto-refresh settings
            self.refresh_interval_seconds = 30
            self._refresh_task: Optional[asyncio.Task] = None
            self._last_refresh: Optional[datetime] = None
            
            # Session management
            self._session: Optional[aiohttp.ClientSession] = None
            
            ConfigurationService._initialized = True
    
    async def initialize(self):
        """Initialize the service and load initial configuration data."""
        logger.info("[ConfigService] Initializing configuration service...")
        
        # Create aiohttp session
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        
        # Load initial data
        await self.refresh()
        
        # Start auto-refresh task
        if self._refresh_task is None or self._refresh_task.done():
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
        
        logger.info(f"[ConfigService] Initialized with {len(self._flat_cache)} parameters")
    
    async def shutdown(self):
        """Shutdown the service and cleanup resources."""
        logger.info("[ConfigService] Shutting down configuration service...")
        
        # Cancel refresh task
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        
        # Close aiohttp session
        if self._session and not self._session.closed:
            await self._session.close()
        
        logger.info("[ConfigService] Shutdown complete")
    
    async def refresh(self):
        """Refresh configuration data from Strapi."""
        try:
            # Fetch all configurations with pagination
            params = {
                "pagination[pageSize]": 100,
                "pagination[page]": 1
            }
            
            async with self._session.get(self.api_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    configs = data.get("data", [])
                    
                    # Clear caches
                    self._cache.clear()
                    new_flat_cache = {}
                    
                    # Process configurations
                    for config in configs:
                        # In Strapi v5, attributes are at root level, not nested
                        section = config.get("section")
                        parameter = config.get("parameter")
                        value_raw = config.get("value")
                        value_type = config.get("value_type")
                        
                        # Parse value from JSON string to actual type
                        try:
                            value = json.loads(value_raw) if isinstance(value_raw, str) else value_raw
                        except (json.JSONDecodeError, TypeError):
                            value = value_raw
                        
                        if section and parameter:
                            # Store in hierarchical cache (with parsed value)
                            if section not in self._cache:
                                self._cache[section] = {}
                            
                            # Update the config with parsed value for storage
                            config_copy = config.copy()
                            config_copy["value"] = value
                            self._cache[section][parameter] = config_copy
                            
                            # Store in flat cache
                            key = f"{section}.{parameter}"
                            new_flat_cache[key] = value
                    
                    # Detect changes and trigger callbacks
                    await self._detect_changes(new_flat_cache)
                    
                    # Update flat cache
                    self._flat_cache = new_flat_cache
                    self._last_refresh = datetime.now()
                    
                    logger.debug(f"[ConfigService] Refreshed {len(configs)} configurations")
                else:
                    logger.error(f"[ConfigService] Failed to refresh: HTTP {response.status}")
        
        except Exception as e:
            logger.error(f"[ConfigService] Error refreshing configuration: {e}")
    
    async def _detect_changes(self, new_cache: Dict[str, Any]):
        """Detect changes and trigger callbacks."""
        for key, new_value in new_cache.items():
            old_value = self._previous_values.get(key)
            
            if old_value is not None and old_value != new_value:
                logger.info(f"[ConfigService] Configuration changed: {key} = {old_value} → {new_value}")
                
                # Trigger callbacks
                if key in self._change_callbacks:
                    for callback in self._change_callbacks[key]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(key, old_value, new_value)
                            else:
                                callback(key, old_value, new_value)
                        except Exception as e:
                            logger.error(f"[ConfigService] Error in change callback for {key}: {e}")
        
        # Update previous values
        self._previous_values = new_cache.copy()
    
    async def _auto_refresh_loop(self):
        """Background task to auto-refresh configuration data."""
        logger.info(f"[ConfigService] Auto-refresh started (interval: {self.refresh_interval_seconds}s)")
        
        try:
            while True:
                await asyncio.sleep(self.refresh_interval_seconds)
                await self.refresh()
        except asyncio.CancelledError:
            logger.info("[ConfigService] Auto-refresh stopped")
        except Exception as e:
            logger.error(f"[ConfigService] Error in auto-refresh loop: {e}")
    
    async def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation path.
        
        Args:
            path: Dot-notation path (e.g., "conductor.proximity.pickup_radius_km")
            default: Default value if configuration not found
        
        Returns:
            Configuration value or default
        
        Example:
            radius = await config.get("conductor.proximity.pickup_radius_km", default=0.2)
        """
        value = self._flat_cache.get(path)
        
        if value is None:
            logger.debug(f"[ConfigService] Configuration not found: {path}, using default: {default}")
            return default
        
        return value
    
    async def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get all configuration parameters in a section.
        
        Args:
            section: Section name (e.g., "conductor.proximity")
        
        Returns:
            Dictionary of {parameter: value}
        
        Example:
            proximity_config = await config.get_section("conductor.proximity")
            # {"pickup_radius_km": 0.2, "boarding_time_window_minutes": 5.0}
        """
        section_data = self._cache.get(section, {})
        return {param: data.get("value") for param, data in section_data.items()}
    
    async def get_full(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get full configuration metadata including constraints, defaults, etc.
        
        Args:
            path: Dot-notation path (e.g., "conductor.proximity.pickup_radius_km")
        
        Returns:
            Full configuration dictionary or None
        
        Example:
            config_data = await config.get_full("conductor.proximity.pickup_radius_km")
            # {
            #   "value": 0.2,
            #   "value_type": "number",
            #   "default_value": 0.2,
            #   "constraints": {"min": 0.05, "max": 5.0, "step": 0.05},
            #   "description": "...",
            #   ...
            # }
        """
        # Split path into section and parameter
        parts = path.split(".")
        if len(parts) < 2:
            return None
        
        # Last part is parameter, everything else is section
        parameter = parts[-1]
        section = ".".join(parts[:-1])
        
        return self._cache.get(section, {}).get(parameter)
    
    def on_change(self, path: str, callback: Callable):
        """
        Register a callback for configuration changes.
        
        Args:
            path: Dot-notation path to monitor
            callback: Function to call on change (key, old_value, new_value)
        
        Example:
            def on_radius_change(key, old_val, new_val):
                print(f"Radius changed: {old_val} → {new_val}")
            
            config.on_change("conductor.proximity.pickup_radius_km", on_radius_change)
        """
        self._change_callbacks[path].append(callback)
        logger.debug(f"[ConfigService] Registered change callback for: {path}")
    
    def off_change(self, path: str, callback: Callable):
        """
        Unregister a change callback.
        
        Args:
            path: Dot-notation path
            callback: Callback function to remove
        """
        if path in self._change_callbacks:
            self._change_callbacks[path].remove(callback)
    
    async def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration parameters as flat dictionary.
        
        Returns:
            Dictionary of {"section.parameter": value}
        """
        return self._flat_cache.copy()
    
    def get_last_refresh(self) -> Optional[datetime]:
        """Get timestamp of last refresh."""
        return self._last_refresh
    
    def is_stale(self, max_age_seconds: int = 60) -> bool:
        """Check if cache is stale."""
        if self._last_refresh is None:
            return True
        
        age = (datetime.now() - self._last_refresh).total_seconds()
        return age > max_age_seconds


# Global singleton instance
_config_service = ConfigurationService()


async def get_config_service() -> ConfigurationService:
    """
    Get the global configuration service instance.
    
    Returns:
        Initialized ConfigurationService instance
    """
    if not _config_service._session or _config_service._session.closed:
        await _config_service.initialize()
    
    return _config_service
