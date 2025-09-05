# world/fleet_manager/api/routers/admin.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

from ...services.route_manager import RouteManager
from ..deps import get_route_manager

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/link-shape")
def link_shape_to_route(
    route_id: UUID = Query(...),
    shape_id: UUID = Query(...),
    rm: RouteManager = Depends(get_route_manager),
):
    r = rm.get_route_by_id(route_id)
    if not r:
        raise HTTPException(404, "Route not found")
    rm.link_shape_to_route(route_id, shape_id)
    return {"ok": True}
