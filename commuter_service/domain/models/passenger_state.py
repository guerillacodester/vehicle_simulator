"""
Passenger State Machine

Manages passenger lifecycle states based on timestamps:
- WAITING: spawned_at set, boarded_at is null
- BOARDED: boarded_at set, alighted_at is null
- ALIGHTED: alighted_at set
- CANCELLED: explicitly cancelled

State transitions are determined by timestamps, not explicit state field.
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PassengerStatus(str, Enum):
    """Passenger lifecycle states"""
    WAITING = "WAITING"
    BOARDED = "BOARDED"
    ALIGHTED = "ALIGHTED"
    CANCELLED = "CANCELLED"


class PassengerStateTransition(BaseModel):
    """Record of a state transition"""
    from_state: PassengerStatus
    to_state: PassengerStatus
    timestamp: datetime
    triggered_by: str = Field(..., description="What caused the transition (external, internal, vehicle_id)")
    

def calculate_passenger_state(
    spawned_at: Optional[datetime],
    boarded_at: Optional[datetime],
    alighted_at: Optional[datetime],
    status: Optional[str] = None
) -> PassengerStatus:
    """
    Calculate passenger state based on timestamps.
    
    Business Logic:
    - If status == CANCELLED: CANCELLED (explicit override)
    - If alighted_at is set: ALIGHTED
    - If boarded_at is set: BOARDED
    - If spawned_at is set: WAITING
    - Otherwise: Invalid state
    
    Args:
        spawned_at: When passenger spawned
        boarded_at: When passenger boarded vehicle
        alighted_at: When passenger alighted vehicle
        status: Optional explicit status override
    
    Returns:
        PassengerStatus enum
    """
    # Explicit cancellation overrides everything
    if status == PassengerStatus.CANCELLED.value:
        return PassengerStatus.CANCELLED
    
    # Timestamp-based state determination
    if alighted_at is not None:
        return PassengerStatus.ALIGHTED
    
    if boarded_at is not None:
        return PassengerStatus.BOARDED
    
    if spawned_at is not None:
        return PassengerStatus.WAITING
    
    # Should never reach here in production
    raise ValueError("Invalid passenger state: no timestamps set")


def validate_state_transition(
    current_state: PassengerStatus,
    new_state: PassengerStatus
) -> bool:
    """
    Validate if a state transition is allowed.
    
    Allowed transitions:
    - WAITING → BOARDED
    - WAITING → CANCELLED
    - BOARDED → ALIGHTED
    - BOARDED → CANCELLED
    - CANCELLED → WAITING (resurrection)
    
    Disallowed:
    - ALIGHTED → anything (final state)
    - Backwards transitions (except CANCELLED → WAITING)
    
    Args:
        current_state: Current passenger state
        new_state: Desired new state
    
    Returns:
        True if transition is valid
    """
    # ALIGHTED is final - no transitions allowed
    if current_state == PassengerStatus.ALIGHTED:
        return False
    
    # Valid transitions
    valid_transitions = {
        PassengerStatus.WAITING: {PassengerStatus.BOARDED, PassengerStatus.CANCELLED},
        PassengerStatus.BOARDED: {PassengerStatus.ALIGHTED, PassengerStatus.CANCELLED},
        PassengerStatus.CANCELLED: {PassengerStatus.WAITING}  # Allow resurrection
    }
    
    allowed = valid_transitions.get(current_state, set())
    return new_state in allowed


class PassengerStateChange(BaseModel):
    """Detected state change for monitoring"""
    passenger_id: str
    previous_state: PassengerStatus
    new_state: PassengerStatus
    changed_fields: list[str]
    timestamp: datetime
    external_trigger: bool = Field(..., description="True if changed by external process")
