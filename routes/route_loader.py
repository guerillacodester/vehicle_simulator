import json
from typing import List, Tuple

def load_route_coordinates(route_file: str) -> List[Tuple[float, float]]:
    with open(route_file) as f:
        data = json.load(f)
    coords = []
    for feature in data["features"]:
        for coord_set in feature["geometry"]["coordinates"]:
            for coord in coord_set:
                coords.append(tuple(coord))
    return coords
