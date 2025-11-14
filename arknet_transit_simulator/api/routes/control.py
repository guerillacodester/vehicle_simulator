"""Control endpoints for fleet management."""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_simulator
from ..models import CommandResponse

router = APIRouter(prefix="/api", tags=["control"])


@router.post("/vehicles/{vehicle_id}/start-engine", response_model=CommandResponse)
async def start_engine(vehicle_id: str, sim=Depends(get_simulator)):
    """Start the engine for a specific vehicle."""
    for driver in sim.active_drivers:
        if driver.vehicle_id == vehicle_id:
            if hasattr(driver, 'start_engine'):
                try:
                    result = await driver.start_engine()
                    return CommandResponse(
                        success=True,
                        message=f"Engine started for vehicle {vehicle_id}",
                        data={"result": result}
                    )
                except Exception as e:
                    return CommandResponse(
                        success=False,
                        message=f"Failed to start engine: {str(e)}"
                    )
            else:
                return CommandResponse(
                    success=False,
                    message=f"Vehicle {vehicle_id} does not support start_engine"
                )
    
    raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")


@router.post("/vehicles/{vehicle_id}/stop-engine", response_model=CommandResponse)
async def stop_engine(vehicle_id: str, sim=Depends(get_simulator)):
    """Stop the engine for a specific vehicle."""
    for driver in sim.active_drivers:
        if driver.vehicle_id == vehicle_id:
            if hasattr(driver, 'stop_engine'):
                try:
                    result = await driver.stop_engine()
                    return CommandResponse(
                        success=True,
                        message=f"Engine stopped for vehicle {vehicle_id}",
                        data={"result": result}
                    )
                except Exception as e:
                    return CommandResponse(
                        success=False,
                        message=f"Failed to stop engine: {str(e)}"
                    )
            else:
                return CommandResponse(
                    success=False,
                    message=f"Vehicle {vehicle_id} does not support stop_engine"
                )
    
    raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")


@router.post("/vehicles/{vehicle_id}/enable-boarding", response_model=CommandResponse)
async def enable_boarding(vehicle_id: str, sim=Depends(get_simulator)):
    """Enable passenger boarding for a specific vehicle."""
    for driver in sim.active_drivers:
        if driver.vehicle_id == vehicle_id:
            if hasattr(driver, 'conductor') and driver.conductor:
                driver.conductor.boarding_active = True
                return CommandResponse(
                    success=True,
                    message=f"Boarding enabled for vehicle {vehicle_id}"
                )
            else:
                return CommandResponse(
                    success=False,
                    message=f"No conductor found for vehicle {vehicle_id}"
                )
    
    raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")


@router.post("/vehicles/{vehicle_id}/disable-boarding", response_model=CommandResponse)
async def disable_boarding(vehicle_id: str, sim=Depends(get_simulator)):
    """Disable passenger boarding for a specific vehicle."""
    for driver in sim.active_drivers:
        if driver.vehicle_id == vehicle_id:
            if hasattr(driver, 'conductor') and driver.conductor:
                driver.conductor.boarding_active = False
                return CommandResponse(
                    success=True,
                    message=f"Boarding disabled for vehicle {vehicle_id}"
                )
            else:
                return CommandResponse(
                    success=False,
                    message=f"No conductor found for vehicle {vehicle_id}"
                )
    
    raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")


@router.post("/vehicles/{vehicle_id}/trigger-boarding", response_model=CommandResponse)
async def trigger_boarding(vehicle_id: str, sim=Depends(get_simulator)):
    """Manually trigger passenger boarding check for a specific vehicle."""
    for driver in sim.active_drivers:
        if driver.vehicle_id == vehicle_id:
            if hasattr(driver, 'conductor') and driver.conductor:
                conductor = driver.conductor
                if hasattr(conductor, 'current_vehicle_position') and conductor.current_vehicle_position:
                    lat, lon = conductor.current_vehicle_position
                    route_id = conductor.assigned_route_id
                    try:
                        boarded = await conductor.check_for_passengers(lat, lon, route_id)
                        return CommandResponse(
                            success=True,
                            message=f"Boarding check completed for vehicle {vehicle_id}",
                            data={"passengers_boarded": boarded}
                        )
                    except Exception as e:
                        return CommandResponse(
                            success=False,
                            message=f"Boarding check failed: {str(e)}"
                        )
                else:
                    return CommandResponse(
                        success=False,
                        message=f"No position available for vehicle {vehicle_id}"
                    )
            else:
                return CommandResponse(
                    success=False,
                    message=f"No conductor found for vehicle {vehicle_id}"
                )
    
    raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
