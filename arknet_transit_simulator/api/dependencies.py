"""Dependencies for FastAPI endpoints."""

from typing import TYPE_CHECKING

from .events.event_bus import EventBus

if TYPE_CHECKING:
    from arknet_transit_simulator.simulator import CleanVehicleSimulator


# Global reference to the simulator instance
_simulator: 'CleanVehicleSimulator | None' = None

# Global event bus instance
_event_bus: EventBus = EventBus()


def set_simulator(sim: 'CleanVehicleSimulator'):
    """Set the global simulator instance."""
    global _simulator
    _simulator = sim


def get_simulator() -> 'CleanVehicleSimulator':
    """Dependency to get the simulator instance."""
    if _simulator is None:
        raise RuntimeError("Simulator not initialized")
    return _simulator


def get_event_bus() -> EventBus:
    """Dependency to get the event bus instance."""
    return _event_bus
