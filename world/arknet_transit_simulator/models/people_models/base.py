#!/usr/bin/env python3
"""
Base Interface for People Distribution Models
============================================

This module defines the plugin interface for passenger distribution models.
All distribution models must implement IPeopleDistributionModel to be compatible
with the PeopleSimulator engine.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

# Forward declaration to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..people import Passenger


class IPeopleDistributionModel(ABC):
    """
    Interface for passenger distribution models.
    
    This plugin architecture allows swapping different passenger generation
    patterns (Poisson, peak times, business locations, etc.).
    
    All distribution models must implement this interface to work with
    the PeopleSimulator engine.
    """
    
    @abstractmethod
    async def generate_passengers(
        self, 
        available_routes: List[str], 
        current_time: datetime,
        simulation_duration: int
    ) -> List['Passenger']:
        """
        Generate passengers based on the distribution model.
        
        Args:
            available_routes: List of route IDs available for passenger assignment
            current_time: Current simulation time
            simulation_duration: Total simulation duration in seconds
            
        Returns:
            List of generated passengers
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of this distribution model."""
        pass
    
    @abstractmethod
    def get_model_parameters(self) -> Dict[str, Any]:
        """Return the current parameters of this distribution model."""
        pass