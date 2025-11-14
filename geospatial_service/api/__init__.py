"""API module"""

from .geocoding import router as geocoding_router
from .geofence import router as geofence_router
from .spatial import router as spatial_router

__all__ = ["geocoding_router", "geofence_router", "spatial_router"]
