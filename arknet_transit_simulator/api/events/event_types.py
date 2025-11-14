"""Event types for the fleet management event bus."""

from enum import Enum


class EventType(str, Enum):
    """All possible event types in the system."""
    
    # Vehicle events
    POSITION_UPDATE = "position_update"
    ENGINE_STARTED = "engine_started"
    ENGINE_STOPPED = "engine_stopped"
    
    # Driver events
    DRIVER_STATE_CHANGED = "driver_state_changed"
    
    # GPS events
    GPS_STARTED = "gps_started"
    GPS_STOPPED = "gps_stopped"
    
    # Conductor events
    PASSENGER_BOARDED = "passenger_boarded"
    PASSENGER_ALIGHTED = "passenger_alighted"
    BOARDING_ENABLED = "boarding_enabled"
    BOARDING_DISABLED = "boarding_disabled"
    DEPOT_BOARDING_STARTED = "depot_boarding_started"
    DEPOT_BOARDING_ENDED = "depot_boarding_ended"
    
    # System events
    SIMULATOR_STARTED = "simulator_started"
    SIMULATOR_STOPPED = "simulator_stopped"
