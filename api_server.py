#!/usr/bin/env python3
"""
ArkNet Transit Simulator API Server
===================================

FastAPI-based REST API server for controlling and monitoring the transit simulator.
Allows real-time interaction with vehicles, passengers, routes, and drivers via HTTP endpoints.

Usage:
    python api_server.py
    
    # Or with custom settings:
    python api_server.py --host 0.0.0.0 --port 8080 --reload
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import simulator components (these will be adapted based on your actual structure)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'world'))

# We'll import these dynamically to avoid import errors
simulator_instance_data = {
    'simulator': None,
    'depot': None,
    'dispatcher': None,
    'start_time': None,
    'mode': None,
    'duration': None,
    'status': 'stopped'
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global simulator instance
simulator_instance: Optional[ArkNetTransitSimulator] = None
depot_instance: Optional[MainDepot] = None
dispatcher_instance: Optional[FleetDispatcher] = None

# API Models
class SimulatorStartRequest(BaseModel):
    mode: str = "depot"
    duration: Optional[int] = None
    debug: bool = False

class SimulatorStatus(BaseModel):
    status: str
    uptime_seconds: Optional[float] = None
    active_vehicles: int = 0
    active_passengers: int = 0
    active_routes: List[str] = []

class VehicleStatus(BaseModel):
    vehicle_id: str
    driver_name: Optional[str] = None
    route_id: Optional[str] = None
    status: str
    gps_enabled: bool = False
    engine_status: str = "unknown"
    location: Optional[Dict[str, float]] = None

class PassengerStats(BaseModel):
    total_scheduled: int = 0
    total_active: int = 0
    total_completed: int = 0
    spawn_rate_per_minute: float = 0.0
    memory_usage_mb: float = 0.0

class RouteInfo(BaseModel):
    route_id: str
    route_name: str
    vehicle_count: int = 0
    passenger_count: int = 0
    gps_points: int = 0
    status: str = "inactive"

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage simulator lifecycle"""
    logger.info("🚀 Starting ArkNet Transit Simulator API Server")
    yield
    logger.info("🛑 Shutting down ArkNet Transit Simulator API Server")
    if simulator_instance:
        await simulator_instance.shutdown()

# Initialize FastAPI app
app = FastAPI(
    title="ArkNet Transit Simulator API",
    description="REST API for controlling and monitoring the ArkNet Transit Simulator",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Simulator Control Endpoints
@app.post("/simulator/start")
async def start_simulator(request: SimulatorStartRequest, background_tasks: BackgroundTasks):
    """Start the transit simulator"""
    global simulator_instance, depot_instance, dispatcher_instance
    
    if simulator_instance and hasattr(simulator_instance, 'is_running') and simulator_instance.is_running:
        raise HTTPException(status_code=400, detail="Simulator is already running")
    
    try:
        # Initialize simulator
        simulator_instance = ArkNetTransitSimulator()
        
        # Start simulator in background
        background_tasks.add_task(
            run_simulator_background, 
            request.mode, 
            request.duration, 
            request.debug
        )
        
        return {
            "status": "starting",
            "mode": request.mode,
            "duration": request.duration,
            "debug": request.debug,
            "message": "Simulator initialization started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start simulator: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start simulator: {str(e)}")

@app.post("/simulator/stop")
async def stop_simulator():
    """Stop the transit simulator"""
    global simulator_instance
    
    if not simulator_instance:
        raise HTTPException(status_code=400, detail="Simulator is not running")
    
    try:
        await simulator_instance.shutdown()
        simulator_instance = None
        return {"status": "stopped", "message": "Simulator stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop simulator: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop simulator: {str(e)}")

@app.get("/simulator/status", response_model=SimulatorStatus)
async def get_simulator_status():
    """Get current simulator status"""
    if not simulator_instance:
        return SimulatorStatus(status="stopped")
    
    try:
        # Get status from simulator components
        active_vehicles = 0
        active_passengers = 0
        active_routes = []
        
        if depot_instance:
            active_vehicles = len(depot_instance.get_active_vehicles()) if hasattr(depot_instance, 'get_active_vehicles') else 0
            active_routes = depot_instance.get_active_routes() if hasattr(depot_instance, 'get_active_routes') else []
        
        return SimulatorStatus(
            status="running" if hasattr(simulator_instance, 'is_running') and simulator_instance.is_running else "unknown",
            active_vehicles=active_vehicles,
            active_passengers=active_passengers,
            active_routes=active_routes
        )
    except Exception as e:
        logger.error(f"Error getting simulator status: {e}")
        return SimulatorStatus(status="error")

# Vehicle Management Endpoints
@app.get("/vehicles", response_model=List[VehicleStatus])
async def get_all_vehicles():
    """Get status of all vehicles"""
    if not depot_instance:
        raise HTTPException(status_code=503, detail="Simulator not running")
    
    try:
        vehicles = []
        # Implementation depends on depot structure
        # This is a placeholder - you'll need to adapt based on your depot API
        return vehicles
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vehicles/{vehicle_id}", response_model=VehicleStatus)
async def get_vehicle_status(vehicle_id: str):
    """Get status of a specific vehicle"""
    if not depot_instance:
        raise HTTPException(status_code=503, detail="Simulator not running")
    
    try:
        # Implementation depends on depot structure
        # This is a placeholder
        raise HTTPException(status_code=404, detail="Vehicle not found")
    except Exception as e:
        logger.error(f"Error getting vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vehicles/{vehicle_id}/start")
async def start_vehicle(vehicle_id: str):
    """Start a specific vehicle"""
    if not depot_instance:
        raise HTTPException(status_code=503, detail="Simulator not running")
    
    try:
        # Implementation for starting vehicle
        return {"status": "started", "vehicle_id": vehicle_id}
    except Exception as e:
        logger.error(f"Error starting vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vehicles/{vehicle_id}/stop")
async def stop_vehicle(vehicle_id: str):
    """Stop a specific vehicle"""
    if not depot_instance:
        raise HTTPException(status_code=503, detail="Simulator not running")
    
    try:
        # Implementation for stopping vehicle
        return {"status": "stopped", "vehicle_id": vehicle_id}
    except Exception as e:
        logger.error(f"Error stopping vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Passenger Management Endpoints
@app.get("/passengers/stats", response_model=PassengerStats)
async def get_passenger_stats():
    """Get passenger service statistics"""
    if not depot_instance or not hasattr(depot_instance, 'passenger_service'):
        raise HTTPException(status_code=503, detail="Passenger service not available")
    
    try:
        service = depot_instance.passenger_service
        return PassengerStats(
            total_scheduled=len(getattr(service, 'scheduled_passengers', [])),
            total_active=len(getattr(service, 'active_passengers', {})),
            spawn_rate_per_minute=getattr(service.stats, 'spawn_rate_per_minute', 0.0) if hasattr(service, 'stats') else 0.0,
            memory_usage_mb=service.get_memory_usage() if hasattr(service, 'get_memory_usage') else 0.0
        )
    except Exception as e:
        logger.error(f"Error getting passenger stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/passengers/scheduled")
async def get_scheduled_passengers(limit: int = Query(10, ge=1, le=100)):
    """Get list of scheduled passengers"""
    if not depot_instance or not hasattr(depot_instance, 'passenger_service'):
        raise HTTPException(status_code=503, detail="Passenger service not available")
    
    try:
        service = depot_instance.passenger_service
        scheduled = getattr(service, 'scheduled_passengers', [])
        return {"passengers": scheduled[:limit], "total": len(scheduled)}
    except Exception as e:
        logger.error(f"Error getting scheduled passengers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/passengers/active")
async def get_active_passengers(limit: int = Query(10, ge=1, le=100)):
    """Get list of active passengers"""
    if not depot_instance or not hasattr(depot_instance, 'passenger_service'):
        raise HTTPException(status_code=503, detail="Passenger service not available")
    
    try:
        service = depot_instance.passenger_service
        active = getattr(service, 'active_passengers', {})
        active_list = list(active.values())[:limit]
        return {"passengers": active_list, "total": len(active)}
    except Exception as e:
        logger.error(f"Error getting active passengers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route Management Endpoints
@app.get("/routes", response_model=List[RouteInfo])
async def get_all_routes():
    """Get information about all routes"""
    if not dispatcher_instance:
        raise HTTPException(status_code=503, detail="Dispatcher not available")
    
    try:
        routes = []
        # Implementation depends on dispatcher structure
        return routes
    except Exception as e:
        logger.error(f"Error getting routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/routes/{route_id}", response_model=RouteInfo)
async def get_route_info(route_id: str):
    """Get detailed information about a specific route"""
    if not dispatcher_instance:
        raise HTTPException(status_code=503, detail="Dispatcher not available")
    
    try:
        # Implementation for getting route info
        raise HTTPException(status_code=404, detail="Route not found")
    except Exception as e:
        logger.error(f"Error getting route {route_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Driver Management Endpoints
@app.get("/drivers")
async def get_all_drivers():
    """Get status of all drivers"""
    if not depot_instance:
        raise HTTPException(status_code=503, detail="Simulator not running")
    
    try:
        drivers = []
        # Implementation for getting driver info
        return {"drivers": drivers}
    except Exception as e:
        logger.error(f"Error getting drivers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/drivers/{driver_id}")
async def get_driver_status(driver_id: str):
    """Get status of a specific driver"""
    if not depot_instance:
        raise HTTPException(status_code=503, detail="Simulator not running")
    
    try:
        # Implementation for getting specific driver info
        raise HTTPException(status_code=404, detail="Driver not found")
    except Exception as e:
        logger.error(f"Error getting driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for running simulator
async def run_simulator_background(mode: str, duration: Optional[int], debug: bool):
    """Run simulator in background"""
    global simulator_instance, depot_instance, dispatcher_instance
    
    try:
        logger.info(f"Starting simulator in background: mode={mode}, duration={duration}, debug={debug}")
        
        # This is where you'd integrate your existing simulator logic
        # You'll need to adapt your main simulator code to work asynchronously
        
        # For now, this is a placeholder
        await asyncio.sleep(1)  # Simulate initialization
        
        # Set up depot and dispatcher references
        if simulator_instance:
            depot_instance = getattr(simulator_instance, 'depot', None)
            dispatcher_instance = getattr(simulator_instance, 'dispatcher', None)
        
        logger.info("Simulator background task started successfully")
        
    except Exception as e:
        logger.error(f"Error in simulator background task: {e}")
        simulator_instance = None

# Command line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ArkNet Transit Simulator API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8090, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    
    args = parser.parse_args()
    
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )