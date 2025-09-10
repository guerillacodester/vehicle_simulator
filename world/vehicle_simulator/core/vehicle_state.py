"""
Vehicle State Management
-----------------------
Manages vehicle states throughout the complete operational cycle.
Tracks vehicles from depot queue through route execution and return.
"""

import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class VehicleState(Enum):
    """Vehicle operational states in the ZR van cycle"""
    QUEUED = "queued"           # Waiting in depot queue
    LOADING = "loading"         # Active passenger boarding
    FULL = "full"              # Passengers full, awaiting route
    DISPATCHED = "dispatched"   # Route received, engine starting
    EN_ROUTE = "en_route"      # Following route to destination
    AT_DESTINATION = "at_destination"  # Loitering at destination
    RETURNING = "returning"     # Following return route
    COMPLETING = "completing"   # Approaching depot
    DISEMBARKING = "disembarking"  # Passengers leaving at depot


@dataclass
class VehicleStatus:
    """Complete vehicle status information"""
    vehicle_id: str
    state: VehicleState
    passengers: int
    capacity: int
    queue_position: Optional[int] = None
    route_id: Optional[str] = None
    destination: Optional[str] = None
    engine_on: bool = False
    last_updated: datetime = None
    journey_start_time: Optional[datetime] = None
    destination_arrival_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @property
    def is_full(self) -> bool:
        return self.passengers >= self.capacity
    
    @property
    def loading_progress(self) -> str:
        return f"{self.passengers}/{self.capacity}"
    
    @property
    def can_depart(self) -> bool:
        return self.state == VehicleState.FULL


