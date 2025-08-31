import json
from typing import List, Tuple

def load_route_coordinates(route_file: str) -> List[Tuple[float, float]]:
    """Load coordinates from a GeoJSON route file (LineString, MultiLineString, or Point)."""
    with open(route_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    coordinates: List[Tuple[float, float]] = []

    for feature in data["features"]:
        coords = feature["geometry"]["coordinates"]

        # MultiLineStrings
        if isinstance(coords[0], list) and isinstance(coords[0][0], list):
            for line in coords:
                for coord_set in line:
                    coordinates.append(tuple(coord_set))

        # LineString
        elif isinstance(coords[0], list):
            for coord_set in coords:
                coordinates.append(tuple(coord_set))

        # Point
        elif isinstance(coords[0], (float, int)):
            coordinates.append(tuple(coords))

    return coordinates
