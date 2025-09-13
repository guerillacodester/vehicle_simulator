"""
Context-specific state management for vehicle simulator components.

Each component type has states that reflect their real-world operational context.
"""

import logging
from enum import Enum


class DepotState(Enum):
    """States for depot/building components."""
    CLOSED = "CLOSED"             # Depot is closed
    OPENING = "OPENING"           # Depot is opening up
    OPEN = "OPEN"                 # Depot is open and operational
    CLOSING = "CLOSING"           # Depot is closing down
    MAINTENANCE = "MAINTENANCE"   # Depot under maintenance


class PersonState(Enum):
    """States for person components (depot_manager, dispatcher, conductor)."""
    OFFSITE = "OFFSITE"          # Person is not at work location
    ARRIVING = "ARRIVING"        # Person is coming to work
    ONSITE = "ONSITE"           # Person is at work location and active
    DEPARTING = "DEPARTING"     # Person is leaving work
    UNAVAILABLE = "UNAVAILABLE" # Person is unavailable (sick, etc.)


class DriverState(Enum):
    """States for driver components."""
    DISEMBARKED = "DISEMBARKED"  # Driver not on vehicle
    BOARDING = "BOARDING"        # Driver getting on vehicle
    WAITING = "WAITING"          # Driver on vehicle, engine off, waiting for start trigger
    ONBOARD = "ONBOARD"         # Driver is on vehicle and driving
    DISEMBARKING = "DISEMBARKING" # Driver getting off vehicle
    BREAK = "BREAK"             # Driver on break


class DeviceState(Enum):
    """States for device components (GPS, Engine, etc.)."""
    OFF = "OFF"                  # Device is powered off
    STARTING = "STARTING"        # Device is starting up
    ON = "ON"                   # Device is powered on and operational
    STOPPING = "STOPPING"       # Device is shutting down
    ERROR = "ERROR"             # Device has malfunction


class StateMachine:
    """
    Generic state machine base class for vehicle simulator components.
    
    Can work with any state enum type (DepotState, PersonState, etc.).
    Provides state management with transition logging.
    """
    
    def __init__(self, component_name: str, initial_state: Enum):
        self.component_name = component_name
        self.current_state = initial_state
        self.logger = logging.getLogger(__name__)
    
    async def transition_to(self, new_state: Enum) -> bool:
        """
        Transition to a new state with logging.
        
        Args:
            new_state: The state to transition to (must be same type as current_state)
            
        Returns:
            bool: True if transition successful
        """
        if new_state == self.current_state:
            return True
            
        # Verify state types match
        if type(new_state) != type(self.current_state):
            self.logger.error(f"[{self.component_name}] Invalid state type: {type(new_state)} != {type(self.current_state)}")
            return False
            
        old_state = self.current_state
        self.current_state = new_state
        
        self.logger.info(f"[{self.component_name}] State transition: {old_state.value} → {new_state.value}")
        return True