class DepotQueueManager:
    """
    Manages vehicle queue operations at the depot.
    Handles queue ordering, vehicle activation, and cycle management.
    """
    
    def __init__(self):
        self.vehicle_queue: List[str] = []
        self.vehicle_states: Dict[str, VehicleStatus] = {}
        self.active_loading_vehicle: Optional[str] = None
        
    def add_vehicle_to_queue(self, vehicle_id: str, capacity: int = 11) -> int:
        """Add vehicle to depot queue"""
        if vehicle_id not in self.vehicle_queue:
            self.vehicle_queue.append(vehicle_id)
            
        # Create vehicle status
        queue_position = self.vehicle_queue.index(vehicle_id) + 1
        self.vehicle_states[vehicle_id] = VehicleStatus(
            vehicle_id=vehicle_id,
            state=VehicleState.QUEUED,
            passengers=0,
            capacity=capacity,
            queue_position=queue_position
        )
        
        logger.info(f"🚐 Vehicle {vehicle_id} added to depot queue at position {queue_position}")
        self._update_queue_positions()
        self._activate_next_vehicle()
        
        return queue_position
    
    def _update_queue_positions(self):
        """Update queue positions for all vehicles"""
        for i, vehicle_id in enumerate(self.vehicle_queue):
            if vehicle_id in self.vehicle_states:
                self.vehicle_states[vehicle_id].queue_position = i + 1
    
    def _activate_next_vehicle(self):
        """Activate the next vehicle in queue for loading"""
        if self.active_loading_vehicle is None and self.vehicle_queue:
            next_vehicle = self.vehicle_queue[0]
            self.active_loading_vehicle = next_vehicle
            
            if next_vehicle in self.vehicle_states:
                self.vehicle_states[next_vehicle].state = VehicleState.LOADING
                logger.info(f"🚌 Vehicle {next_vehicle} is now ACTIVE for passenger loading")
    
    def board_passengers(self, vehicle_id: str, count: int = 1) -> bool:
        """Board passengers onto active loading vehicle"""
        if vehicle_id != self.active_loading_vehicle:
            return False
            
        if vehicle_id not in self.vehicle_states:
            return False
            
        status = self.vehicle_states[vehicle_id]
        if status.state != VehicleState.LOADING:
            return False
            
        # Add passengers up to capacity
        new_passenger_count = min(status.passengers + count, status.capacity)
        actual_boarded = new_passenger_count - status.passengers
        status.passengers = new_passenger_count
        status.last_updated = datetime.now()
        
        logger.info(f"🚶 {actual_boarded} passengers boarded {vehicle_id} ({status.loading_progress})")
        
        # Check if vehicle is full
        if status.is_full:
            status.state = VehicleState.FULL
            logger.info(f"🚌 Vehicle {vehicle_id} is FULL ({status.loading_progress}) - ready for route dispatch!")
            return True
            
        return actual_boarded > 0
    
    def dispatch_vehicle(self, vehicle_id: str, route_data: Dict[str, Any]) -> bool:
        """Dispatch vehicle with route after receiving from fleet manager"""
        if vehicle_id not in self.vehicle_states:
            return False
            
        status = self.vehicle_states[vehicle_id]
        if status.state != VehicleState.FULL:
            return False
            
        # Update vehicle status for dispatch
        status.state = VehicleState.DISPATCHED
        status.route_id = route_data.get('route_id')
        status.destination = route_data.get('destination')
        status.engine_on = True
        status.journey_start_time = datetime.now()
        status.last_updated = datetime.now()
        
        # Remove from queue and activate next vehicle
        if vehicle_id in self.vehicle_queue:
            self.vehicle_queue.remove(vehicle_id)
        self.active_loading_vehicle = None
        self._update_queue_positions()
        self._activate_next_vehicle()
        
        logger.info(f"🚀 Vehicle {vehicle_id} DISPATCHED on route {status.route_id} to {status.destination}")
        return True
    
    def vehicle_completed_journey(self, vehicle_id: str) -> bool:
        """Handle vehicle returning to depot after complete journey"""
        if vehicle_id not in self.vehicle_states:
            return False
            
        status = self.vehicle_states[vehicle_id]
        
        # All passengers disembark
        disembarked_passengers = status.passengers
        status.passengers = 0
        status.state = VehicleState.DISEMBARKING
        status.engine_on = False
        status.route_id = None
        status.destination = None
        status.journey_start_time = None
        status.destination_arrival_time = None
        status.last_updated = datetime.now()
        
        logger.info(f"🏁 Vehicle {vehicle_id} completed journey - {disembarked_passengers} passengers disembarked")
        
        # Add back to queue
        self.add_vehicle_to_queue(vehicle_id, status.capacity)
        
        return True
    
    def update_vehicle_state(self, vehicle_id: str, new_state: VehicleState, **kwargs):
        """Update vehicle state during journey"""
        if vehicle_id not in self.vehicle_states:
            return
            
        status = self.vehicle_states[vehicle_id]
        status.state = new_state
        status.last_updated = datetime.now()
        
        # Update specific fields
        for key, value in kwargs.items():
            if hasattr(status, key):
                setattr(status, key, value)
        
        logger.info(f"🔄 Vehicle {vehicle_id} state updated to {new_state.value}")
    
    def get_vehicle_status(self, vehicle_id: str) -> Optional[VehicleStatus]:
        """Get current status of a vehicle"""
        return self.vehicle_states.get(vehicle_id)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get complete depot queue status"""
        return {
            'queue_length': len(self.vehicle_queue),
            'active_loading_vehicle': self.active_loading_vehicle,
            'queue_order': self.vehicle_queue.copy(),
            'vehicle_states': {vid: {
                'state': status.state.value,
                'passengers': status.passengers,
                'capacity': status.capacity,
                'queue_position': status.queue_position,
                'engine_on': status.engine_on
            } for vid, status in self.vehicle_states.items()}
        }
    
    def get_loading_vehicle_status(self) -> Optional[Dict[str, Any]]:
        """Get status of currently loading vehicle"""
        if not self.active_loading_vehicle:
            return None
            
        status = self.vehicle_states.get(self.active_loading_vehicle)
        if not status:
            return None
            
        return {
            'vehicle_id': status.vehicle_id,
            'state': status.state.value,
            'passengers': status.passengers,
            'capacity': status.capacity,
            'loading_progress': status.loading_progress,
            'is_full': status.is_full,
            'can_depart': status.can_depart
        }
