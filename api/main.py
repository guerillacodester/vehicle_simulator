#!/usr/bin/env python3
"""
Vehicle Simulator API
====================
FastAPI-based remote interface for fleet management and simulator control.

Two main wings:
1. Fleet Management - Upload routes, timetables, vehicles by country
2. Simulator Control - Start/stop simulation remotely
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
from contextlib import asynccontextmanager

from fleet_management.routes import router as fleet_router
from simulator_control.routes import router as sim_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(fleet_router, prefix="/fleet", tags=["Fleet Management"])
app.include_router(sim_router, prefix="/simulator", tags=["Simulator Control"])

# Include GTFS API endpoints
from .endpoints import api_router
app.include_router(api_router, prefix="/api/v1", tags=["GTFS API"])

# Serve static files for uploads and assets
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/fleet-management", response_class=HTMLResponse)
async def fleet_management_interface(request: Request):
    """Professional fleet management interface"""
    return templates.TemplateResponse("fleet-management.html", {"request": request})

@app.get("/simulator-control", response_class=HTMLResponse)
async def simulator_control_interface(request: Request):
    """Professional simulator control interface"""
    return templates.TemplateResponse("simulator-control.html", {"request": request})

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
