"""Simulator lifecycle control endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_simulator
from ..models import CommandResponse

router = APIRouter(prefix="/api/sim", tags=["simulator"])


class SimulatorStatus(BaseModel):
    """Simulator status response"""
    running: bool
    sim_time: Optional[datetime] = None
    active_vehicles: int
    idle_vehicles: int


class SetTimeRequest(BaseModel):
    """Request to set simulation time"""
    sim_time: datetime


@router.get("/status", response_model=SimulatorStatus)
async def get_simulator_status(sim=Depends(get_simulator)):
    """Get simulator running status and current time."""
    return SimulatorStatus(
        running=sim.is_running(),
        sim_time=sim.get_sim_time(),
        active_vehicles=len(sim.active_drivers),
        idle_vehicles=len(sim.idle_drivers)
    )


@router.post("/pause", response_model=CommandResponse)
async def pause_simulator(sim=Depends(get_simulator)):
    """Pause the simulator."""
    success = sim.pause()
    return CommandResponse(
        success=success,
        message="Simulator paused" if success else "Simulator already paused"
    )


@router.post("/resume", response_model=CommandResponse)
async def resume_simulator(sim=Depends(get_simulator)):
    """Resume the simulator."""
    success = sim.resume()
    return CommandResponse(
        success=success,
        message="Simulator resumed" if success else "Simulator already running"
    )


@router.post("/stop", response_model=CommandResponse)
async def stop_simulator(sim=Depends(get_simulator)):
    """Stop the simulator (triggers shutdown)."""
    success = sim.stop()
    return CommandResponse(
        success=success,
        message="Simulator stop requested" if success else "Simulator already stopped"
    )


@router.post("/set-time", response_model=CommandResponse)
async def set_simulation_time(request: SetTimeRequest, sim=Depends(get_simulator)):
    """Set the simulation time."""
    try:
        sim.set_sim_time(request.sim_time)
        return CommandResponse(
            success=True,
            message=f"Simulation time set to {request.sim_time}",
            data={"sim_time": request.sim_time.isoformat()}
        )
    except Exception as e:
        return CommandResponse(
            success=False,
            message=f"Failed to set time: {str(e)}"
        )
