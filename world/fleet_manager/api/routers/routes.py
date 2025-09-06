from __future__ import annotations
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ...services.route_manager import RouteManager
from ..deps import get_route_manager
from ..schemas.route import RouteOut, RouteCreate, RouteUpdate, CoordinatesResponse

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])

@router.get("", response_model=List[RouteOut])
def list_routes(active_only: bool = Query(True),
                rm: RouteManager = Depends(get_route_manager)):
    items = rm.list_routes(active_only=active_only)
    return [
        RouteOut(
            route_id=r.route_id,
            short_name=r.short_name,
            long_name=getattr(r, "long_name", None),
            parishes=getattr(r, "parishes", None),
            is_active=getattr(r, "is_active", True),
        ) for r in items
    ]

@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: UUID, rm: RouteManager = Depends(get_route_manager)):
    r = rm.get_route_by_id(route_id)
    if not r:
        raise HTTPException(404, detail=f"Route not found: {route_id}")
    return RouteOut(
        route_id=r.route_id,
        short_name=r.short_name,
        long_name=getattr(r, "long_name", None),
        parishes=getattr(r, "parishes", None),
        is_active=getattr(r, "is_active", True),
    )

@router.get("/by-short-name/{short_name}", response_model=RouteOut)
def get_route_by_short_name(short_name: str, rm: RouteManager = Depends(get_route_manager)):
    r = rm.get_route_by_short_name(short_name)
    if not r:
        raise HTTPException(404, detail=f"Route not found: {short_name}")
    return RouteOut(
        route_id=r.route_id,
        short_name=r.short_name,
        long_name=getattr(r, "long_name", None),
        parishes=getattr(r, "parishes", None),
        is_active=getattr(r, "is_active", True),
    )

@router.post("", response_model=RouteOut, status_code=201)
def create_route(payload: RouteCreate, rm: RouteManager = Depends(get_route_manager)):
    r = rm.create_route(
        country_id=payload.country_id,
        short_name=payload.short_name,
        long_name=payload.long_name,
        parishes=payload.parishes,
        is_active=payload.is_active,
    )
    return RouteOut(
        route_id=r.route_id,
        short_name=r.short_name,
        long_name=getattr(r, "long_name", None),
        parishes=getattr(r, "parishes", None),
        is_active=getattr(r, "is_active", True),
    )

@router.patch("/{route_id}", response_model=RouteOut)
def update_route(route_id: UUID, payload: RouteUpdate,
                 rm: RouteManager = Depends(get_route_manager)):
    r = rm.update_route(route_id, **payload.dict(exclude_unset=True))
    return RouteOut(
        route_id=r.route_id,
        short_name=r.short_name,
        long_name=getattr(r, "long_name", None),
        parishes=getattr(r, "parishes", None),
        is_active=getattr(r, "is_active", True),
    )

@router.delete("/{route_id}", status_code=204)
def delete_route(route_id: UUID, rm: RouteManager = Depends(get_route_manager)):
    rm.delete_route(route_id)
    return

# ----- route coordinates -----
@router.get("/{short_name}/coordinates", response_model=CoordinatesResponse)
def get_route_coords(short_name: str,
                     split_by_shape: bool = Query(False),
                     variant_code: Optional[str] = Query(None),
                     rm: RouteManager = Depends(get_route_manager)):
    coords = rm.get_route_coordinates(
        short_name,
        variant_code=variant_code,
        split_by_shape=split_by_shape,
        prefer_default=True,
    )
    return CoordinatesResponse(route=short_name, split_by_shape=split_by_shape, coordinates=coords)

@router.get("/{short_name}/coordinates.csv")
def get_route_coords_csv(short_name: str,
                         split_by_shape: bool = Query(False),
                         variant_code: Optional[str] = Query(None),
                         rm: RouteManager = Depends(get_route_manager)):
    coords = rm.get_route_coordinates(
        short_name,
        variant_code=variant_code,
        split_by_shape=split_by_shape,
        prefer_default=True,
    )
    def _iter():
        yield "lon,lat\n"
        if split_by_shape:
            for seg in coords:            # type: ignore
                for lon, lat in seg:
                    yield f"{lon},{lat}\n"
        else:
            for lon, lat in coords:       # type: ignore
                yield f"{lon},{lat}\n"
    return StreamingResponse(_iter(), media_type="text/csv")
