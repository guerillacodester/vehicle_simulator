from sqlalchemy.orm import Session
from shapely import wkb
from typing import List, Tuple
from ..models import Route

class RouteManager:
    def __init__(self, db: Session):
        self.db = db

    def get_route_coordinates(self, short_name: str) -> List[Tuple[float, float]]:
        """
        Fetch the geometry for a given route short_name.
        Always returns *all* coordinates in order.
        """
        route = (
            self.db.query(Route)
            .filter(Route.short_name == short_name)
            .first()
        )

        if not route:
            raise ValueError(f"Route '{short_name}' not found")

        coords: List[Tuple[float, float]] = []

        for rs in route.route_shapes:
            geom = wkb.loads(bytes(rs.shape.geom.data))  # Shapely geometry
            coords.extend(list(geom.coords))

        return coords
