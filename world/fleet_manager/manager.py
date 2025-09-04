"""
manager.py
----------
FleetManager façade class.
Coordinates access to sub-managers (routes, vehicles, timetables, etc.).
"""

from . import database
from .services.route_manager import RouteManager


class FleetManager:
    """
    Entry point for all DB-backed fleet operations.
    Provides read-only access for simulation components.
    """

    def __init__(self):
        # initialize DB engine & session factory
        database.init_engine()
        self.db = database.SessionLocal()
        self.routes = RouteManager(self.db)

    def close(self):
        if self.db:
            self.db.close()
