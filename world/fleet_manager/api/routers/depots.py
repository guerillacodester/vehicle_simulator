# world/fleet_manager/api/routers/depots.py
from fastapi import APIRouter, Depends, HTTPException
from .. import deps
from ..schemas.depot import DepotCreate, DepotRead, DepotUpdate

router = APIRouter(prefix="/api/v1/depots", tags=["depots"])


@router.get("/", response_model=list[DepotRead])
def list_depots(fm=Depends(deps.get_fm)):
    depots = fm.depots.list_depots()
    if not depots:
        raise HTTPException(status_code=404, detail="No depots found")
    return depots


@router.get("/{depot_id}", response_model=DepotRead)
def get_depot(depot_id: str, fm=Depends(deps.get_fm)):
    depot = fm.depots.get_depot(depot_id)
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot


@router.post("/", response_model=DepotRead)
def create_depot(payload: DepotCreate, fm=Depends(deps.get_fm)):
    return fm.depots.create_depot(
        country_id=str(payload.country_id),
        name=payload.name,
        capacity=payload.capacity,
        notes=payload.notes,
    )


@router.put("/{depot_id}", response_model=DepotRead)
def update_depot(depot_id: str, payload: DepotUpdate, fm=Depends(deps.get_fm)):
    depot = fm.depots.update_depot(depot_id, **payload.dict(exclude_unset=True))
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot


@router.delete("/{depot_id}")
def delete_depot(depot_id: str, fm=Depends(deps.get_fm)):
    ok = fm.depots.delete_depot(depot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Depot not found")
    return {"deleted": True}
