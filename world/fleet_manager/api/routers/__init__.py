"""
Router initialization for Fleet Management API
"""
from .countries import router as countries_router
from .depots import router as depots_router
from .vehicles import router as vehicles_router
from .drivers import router as drivers_router
from .stops import router as stops_router
from .trips import router as trips_router
from .services import router as services_router
from .blocks import router as blocks_router

__all__ = [
    "countries_router",
    "depots_router", 
    "vehicles_router",
    "drivers_router",
    "stops_router",
    "trips_router",
    "services_router",
    "blocks_router",
]
