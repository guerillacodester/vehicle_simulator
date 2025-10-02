"""
Passenger Service Package
Statistical passenger spawning and behavior simulation using GeoJSON data
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

__all__ = [
    'get_api_client', 
    'get_poisson_spawner',
    'get_spawn_manager'
]