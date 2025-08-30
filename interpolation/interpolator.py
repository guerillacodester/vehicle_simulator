from typing import Tuple

def interpolate_position(lat1: float, lon1: float, lat2: float, lon2: float, fraction: float) -> Tuple[float, float]:
    return (lat1 + (lat2 - lat1) * fraction, lon1 + (lon2 - lon1) * fraction)
