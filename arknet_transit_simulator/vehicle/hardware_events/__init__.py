"""
Hardware Event System
====================

Unified interface for passenger boarding/alighting events that can be triggered by:
- Physical hardware (RFID readers, door sensors, GPS, driver tablets)
- Simulated conductor (for testing/simulation)

Both use the same API endpoints, ensuring simulation matches real-world behavior.
"""

from .event_client import HardwareEventClient
# from .door_sensor import DoorSensor
# from .rfid_reader import RFIDReader
# from .passenger_counter import PassengerCounter

__all__ = [
    'HardwareEventClient',
    'DoorSensor', 
    'RFIDReader',
    'PassengerCounter',
]
