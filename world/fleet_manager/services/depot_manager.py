from sqlalchemy.orm import Session
from uuid import UUID
from ..models.depot import Depot
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

class DepotManager:
    def __init__(self, db: Session):
        self.db = db

    def _to_geom(self, location):
        """Convert tuple/list or GeoJSON dict into a PostGIS Point."""
        if isinstance(location, (list, tuple)) and len(location) == 2:
            return from_shape(Point(location), srid=4326)
        if isinstance(location, dict) and location.get("type") == "Point":
            return from_shape(Point(location["coordinates"]), srid=4326)
        return None

    def create_depot(
        self,
        country_id: UUID,
        name: str,
        location=None,
        capacity: int | None = None,
        notes: str | None = None,
    ) -> Depot | None:
        # 🔒 Duplicate check by name
        existing = self.db.query(Depot).filter(Depot.name == name).first()
        if existing:
            return None

        geom = self._to_geom(location)
        depot = Depot(
            country_id=country_id,
            name=name,
            location=geom,
            capacity=capacity,
            notes=notes,
        )
        self.db.add(depot)
        self.db.commit()
        self.db.refresh(depot)
        return depot

    def get_depot(self, depot_id: UUID) -> Depot | None:
        return self.db.query(Depot).filter(Depot.depot_id == depot_id).first()

    def list_depots(self) -> list[Depot]:
        return self.db.query(Depot).order_by(Depot.name).all()

    def update_depot(self, depot_id: UUID, **kwargs) -> Depot | None:
        depot = self.get_depot(depot_id)
        if not depot:
            return None
        if "location" in kwargs:
            kwargs["location"] = self._to_geom(kwargs["location"])
        for key, value in kwargs.items():
            setattr(depot, key, value)
        self.db.commit()
        self.db.refresh(depot)
        return depot

    def delete_depot(self, depot_id: UUID) -> bool:
        depot = self.get_depot(depot_id)
        if not depot:
            return False
        self.db.delete(depot)
        self.db.commit()
        return True
