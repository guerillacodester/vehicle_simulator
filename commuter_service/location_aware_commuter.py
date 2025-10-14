"""
Location-Aware Smart Commuter
============================

Enhanced commuter with GPS position tracking, destination awareness,
and intelligent pickup eligibility based on route proximity and direction.

Key Features:
- Real-time position tracking
- Route proximity detection
- Direction compatibility validation
- Walking distance optimization
- Dynamic pickup eligibility
"""

import math
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from .commuter_config import get_commuter_config, CommuterBehaviorConfig, explain_priority


class CommuterState(Enum):
    """Smart commuter operational states"""
    WAITING_TO_BOARD = "waiting_to_board"           # At spawn location, looking for vehicle
    WALKING_TO_PICKUP = "walking_to_pickup"         # Moving toward pickup point
    REQUESTING_PICKUP = "requesting_pickup"         # Signaling for vehicle pickup
    BOARDING = "boarding"                           # Getting on vehicle
    ONBOARD = "onboard"                            # Traveling in vehicle
    REQUESTING_DISEMBARK = "requesting_disembark"   # Near destination, want to get off
    DISEMBARKING = "disembarking"                  # Getting off vehicle
    COMPLETED = "completed"                         # Journey finished


@dataclass
class PickupEligibility:
    """Comprehensive pickup eligibility assessment"""
    is_qualified: bool = False
    route_proximity_m: float = float('inf')         # Distance to nearest route point
    walking_distance_m: float = float('inf')        # Walking distance to pickup point
    direction_compatible: bool = False              # Vehicle heading toward destination
    priority_score: float = 0.0                    # Overall pickup priority
    pickup_point: Optional[Tuple[float, float]] = None  # Optimal pickup coordinates
    reasons: List[str] = field(default_factory=list)   # Eligibility details


class LocationAwareCommuter:
    """
    Enhanced commuter with location intelligence and pickup optimization.
    
    This commuter can:
    1. Track real-time GPS position
    2. Calculate distance to destination
    3. Evaluate pickup eligibility based on vehicle route
    4. Request dynamic pickup when qualified
    5. Detect arrival at destination
    """
    
    def __init__(
        self,
        person_id: str,
        spawn_location: Tuple[float, float],
        destination_location: Tuple[float, float],
        trip_purpose: str = "personal",
        person_name: Optional[str] = None,
        priority: float = 0.5,
        area_type: str = "suburban",                # urban/suburban/rural for disembark threshold
        personality: str = "standard",              # impatient/standard/patient for flexibility
        walking_ability: str = "default",           # slow/default/fast for walking speed
        config: Optional[CommuterBehaviorConfig] = None  # Override default config
    ):
        """Initialize location-aware commuter with enhanced capabilities."""
        
        # Load configuration
        self.config = config or get_commuter_config()
        
        # Core identification
        self.person_id = person_id
        self.person_name = person_name or f"Commuter_{trip_purpose}"
        self.trip_purpose = trip_purpose
        self.priority = priority
        self.priority_explanation = explain_priority(priority)
        
        # Location tracking
        self.current_position = spawn_location
        self.destination_position = destination_location
        self.spawn_location = spawn_location
        self.area_type = area_type
        
        # Behavioral parameters from configuration
        walking_speeds = {
            "slow": self.config.slow_walking_speed_ms,
            "default": self.config.default_walking_speed_ms,
            "fast": self.config.fast_walking_speed_ms
        }
        self.walking_speed_ms = walking_speeds.get(walking_ability, self.config.default_walking_speed_ms)
        
        self.max_walking_distance_m = self.config.get_walking_distance_for_priority(priority)
        self.disembark_threshold_m = self.config.get_disembark_threshold_for_area(area_type)
        self.pickup_flexibility = self.config.get_flexibility_for_personality(personality)
        
        # State management
        self.state = CommuterState.WAITING_TO_BOARD
        self.last_position_update = datetime.now()
        
        # Journey tracking
        self.journey_start_time: Optional[datetime] = None
        self.pickup_time: Optional[datetime] = None
        self.disembark_time: Optional[datetime] = None
    
    def update_position(self, lat: float, lon: float) -> None:
        """Update commuter's current GPS position."""
        self.current_position = (lat, lon)
        self.last_position_update = datetime.now()
        
        # Check if arrived at destination
        if self.state == CommuterState.ONBOARD and self.is_at_destination():
            self.state = CommuterState.REQUESTING_DISEMBARK
    
    def distance_to_destination(self) -> float:
        """Calculate straight-line distance to destination in meters."""
        return self._haversine_distance(
            self.current_position[0], self.current_position[1],
            self.destination_position[0], self.destination_position[1]
        )
    
    def is_at_destination(self) -> bool:
        """Check if commuter is within disembark threshold of destination."""
        return self.distance_to_destination() <= self.disembark_threshold_m
    
    def evaluate_pickup_eligibility(
        self,
        vehicle_position: Tuple[float, float],
        vehicle_route: List[Tuple[float, float]],
        vehicle_direction: Optional[float] = None,
        available_seats: int = 1
    ) -> PickupEligibility:
        """
        Comprehensive pickup eligibility evaluation.
        
        Args:
            vehicle_position: Current vehicle GPS coordinates
            vehicle_route: List of route coordinates [(lat, lon), ...]
            vehicle_direction: Vehicle bearing in degrees (optional)
            available_seats: Number of available seats
            
        Returns:
            PickupEligibility assessment with detailed reasoning
        """
        eligibility = PickupEligibility()
        
        # 1. Check capacity
        if available_seats <= 0:
            eligibility.reasons.append("Vehicle at capacity")
            return eligibility
        
        # 2. Find closest point on route
        closest_route_point, route_distance = self._find_closest_route_point(vehicle_route)
        eligibility.route_proximity_m = route_distance
        eligibility.pickup_point = closest_route_point
        
        # 3. Check if within acceptable walking distance
        walking_distance = self._haversine_distance(
            self.current_position[0], self.current_position[1],
            closest_route_point[0], closest_route_point[1]
        )
        eligibility.walking_distance_m = walking_distance
        
        if walking_distance > self.max_walking_distance_m:
            eligibility.reasons.append(f"Too far to walk: {walking_distance:.0f}m > {self.max_walking_distance_m}m")
            return eligibility
        
        # 4. Check direction compatibility
        eligibility.direction_compatible = self._is_direction_compatible(
            vehicle_position, vehicle_route, closest_route_point
        )
        
        if not eligibility.direction_compatible:
            eligibility.reasons.append("Vehicle not heading toward destination")
            return eligibility
        
        # 5. Calculate priority score
        distance_factor = max(0, 1 - (walking_distance / self.max_walking_distance_m))
        priority_factor = self.priority
        flexibility_factor = self.pickup_flexibility
        
        eligibility.priority_score = (distance_factor * 0.4 + 
                                    priority_factor * 0.4 + 
                                    flexibility_factor * 0.2)
        
        # 6. Final qualification
        eligibility.is_qualified = True
        eligibility.reasons.append(f"Qualified: {walking_distance:.0f}m walk, priority {self.priority:.2f}")
        
        return eligibility
    
    def request_pickup(self, pickup_point: Tuple[float, float]) -> bool:
        """Request pickup at specified location."""
        if self.state != CommuterState.WAITING_TO_BOARD:
            return False
        
        self.state = CommuterState.REQUESTING_PICKUP
        # In real implementation, would signal conductor here
        return True
    
    def board_vehicle(self) -> bool:
        """Board the vehicle (called by conductor)."""
        valid_states = [
            CommuterState.WAITING_TO_BOARD,
            CommuterState.REQUESTING_PICKUP, 
            CommuterState.WALKING_TO_PICKUP
        ]
        if self.state not in valid_states:
            return False
        
        self.state = CommuterState.ONBOARD
        self.pickup_time = datetime.now()
        if not self.journey_start_time:
            self.journey_start_time = self.pickup_time
        return True
    
    def request_disembark(self) -> bool:
        """Request to disembark (automatic when near destination)."""
        if self.state != CommuterState.ONBOARD:
            return False
        
        self.state = CommuterState.REQUESTING_DISEMBARK
        return True
    
    def disembark_vehicle(self) -> bool:
        """Disembark the vehicle (called by conductor)."""
        if self.state != CommuterState.REQUESTING_DISEMBARK:
            return False
        
        self.state = CommuterState.COMPLETED
        self.disembark_time = datetime.now()
        return True
    
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
    
    def _find_closest_route_point(self, route: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], float]:
        """Find the closest point on the route to commuter's current position."""
        if not route:
            return self.current_position, float('inf')
        
        min_distance = float('inf')
        closest_point = route[0]
        
        for point in route:
            distance = self._haversine_distance(
                self.current_position[0], self.current_position[1],
                point[0], point[1]
            )
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        
        return closest_point, min_distance
    
    def _is_direction_compatible(
        self,
        vehicle_pos: Tuple[float, float],
        vehicle_route: List[Tuple[float, float]],
        pickup_point: Tuple[float, float]
    ) -> bool:
        """Check if vehicle is moving toward commuter's destination."""
        if len(vehicle_route) < 2:
            return True  # Assume compatible if route too short to determine
        
        # Find pickup point index in route
        pickup_index = -1
        for i, point in enumerate(vehicle_route):
            if abs(point[0] - pickup_point[0]) < 0.0001 and abs(point[1] - pickup_point[1]) < 0.0001:
                pickup_index = i
                break
        
        if pickup_index == -1:
            return False  # Pickup point not on route
        
        # Check if destination is reachable from pickup point
        remaining_route = vehicle_route[pickup_index:]
        
        # Simple check: destination should be closer to end of route than to pickup point
        dest_to_pickup = self._haversine_distance(
            self.destination_position[0], self.destination_position[1],
            pickup_point[0], pickup_point[1]
        )
        
        if len(remaining_route) > 1:
            dest_to_route_end = self._haversine_distance(
                self.destination_position[0], self.destination_position[1],
                remaining_route[-1][0], remaining_route[-1][1]
            )
            return dest_to_route_end <= dest_to_pickup
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'person_id': self.person_id,
            'person_name': self.person_name,
            'trip_purpose': self.trip_purpose,
            'priority': self.priority,
            'current_position': self.current_position,
            'destination_position': self.destination_position,
            'spawn_location': self.spawn_location,
            'state': self.state.value,
            'walking_speed_ms': self.walking_speed_ms,
            'max_walking_distance_m': self.max_walking_distance_m,
            'disembark_threshold_m': self.disembark_threshold_m,
            'pickup_flexibility': self.pickup_flexibility,
            'journey_start_time': self.journey_start_time.isoformat() if self.journey_start_time else None,
            'pickup_time': self.pickup_time.isoformat() if self.pickup_time else None,
            'disembark_time': self.disembark_time.isoformat() if self.disembark_time else None
        }