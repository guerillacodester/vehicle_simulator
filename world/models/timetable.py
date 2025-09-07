from dataclasses import dataclass
from datetime import time
from typing import Optional

@dataclass
class Departure:
    """Single departure time entry"""
    vehicle_id: str
    route_id: str
    departure_time: time
    terminal_id: Optional[str] = None