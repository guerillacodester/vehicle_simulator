"""Vehicle state endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..dependencies import get_simulator
from ..models import VehicleResponse, DriverListResponse

router = APIRouter(prefix="/api", tags=["vehicles"])


@router.get("/vehicles", response_model=DriverListResponse)
async def list_vehicles(sim=Depends(get_simulator)):
    """Get list of all vehicles with their current state."""
    vehicles = []
    
    for driver in sim.active_drivers:
        # Get conductor info if available
        passenger_count = 0
        capacity = 0
        boarding_active = False
        
        if hasattr(driver, 'conductor') and driver.conductor:
            conductor = driver.conductor
            passenger_count = getattr(conductor, 'passengers_on_board', 0)
            capacity = getattr(conductor, 'capacity', 0)
            boarding_active = getattr(conductor, 'boarding_active', False)
        
        # Get engine state
        engine_running = False
        if hasattr(driver, 'engine') and driver.engine:
            engine_running = getattr(driver.engine, 'running', False)
        
        # Get GPS state
        gps_running = False
        if hasattr(driver, 'gps_device') and driver.gps_device:
            gps_running = True  # If device exists, it's running
        
        # Get position
        current_lat = None
        current_lon = None
        if hasattr(driver, 'conductor') and driver.conductor:
            if hasattr(driver.conductor, 'current_vehicle_position') and driver.conductor.current_vehicle_position:
                current_lat, current_lon = driver.conductor.current_vehicle_position
        
        vehicle = VehicleResponse(
            vehicle_id=driver.vehicle_id,
            driver_id=getattr(driver, 'component_id', driver.vehicle_id),
            driver_name=driver.person_name,
            route_id=getattr(driver, 'assigned_route_id', None),
            current_lat=current_lat,
            current_lon=current_lon,
            driver_state=driver.current_state.value if hasattr(driver, 'current_state') else 'UNKNOWN',
            engine_running=engine_running,
            gps_running=gps_running,
            passenger_count=passenger_count,
            capacity=capacity,
            boarding_active=boarding_active
        )
        vehicles.append(vehicle)
    
    return DriverListResponse(
        drivers=vehicles,
        total=len(vehicles)
    )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str, sim=Depends(get_simulator)):
    """Get detailed state of a specific vehicle."""
    for driver in sim.active_drivers:
        if driver.vehicle_id == vehicle_id:
            # Get conductor info
            passenger_count = 0
            capacity = 0
            boarding_active = False
            
            if hasattr(driver, 'conductor') and driver.conductor:
                conductor = driver.conductor
                passenger_count = getattr(conductor, 'passengers_on_board', 0)
                capacity = getattr(conductor, 'capacity', 0)
                boarding_active = getattr(conductor, 'boarding_active', False)
            
            # Get engine state
            engine_running = False
            if hasattr(driver, 'engine') and driver.engine:
                engine_running = getattr(driver.engine, 'running', False)
            
            # Get GPS state
            gps_running = False
            if hasattr(driver, 'gps_device') and driver.gps_device:
                gps_running = True
            
            # Get position
            current_lat = None
            current_lon = None
            if hasattr(driver, 'conductor') and driver.conductor:
                if hasattr(driver.conductor, 'current_vehicle_position') and driver.conductor.current_vehicle_position:
                    current_lat, current_lon = driver.conductor.current_vehicle_position
            
            return VehicleResponse(
                vehicle_id=driver.vehicle_id,
                driver_id=getattr(driver, 'component_id', driver.vehicle_id),
                driver_name=driver.person_name,
                route_id=getattr(driver, 'assigned_route_id', None),
                current_lat=current_lat,
                current_lon=current_lon,
                driver_state=driver.current_state.value if hasattr(driver, 'current_state') else 'UNKNOWN',
                engine_running=engine_running,
                gps_running=gps_running,
                passenger_count=passenger_count,
                capacity=capacity,
                boarding_active=boarding_active
            )
    
    raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
