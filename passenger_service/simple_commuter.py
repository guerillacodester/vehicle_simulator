"""
Simple Commuter Class
=====================

A lightweight commuter class for the reservoir system that doesn't require
the full BaseComponent/StateMachine implementation.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class SimpleCommuter:
    """
    Simple commuter class for reservoir system.
    
    Contains all commuter information without the complex state machine
    requirements of BasePerson.
    """
    person_id: str
    person_type: str = "Commuter"
    person_name: Optional[str] = None
    origin_stop_id: Optional[str] = None
    destination_stop_id: Optional[str] = None
    depart_time: Optional[datetime] = None
    trip_purpose: Optional[str] = None
    priority: float = 0.5
    spawn_location: Optional[tuple] = None  # (lat, lon)
    destination_location: Optional[tuple] = None  # (lat, lon)
    
    def __post_init__(self):
        """Set default name if not provided"""
        if not self.person_name:
            self.person_name = f"Commuter_{self.trip_purpose or 'Unknown'}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert commuter to dictionary"""
        return {
            'person_id': self.person_id,
            'person_type': self.person_type,
            'person_name': self.person_name,
            'origin_stop_id': self.origin_stop_id,
            'destination_stop_id': self.destination_stop_id,
            'depart_time': self.depart_time.isoformat() if self.depart_time else None,
            'trip_purpose': self.trip_purpose,
            'priority': self.priority,
            'spawn_location': self.spawn_location,
            'destination_location': self.destination_location
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimpleCommuter':
        """Create commuter from dictionary"""
        if data.get('depart_time'):
            data['depart_time'] = datetime.fromisoformat(data['depart_time'])
        return cls(**data)