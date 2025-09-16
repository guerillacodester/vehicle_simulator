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
from datetime import datetime

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
    
    def __init__(self, person_id: str, person_type: str = "Person", person_name: str = None, 
                 origin_stop_id: str = None, destination_stop_id: str = None, 
                 depart_time: datetime = None, **kwargs):
        """
        Initialize base person component.
        
        Args:
            person_id: Unique identifier for this person (e.g., driver ID, passenger ID)
            person_type: Type of person (for logging, e.g., "VehicleDriver", "Conductor", "Passenger")
            person_name: Human-readable name (optional)
            origin_stop_id: Origin stop for passengers (optional)
            destination_stop_id: Destination stop for passengers (optional)
            depart_time: Desired departure time for passengers (optional)
            **kwargs: Additional passenger-specific attributes
        """
        super().__init__(person_id, person_type, PersonState.OFFSITE)
        self.person_name = person_name or person_id
        
        # Passenger-specific attributes (only used when person_type is "Passenger")
        if person_type == "Passenger" or origin_stop_id or destination_stop_id:
            from datetime import datetime
            self.origin_stop_id = origin_stop_id
            self.destination_stop_id = destination_stop_id
            self.depart_time = depart_time or datetime.now()
            self.created_at = datetime.now()
            self.boarding_time = None
            self.arrival_time = None
            self.current_vehicle = None
            self.travel_status = "waiting"  # waiting -> boarding -> traveling -> arrived
            
            # Additional passenger attributes from kwargs
            for key, value in kwargs.items():
                setattr(self, key, value)
        
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
        
        # Add passenger-specific status if this is a passenger
        if hasattr(self, 'origin_stop_id'):
            status.update({
                "origin_stop_id": self.origin_stop_id,
                "destination_stop_id": self.destination_stop_id,
                "depart_time": self.depart_time.isoformat() if self.depart_time else None,
                "travel_status": getattr(self, 'travel_status', 'unknown'),
                "current_vehicle": getattr(self, 'current_vehicle', None)
            })
        
        return status
    
    # Passenger-specific methods (only relevant when person_type is "Passenger")
    def board_vehicle(self, vehicle_id: str) -> bool:
        """
        Passenger boards a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle being boarded
            
        Returns:
            bool: True if boarding successful
        """
        if hasattr(self, 'travel_status'):
            self.current_vehicle = vehicle_id
            self.boarding_time = datetime.now()
            self.travel_status = "traveling"
            self.logger.info(f"Passenger {self.person_id} boarded vehicle {vehicle_id}")
            return True
        return False
    
    def arrive_at_destination(self) -> bool:
        """
        Passenger arrives at destination.
        
        Returns:
            bool: True if arrival processed successfully
        """
        if hasattr(self, 'travel_status'):
            self.arrival_time = datetime.now()
            self.travel_status = "arrived"
            
            if hasattr(self, 'boarding_time') and self.boarding_time:
                travel_time = (self.arrival_time - self.boarding_time).total_seconds()
                self.logger.info(f"Passenger {self.person_id} arrived after {travel_time:.1f}s travel time")
            else:
                self.logger.info(f"Passenger {self.person_id} arrived at destination")
            return True
        return False
    
    def get_wait_time(self) -> float:
        """
        Get how long passenger has been waiting.
        
        Returns:
            float: Wait time in seconds
        """
        if hasattr(self, 'created_at') and hasattr(self, 'travel_status'):
            if self.travel_status == "waiting":
                return (datetime.now() - self.created_at).total_seconds()
        return 0.0