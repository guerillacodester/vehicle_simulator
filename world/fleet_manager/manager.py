from . import database
from .services.route_manager import RouteManager
from .services.vehicle_manager import VehicleManager
from .services.country_manager import CountryManager
from .services.depot_manager import DepotManager   # ✅ add this


class FleetManager:
    """
    Entry point for all DB-backed fleet operations.
    Provides access to sub-managers (routes, vehicles, countries, depots, etc.).
    """

    def __init__(self):
        database.init_engine()
        self.db = database.SessionLocal()

        self.routes = RouteManager(self.db)
        self.vehicles = VehicleManager(self.db)
        self.countries = CountryManager(self.db)
        self.depots = DepotManager(self.db)        # ✅ wire it in here

    def close(self):
        if self.db:
            self.db.close()
