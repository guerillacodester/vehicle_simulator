"""
Vehicle CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.vehicle import Vehicle as VehicleModel
from ..schemas.vehicle import Vehicle, VehicleCreate, VehicleUpdate

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Vehicle)
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db)
):
    """Create a new vehicle"""
    db_vehicle = VehicleModel(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/", response_model=List[Vehicle])
def read_vehicles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all vehicles with pagination"""
    vehicles = db.query(VehicleModel).offset(skip).limit(limit).all()
    return vehicles

@router.get("/{vehicle_id}", response_model=Vehicle)
def read_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific vehicle by ID"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.get("/depot/{depot_id}", response_model=List[Vehicle])
def read_vehicles_by_depot(
    depot_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all vehicles for a specific depot"""
    vehicles = db.query(VehicleModel).filter(VehicleModel.depot_id == depot_id).all()
    return vehicles

@router.get("/status/{status}", response_model=List[Vehicle])
def read_vehicles_by_status(
    status: str,
    db: Session = Depends(get_db)
):
    """Get all vehicles with a specific status"""
    vehicles = db.query(VehicleModel).filter(VehicleModel.status == status).all()
    return vehicles

@router.get("/license/{license_plate}", response_model=Vehicle)
def read_vehicle_by_license(
    license_plate: str,
    db: Session = Depends(get_db)
):
    """Get a vehicle by license plate"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.license_plate == license_plate).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.put("/{vehicle_id}", response_model=Vehicle)
def update_vehicle(
    vehicle_id: UUID,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific vehicle"""
    db_vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    update_data = vehicle.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific vehicle"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(vehicle)
    db.commit()
    return {"message": "Vehicle deleted successfully"}

@router.put("/{vehicle_id}/assign-driver/{driver_id}")
def assign_driver_to_vehicle(
    vehicle_id: UUID,
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """Assign a driver to a vehicle"""
    # Check if vehicle exists
    vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Check if driver exists
    from ...models.driver import Driver as DriverModel
    driver = db.query(DriverModel).filter(DriverModel.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Assign driver to vehicle
    vehicle.assigned_driver_id = driver_id
    db.commit()
    db.refresh(vehicle)
    
    return {"message": "Driver assigned successfully", "vehicle_id": vehicle_id, "driver_id": driver_id}

@router.delete("/{vehicle_id}/unassign-driver")
def unassign_driver_from_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove driver assignment from a vehicle"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    vehicle.assigned_driver_id = None
    db.commit()
    db.refresh(vehicle)
    
    return {"message": "Driver unassigned successfully", "vehicle_id": vehicle_id}

@router.get("/all/detailed", response_model=List[dict])
def get_vehicles_detailed(
    db: Session = Depends(get_db)
):
    """Get all vehicles with detailed information including assigned driver and route"""
    from ...models.driver import Driver as DriverModel
    from ...models.route import Route as RouteModel
    from ...models.depot import Depot as DepotModel
    
    vehicles = db.query(VehicleModel).all()
    detailed_vehicles = []
    
    for vehicle in vehicles:
        # Get assigned driver details
        driver_info = None
        if vehicle.assigned_driver_id:
            driver = db.query(DriverModel).filter(DriverModel.driver_id == vehicle.assigned_driver_id).first()
            if driver:
                driver_info = {
                    "driver_id": str(driver.driver_id),
                    "name": driver.name,
                    "license_no": driver.license_no,
                    "employment_status": driver.employment_status
                }
        
        # Get route details
        route_info = None
        if vehicle.preferred_route_id:
            route = db.query(RouteModel).filter(RouteModel.route_id == vehicle.preferred_route_id).first()
            if route:
                route_info = {
                    "route_id": str(route.route_id),
                    "short_name": route.short_name,
                    "long_name": route.long_name
                }
        
        # Get depot details
        depot_info = None
        if vehicle.home_depot_id:
            depot = db.query(DepotModel).filter(DepotModel.depot_id == vehicle.home_depot_id).first()
            if depot:
                depot_info = {
                    "depot_id": str(depot.depot_id),
                    "name": depot.name
                }
        
        vehicle_detail = {
            "vehicle_id": str(vehicle.vehicle_id),
            "reg_code": vehicle.reg_code,
            "status": vehicle.status.value if hasattr(vehicle.status, 'value') else str(vehicle.status),
            "capacity": vehicle.capacity,
            "assigned_driver_id": str(vehicle.assigned_driver_id) if vehicle.assigned_driver_id else None,
            "assigned_driver": driver_info,
            "preferred_route_id": str(vehicle.preferred_route_id) if vehicle.preferred_route_id else None,
            "assigned_route": route_info,
            "home_depot_id": str(vehicle.home_depot_id) if vehicle.home_depot_id else None,
            "depot": depot_info,
            "created_at": vehicle.created_at,
            "updated_at": vehicle.updated_at
        }
        
        detailed_vehicles.append(vehicle_detail)
    
    return detailed_vehicles
