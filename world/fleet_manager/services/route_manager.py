from __future__ import annotations
from typing import Iterable, List, Optional, Tuple, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from shapely import wkb
from shapely.geometry import LineString
from geoalchemy2.shape import from_shape, to_shape

from ..models.route import Route
from ..models.shape import Shape
from ..models.route_shape import RouteShape

LonLat = Tuple[float, float]


class RouteManager:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # ROUTES — CRUD
    # -------------------------
    def list_routes(self, *, active_only: bool = True) -> List[Route]:
        stmt = select(Route)
        if active_only:
            stmt = stmt.where(Route.is_active.is_(True))
        return list(self.db.scalars(stmt))

    def get_route_by_id(self, route_id: UUID) -> Optional[Route]:
        return self.db.get(Route, route_id)

    def get_route_by_short_name(self, short_name: str) -> Optional[Route]:
        stmt = select(Route).where(Route.short_name == short_name)
        return self.db.scalars(stmt).first()

    def create_route(
        self,
        *,
        country_id: UUID,
        short_name: str,
        long_name: Optional[str] = None,
        parishes: Optional[str] = None,
        is_active: bool = True,
    ) -> Route:
        r = Route(
            route_id=uuid4(),
            short_name=short_name,
            long_name=long_name,
            parishes=parishes,
            is_active=is_active,
        )
        if hasattr(r, "country_id"):
            setattr(r, "country_id", country_id)

        self.db.add(r)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail=f"Route '{short_name}' already exists")
        self.db.refresh(r)
        return r

    def update_route(self, route_id: UUID, **fields: Any) -> Route:
        r = self.get_route_by_id(route_id)
        if not r:
            raise HTTPException(status_code=404, detail=f"Route not found: {route_id}")

        for k, v in fields.items():
            if hasattr(r, k):
                setattr(r, k, v)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Duplicate route constraint")
        self.db.refresh(r)
        return r

    def delete_route(self, route_id: UUID) -> None:
        r = self.get_route_by_id(route_id)
        if not r:
            raise HTTPException(status_code=404, detail=f"Route not found: {route_id}")
        self.db.delete(r)
        self.db.commit()

    # -------------------------
    # SHAPES — CRUD
    # -------------------------
    def create_shape(self, coords: Iterable[LonLat]) -> Shape:
        pts = list(coords)
        if len(pts) < 2:
            raise HTTPException(status_code=400, detail="Shape requires at least 2 points (lon,lat).")
        geom = from_shape(LineString(pts), srid=4326)
        s = Shape(shape_id=uuid4(), geom=geom)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def update_shape(self, shape_id: UUID, coords: Iterable[LonLat]) -> Shape:
        s = self.db.get(Shape, shape_id)
        if not s:
            raise HTTPException(status_code=404, detail=f"Shape not found: {shape_id}")
        pts = list(coords)
        if len(pts) < 2:
            raise HTTPException(status_code=400, detail="Shape requires at least 2 points (lon,lat).")
        s.geom = from_shape(LineString(pts), srid=4326)
        self.db.commit()
        self.db.refresh(s)
        return s

    def delete_shape(self, shape_id: UUID) -> None:
        s = self.db.get(Shape, shape_id)
        if not s:
            raise HTTPException(status_code=404, detail=f"Shape not found: {shape_id}")
        self.db.delete(s)
        self.db.commit()

    def get_shape_coords(self, shape_id: UUID) -> List[LonLat]:
        s = self.db.get(Shape, shape_id)
        if not s:
            raise HTTPException(status_code=404, detail=f"Shape not found: {shape_id}")
        geom = to_shape(s.geom)
        return list(geom.coords)

    # -------------------------
    # ROUTE_SHAPES — links / variants
    # -------------------------
    def link_shape_to_route(
        self,
        route_id: UUID,
        shape_id: UUID,
        *,
        variant_code: Optional[str] = None,
        is_default: bool = False,
    ) -> RouteShape:
        if is_default:
            self.db.execute(
                update(RouteShape)
                .where(RouteShape.route_id == route_id)
                .values(is_default=False)
            )
        rs = RouteShape(
            route_id=route_id,
            shape_id=shape_id,
            variant_code=variant_code,
            is_default=is_default,
        )
        self.db.merge(rs)
        self.db.commit()
        return rs

    def unlink_shape_from_route(self, route_id: UUID, shape_id: UUID) -> None:
        self.db.execute(
            delete(RouteShape)
            .where(RouteShape.route_id == route_id, RouteShape.shape_id == shape_id)
        )
        self.db.commit()

    def set_default_shape(self, route_id: UUID, shape_id: UUID) -> None:
        self.db.execute(
            update(RouteShape)
            .where(RouteShape.route_id == route_id)
            .values(is_default=False)
        )
        self.db.execute(
            update(RouteShape)
            .where(
                RouteShape.route_id == route_id,
                RouteShape.shape_id == shape_id,
            )
            .values(is_default=True)
        )
        self.db.commit()

    def list_route_shapes(self, route_id: UUID) -> List[Dict[str, Any]]:
        stmt = select(RouteShape).where(RouteShape.route_id == route_id)
        rows = list(self.db.scalars(stmt))
        out: List[Dict[str, Any]] = []
        for rs in rows:
            coords = self.get_shape_coords(rs.shape_id)
            out.append(
                {
                    "route_id": route_id,
                    "shape_id": rs.shape_id,
                    "variant_code": rs.variant_code,
                    "is_default": rs.is_default,
                    "num_points": len(coords),
                }
            )
        return out

    # -------------------------
    # READ helpers
    # -------------------------
    def get_route_coordinates(
        self,
        short_name: str,
        *,
        variant_code: Optional[str] = None,
        split_by_shape: bool = False,
        prefer_default: bool = True,
    ) -> List[LonLat] | List[List[LonLat]]:
        route = self.get_route_by_short_name(short_name)
        if not route:
            raise HTTPException(status_code=404, detail=f"Route '{short_name}' not found")

        shapes = []
        for rs in route.shapes:
            if variant_code is not None and rs.variant_code != variant_code:
                continue
            geom = wkb.loads(bytes(rs.shape.geom.data))
            shapes.append((rs.is_default, list(geom.coords)))

        if not shapes:
            return [] if not split_by_shape else []

        if prefer_default:
            shapes.sort(key=lambda t: (not t[0]))

        segments = [coords for _, coords in shapes]
        if split_by_shape:
            return segments

        flat: List[LonLat] = []
        for seg in segments:
            flat.extend(seg)
        return flat
