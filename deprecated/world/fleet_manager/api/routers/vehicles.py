"""
Vehicle CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from ..dependencies import get_db
from ...models.vehicle import Vehicle as VehicleModel
from ..schemas.vehicle import (
    Vehicle, VehicleCreate, VehicleUpdate,
    VehiclePublic, VehiclePublicCreate, VehiclePublicUpdate,
    VehiclePerformance, VehiclePerformanceUpdate, PerformanceProfile
)

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    responses={404: {"description": "Not found"}},
)



@router.get("/public", response_model=List[VehiclePublic])
def read_vehicles_public(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all vehicles without UUIDs for enhanced security"""
    vehicles = db.query(VehicleModel).offset(skip).limit(limit).all()
    # Convert to public schema (excludes UUIDs)
    return [VehiclePublic(
        reg_code=vehicle.reg_code,
        status=vehicle.status,
        profile_id=vehicle.profile_id,
        notes=vehicle.notes,
        max_speed_kmh=vehicle.max_speed_kmh,
        acceleration_mps2=vehicle.acceleration_mps2,
        braking_mps2=vehicle.braking_mps2,
        eco_mode=vehicle.eco_mode,
        performance_profile=vehicle.performance_profile
    ) for vehicle in vehicles]

@router.post("/public", response_model=VehiclePublic)
def create_vehicle_public(
    vehicle: VehiclePublicCreate,
    db: Session = Depends(get_db)
):
    """Create a new vehicle using PUBLIC API with business identifiers only - NO UUIDs"""
    from ...models.country import Country as CountryModel
    from ...models.depot import Depot as DepotModel
    from ...models.route import Route as RouteModel
    
    # Look up UUIDs from business identifiers (internal use only)
    country_id = None
    if vehicle.country_code:
        country = db.query(CountryModel).filter(CountryModel.iso_code == vehicle.country_code).first()
        if country:
            country_id = country.country_id
        else:
            raise HTTPException(status_code=400, detail=f"Country code '{vehicle.country_code}' not found")
    else:
        # Default to first available country if none specified
        default_country = db.query(CountryModel).first()
        if default_country:
            country_id = default_country.country_id
        else:
            raise HTTPException(status_code=500, detail="No countries configured in system")
    
    depot_id = None  
    if vehicle.depot_name:
        depot = db.query(DepotModel).filter(DepotModel.name == vehicle.depot_name).first()
        if depot:
            depot_id = depot.depot_id
    
    route_id = None
    if vehicle.preferred_route_code:
        route = db.query(RouteModel).filter(RouteModel.short_name == vehicle.preferred_route_code).first()
        if route:
            route_id = route.route_id
    
    # Create vehicle with internal UUIDs (hidden from response)
    db_vehicle = VehicleModel(
        reg_code=vehicle.reg_code,
        status=vehicle.status,
        capacity=vehicle.capacity,
        profile_id=vehicle.profile_id,
        notes=vehicle.notes,
        country_id=country_id,
        home_depot_id=depot_id,
        preferred_route_id=route_id
    )
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    
    # Return public schema (no UUIDs)
    return VehiclePublic(
        reg_code=db_vehicle.reg_code,
        status=db_vehicle.status,
        profile_id=db_vehicle.profile_id,
        notes=db_vehicle.notes
    )

@router.get("/public/{reg_code}", response_model=VehiclePublic)
def read_vehicle_public(
    reg_code: str,
    db: Session = Depends(get_db)
):
    """Get a specific vehicle by registration code - PUBLIC API with NO UUIDs"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.reg_code == reg_code).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {reg_code} not found")
    
    return VehiclePublic(
        reg_code=vehicle.reg_code,
        status=vehicle.status,
        profile_id=vehicle.profile_id,
        notes=vehicle.notes
    )

@router.put("/public/{reg_code}", response_model=VehiclePublic)
def update_vehicle_public(
    reg_code: str,
    vehicle_update: VehiclePublicUpdate,
    db: Session = Depends(get_db)
):
    """Update a vehicle using PUBLIC API with business identifiers only - NO UUIDs"""
    from ...models.depot import Depot as DepotModel
    from ...models.route import Route as RouteModel
    
    # Find vehicle by registration code
    db_vehicle = db.query(VehicleModel).filter(VehicleModel.reg_code == reg_code).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {reg_code} not found")
    
    # Update basic fields
    if vehicle_update.status is not None:
        db_vehicle.status = vehicle_update.status
    if vehicle_update.capacity is not None:
        db_vehicle.capacity = vehicle_update.capacity
    if vehicle_update.profile_id is not None:
        db_vehicle.profile_id = vehicle_update.profile_id
    if vehicle_update.notes is not None:
        db_vehicle.notes = vehicle_update.notes
    
    # Update depot assignment using business identifier
    if vehicle_update.depot_name is not None:
        depot = db.query(DepotModel).filter(DepotModel.name == vehicle_update.depot_name).first()
        if depot:
            db_vehicle.home_depot_id = depot.depot_id
        else:
            raise HTTPException(status_code=400, detail=f"Depot '{vehicle_update.depot_name}' not found")
    
    # Update route assignment using business identifier  
    if vehicle_update.preferred_route_code is not None:
        route = db.query(RouteModel).filter(RouteModel.short_name == vehicle_update.preferred_route_code).first()
        if route:
            db_vehicle.preferred_route_id = route.route_id
        else:
            raise HTTPException(status_code=400, detail=f"Route '{vehicle_update.preferred_route_code}' not found")
    
    db.commit()
    db.refresh(db_vehicle)
    
    # Return public schema (no UUIDs)
    return VehiclePublic(
        reg_code=db_vehicle.reg_code,
        status=db_vehicle.status,
        profile_id=db_vehicle.profile_id,
        notes=db_vehicle.notes
    )

@router.delete("/public/{reg_code}")
def delete_vehicle_public(
    reg_code: str,
    db: Session = Depends(get_db)
):
    """Delete a vehicle using PUBLIC API with business identifier - NO UUIDs"""
    db_vehicle = db.query(VehicleModel).filter(VehicleModel.reg_code == reg_code).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {reg_code} not found")
    
    db.delete(db_vehicle)
    db.commit()
    return {"message": f"Vehicle {reg_code} deleted successfully"}



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


# Performance Management Endpoints

@router.get("/public/{reg_code}/performance", response_model=VehiclePerformance)
def get_vehicle_performance_public(
    reg_code: str,
    db: Session = Depends(get_db)
):
    """Get vehicle performance characteristics by registration code"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.reg_code == reg_code).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle with registration '{reg_code}' not found")
    
    return VehiclePerformance(
        max_speed_kmh=vehicle.max_speed_kmh,
        acceleration_mps2=vehicle.acceleration_mps2,
        braking_mps2=vehicle.braking_mps2,
        eco_mode=vehicle.eco_mode,
        performance_profile=vehicle.performance_profile
    )


