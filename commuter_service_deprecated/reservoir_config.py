"""
Commuter Reservoir Configuration

Externalized configuration for reservoir behavior, thresholds, and operational parameters.
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class ReservoirConfig:
    """Configuration for commuter reservoir operations"""
    
    # Socket.IO connection settings
    socketio_url: str = "http://localhost:1337"
    socketio_reconnect_delay: int = 5  # seconds
    socketio_max_reconnect_attempts: int = 10
    
    # Commuter expiration settings
    commuter_max_wait_time_minutes: int = 30  # Max time before expiration
    expiration_check_interval_seconds: int = 60  # How often to check for expired
    
    # Spatial indexing (for route reservoir)
    grid_cell_size_degrees: float = 0.01  # ~1km at equator
    default_search_radius_km: float = 2.0  # Default proximity search radius
    
    # Query limits
    max_commuters_per_query: int = 100  # Safety limit for queries
    default_pickup_distance_meters: float = 500.0  # Default max walking distance
    
    # Performance settings
    max_active_commuters_per_queue: int = 500  # Per depot or segment
    enable_statistics_tracking: bool = True
    enable_socketio_events: bool = True
    
    # Earth radius for distance calculations
    earth_radius_meters: float = 6371000.0
    
    @staticmethod
    def load_from_env() -> 'ReservoirConfig':
        """Load configuration from environment variables"""
        config = ReservoirConfig()
        
        # Socket.IO settings
        config.socketio_url = os.getenv('RESERVOIR_SOCKETIO_URL', config.socketio_url)
        config.socketio_reconnect_delay = int(os.getenv('RESERVOIR_RECONNECT_DELAY', config.socketio_reconnect_delay))
        
        # Expiration settings
        config.commuter_max_wait_time_minutes = int(os.getenv('COMMUTER_MAX_WAIT_MINUTES', config.commuter_max_wait_time_minutes))
        config.expiration_check_interval_seconds = int(os.getenv('EXPIRATION_CHECK_INTERVAL', config.expiration_check_interval_seconds))
        
        # Spatial settings
        config.grid_cell_size_degrees = float(os.getenv('GRID_CELL_SIZE', config.grid_cell_size_degrees))
        config.default_search_radius_km = float(os.getenv('SEARCH_RADIUS_KM', config.default_search_radius_km))
        
        # Query limits
        config.max_commuters_per_query = int(os.getenv('MAX_COMMUTERS_PER_QUERY', config.max_commuters_per_query))
        config.default_pickup_distance_meters = float(os.getenv('DEFAULT_PICKUP_DISTANCE', config.default_pickup_distance_meters))
        
        return config
    
    @staticmethod
    def get_default() -> 'ReservoirConfig':
        """Get default configuration"""
        return ReservoirConfig()


# Global configuration instance
_reservoir_config: Optional[ReservoirConfig] = None


def get_reservoir_config() -> ReservoirConfig:
    """Get the global reservoir configuration instance"""
    global _reservoir_config
    if _reservoir_config is None:
        _reservoir_config = ReservoirConfig.load_from_env()
    return _reservoir_config


def set_reservoir_config(config: ReservoirConfig) -> None:
    """Set the global reservoir configuration (for testing/override)"""
    global _reservoir_config
    _reservoir_config = config
