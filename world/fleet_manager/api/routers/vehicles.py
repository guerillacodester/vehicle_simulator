# world/fleet_manager/api/routers/vehicles.py
from fastapi import APIRouter, Depends, HTTPException
from .. import deps
from ..schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])


@router.get("/", response_model=list[VehicleRead])
def list_vehicles(fm=Depends(deps.get_fm)):
    vehicles = fm.vehicles.list_vehicles()
    if not vehicles:
        raise HTTPException(status_code=404, detail="No vehicles found")
    return vehicles


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: str, fm=Depends(deps.get_fm)):
    vehicle = fm.vehicles.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.post("/", response_model=VehicleRead)
def create_vehicle(payload: VehicleCreate, fm=Depends(deps.get_fm)):
    return fm.vehicles.create_vehicle(
        country_id=str(payload.country_id),
        reg_code=payload.reg_code,
        home_depot_id=str(payload.home_depot_id) if payload.home_depot_id else None,
        preferred_route_id=str(payload.preferred_route_id) if payload.preferred_route_id else None,
        status=payload.status,
        profile_id=payload.profile_id,
        notes=payload.notes,
    )


@router.put("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(vehicle_id: str, payload: VehicleUpdate, fm=Depends(deps.get_fm)):
    vehicle = fm.vehicles.update_vehicle(vehicle_id, **payload.dict(exclude_unset=True))
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: str, fm=Depends(deps.get_fm)):
    ok = fm.vehicles.delete_vehicle(vehicle_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"deleted": True}
