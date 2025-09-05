from __future__ import annotations
from fastapi import Depends
from ..manager import FleetManager
from ..services.route_manager import RouteManager
from ..services.shape_manager import ShapeManager

def get_fm():
    fm = FleetManager()     # opens SSH tunnel/engine per your database.py
    try:
        yield fm
    finally:
        fm.close()

def get_route_manager(fm: FleetManager = Depends(get_fm)) -> RouteManager:
    return fm.routes

def get_shape_manager(fm=Depends(get_fm)) -> ShapeManager:
    return fm.shapes