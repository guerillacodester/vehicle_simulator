"""
Route Segment - Bidirectional Commuter Management for Route Sections

This module manages commuters waiting along a specific segment of a bus route.
Extracted from RouteReservoir to follow Single Responsibility Principle.

Responsibilities:
- Track commuters in both directions (inbound/outbound)
- Add/remove commuters from segment
- Query commuters by direction
- Maintain segment statistics

Key Concepts:
- INBOUND: Traveling toward city center (e.g., suburbs → downtown)
- OUTBOUND: Traveling away from city center (e.g., downtown → suburbs)
- Grid Cell: Spatial index for fast proximity searches
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from commuter_service.location_aware_commuter import LocationAwareCommuter
from commuter_service.socketio_client import CommuterDirection


@dataclass
class RouteSegment:
    """
    Segment of a route with bidirectional commuter tracking.
    
    A segment represents a portion of a bus route where commuters can
    spawn and wait for pickup. Segments track both inbound and outbound
    commuters separately.
    
    Example:
        segment = RouteSegment(
            route_id="ROUTE_1A",
            segment_id="1A_SPEIGHT_HOLE_OUT",
            grid_cell=(1309, -5961)  # Spatial index
        )
        
        # Add outbound commuter
        segment.add_commuter(commuter_outbound)
        
        # Get all outbound commuters
        outbound = segment.get_commuters_by_direction(CommuterDirection.OUTBOUND)
    """
    
    route_id: str
    segment_id: str
    grid_cell: Tuple[int, int]  # Spatial index (grid_x, grid_y)
    commuters_inbound: List[LocationAwareCommuter] = field(default_factory=list)
    commuters_outbound: List[LocationAwareCommuter] = field(default_factory=list)
    total_spawned: int = 0
    total_picked_up: int = 0
    total_expired: int = 0
    
    def add_commuter(self, commuter: LocationAwareCommuter):
        """
        Add commuter to appropriate direction list.
        
        Args:
            commuter: Commuter to add (must have .direction attribute)
        """
        if commuter.direction == CommuterDirection.INBOUND:
            self.commuters_inbound.append(commuter)
        else:
            self.commuters_outbound.append(commuter)
        self.total_spawned += 1
    
    def remove_commuter(self, commuter_id: str) -> Optional[LocationAwareCommuter]:
        """
        Remove commuter from segment by ID.
        
        Searches both inbound and outbound lists.
        
        Args:
            commuter_id: Unique identifier of commuter to remove
            
        Returns:
            Removed commuter if found, None otherwise
        """
        # Check inbound commuters
        for i, commuter in enumerate(self.commuters_inbound):
            if commuter.person_id == commuter_id:
                return self.commuters_inbound.pop(i)
        
        # Check outbound commuters
        for i, commuter in enumerate(self.commuters_outbound):
            if commuter.person_id == commuter_id:
                return self.commuters_outbound.pop(i)
        
        return None
    
    def get_commuters_by_direction(
        self,
        direction: CommuterDirection
    ) -> List[LocationAwareCommuter]:
        """
        Get all commuters traveling in specific direction.
        
        Args:
            direction: CommuterDirection.INBOUND or CommuterDirection.OUTBOUND
            
        Returns:
            List of commuters traveling in specified direction
        """
        if direction == CommuterDirection.INBOUND:
            return self.commuters_inbound
        else:
            return self.commuters_outbound
    
    def count(self) -> int:
        """
        Get total number of commuters in segment (both directions).
        
        Returns:
            Total count of inbound + outbound commuters
        """
        return len(self.commuters_inbound) + len(self.commuters_outbound)
    
    def count_by_direction(self, direction: CommuterDirection) -> int:
        """
        Get count of commuters in specific direction.
        
        Args:
            direction: CommuterDirection.INBOUND or CommuterDirection.OUTBOUND
            
        Returns:
            Count of commuters in specified direction
        """
        if direction == CommuterDirection.INBOUND:
            return len(self.commuters_inbound)
        else:
            return len(self.commuters_outbound)
    
    def get_stats(self) -> dict:
        """
        Get segment statistics.
        
        Returns:
            Dictionary with segment stats including counts by direction
        """
        return {
            "route_id": self.route_id,
            "segment_id": self.segment_id,
            "grid_cell": self.grid_cell,
            "inbound_count": len(self.commuters_inbound),
            "outbound_count": len(self.commuters_outbound),
            "total_waiting": self.count(),
            "total_spawned": self.total_spawned,
            "total_picked_up": self.total_picked_up,
            "total_expired": self.total_expired,
        }
