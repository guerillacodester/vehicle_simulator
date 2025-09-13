#!/usr/bin/env python3
"""
BasePerson
----------
Base class for all vehicle person components that need state management.

This class integrates the core StateMachine functionality with person-specific
lifecycle patterns. All person components (VehicleDriver, Conductor) can inherit 
from this to get consistent PersonState management.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from .base_component import BaseComponent
from ..core.states import PersonState


class BasePerson(BaseComponent):
    """
    Base class for person components with PersonState management.
    
    Provides a consistent interface for person lifecycle:
    - arrive() - Person arrives at work location (OFFSITE → ARRIVING → ONSITE)
    - depart() - Person leaves work location (ONSITE → DEPARTING → OFFSITE)
    - go_unavailable() - Person becomes unavailable (any state → UNAVAILABLE)
    - State transitions with logging
    """
    
    def __init__(self, person_id: str, person_type: str, person_name: str = None):
        """
        Initialize base person component.
        
        Args:
            person_id: Unique identifier for this person (e.g., driver ID)
            person_type: Type of person (for logging, e.g., "VehicleDriver", "Conductor")
            person_name: Human-readable name (optional)
        """
        super().__init__(person_id, person_type, PersonState.OFFSITE)
        self.person_name = person_name or person_id
        
    async def arrive(self) -> bool:
        """
        Person arrives at work location.
        Alias for start() that's more semantically appropriate for people.
        """
        return await self.start()
    
    async def depart(self) -> bool:
        """
        Person departs from work location.
        Alias for stop() that's more semantically appropriate for people.
        """
        return await self.stop()
    
    async def go_unavailable(self, reason: str = "Unknown") -> bool:
        """
        Mark person as unavailable (sick, emergency, etc.).
        
        Args:
            reason: Reason for unavailability (for logging)
            
        Returns:
            bool: True if transition successful
        """
        current = self.current_state
        success = await self.transition_to(PersonState.UNAVAILABLE)
        if success:
            self.logger.info(f"{self.person_name} ({self.component_id}) unavailable: {reason}")
        return success
    
    async def return_to_duty(self) -> bool:
        """
        Return person from unavailable to onsite status.
        
        Returns:
            bool: True if transition successful
        """
        if self.current_state == PersonState.UNAVAILABLE:
            return await self.transition_to(PersonState.ONSITE)
        return True
    
    def is_available(self) -> bool:
        """
        Check if person is available for work.
        
        Returns:
            bool: True if person is onsite and available
        """
        return self.current_state == PersonState.ONSITE
    
    def is_present(self) -> bool:
        """
        Check if person is physically present (onsite or arriving).
        
        Returns:
            bool: True if person is at work location
        """
        return self.current_state in [PersonState.ONSITE, PersonState.ARRIVING]
    
    def get_person_status(self) -> dict:
        """
        Get person-specific status information.
        
        Returns:
            dict: Status information including person details
        """
        status = self.get_status()
        status.update({
            "person_name": self.person_name,
            "is_available": self.is_available(),
            "is_present": self.is_present()
        })
        return status