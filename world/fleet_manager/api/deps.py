# world/fleet_manager/api/deps.py
from __future__ import annotations
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

# ✅ import the module, not the name
from .. import database
from ..manager import FleetManager
from ..services.route_manager import RouteManager
from ..services.shape_manager import ShapeManager

def get_db():
    # Optional guard
    if database.SessionLocal is None:
        raise HTTPException(status_code=503, detail="DB not initialized")
    db: Session = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_fm(db: Session = Depends(get_db)) -> FleetManager:
    return FleetManager(db)

def get_route_manager(db: Session = Depends(get_db)) -> RouteManager:
    return RouteManager(db)

def get_shape_manager(db: Session = Depends(get_db)) -> ShapeManager:
    return ShapeManager(db)
