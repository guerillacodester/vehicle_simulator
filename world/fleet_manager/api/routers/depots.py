# world/fleet_manager/api/routers/depots.py
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from .. import deps
from ..schemas.depot import DepotCreate, DepotRead, DepotUpdate

router = APIRouter(prefix="/api/v1/depots", tags=["depots"])

@router.get("/", response_model=list[DepotRead])
def list_depots(fm=Depends(deps.get_fm)):
    return fm.depots.list_depots()

@router.get("/{depot_id}", response_model=DepotRead)
def get_depot(depot_id: UUID, fm=Depends(deps.get_fm)):
    depot = fm.depots.get_depot(depot_id)
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot

@router.post("/", response_model=DepotRead, status_code=201)
def create_depot(payload: DepotCreate, fm=Depends(deps.get_fm)):
    # Optional duplicate check
    existing = [d for d in fm.depots.list_depots() if d.name == payload.name]
    if existing:
        raise HTTPException(status_code=409, detail=f"Depot '{payload.name}' already exists")

    return fm.depots.create_depot(
        country_id=payload.country_id,   # ✅ UUID stays UUID
        name=payload.name,
        location=getattr(payload, "location", None),
        capacity=payload.capacity,
        notes=payload.notes,
    )

@router.patch("/{depot_id}", response_model=DepotRead)
def update_depot(depot_id: UUID, payload: DepotUpdate, fm=Depends(deps.get_fm)):
    depot = fm.depots.update_depot(depot_id, **payload.dict(exclude_unset=True))
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot

@router.delete("/{depot_id}", status_code=204)
def delete_depot(depot_id: UUID, fm=Depends(deps.get_fm)):
    ok = fm.depots.delete_depot(depot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Depot not found")
    return
