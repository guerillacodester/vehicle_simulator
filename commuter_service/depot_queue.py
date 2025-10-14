"""
Depot Queue - FIFO Queue Management for Depot Commuters

This module provides queue management for commuters waiting at depot locations.
Extracted from DepotReservoir to follow Single Responsibility Principle.

Responsibilities:
- FIFO queue management for commuters
- Proximity-based commuter queries
- Queue statistics tracking
"""

from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from math import radians, sin, cos, sqrt, atan2

from commuter_service.location_aware_commuter import LocationAwareCommuter


@dataclass
class DepotQueue:
    """Queue of commuters waiting at a specific depot"""
    depot_id: str
    depot_location: tuple[float, float]  # (lat, lon)
    route_id: str
    commuters: deque = field(default_factory=deque)
    total_spawned: int = 0
    total_picked_up: int = 0
    total_expired: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __len__(self) -> int:
        """Return number of commuters in queue"""
        return len(self.commuters)
    
    def add_commuter(self, commuter: LocationAwareCommuter):
        """Add commuter to end of queue (FIFO)"""
        self.commuters.append(commuter)
        self.total_spawned += 1
    
    def remove_commuter(self, commuter_id: str) -> Optional[LocationAwareCommuter]:
        """Remove specific commuter from queue by ID"""
        for i, commuter in enumerate(self.commuters):
            if commuter.person_id == commuter_id:
                removed = self.commuters[i]
                del self.commuters[i]
                return removed
        return None
    
    def get_available_commuters(
        self,
        vehicle_location: tuple[float, float],
        max_distance: float,
        max_count: int
    ) -> List[LocationAwareCommuter]:
        """
        Get available commuters within distance threshold.
        
        Args:
            vehicle_location: (lat, lon) of vehicle
            max_distance: Maximum distance in meters
            max_count: Maximum number of commuters to return
            
        Returns:
            List of commuters within distance, up to max_count
        """
        available = []
        
        for commuter in self.commuters:
            # Calculate distance between commuter and vehicle using Haversine
            distance = self._calculate_distance(
                commuter.current_position,
                vehicle_location
            )
            
            if distance <= max_distance:
                available.append(commuter)
                if len(available) >= max_count:
                    break
        
        return available
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            "depot_id": self.depot_id,
            "route_id": self.route_id,
            "waiting_count": len(self.commuters),
            "total_spawned": self.total_spawned,
            "total_picked_up": self.total_picked_up,
            "total_expired": self.total_expired,
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
        }
    
    @staticmethod
    def _calculate_distance(
        location1: tuple[float, float],
        location2: tuple[float, float]
    ) -> float:
        """
        Calculate Haversine distance between two locations.
        
        Args:
            location1: (lat, lon) first location
            location2: (lat, lon) second location
            
        Returns:
            Distance in meters
        """
        lat1, lon1 = location1
        lat2, lon2 = location2
        
        # Earth radius in meters
        R = 6371000
        
        # Haversine formula
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance
