#!/usr/bin/env python3
"""
ArkNet Transit Simulator API Server
===================================

FastAPI-based REST API server for controlling and monitoring the transit simulator.
Allows real-time interaction with vehicles, passengers, routes, and drivers via HTTP endpoints.

Usage:
    cd api/
    python server.py
    
    # Or with custom settings:
    python server.py --host 0.0.0.0 --port 8090 --reload
"""

import asyncio
import logging
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global simulator state
simulator_state = {
    'process': None,
    'status': 'stopped',
    'start_time': None,
    'mode': None,
    'duration': None,
    'pid': None
}

# API Models
class SimulatorStartRequest(BaseModel):
    mode: str = "depot"
    duration: Optional[int] = 60
    debug: bool = False

class SimulatorStatus(BaseModel):
    status: str
    uptime_seconds: Optional[float] = None
    mode: Optional[str] = None
    duration: Optional[int] = None
    pid: Optional[int] = None

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
    spawn_rate_per_minute: float = 0.0
    memory_usage_mb: float = 0.0

class RouteInfo(BaseModel):
    route_id: str
    route_name: str
    vehicle_count: int = 0
    passenger_count: int = 0
    gps_points: int = 0
    status: str = "inactive"

class CommandResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage API server lifecycle"""
    logger.info("🚀 Starting ArkNet Transit Simulator API Server")
    yield
    logger.info("🛑 Shutting down ArkNet Transit Simulator API Server")
    # Clean up any running simulator processes
    if simulator_state['process']:
        try:
            simulator_state['process'].terminate()
            simulator_state['process'].wait(timeout=5)
        except:
            pass

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
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "simulator_status": simulator_state['status']
    }

# Simulator Control Endpoints
@app.post("/simulator/start", response_model=CommandResponse)
async def start_simulator(request: SimulatorStartRequest):
    """Start the transit simulator as a subprocess"""
    
    if simulator_state['status'] == 'running':
        raise HTTPException(status_code=400, detail="Simulator is already running")
    
    try:
        # Build command
        cmd = [
            sys.executable, "-m", "world.arknet_transit_simulator",
            "--mode", request.mode,
            "--duration", str(request.duration)
        ]
        
        if request.debug:
            cmd.append("--debug")
        
        # Change to parent directory to run simulator
        parent_dir = Path(__file__).parent.parent
        
        # Start simulator process
        process = subprocess.Popen(
            cmd,
            cwd=parent_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Update state
        simulator_state.update({
            'process': process,
            'status': 'running',
            'start_time': datetime.now(),
            'mode': request.mode,
            'duration': request.duration,
            'pid': process.pid
        })
        
        logger.info(f"Started simulator process {process.pid} with mode={request.mode}, duration={request.duration}")
        
        return CommandResponse(
            success=True,
            message=f"Simulator started successfully (PID: {process.pid})",
            data={
                "pid": process.pid,
                "mode": request.mode,
                "duration": request.duration,
                "debug": request.debug
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start simulator: {e}")
        simulator_state['status'] = 'error'
        raise HTTPException(status_code=500, detail=f"Failed to start simulator: {str(e)}")

@app.post("/simulator/stop", response_model=CommandResponse)
async def stop_simulator():
    """Stop the transit simulator"""
    
    if simulator_state['status'] != 'running':
        raise HTTPException(status_code=400, detail="Simulator is not running")
    
    try:
        process = simulator_state['process']
        if process and process.poll() is None:
            # Try graceful termination first
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                process.kill()
                process.wait()
        
        # Update state
        simulator_state.update({
            'process': None,
            'status': 'stopped',
            'start_time': None,
            'mode': None,
            'duration': None,
            'pid': None
        })
        
        logger.info("Simulator stopped successfully")
        
        return CommandResponse(
            success=True,
            message="Simulator stopped successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to stop simulator: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop simulator: {str(e)}")

@app.get("/simulator/status", response_model=SimulatorStatus)
async def get_simulator_status():
    """Get current simulator status"""
    
    # Check if process is still running
    if simulator_state['process']:
        if simulator_state['process'].poll() is None:
            # Process is still running
            uptime = None
            if simulator_state['start_time']:
                uptime = (datetime.now() - simulator_state['start_time']).total_seconds()
            
            return SimulatorStatus(
                status="running",
                uptime_seconds=uptime,
                mode=simulator_state['mode'],
                duration=simulator_state['duration'],
                pid=simulator_state['pid']
            )
        else:
            # Process has terminated
            simulator_state.update({
                'process': None,
                'status': 'stopped',
                'start_time': None,
                'mode': None,
                'duration': None,
                'pid': None
            })
    
    return SimulatorStatus(status="stopped")

@app.get("/simulator/output")
async def get_simulator_output(lines: int = Query(50, ge=1, le=1000)):
    """Get recent output from the simulator process"""
    
    if not simulator_state['process']:
        raise HTTPException(status_code=400, detail="Simulator is not running")
    
    try:
        # This is a simplified version - in practice you'd want to capture and buffer output
        return {
            "status": "running",
            "message": "Output capture not fully implemented yet",
            "lines_requested": lines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Comprehensive Status Endpoints

@app.get("/depot/status")
async def get_depot_status():
    """Get comprehensive depot status including depot manager and all components"""
    try:
        # TODO: Connect to actual simulator components
        return {
            "depot_name": "ArkNet Transit Depot", 
            "depot_state": "closed",
            "initialized": False,
            "message": "Depot status - requires active simulator connection",
            "components": {
                "depot_manager": {"status": "offline", "component_type": "DepotManager"},
                "dispatcher": {"status": "offline", "component_type": "Dispatcher"},
                "route_queue_builder": {"status": "offline", "component_type": "RouteQueueBuilder"},
                "passenger_service": {"status": "offline", "component_type": "PassengerServiceFactory"}
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/depot/manager")
async def get_depot_manager_status():
    """Get detailed depot manager status and system overview"""
    try:
        return {
            "manager_name": "DepotManager",
            "current_state": "closed",
            "initialized": False,
            "system_operational": False,
            "message": "Depot manager status - requires active simulator connection",
            "capabilities": [
                "Vehicle assignment validation",
                "Driver assignment coordination", 
                "Route distribution management",
                "Passenger service factory coordination",
                "Depot inventory reporting"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dispatcher/status")
async def get_dispatcher_status():
    """Get dispatcher component status and API connectivity"""
    try:
        return {
            "component_name": "Dispatcher",
            "current_state": "offline",
            "api_base_url": "http://localhost:8000",
            "api_connected": False,
            "message": "Dispatcher status - requires active simulator connection",
            "responsibilities": [
                "Fleet management API connectivity",
                "Vehicle assignment retrieval", 
                "Driver assignment coordination",
                "Route information distribution",
                "Real-time data synchronization"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vehicles")
async def get_all_vehicles():
    """Get comprehensive status of all vehicles"""
    try:
        return {
            "message": "Vehicle status - requires active simulator connection",
            "total_vehicles": 0,
            "active_vehicles": 0,
            "idle_vehicles": 0,
            "maintenance_vehicles": 0,
            "vehicles": [
                # Example structure for when connected to simulator
                # {
                #     "vehicle_id": "BUS_001",
                #     "driver_name": "John Smith",
                #     "driver_status": "ONBOARD",
                #     "route_id": "Route_1",
                #     "route_name": "City Center Loop",
                #     "engine_status": "ON",
                #     "gps_status": "ON", 
                #     "gps_position": {"lat": 13.1939, "lon": -59.5432},
                #     "passengers_on_board": 12,
                #     "conductor_present": True,
                #     "last_update": "2025-09-16T19:45:30"
                # }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vehicles/{vehicle_id}")
async def get_vehicle_status(vehicle_id: str):
    """Get detailed status for a specific vehicle"""
    try:
        return {
            "vehicle_id": vehicle_id,
            "message": f"Vehicle {vehicle_id} status - requires active simulator connection",
            "details": {
                "driver_info": None,
                "engine_info": None,
                "gps_info": None,
                "conductor_info": None,
                "passenger_info": None,
                "route_info": None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/drivers")
async def get_all_drivers():
    """Get comprehensive status of all drivers"""
    try:
        return {
            "message": "Driver status - requires active simulator connection",
            "total_drivers": 0,
            "active_drivers": 0,
            "idle_drivers": 0,
            "onboard_drivers": 0,
            "drivers": [
                # Example structure for when connected to simulator
                # {
                #     "driver_id": "DRV_001",
                #     "driver_name": "John Smith",
                #     "current_state": "ONBOARD",
                #     "vehicle_id": "BUS_001",
                #     "route_name": "City Center Loop",
                #     "gps_position": {"lat": 13.1939, "lon": -59.5432},
                #     "engine_status": "ON",
                #     "gps_device_status": "ON",
                #     "last_update": "2025-09-16T19:45:30"
                # }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/drivers/{driver_id}")
async def get_driver_status(driver_id: str):
    """Get detailed status for a specific driver"""
    try:
        return {
            "driver_id": driver_id,
            "message": f"Driver {driver_id} status - requires active simulator connection",
            "details": {
                "personal_info": None,
                "vehicle_assignment": None,
                "route_assignment": None,
                "current_position": None,
                "component_status": None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conductors")
async def get_all_conductors():
    """Get comprehensive status of all conductors"""
    try:
        return {
            "message": "Conductor status - requires active simulator connection", 
            "total_conductors": 0,
            "active_conductors": 0,
            "monitoring_conductors": 0,
            "boarding_conductors": 0,
            "conductors": [
                # Example structure for when connected to simulator
                # {
                #     "conductor_id": "CON_001",
                #     "conductor_name": "Mary Johnson",
                #     "conductor_state": "monitoring",
                #     "vehicle_id": "BUS_001",
                #     "assigned_route_id": "Route_1",
                #     "passengers_on_board": 12,
                #     "capacity": 40,
                #     "seats_available": 28,
                #     "monitored_passengers": 5,
                #     "boarding_queue": 2,
                #     "last_update": "2025-09-16T19:45:30"
                # }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conductors/{conductor_id}")
async def get_conductor_status(conductor_id: str):
    """Get detailed status for a specific conductor"""
    try:
        return {
            "conductor_id": conductor_id,
            "message": f"Conductor {conductor_id} status - requires active simulator connection",
            "details": {
                "personal_info": None,
                "operational_state": None,
                "passenger_management": None,
                "vehicle_coordination": None,
                "route_monitoring": None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gps/devices")
async def get_all_gps_devices():
    """Get status of all GPS devices across the fleet"""
    try:
        return {
            "message": "GPS devices status - requires active simulator connection",
            "total_devices": 0,
            "active_devices": 0,
            "offline_devices": 0,
            "transmitting_devices": 0,
            "devices": [
                # Example structure for when connected to simulator
                # {
                #     "device_id": "GPS_BUS_001",
                #     "vehicle_id": "BUS_001",
                #     "current_state": "ON",
                #     "last_position": {"lat": 13.1939, "lon": -59.5432},
                #     "last_transmission": "2025-09-16T19:45:30",
                #     "transmitter_connected": True,
                #     "plugin_active": True,
                #     "buffer_status": "active"
                # }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gps/telemetry")
async def get_gps_telemetry():
    """Get real-time GPS telemetry data from all active devices"""
    try:
        return {
            "message": "GPS telemetry - requires active simulator connection",
            "timestamp": datetime.now().isoformat(),
            "active_transmissions": 0,
            "telemetry_data": [
                # Example structure for when connected to simulator
                # {
                #     "device_id": "GPS_BUS_001",
                #     "vehicle_id": "BUS_001", 
                #     "lat": 13.1939,
                #     "lon": -59.5432,
                #     "speed": 35.5,
                #     "heading": 42.0,
                #     "altitude": 50.0,
                #     "timestamp": "2025-09-16T19:45:30",
                #     "accuracy": 3.2
                # }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/passengers/stats")
async def get_passenger_stats():
    """Get comprehensive passenger service statistics"""
    try:
        return {
            "message": "Passenger stats - requires active simulator connection",
            "total_scheduled": 0,
            "total_spawned": 0,
            "active_passengers": 0,
            "passengers_on_board": 0,
            "spawn_rate_per_minute": 0.0,
            "memory_usage_mb": 0.0,
            "stats": PassengerStats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/passengers/active")
async def get_active_passengers():
    """Get list of currently active passengers"""
    try:
        return {
            "message": "Active passengers - requires active simulator connection",
            "count": 0,
            "passengers": [
                # Example structure for when connected to simulator
                # {
                #     "passenger_id": "SCHED_11_0025",
                #     "status": "spawned",
                #     "spawn_time": "2025-09-16T19:02:43",
                #     "origin": "349m WSW of Center Street",
                #     "destination": "Downtown Terminal",
                #     "route_preference": "Route_1",
                #     "current_position": {"lat": 13.1939, "lon": -59.5432}
                # }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/routes")
async def get_all_routes():
    """Get comprehensive information about all routes"""
    try:
        return {
            "message": "Routes information - requires active simulator connection",
            "total_routes": 0,
            "active_routes": 0,
            "routes": [
                # Example structure for when connected to simulator
                # {
                #     "route_id": "Route_1",
                #     "route_name": "City Center Loop",
                #     "assigned_vehicles": 2,
                #     "total_gps_points": 343,
                #     "route_length_km": 12.5,
                #     "estimated_duration_minutes": 45,
                #     "passenger_demand": 25,
                #     "status": "active"
                # }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/routes/{route_id}")
async def get_route_info(route_id: str):
    """Get detailed information about a specific route"""
    try:
        return {
            "route_id": route_id,
            "message": f"Route {route_id} information - requires active simulator connection",
            "details": {
                "route_geometry": None,
                "assigned_vehicles": [],
                "passenger_demand": None,
                "gps_waypoints": None,
                "operational_status": None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Command execution endpoint
@app.post("/command", response_model=CommandResponse)
async def execute_command(command: str, args: Optional[List[str]] = None):
    """Execute a simulator command (for future extension)"""
    return CommandResponse(
        success=False,
        message=f"Command execution not yet implemented: {command}"
    )

# Command line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ArkNet Transit Simulator API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8090, help="Port to bind to")  
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    
    args = parser.parse_args()
    
    print(f"🚀 Starting ArkNet Transit Simulator API Server")
    print(f"📡 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 Interactive API: http://{args.host}:{args.port}/redoc")
    
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )