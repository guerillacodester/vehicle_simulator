"""
Observer pattern for event-driven telemetry updates.

Allows decoupling of telemetry reception from UI/processing logic.
Any observer (GUI, logger, analytics engine) can subscribe to updates.
"""

from abc import ABC, abstractmethod
from typing import Callable, List
from .models import Vehicle


class TelemetryObserver(ABC):
    """
    Abstract observer for telemetry updates.
    
    Implement this interface to receive telemetry events.
    """
    
    @abstractmethod
    def on_vehicle_update(self, vehicle: Vehicle) -> None:
        """
        Called when a vehicle telemetry update is received.
        
        Args:
            vehicle: Updated vehicle telemetry data
        """
        pass
    
    @abstractmethod
    def on_error(self, error: Exception) -> None:
        """
        Called when an error occurs during telemetry reception.
        
        Args:
            error: Exception that occurred
        """
        pass
    
    @abstractmethod
    def on_connected(self) -> None:
        """Called when successfully connected to telemetry stream."""
        pass
    
    @abstractmethod
    def on_disconnected(self) -> None:
        """Called when disconnected from telemetry stream."""
        pass


class CallbackObserver(TelemetryObserver):
    """
    Simple callback-based observer.
    
    Uses function callbacks instead of inheritance.
    Useful for quick prototyping or simple use cases.
    
    Example:
        def on_update(vehicle):
            print(f"Vehicle {vehicle.deviceId} at {vehicle.lat}, {vehicle.lon}")
        
        observer = CallbackObserver(on_vehicle_update=on_update)
    """
    
    def __init__(
        self,
        on_vehicle_update: Callable[[Vehicle], None] = None,
        on_error: Callable[[Exception], None] = None,
        on_connected: Callable[[], None] = None,
        on_disconnected: Callable[[], None] = None,
    ):
        self._on_vehicle_update = on_vehicle_update
        self._on_error = on_error
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
    
    def on_vehicle_update(self, vehicle: Vehicle) -> None:
        if self._on_vehicle_update:
            self._on_vehicle_update(vehicle)
    
    def on_error(self, error: Exception) -> None:
        if self._on_error:
            self._on_error(error)
    
    def on_connected(self) -> None:
        if self._on_connected:
            self._on_connected()
    
    def on_disconnected(self) -> None:
        if self._on_disconnected:
            self._on_disconnected()


class ObservableClient:
    """
    Mixin for observable telemetry clients.
    
    Provides observer registration and notification methods.
    """
    
    def __init__(self):
        self._observers: List[TelemetryObserver] = []
    
    def add_observer(self, observer: TelemetryObserver) -> None:
        """Register an observer to receive telemetry updates."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: TelemetryObserver) -> None:
        """Unregister an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_vehicle_update(self, vehicle: Vehicle) -> None:
        """Notify all observers of a vehicle update."""
        for observer in self._observers:
            try:
                observer.on_vehicle_update(vehicle)
            except Exception as e:
                # Don't let observer errors crash the client
                print(f"Observer error: {e}")
    
    def _notify_error(self, error: Exception) -> None:
        """Notify all observers of an error."""
        for observer in self._observers:
            try:
                observer.on_error(error)
            except Exception as e:
                print(f"Observer error: {e}")
    
    def _notify_connected(self) -> None:
        """Notify all observers of successful connection."""
        for observer in self._observers:
            try:
                observer.on_connected()
            except Exception as e:
                print(f"Observer error: {e}")
    
    def _notify_disconnected(self) -> None:
        """Notify all observers of disconnection."""
        for observer in self._observers:
            try:
                observer.on_disconnected()
            except Exception as e:
                print(f"Observer error: {e}")
