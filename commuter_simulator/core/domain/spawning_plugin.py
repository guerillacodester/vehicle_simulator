"""
Spawning Plugin System - Abstract Base for Passenger Generation

This module provides the plugin architecture for passenger spawning,
supporting both statistical simulation models AND historical data replay.

Plugin Types:
1. Statistical Models - Generate passengers based on mathematical distributions
   - PoissonGeoJSONPlugin: Population-based Poisson spawning
   - UniformRandomPlugin: Simple random spawning
   - ScheduleBasedPlugin: GTFS schedule-driven spawning
   
2. Historical Data - Replay real-world passenger data
   - HistoricalReplayPlugin: Load and replay from database
   - CSVImportPlugin: Import from CSV files
   - APIStreamPlugin: Stream from external API
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging


class PluginType(Enum):
    """Types of spawning plugins"""
    STATISTICAL = "statistical"  # Generate via simulation models
    HISTORICAL = "historical"    # Replay real-world data
    HYBRID = "hybrid"           # Combination of both


class SpawnContext(Enum):
    """Context where spawning occurs"""
    DEPOT = "depot"     # At depot/terminal locations
    ROUTE = "route"     # Along route paths
    ZONE = "zone"       # Within geographic zones
    CUSTOM = "custom"   # Custom locations


@dataclass
class SpawnRequest:
    """Universal spawn request format for all plugins"""
    passenger_id: Optional[str]  # None for new spawns, populated for historical
    spawn_location: Tuple[float, float]  # (lat, lon)
    destination_location: Tuple[float, float]  # (lat, lon)
    route_id: str
    spawn_time: datetime
    spawn_context: SpawnContext
    
    # Optional metadata
    zone_id: Optional[str] = None
    zone_type: Optional[str] = None
    trip_purpose: Optional[str] = None
    priority: float = 1.0
    generation_method: str = "unknown"
    
    # Historical data fields (None for simulated)
    is_historical: bool = False
    actual_pickup_time: Optional[datetime] = None
    actual_dropoff_time: Optional[datetime] = None
    actual_wait_time_seconds: Optional[float] = None
    
    # Plugin metadata
    plugin_name: str = "unknown"
    plugin_version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            'passenger_id': self.passenger_id,
            'spawn_location': {'lat': self.spawn_location[0], 'lon': self.spawn_location[1]},
            'destination': {'lat': self.destination_location[0], 'lon': self.destination_location[1]},
            'route_id': self.route_id,
            'spawn_time': self.spawn_time.isoformat(),
            'spawn_context': self.spawn_context.value,
            'zone_id': self.zone_id,
            'zone_type': self.zone_type,
            'trip_purpose': self.trip_purpose,
            'priority': self.priority,
            'generation_method': self.generation_method,
            'is_historical': self.is_historical,
            'plugin_name': self.plugin_name,
            'plugin_version': self.plugin_version
        }


@dataclass
class PluginConfig:
    """Configuration for a spawning plugin"""
    plugin_name: str
    plugin_type: PluginType
    enabled: bool = True
    priority: int = 100  # Higher priority plugins run first
    
    # Statistical model parameters
    spawn_rate_multiplier: float = 1.0
    temporal_adjustment: bool = True
    use_spatial_cache: bool = True
    
    # Historical data parameters
    data_source: Optional[str] = None  # Database table, file path, API endpoint
    replay_speed: float = 1.0  # 1.0 = real-time, 2.0 = 2x speed, etc.
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Common parameters
    country_code: str = "BB"
    max_spawns_per_cycle: int = 100
    spawn_interval_seconds: float = 300.0  # 5 minutes default
    
    # Plugin-specific parameters (flexible dict)
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


class BaseSpawningPlugin(ABC):
    """
    Abstract base class for all spawning plugins.
    
    All spawning mechanisms (statistical models, historical replay, etc.)
    must implement this interface to be used by the commuter simulator.
    
    Lifecycle:
    1. __init__(config, api_client) - Create plugin with configuration
    2. initialize() - Async initialization (load data, connect to services)
    3. generate_spawn_requests() - Called periodically to generate passengers
    4. shutdown() - Cleanup resources
    
    Example Implementation:
        class MyPlugin(BaseSpawningPlugin):
            async def initialize(self) -> bool:
                # Load data, connect to API, etc.
                return True
                
            async def generate_spawn_requests(self, current_time, time_window, context):
                # Generate spawn requests
                return [SpawnRequest(...), ...]
                
            async def shutdown(self):
                # Cleanup
                pass
    """
    
    def __init__(self, config: PluginConfig, api_client: Any, logger: Optional[logging.Logger] = None):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin configuration
            api_client: Strapi API client for data access
            logger: Optional logger instance
        """
        self.config = config
        self.api_client = api_client
        self.logger = logger or logging.getLogger(f"{__name__}.{config.plugin_name}")
        self._initialized = False
        self._spawn_count = 0
        self._last_spawn_time: Optional[datetime] = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin (load data, connect to services, etc.)
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate_spawn_requests(
        self,
        current_time: datetime,
        time_window_minutes: int,
        context: SpawnContext,
        **kwargs
    ) -> List[SpawnRequest]:
        """
        Generate spawn requests for the current time window.
        
        Args:
            current_time: Current simulation time
            time_window_minutes: Time window for spawning (e.g., 5 minutes)
            context: Spawn context (depot, route, zone, custom)
            **kwargs: Additional context-specific parameters
                     - route_id: For route context
                     - depot_id: For depot context
                     - zone_ids: For zone context
        
        Returns:
            List of spawn requests
        """
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Cleanup plugin resources"""
        pass
    
    # Common helper methods
    
    def is_initialized(self) -> bool:
        """Check if plugin is initialized"""
        return self._initialized
    
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        return {
            'plugin_name': self.config.plugin_name,
            'plugin_type': self.config.plugin_type.value,
            'enabled': self.config.enabled,
            'initialized': self._initialized,
            'total_spawns': self._spawn_count,
            'last_spawn_time': self._last_spawn_time.isoformat() if self._last_spawn_time else None
        }
    
    def _record_spawns(self, spawn_requests: List[SpawnRequest]):
        """Record spawn statistics"""
        self._spawn_count += len(spawn_requests)
        if spawn_requests:
            self._last_spawn_time = spawn_requests[0].spawn_time
    
    def _apply_spawn_rate_multiplier(self, base_rate: float) -> float:
        """Apply configured spawn rate multiplier"""
        return base_rate * self.config.spawn_rate_multiplier
    
    def _should_spawn_now(self, current_time: datetime) -> bool:
        """Check if enough time has passed for next spawn cycle"""
        if self._last_spawn_time is None:
            return True
        
        elapsed = (current_time - self._last_spawn_time).total_seconds()
        return elapsed >= self.config.spawn_interval_seconds
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.config.plugin_name}, type={self.config.plugin_type.value})"


class PluginRegistry:
    """
    Registry for managing spawning plugins.
    
    Allows dynamic loading, configuration, and execution of multiple
    spawning plugins simultaneously.
    
    Usage:
        registry = PluginRegistry(api_client)
        
        # Register plugins
        registry.register_plugin(PoissonGeoJSONPlugin(config1, api_client))
        registry.register_plugin(HistoricalReplayPlugin(config2, api_client))
        
        # Initialize all
        await registry.initialize_all()
        
        # Generate spawns from all active plugins
        spawn_requests = await registry.generate_spawns(
            current_time=datetime.now(),
            time_window_minutes=5,
            context=SpawnContext.DEPOT
        )
    """
    
    def __init__(self, api_client: Any, logger: Optional[logging.Logger] = None):
        self.api_client = api_client
        self.logger = logger or logging.getLogger(__name__)
        self._plugins: Dict[str, BaseSpawningPlugin] = {}
        self._plugin_order: List[str] = []
    
    def register_plugin(self, plugin: BaseSpawningPlugin):
        """Register a spawning plugin"""
        plugin_name = plugin.config.plugin_name
        
        if plugin_name in self._plugins:
            self.logger.warning(f"Plugin {plugin_name} already registered, replacing")
        
        self._plugins[plugin_name] = plugin
        self._update_plugin_order()
        
        self.logger.info(f"Registered plugin: {plugin}")
    
    def unregister_plugin(self, plugin_name: str):
        """Unregister a plugin"""
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            self._update_plugin_order()
            self.logger.info(f"Unregistered plugin: {plugin_name}")
    
    def _update_plugin_order(self):
        """Update plugin execution order based on priority"""
        self._plugin_order = sorted(
            self._plugins.keys(),
            key=lambda name: self._plugins[name].config.priority,
            reverse=True
        )
    
    def get_plugin(self, plugin_name: str) -> Optional[BaseSpawningPlugin]:
        """Get a plugin by name"""
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names"""
        return list(self._plugins.keys())
    
    async def initialize_all(self) -> bool:
        """Initialize all registered plugins"""
        self.logger.info(f"Initializing {len(self._plugins)} plugins...")
        
        success_count = 0
        for plugin_name in self._plugin_order:
            plugin = self._plugins[plugin_name]
            
            if not plugin.config.enabled:
                self.logger.info(f"Skipping disabled plugin: {plugin_name}")
                continue
            
            try:
                if await plugin.initialize():
                    success_count += 1
                    self.logger.info(f"✅ Initialized: {plugin_name}")
                else:
                    self.logger.error(f"❌ Failed to initialize: {plugin_name}")
            except Exception as e:
                self.logger.error(f"❌ Error initializing {plugin_name}: {e}")
        
        self.logger.info(f"Initialized {success_count}/{len(self._plugins)} plugins")
        return success_count > 0
    
    async def generate_spawns(
        self,
        current_time: datetime,
        time_window_minutes: int,
        context: SpawnContext,
        **kwargs
    ) -> List[SpawnRequest]:
        """
        Generate spawn requests from all active plugins.
        
        Plugins are executed in priority order (highest first).
        Results are aggregated and returned.
        """
        all_spawn_requests = []
        
        for plugin_name in self._plugin_order:
            plugin = self._plugins[plugin_name]
            
            if not plugin.config.enabled or not plugin.is_initialized():
                continue
            
            try:
                spawn_requests = await plugin.generate_spawn_requests(
                    current_time=current_time,
                    time_window_minutes=time_window_minutes,
                    context=context,
                    **kwargs
                )
                
                if spawn_requests:
                    all_spawn_requests.extend(spawn_requests)
                    self.logger.debug(
                        f"Plugin {plugin_name} generated {len(spawn_requests)} spawn requests"
                    )
            
            except Exception as e:
                self.logger.error(f"Error generating spawns from {plugin_name}: {e}")
        
        self.logger.info(
            f"Generated {len(all_spawn_requests)} total spawn requests from "
            f"{len([p for p in self._plugins.values() if p.config.enabled])} active plugins"
        )
        
        return all_spawn_requests
    
    async def shutdown_all(self):
        """Shutdown all plugins"""
        self.logger.info("Shutting down all plugins...")
        
        for plugin_name, plugin in self._plugins.items():
            try:
                await plugin.shutdown()
                self.logger.info(f"✅ Shutdown: {plugin_name}")
            except Exception as e:
                self.logger.error(f"❌ Error shutting down {plugin_name}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all plugins"""
        return {
            'total_plugins': len(self._plugins),
            'active_plugins': len([p for p in self._plugins.values() if p.config.enabled]),
            'plugins': {name: plugin.get_stats() for name, plugin in self._plugins.items()}
        }
