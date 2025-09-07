#!/usr/bin/env python3
"""
Vehicle Simulator API
====================
FastAPI-based remote interface for fleet management and simulator control.

Two main wings:
1. Fleet Management - Upload routes, timetables, vehicles by country
2. Simulator Control - Start/stop simulation remotely
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn
import logging
from contextlib import asynccontextmanager

# Import database and models
from .database import get_db
from models.gtfs.country import Country

# Import GTFS API endpoints
from .endpoints.countries import router as countries_router
from .endpoints.vehicles import router as vehicles_router
from .endpoints.routes import router as routes_router
from .endpoints.stops import router as stops_router
from .endpoints.trips import router as trips_router
from .endpoints.timetables import router as timetables_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import existing fleet management (we'll update this)
try:
    from fleet_management.routes import router as fleet_router
except ImportError:
    logger.warning("Fleet management routes not found, will create placeholder")
    fleet_router = None

try:
    from api.endpoints.simulator_control import router as sim_router  
except ImportError:
    logger.warning("Simulator control routes not found, will create placeholder")
    sim_router = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🚀 Vehicle Simulator API starting up...")
    yield
    logger.info("🛑 Vehicle Simulator API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Vehicle Simulator API",
    description="Remote interface for fleet management and simulator control",
    version="1.0.0",
    lifespan=lifespan
)

# Setup templates
templates = Jinja2Templates(directory="api/templates")

# Include routers
if fleet_router:
    app.include_router(fleet_router, prefix="/fleet", tags=["Fleet Management"])
if sim_router:
    app.include_router(sim_router, prefix="/api/v1/simulator", tags=["Simulator Control"])

# Include GTFS API endpoints
app.include_router(countries_router, prefix="/api/v1", tags=["Countries"])
app.include_router(vehicles_router, prefix="/api/v1", tags=["Vehicles"])
app.include_router(routes_router, prefix="/api/v1", tags=["Routes"])
app.include_router(stops_router, prefix="/api/v1", tags=["Stops"])
app.include_router(trips_router, prefix="/api/v1", tags=["Trips"])
app.include_router(timetables_router, prefix="/api/v1", tags=["Timetables"])

# Serve static files for uploads and assets
app.mount("/static", StaticFiles(directory="api/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/fleet-management", response_class=HTMLResponse)
async def fleet_management_interface(request: Request):
    """Professional fleet management interface"""
    return templates.TemplateResponse("fleet-management.html", {"request": request})

@app.get("/simulator-control", response_class=HTMLResponse)
async def simulator_control_interface(request: Request, db: Session = Depends(get_db)):
    """Professional simulator control interface"""
    try:
        # Fetch countries from database
        countries = db.query(Country).all()
        countries_list = [{"code": country.country_code, "name": country.country_name} for country in countries]
    except Exception as e:
        # Fallback to hardcoded countries if database fails
        logger.warning(f"Failed to fetch countries from database: {e}")
        countries_list = [
            {"code": "barbados", "name": "Barbados"},
            {"code": "trinidad", "name": "Trinidad & Tobago"},
            {"code": "jamaica", "name": "Jamaica"}
        ]
    
    return templates.TemplateResponse("simulator-control.html", {
        "request": request,
        "countries": countries_list
    })

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard - Professional fleet management interface"""
    return templates.TemplateResponse("fleet-management.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vehicle_simulator_api"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