@router.put("/public/{reg_code}/performance", response_model=VehiclePerformance)
def update_vehicle_performance_public(
    reg_code: str,
    performance: VehiclePerformanceUpdate,
    db: Session = Depends(get_db)
):
    """Update vehicle performance characteristics by registration code"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.reg_code == reg_code).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle with registration '{reg_code}' not found")
    
    # Update performance fields if provided
    update_data = performance.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)
    
    # Update timestamp
    vehicle.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(vehicle)
    
    return VehiclePerformance(
        max_speed_kmh=vehicle.max_speed_kmh,
        acceleration_mps2=vehicle.acceleration_mps2,
        braking_mps2=vehicle.braking_mps2,
        eco_mode=vehicle.eco_mode,
        performance_profile=vehicle.performance_profile
    )


@router.get("/public/performance-profiles", response_model=List[PerformanceProfile])
def get_available_performance_profiles():
    """Get list of available performance profiles"""
    profiles = [
        PerformanceProfile(
            name="standard",
            max_speed_kmh=25.0,
            acceleration_mps2=1.2,
            braking_mps2=1.8,
            eco_mode=False,
            description="Standard city bus performance"
        ),
        PerformanceProfile(
            name="eco",
            max_speed_kmh=20.0,
            acceleration_mps2=0.8,
            braking_mps2=1.5,
            eco_mode=True,
            description="Eco-friendly, fuel-efficient driving"
        ),
        PerformanceProfile(
            name="performance",
            max_speed_kmh=35.0,
            acceleration_mps2=1.8,
            braking_mps2=2.2,
            eco_mode=False,
            description="High-performance characteristics"
        ),
        PerformanceProfile(
            name="express",
            max_speed_kmh=50.0,
            acceleration_mps2=2.0,
            braking_mps2=2.5,
            eco_mode=False,
            description="Express route high-speed performance"
        )
    ]
    return profiles


@router.put("/public/{reg_code}/performance/apply-profile", response_model=VehiclePerformance)
def apply_performance_profile_public(
    reg_code: str,
    profile_name: str,
    db: Session = Depends(get_db)
):
    """Apply a pre-defined performance profile to a vehicle"""
    vehicle = db.query(VehicleModel).filter(VehicleModel.reg_code == reg_code).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle with registration '{reg_code}' not found")
    
    # Get available profiles
    profiles = {
        "standard": {"max_speed_kmh": 25.0, "acceleration_mps2": 1.2, "braking_mps2": 1.8, "eco_mode": False},
        "eco": {"max_speed_kmh": 20.0, "acceleration_mps2": 0.8, "braking_mps2": 1.5, "eco_mode": True},
        "performance": {"max_speed_kmh": 35.0, "acceleration_mps2": 1.8, "braking_mps2": 2.2, "eco_mode": False},
        "express": {"max_speed_kmh": 50.0, "acceleration_mps2": 2.0, "braking_mps2": 2.5, "eco_mode": False}
    }
    
    if profile_name not in profiles:
        raise HTTPException(status_code=400, detail=f"Profile '{profile_name}' not found. Available: {list(profiles.keys())}")
    
    # Apply profile settings
    profile_data = profiles[profile_name]
    vehicle.max_speed_kmh = profile_data["max_speed_kmh"]
    vehicle.acceleration_mps2 = profile_data["acceleration_mps2"]
    vehicle.braking_mps2 = profile_data["braking_mps2"]
    vehicle.eco_mode = profile_data["eco_mode"]
    vehicle.performance_profile = profile_name
    vehicle.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(vehicle)
    
    return VehiclePerformance(
        max_speed_kmh=vehicle.max_speed_kmh,
        acceleration_mps2=vehicle.acceleration_mps2,
        braking_mps2=vehicle.braking_mps2,
        eco_mode=vehicle.eco_mode,
        performance_profile=vehicle.performance_profile
    )
