#!/usr/bin/env python3
"""
BaseComponent
-------------
Base class for all vehicle components that need state management.

This class integrates the core StateMachine functionality with vehicle-specific
component lifecycle patterns. All vehicle components (Engine, GPS Device,
Conductor, VehicleDriver) can inherit from this to get consistent state management.
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from ..core.states import StateMachine, DeviceState, PersonState, DriverState


class BaseComponent(StateMachine, ABC):
    """
    Base class for vehicle components with state management.
    
    Provides a consistent interface for component lifecycle:
    - start() / on() - Initialize and start the component
    - stop() / off() - Shutdown the component
    - State transitions with logging
    - Abstract methods for component-specific implementation
    """
    
    def __init__(self, component_id: str, component_type: str, initial_state: Enum):
        """
        Initialize base component.
        
        Args:
            component_id: Unique identifier for this component instance
            component_type: Type of component (for logging)
            initial_state: Initial state from appropriate enum
        """
        super().__init__(f"{component_type}({component_id})", initial_state)
        self.component_id = component_id
        self.component_type = component_type
        self.logger = logging.getLogger(__name__)
        
    @abstractmethod
    async def _start_implementation(self) -> bool:
        """
        Component-specific startup implementation.
        
        Returns:
            bool: True if startup successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def _stop_implementation(self) -> bool:
        """
        Component-specific shutdown implementation.
        
        Returns:
            bool: True if shutdown successful, False otherwise
        """
        pass
    
    async def start(self) -> bool:
        """
        Start the component with state management.
        
        Returns:
            bool: True if started successfully
        """
        # Handle different state types
        if isinstance(self.current_state, DeviceState):
            if self.current_state == DeviceState.ON:
                return True
            
            # Transition to STARTING
            await self.transition_to(DeviceState.STARTING)
            
            # Call component implementation
            success = await self._start_implementation()
            
            if success:
                await self.transition_to(DeviceState.ON)
            else:
                await self.transition_to(DeviceState.ERROR)
                
            return success
            
        elif isinstance(self.current_state, PersonState):
            if self.current_state == PersonState.ONSITE:
                return True
                
            # Transition to arriving
            await self.transition_to(PersonState.ARRIVING)
            
            # Call component implementation
            success = await self._start_implementation()
            
            if success:
                await self.transition_to(PersonState.ONSITE)
            else:
                await self.transition_to(PersonState.UNAVAILABLE)
                
            return success
            
        elif isinstance(self.current_state, DriverState):
            if self.current_state == DriverState.ONBOARD:
                return True
                
            # Transition to boarding
            await self.transition_to(DriverState.BOARDING)
            
            # Call component implementation  
            success = await self._start_implementation()
            
            if success:
                await self.transition_to(DriverState.ONBOARD)
            else:
                await self.transition_to(DriverState.DISEMBARKED)
                
            return success
        
        return False
    
    async def stop(self) -> bool:
        """
        Stop the component with state management.
        
        Returns:
            bool: True if stopped successfully
        """
        # Handle different state types
        if isinstance(self.current_state, DeviceState):
            if self.current_state == DeviceState.OFF:
                return True
                
            # Transition to STOPPING
            await self.transition_to(DeviceState.STOPPING)
            
            # Call component implementation
            success = await self._stop_implementation()
            
            # Always transition to OFF, even if stop had issues
            await self.transition_to(DeviceState.OFF)
            return success
            
        elif isinstance(self.current_state, PersonState):
            if self.current_state == PersonState.OFFSITE:
                return True
                
            # Transition to departing
            await self.transition_to(PersonState.DEPARTING)
            
            # Call component implementation
            success = await self._stop_implementation()
            
            # Always transition to OFFSITE
            await self.transition_to(PersonState.OFFSITE)
            return success
            
        elif isinstance(self.current_state, DriverState):
            if self.current_state == DriverState.DISEMBARKED:
                return True
                
            # Transition to disembarking
            await self.transition_to(DriverState.DISEMBARKING)
            
            # Call component implementation
            success = await self._stop_implementation()
            
            # Always transition to DISEMBARKED
            await self.transition_to(DriverState.DISEMBARKED)
            return success
        
        return False
    
    # Convenience aliases for device components
    async def on(self) -> bool:
        """Alias for start() - common for device components."""
        return await self.start()
    
    async def off(self) -> bool:
        """Alias for stop() - common for device components."""
        return await self.stop()
    
    def get_status(self) -> dict:
        """
        Get component status information.
        
        Returns:
            dict: Status information including state and component details
        """
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "current_state": self.current_state.value,
            "state_type": type(self.current_state).__name__
        }
    
    def is_active(self) -> bool:
        """
        Check if component is in an active/operational state.
        
        Returns:
            bool: True if component is active
        """
        if isinstance(self.current_state, DeviceState):
            return self.current_state == DeviceState.ON
        elif isinstance(self.current_state, PersonState):
            return self.current_state == PersonState.ONSITE
        elif isinstance(self.current_state, DriverState):
            return self.current_state == DriverState.ONBOARD
        
        return False