"""
Commuter Service Package
Statistical commuter spawning, reservoir management, and Socket.IO integration
"""

__version__ = "1.0.0"

# Lazy imports to avoid dependency issues
def get_api_client():
    """Get StrapiApiClient class"""
    from .strapi_api_client import StrapiApiClient
    return StrapiApiClient

def get_poisson_spawner():
    """Get PoissonGeoJSONSpawner class"""
    from .poisson_geojson_spawner import PoissonGeoJSONSpawner
    return PoissonGeoJSONSpawner

def get_spawn_manager():
    """Get PassengerSpawnManager and strategy classes"""
    from .spawn_interface import PassengerSpawnManager, DepotSpawnStrategy, RouteSpawnStrategy, MixedSpawnStrategy
    return PassengerSpawnManager, DepotSpawnStrategy, RouteSpawnStrategy, MixedSpawnStrategy

def get_depot_reservoir():
    """Get DepotReservoir class"""
    from .depot_reservoir import DepotReservoir
    return DepotReservoir

def get_route_reservoir():
    """Get RouteReservoir class"""
    from .route_reservoir import RouteReservoir
    return RouteReservoir

def get_socketio_client():
    """Get SocketIOClient class and related types"""
    from .socketio_client import SocketIOClient, CommuterDirection
    return SocketIOClient, CommuterDirection

__all__ = [
    'get_api_client', 
    'get_poisson_spawner',
    'get_spawn_manager',
    'get_depot_reservoir',
    'get_route_reservoir',
    'get_socketio_client'
]