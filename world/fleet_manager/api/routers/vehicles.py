from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from psycopg2 import errorcodes
from uuid import UUID
from .. import deps
from ..schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])

@router.get("/", response_model=list[VehicleRead])
def list_vehicles(fm=Depends(deps.get_fm)):
    return fm.vehicles.list_vehicles()

@router.get("/by-reg-code/{reg_code}", response_model=VehicleRead)
def get_by_reg_code(reg_code: str, fm=Depends(deps.get_fm)):
    v = fm.vehicles.get_by_reg_code(reg_code)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v

@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: UUID, fm=Depends(deps.get_fm)):
    v = fm.vehicles.get_vehicle(vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v

@router.post("/", response_model=VehicleRead, status_code=201)
def create_vehicle(payload: VehicleCreate, fm=Depends(deps.get_fm)):
    if payload.home_depot_id and not fm.depots.get_depot(payload.home_depot_id):
        raise HTTPException(400, "home_depot_id does not exist")
    if payload.preferred_route_id:
        r = fm.routes.get_route_by_id(payload.preferred_route_id)
        if not r:
            raise HTTPException(400, "preferred_route_id does not exist")

    try:
        return fm.vehicles.create_vehicle(
            country_id=payload.country_id,
            reg_code=payload.reg_code,
            status=payload.status,
            notes=payload.notes,
            home_depot_id=payload.home_depot_id,
            preferred_route_id=payload.preferred_route_id,
            profile_id=payload.profile_id,
        )
    except IntegrityError as e:
        code = getattr(getattr(e, "orig", None), "pgcode", None)
        if code == errorcodes.UNIQUE_VIOLATION:
            raise HTTPException(409, "reg_code already exists")
        if code == errorcodes.FOREIGN_KEY_VIOLATION:
            raise HTTPException(400, "Invalid foreign key (country_id/home_depot_id/preferred_route_id)")
        if code == errorcodes.NOT_NULL_VIOLATION:
            raise HTTPException(400, "A required field is null")
        if code == errorcodes.CHECK_VIOLATION:
            raise HTTPException(400, "reg_code must match pattern ZR###")
        raise

@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(vehicle_id: UUID, payload: VehicleUpdate, fm=Depends(deps.get_fm)):
    if payload.home_depot_id and not fm.depots.get_depot(payload.home_depot_id):
        raise HTTPException(400, "home_depot_id does not exist")
    if payload.preferred_route_id:
        r = fm.routes.get_route_by_id(payload.preferred_route_id)
        if not r:
            raise HTTPException(400, "preferred_route_id does not exist")

    v = fm.vehicles.update_vehicle(vehicle_id, **payload.dict(exclude_unset=True))
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v

@router.delete("/{vehicle_id}", status_code=204)
def delete_vehicle(vehicle_id: UUID, fm=Depends(deps.get_fm)):
    if not fm.vehicles.delete_vehicle(vehicle_id):
        raise HTTPException(404, "Vehicle not found")
    return
