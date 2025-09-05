from __future__ import annotations
from fastapi import Depends
from ..manager import FleetManager
from ..services.route_manager import RouteManager

def get_fm():
    fm = FleetManager()     # opens SSH tunnel/engine per your database.py
    try:
        yield fm
    finally:
        fm.close()

def get_route_manager(fm: FleetManager = Depends(get_fm)) -> RouteManager:
    return fm.routes
