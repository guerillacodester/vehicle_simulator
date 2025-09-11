#!/usr/bin/env python3
"""
Vehicle Conductor - Passenger Management Component
-------------------------------------------------
The Conductor manages passenger boarding, counting, and departure decisions.
Part of the 4-layer hierarchy: DepotManager → Dispatcher → VehicleDriver → Conductor

Key Responsibilities:
- Count available seats
- Manage passenger boarding
- Signal driver when vehicle is full
- Handle passenger loading/unloading
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class Conductor:
    """
    Vehicle Conductor for passenger management
    
    The conductor is responsible for:
    1. Counting available seats
    2. Managing passenger boarding
    3. Signaling driver when full
    4. Passenger capacity management
    """
    
    def __init__(self, vehicle_id: str, capacity: int = 40, tick_time: float = 1.0):
        self.vehicle_id = vehicle_id
        self.capacity = capacity
        self.tick_time = tick_time
        
        # Passenger state
        self.passengers_on_board = 0
        self.seats_available = capacity
        self.boarding_active = False
        
        # Callbacks
        self.on_full_callback: Optional[Callable] = None
        self.on_empty_callback: Optional[Callable] = None
        
        # Threading
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        logger.info(f"Conductor initialized for vehicle {vehicle_id} (capacity: {capacity})")
    
    def set_departure_callback(self, callback: Callable):
        """Set callback to notify driver when vehicle is full"""
        self.on_full_callback = callback
        
    def set_empty_callback(self, callback: Callable):
        """Set callback to notify when vehicle is empty"""
        self.on_empty_callback = callback
    
    def board_passengers(self, count: int) -> bool:
        """
        Board passengers onto the vehicle
        
        Args:
            count: Number of passengers to board
            
        Returns:
            bool: True if passengers could board, False if not enough seats
        """
        if count <= 0:
            return False
            
        if self.passengers_on_board + count > self.capacity:
            # Can't board - not enough seats
            available = self.capacity - self.passengers_on_board
            logger.info(f"Conductor {self.vehicle_id}: Only {available} seats available, can't board {count}")
            return False
            
        # Board the passengers
        self.passengers_on_board += count
        self.seats_available = self.capacity - self.passengers_on_board
        
        logger.info(f"Conductor {self.vehicle_id}: Boarded {count} passengers ({self.passengers_on_board}/{self.capacity})")
        
        # Check if vehicle is now full
        if self.is_full():
            logger.info(f"Conductor {self.vehicle_id}: VEHICLE FULL! Signaling driver to depart")
            if self.on_full_callback:
                self.on_full_callback()
                
        return True
    
    def alight_passengers(self, count: int = None) -> int:
        """
        Passengers alighting (getting off)
        
        Args:
            count: Number of passengers alighting (None = all passengers)
            
        Returns:
            int: Number of passengers that alighted
        """
        if count is None:
            count = self.passengers_on_board
            
        alighted = min(count, self.passengers_on_board)
        self.passengers_on_board -= alighted
        self.seats_available = self.capacity - self.passengers_on_board
        
        logger.info(f"Conductor {self.vehicle_id}: {alighted} passengers alighted ({self.passengers_on_board}/{self.capacity})")
        
        # Check if vehicle is now empty
        if self.is_empty() and self.on_empty_callback:
            self.on_empty_callback()
            
        return alighted
    
    def is_full(self) -> bool:
        """Check if vehicle is at capacity"""
        return self.passengers_on_board >= self.capacity
        
    def is_empty(self) -> bool:
        """Check if vehicle has no passengers"""
        return self.passengers_on_board == 0
        
    def has_seats_available(self) -> bool:
        """Check if vehicle has available seats"""
        return self.seats_available > 0
        
    def get_passenger_count(self) -> int:
        """Get current passenger count"""
        return self.passengers_on_board
        
    def get_available_seats(self) -> int:
        """Get number of available seats"""
        return self.seats_available
        
    def get_capacity(self) -> int:
        """Get vehicle capacity"""
        return self.capacity
        
    def start_boarding(self):
        """Start accepting passengers"""
        self.boarding_active = True
        logger.info(f"Conductor {self.vehicle_id}: Boarding started - {self.seats_available} seats available")
        
    def stop_boarding(self):
        """Stop accepting passengers"""
        self.boarding_active = False
        logger.info(f"Conductor {self.vehicle_id}: Boarding stopped")
        
    def is_boarding_active(self) -> bool:
        """Check if boarding is active"""
        return self.boarding_active
        
    def get_status(self) -> Dict[str, Any]:
        """Get conductor status"""
        return {
            'vehicle_id': self.vehicle_id,
            'passengers': self.passengers_on_board,
            'capacity': self.capacity,
            'seats_available': self.seats_available,
            'boarding_active': self.boarding_active,
            'is_full': self.is_full(),
            'is_empty': self.is_empty()
        }
        
    def reset(self):
        """Reset conductor state (for new journey)"""
        self.passengers_on_board = 0
        self.seats_available = self.capacity
        self.boarding_active = False
        logger.info(f"Conductor {self.vehicle_id}: Reset for new journey")
        
    def __str__(self):
        """String representation"""
        status = "FULL" if self.is_full() else f"{self.seats_available} seats"
        boarding = "BOARDING" if self.boarding_active else "CLOSED"
        return f"Conductor({self.vehicle_id}): {self.passengers_on_board}/{self.capacity} - {status} - {boarding}"