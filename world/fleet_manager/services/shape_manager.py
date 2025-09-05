# world/fleet_manager/services/shape_manager.py
from __future__ import annotations
from typing import List, Tuple, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from shapely.geometry import LineString
from shapely import wkb
from geoalchemy2.shape import from_shape, to_shape

from ..models.shape import Shape

LonLat = Tuple[float, float]

class ShapeManager:
    def __init__(self, db: Session):
        self.db = db

    def create_shape(self, coords: List[LonLat]) -> Shape:
        if len(coords) < 2:
            raise ValueError("Shape must have at least 2 points")
        geom = from_shape(LineString(coords), srid=4326)
        s = Shape(shape_id=uuid4(), geom=geom)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def get_shape(self, shape_id: UUID) -> Optional[Shape]:
        return self.db.get(Shape, shape_id)

    def list_shapes(self) -> List[Shape]:
        return list(self.db.query(Shape).all())

    def delete_shape(self, shape_id: UUID) -> None:
        s = self.get_shape(shape_id)
        if s:
            self.db.delete(s)
            self.db.commit()

    def get_coords(self, shape_id: UUID) -> List[LonLat]:
        s = self.get_shape(shape_id)
        if not s:
            raise ValueError("Shape not found")
        geom = to_shape(s.geom)
        return list(geom.coords)
