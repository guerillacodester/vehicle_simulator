"""
API Endpoints Router
===================
Main router that includes all GTFS API endpoints
"""

from fastapi import APIRouter

from .countries import router as countries_router
from .routes import router as routes_router
from .vehicles import router as vehicles_router
from .stops import router as stops_router
from .trips import router as trips_router
from .depots import router as depots_router
from .drivers import router as drivers_router
from .services import router as services_router
from .timetables import router as timetables_router
from .shapes import router as shapes_router
from .blocks import router as blocks_router
from .stop_times import router as stop_times_router
from .route_shapes import router as route_shapes_router
from .frequencies import router as frequencies_router
from .vehicle_assignments import router as vehicle_assignments_router
from .driver_assignments import router as driver_assignments_router
from .vehicle_status_events import router as vehicle_status_events_router
from .block_trips import router as block_trips_router
from .block_breaks import router as block_breaks_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    countries_router,
    prefix="/countries",
    tags=["Countries"]
)

api_router.include_router(
    routes_router,
    prefix="/routes", 
    tags=["Routes"]
)

api_router.include_router(
    vehicles_router,
    prefix="/vehicles",
    tags=["Vehicles"]
)

api_router.include_router(
    stops_router,
    prefix="/stops",
    tags=["Stops"]
)

api_router.include_router(
    trips_router,
    prefix="/trips", 
    tags=["Trips"]
)

api_router.include_router(
    depots_router,
    prefix="/depots",
    tags=["Depots"]
)

api_router.include_router(
    drivers_router,
    prefix="/drivers",
    tags=["Drivers"]
)

api_router.include_router(
    services_router,
    prefix="/services",
    tags=["Services"]
)

api_router.include_router(timetables_router, prefix="/timetables", tags=["Timetables"])
api_router.include_router(shapes_router, prefix="/shapes", tags=["Shapes"])
api_router.include_router(blocks_router, prefix="/blocks", tags=["Blocks"])
api_router.include_router(stop_times_router, prefix="/stop-times", tags=["Stop Times"])
api_router.include_router(route_shapes_router, prefix="/route-shapes", tags=["Route Shapes"])
api_router.include_router(frequencies_router, prefix="/frequencies", tags=["Frequencies"])
api_router.include_router(vehicle_assignments_router, prefix="/vehicle-assignments", tags=["Vehicle Assignments"])
api_router.include_router(driver_assignments_router, prefix="/driver-assignments", tags=["Driver Assignments"])
api_router.include_router(vehicle_status_events_router, prefix="/vehicle-status-events", tags=["Vehicle Status Events"])
api_router.include_router(block_trips_router, prefix="/block-trips", tags=["Block Trips"])
api_router.include_router(block_breaks_router, prefix="/block-breaks", tags=["Block Breaks"])
