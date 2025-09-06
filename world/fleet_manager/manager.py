# world/fleet_manager/manager.py
from sqlalchemy.orm import Session
from .services.route_manager import RouteManager
from .services.vehicle_manager import VehicleManager
from .services.country_manager import CountryManager
from .services.depot_manager import DepotManager
from .services.shape_manager import ShapeManager
from .services.timetable_manager import TimetableManager

class FleetManager:
    """
    Entry point for all DB-backed fleet operations.
    Provides access to sub-managers (routes, vehicles, countries, depots, etc.).
    """

    def __init__(self, db: Session):     # ✅ take a session, don’t init engine
        self.db = db
        self.routes = RouteManager(db)
        self.vehicles = VehicleManager(db)
        self.countries = CountryManager(db)
        self.depots = DepotManager(db)
        self.shapes = ShapeManager(db)
        self.timetables = TimetableManager(db)
        
    def close(self):
        if self.db:
            self.db.close()
