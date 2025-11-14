"""Conductor state endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_simulator
from ..models import ConductorResponse, ConductorListResponse

router = APIRouter(prefix="/api", tags=["conductors"])


@router.get("/conductors", response_model=ConductorListResponse)
async def list_conductors(sim=Depends(get_simulator)):
    """Get list of all conductors with their current state."""
    conductors = []
    
    for driver in sim.active_drivers:
        if hasattr(driver, 'conductor') and driver.conductor:
            conductor = driver.conductor
            
            cond = ConductorResponse(
                conductor_id=getattr(conductor, 'component_id', f"COND-{driver.vehicle_id}"),
                vehicle_id=driver.vehicle_id,
                conductor_name=conductor.person_name,
                conductor_state=conductor.conductor_state.value if hasattr(conductor, 'conductor_state') else 'UNKNOWN',
                passengers_on_board=getattr(conductor, 'passengers_on_board', 0),
                capacity=getattr(conductor, 'capacity', 0),
                boarding_active=getattr(conductor, 'boarding_active', False),
                depot_boarding_active=getattr(conductor, 'depot_boarding_active', False)
            )
            conductors.append(cond)
    
    return ConductorListResponse(
        conductors=conductors,
        total=len(conductors)
    )


@router.get("/conductors/{vehicle_id}", response_model=ConductorResponse)
async def get_conductor(vehicle_id: str, sim=Depends(get_simulator)):
    """Get detailed state of a specific conductor."""
    for driver in sim.active_drivers:
        if driver.vehicle_id == vehicle_id:
            if hasattr(driver, 'conductor') and driver.conductor:
                conductor = driver.conductor
                
                return ConductorResponse(
                    conductor_id=getattr(conductor, 'component_id', f"COND-{driver.vehicle_id}"),
                    vehicle_id=driver.vehicle_id,
                    conductor_name=conductor.person_name,
                    conductor_state=conductor.conductor_state.value if hasattr(conductor, 'conductor_state') else 'UNKNOWN',
                    passengers_on_board=getattr(conductor, 'passengers_on_board', 0),
                    capacity=getattr(conductor, 'capacity', 0),
                    boarding_active=getattr(conductor, 'boarding_active', False),
                    depot_boarding_active=getattr(conductor, 'depot_boarding_active', False)
                )
            else:
                raise HTTPException(status_code=404, detail=f"No conductor found for vehicle {vehicle_id}")
    
    raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
