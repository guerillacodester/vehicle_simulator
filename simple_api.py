#!/usr/bin/env python3
"""
Simplified Vehicle Simulator API
===============================
Basic FastAPI server for testing fleet management integration
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import database and models
from api.database import get_db
from models.gtfs import Country, Vehicle, Route, Stop, Trip, Timetable

app = FastAPI(
    title="Vehicle Simulator API",
    description="Simplified API for fleet management integration testing",
    version="0.1.0"
)

# Import and include simulator control endpoints
try:
    from api.endpoints.simulator_control import router as simulator_router
    app.include_router(simulator_router, prefix="/api/v1/simulator", tags=["simulator"])
except ImportError:
    print("Warning: Simulator control endpoints not available")

# Setup static files and templates
app.mount("/static", StaticFiles(directory="api/static"), name="static")
templates = Jinja2Templates(directory="api/templates")

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Vehicle Simulator API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Basic GTFS endpoints for testing
@app.get("/api/v1/countries")
async def get_countries(db: Session = Depends(get_db)):
    countries = db.query(Country).all()
    return [{"country_id": str(c.country_id), "iso_code": c.iso_code, "name": c.name} for c in countries]

@app.get("/api/v1/vehicles")
async def get_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    return [{"vehicle_id": str(v.vehicle_id), "license_plate": v.license_plate, "status": v.status} for v in vehicles]

@app.get("/api/v1/routes")
async def get_routes(db: Session = Depends(get_db)):
    routes = db.query(Route).all()
    return [{"route_id": str(r.route_id), "route_name": r.route_name, "route_type": r.route_type} for r in routes]

@app.get("/api/v1/stops")
async def get_stops(db: Session = Depends(get_db)):
    stops = db.query(Stop).all()
    return [{"stop_id": str(s.stop_id), "stop_name": s.stop_name, "latitude": float(s.latitude), "longitude": float(s.longitude)} for s in stops]

@app.get("/api/v1/trips")
async def get_trips(db: Session = Depends(get_db)):
    trips = db.query(Trip).all()
    return [{"trip_id": str(t.trip_id), "trip_headsign": t.trip_headsign, "direction_id": t.direction_id} for t in trips]

@app.get("/api/v1/timetables")
async def get_timetables(db: Session = Depends(get_db)):
    timetables = db.query(Timetable).all()
    return [{"timetable_id": str(t.timetable_id), "service_pattern": t.service_pattern} for t in timetables]

if __name__ == "__main__":
    print("🚀 Starting Simplified Vehicle Simulator API...")
    print("📊 Health Check: http://localhost:8000/health")
    print("📖 Available endpoints:")
    print("   - GET /api/v1/countries")
    print("   - GET /api/v1/vehicles") 
    print("   - GET /api/v1/routes")
    print("   - GET /api/v1/stops")
    print("   - GET /api/v1/trips")
    print("   - GET /api/v1/timetables")
    print()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
