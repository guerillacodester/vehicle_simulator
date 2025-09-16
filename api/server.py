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

# Placeholder endpoints for future implementation
@app.get("/vehicles")
async def get_all_vehicles():
    """Get status of all vehicles (placeholder)"""
    return {
        "message": "Vehicle status endpoint - to be implemented",
        "vehicles": []
    }

@app.get("/passengers/stats")
async def get_passenger_stats():
    """Get passenger service statistics (placeholder)"""
    return {
        "message": "Passenger stats endpoint - to be implemented",
        "stats": PassengerStats()
    }

@app.get("/routes")
async def get_all_routes():
    """Get information about all routes (placeholder)"""
    return {
        "message": "Routes endpoint - to be implemented",
        "routes": []
    }

@app.get("/drivers")
async def get_all_drivers():
    """Get status of all drivers (placeholder)"""
    return {
        "message": "Drivers endpoint - to be implemented", 
        "drivers": []
    }

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