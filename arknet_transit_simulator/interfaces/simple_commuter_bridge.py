"""
Simple Commuter-Vehicle Bridge
=============================

Basic interface between commuter reservoir and vehicle conductor.
Focuses on proximity detection and simple boarding coordination.

NO SMART FEATURES - Just basic proximity and direction matching.
"""

from typing import List, Tuple, Optional, Dict, Any
import math
from datetime import datetime

from commuter_service.location_aware_commuter import LocationAwareCommuter, CommuterState
from commuter_service.commuter_reservoir import CommuterReservoir


class SimpleCommuterBridge:
    """
    Basic bridge for commuter-vehicle coordination.
    
    Responsibilities:
    1. Query nearby commuters for a vehicle
    2. Check basic direction compatibility  
    3. Return simple list of eligible commuters
    4. No complex scoring or optimization
    """
    
    def __init__(self, proximity_radius_m: float = 200):
        """
        Initialize simple bridge.
        
        Args:
            proximity_radius_m: How close a commuter must be to vehicle route (meters)
        """
        self.proximity_radius_m = proximity_radius_m
        self.commuter_reservoir: Optional[CommuterReservoir] = None
        
    def connect_reservoir(self, reservoir: CommuterReservoir) -> None:
        """Connect to the commuter reservoir."""
        self.commuter_reservoir = reservoir
        
    def find_nearby_commuters(
        self,
        vehicle_position: Tuple[float, float],
        vehicle_route: List[Tuple[float, float]],
        route_id: str
    ) -> List[LocationAwareCommuter]:
        """
        Find commuters near the vehicle route who want to go in the same direction.
        
        Args:
            vehicle_position: Current vehicle GPS coordinates (lat, lon)
            vehicle_route: List of route GPS coordinates
            route_id: Route identifier (e.g., "1A")
            
        Returns:
            List of commuters who are close enough and going the right direction
        """
        if not self.commuter_reservoir:
            return []
        
        # Get all waiting commuters from reservoir
        all_commuters = self.commuter_reservoir.get_all_commuters()
        
        # Filter for commuters who are waiting to board
        waiting_commuters = [
            c for c in all_commuters 
            if hasattr(c, 'state') and c.state == CommuterState.WAITING_TO_BOARD
        ]
        
        eligible_commuters = []
        
        for commuter in waiting_commuters:
            # Check if commuter is close enough to vehicle route
            if self._is_commuter_near_route(commuter, vehicle_route):
                # Check if commuter wants to go in compatible direction
                if self._is_direction_compatible(commuter, vehicle_route, vehicle_position):
                    eligible_commuters.append(commuter)
        
        return eligible_commuters
    
    def _is_commuter_near_route(
        self, 
        commuter: LocationAwareCommuter, 
        vehicle_route: List[Tuple[float, float]]
    ) -> bool:
        """Check if commuter is within proximity radius of any point on the route."""
        commuter_lat, commuter_lon = commuter.current_position
        
        for route_lat, route_lon in vehicle_route:
            distance = self._haversine_distance(
                commuter_lat, commuter_lon, 
                route_lat, route_lon
            )
            if distance <= self.proximity_radius_m:
                return True
        
        return False
    
    def _is_direction_compatible(
        self,
        commuter: LocationAwareCommuter,
        vehicle_route: List[Tuple[float, float]],
        vehicle_position: Tuple[float, float]
    ) -> bool:
        """
        Simple direction compatibility check.
        
        Logic: If commuter's destination is closer to the END of the route
        than to the vehicle's current position, then it's compatible.
        """
        if len(vehicle_route) < 2:
            return True  # Can't determine direction, assume compatible
        
        commuter_dest_lat, commuter_dest_lon = commuter.destination_position
        vehicle_lat, vehicle_lon = vehicle_position
        route_end_lat, route_end_lon = vehicle_route[-1]  # Last point on route
        
        # Distance from commuter destination to vehicle current position
        dist_to_vehicle = self._haversine_distance(
            commuter_dest_lat, commuter_dest_lon,
            vehicle_lat, vehicle_lon
        )
        
        # Distance from commuter destination to end of route
        dist_to_route_end = self._haversine_distance(
            commuter_dest_lat, commuter_dest_lon,
            route_end_lat, route_end_lon
        )
        
        # If destination is closer to route end, then vehicle is heading toward destination
        return dist_to_route_end < dist_to_vehicle
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate haversine distance between two points in meters."""
        R = 6371000  # Earth's radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def request_boarding(self, commuter: LocationAwareCommuter) -> bool:
        """
        Request boarding for a commuter (called by conductor).
        
        Args:
            commuter: The commuter who wants to board
            
        Returns:
            True if boarding request successful
        """
        if hasattr(commuter, 'state') and commuter.state == CommuterState.WAITING_TO_BOARD:
            # Mark commuter as requesting pickup
            commuter.state = CommuterState.REQUESTING_PICKUP
            return True
        return False
    
    def complete_boarding(self, commuter: LocationAwareCommuter) -> bool:
        """
        Complete boarding process (called when commuter gets on vehicle).
        
        Args:
            commuter: The commuter who is boarding
            
        Returns:
            True if boarding completed successfully
        """
        if hasattr(commuter, 'board_vehicle'):
            return commuter.board_vehicle()
        return False
    
    def get_bridge_status(self) -> Dict[str, Any]:
        """Get current bridge status for debugging."""
        return {
            'connected_to_reservoir': self.commuter_reservoir is not None,
            'proximity_radius_m': self.proximity_radius_m,
            'timestamp': datetime.now().isoformat()
        }


class SimpleBoardingCoordinator:
    """
    Simple coordinator for conductor-commuter-driver interactions.
    Handles the basic boarding workflow without complex optimization.
    """
    
    def __init__(self, bridge: SimpleCommuterBridge):
        self.bridge = bridge
        self.boarding_in_progress = False
        self.current_boarding_commuters: List[LocationAwareCommuter] = []
    
    def scan_for_boarding_opportunities(
        self,
        vehicle_position: Tuple[float, float],
        vehicle_route: List[Tuple[float, float]],
        route_id: str,
        available_seats: int = 999  # Assume unlimited seats for now
    ) -> List[LocationAwareCommuter]:
        """
        Scan for commuters who should be picked up.
        
        Returns:
            List of commuters ready for boarding
        """
        if self.boarding_in_progress:
            return []  # Don't scan while boarding
        
        # Find nearby eligible commuters
        eligible_commuters = self.bridge.find_nearby_commuters(
            vehicle_position, vehicle_route, route_id
        )
        
        # For simplicity, just return all eligible commuters
        # (No capacity checking, no priority sorting for now)
        return eligible_commuters
    
    def initiate_boarding(self, commuters: List[LocationAwareCommuter]) -> bool:
        """
        Start the boarding process for a list of commuters.
        
        Args:
            commuters: List of commuters to board
            
        Returns:
            True if boarding initiated successfully
        """
        if self.boarding_in_progress:
            return False
        
        if not commuters:
            return False
        
        # Mark boarding in progress
        self.boarding_in_progress = True
        self.current_boarding_commuters = commuters.copy()
        
        # Request boarding for each commuter
        for commuter in commuters:
            self.bridge.request_boarding(commuter)
        
        return True
    
    def complete_boarding(self) -> int:
        """
        Complete the boarding process.
        
        Returns:
            Number of commuters successfully boarded
        """
        if not self.boarding_in_progress:
            return 0
        
        boarded_count = 0
        
        # Complete boarding for each commuter
        for commuter in self.current_boarding_commuters:
            if self.bridge.complete_boarding(commuter):
                boarded_count += 1
        
        # Reset boarding state
        self.boarding_in_progress = False
        self.current_boarding_commuters = []
        
        return boarded_count
    
    def is_boarding_in_progress(self) -> bool:
        """Check if boarding is currently in progress."""
        return self.boarding_in_progress
    
    def get_boarding_status(self) -> Dict[str, Any]:
        """Get current boarding status."""
        return {
            'boarding_in_progress': self.boarding_in_progress,
            'commuters_boarding': len(self.current_boarding_commuters),
            'commuter_ids': [c.person_id for c in self.current_boarding_commuters] if hasattr(self, 'current_boarding_commuters') else []
        }