"""
Simulator Control Routes
=======================
Handle starting, stopping, and monitoring vehicle simulations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

from .services import SimulatorService
from .models import SimulationRequest, SimulationStatus, VehicleStatus

logger = logging.getLogger(__name__)
router = APIRouter()
sim_service = SimulatorService()

@router.post("/start", response_model=SimulationStatus)
async def start_simulation(
    background_tasks: BackgroundTasks,
    request: SimulationRequest
):
    """
    Start a vehicle simulation
    
    - **country**: Country to simulate (optional, default: all)
    - **duration_seconds**: How long to run simulation (default: 60)
    - **update_interval**: Update frequency in seconds (default: 1.0)
    - **gps_enabled**: Enable GPS transmission (default: true)
    """
    try:
        logger.info(f"▶️ Starting simulation for {request.country or 'all countries'}")
        
        # Check if simulation is already running
        if sim_service.is_running():
            raise HTTPException(
                status_code=409, 
                detail="Simulation is already running. Stop current simulation first."
            )
        
        # Start simulation in background
        background_tasks.add_task(
            sim_service.start_simulation,
            request.country,
            request.duration_seconds,
            request.update_interval,
            request.gps_enabled
        )
        
        return SimulationStatus(
            is_running=True,
            country=request.country,
            start_time=datetime.now(),
            duration_seconds=request.duration_seconds,
            update_interval=request.update_interval,
            gps_enabled=request.gps_enabled,
            message="Simulation started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_simulation():
    """
    Stop the currently running simulation
    """
    try:
        logger.info("⏹️ Stopping simulation")
        
        if not sim_service.is_running():
            raise HTTPException(status_code=404, detail="No simulation is currently running")
        
        await sim_service.stop_simulation()
        
        return {"message": "Simulation stopped successfully", "stopped_at": datetime.now()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error stopping simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=SimulationStatus)
async def simulation_status():
    """
    Get current simulation status
    """
    try:
        status = await sim_service.get_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting simulation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles", response_model=List[VehicleStatus])
async def list_active_vehicles():
    """
    Get list of currently active vehicles in simulation
    """
    try:
        vehicles = await sim_service.get_active_vehicles()
        return vehicles
        
    except Exception as e:
        logger.error(f"❌ Error getting active vehicles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle_details(vehicle_id: str):
    """
    Get detailed information about a specific vehicle
    """
    try:
        vehicle = await sim_service.get_vehicle_details(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
        return vehicle
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vehicles/{vehicle_id}/activate")
async def activate_vehicle(vehicle_id: str):
    """
    Activate a specific vehicle in the simulation
    """
    try:
        result = await sim_service.activate_vehicle(vehicle_id)
        return {"message": f"Vehicle {vehicle_id} activated", "vehicle": result}
        
    except Exception as e:
        logger.error(f"❌ Error activating vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vehicles/{vehicle_id}/deactivate")
async def deactivate_vehicle(vehicle_id: str):
    """
    Deactivate a specific vehicle in the simulation
    """
    try:
        result = await sim_service.deactivate_vehicle(vehicle_id)
        return {"message": f"Vehicle {vehicle_id} deactivated", "vehicle": result}
        
    except Exception as e:
        logger.error(f"❌ Error deactivating vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_simulation_logs(lines: int = 100):
    """
    Get recent simulation logs
    
    - **lines**: Number of recent log lines to return (default: 100)
    """
    try:
        logs = await sim_service.get_logs(lines)
        return {"logs": logs, "lines_returned": len(logs)}
        
    except Exception as e:
        logger.error(f"❌ Error getting logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_simulation_metrics():
    """
    Get simulation performance metrics
    """
    try:
        metrics = await sim_service.get_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
