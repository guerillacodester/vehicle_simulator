#!/usr/bin/env python3
"""
People Simulator
================

Realistic passenger simulation with pluggable distribution models.

This module provides:
- Passenger class for modeling individual passengers with pickup/destination points
- Pluggable distribution models (Poisson, peak times, business locations)
- PeopleSimulator engine for continuous passenger generation
- Real-world passenger behavior modeling

Architecture:
- Passenger: Individual passenger with journey details
- IPeopleDistributionModel: Plugin interface for distribution models (now in people_models/base.py)
- PoissonDistributionModel: First distribution model implementation (now in people_models/poisson.py)
- PeopleSimulator: Core engine for passenger generation and lifecycle management
"""

import logging
import uuid
import asyncio
import math
import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import numpy as np
import aiohttp

from ..vehicle.base_person import BasePerson

# Import plugin models from separate files
from .people_models import IPeopleDistributionModel, PoissonDistributionModel


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PeopleSimulatorConfig:
    """Configuration for the people simulator."""
    api_base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    request_timeout: int = 10
    
    @property
    def api_url(self) -> str:
        """Get the full API base URL."""
        return f"{self.api_base_url}/api/{self.api_version}"


# ============================================================================
# PASSENGER CLASSES
# ============================================================================

@dataclass
class JourneyDetails:
    """Details about a passenger's journey."""
    route_id: str
    pickup_lat: float
    pickup_lon: float  
    destination_lat: float
    destination_lon: float
    pickup_time: datetime = field(default_factory=datetime.now)
    destination_time: Optional[datetime] = None
    journey_distance_km: float = field(init=False)
    
    def __post_init__(self):
        """Calculate journey distance after initialization."""
        self.journey_distance_km = self._calculate_distance()
    
    def _calculate_distance(self) -> float:
        """Calculate distance between pickup and destination using Haversine formula."""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(self.pickup_lat), math.radians(self.pickup_lon)
        lat2, lon2 = math.radians(self.destination_lat), math.radians(self.destination_lon)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r


class Passenger(BasePerson):
    """
    A passenger with pickup and destination points along a route.
    
    Passengers are created by distribution models and represent real-world
    passenger behavior patterns. They are permanently deleted when their
    journey (pickup to destination) is satisfied.
    """
    
    def __init__(
        self,
        passenger_id: str = None,
        journey: JourneyDetails = None,
        passenger_type: str = "regular"
    ):
        """
        Initialize a passenger with journey details.
        
        Args:
            passenger_id: Unique identifier (auto-generated if None)
            journey: Journey details including route, pickup, destination
            passenger_type: Type of passenger (regular, priority, etc.)
        """
        passenger_id = passenger_id or f"PASS_{uuid.uuid4().hex[:8].upper()}"
        super().__init__(passenger_id, "Passenger", f"Passenger-{passenger_id}")
        
        self.journey = journey or JourneyDetails("unknown", 0.0, 0.0, 0.0, 0.0)
        self.passenger_type = passenger_type
        self.is_picked_up = False
        self.is_journey_complete = False
        self.pickup_satisfied = False
        self.destination_satisfied = False
        
        # Validation
        self._validate_journey()
        
        self.logger.info(
            f"Passenger {self.component_id} created: "
            f"Route {self.journey.route_id}, "
            f"pickup ({self.journey.pickup_lat:.6f}, {self.journey.pickup_lon:.6f}), "
            f"destination ({self.journey.destination_lat:.6f}, {self.journey.destination_lon:.6f}), "
            f"distance {self.journey.journey_distance_km:.2f}km"
        )
    
    def _validate_journey(self) -> None:
        """Validate journey parameters meet real-world expectations."""
        if not self.journey:
            raise ValueError("Journey details are required")
        
        # Check distance is realistic (between 0.5km and 50km for urban transit)
        if self.journey.journey_distance_km < 0.5:
            self.logger.warning(
                f"Journey distance {self.journey.journey_distance_km:.2f}km is very short "
                f"for passenger {self.component_id}"
            )
        elif self.journey.journey_distance_km > 50:
            self.logger.warning(
                f"Journey distance {self.journey.journey_distance_km:.2f}km is very long "
                f"for passenger {self.component_id}"
            )
        
        # Check coordinates are not the same
        if (abs(self.journey.pickup_lat - self.journey.destination_lat) < 0.0001 and
            abs(self.journey.pickup_lon - self.journey.destination_lon) < 0.0001):
            raise ValueError("Pickup and destination cannot be the same location")
    
    async def _start_implementation(self) -> bool:
        """Passenger appears at pickup point and begins waiting."""
        try:
            self.logger.info(
                f"Passenger {self.component_id} waiting at pickup point: "
                f"({self.journey.pickup_lat:.6f}, {self.journey.pickup_lon:.6f})"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to start passenger {self.component_id}: {e}")
            return False
    
    async def _stop_implementation(self) -> bool:
        """Passenger completes journey and is removed from simulation."""
        try:
            self.is_journey_complete = True
            self.logger.info(
                f"Passenger {self.component_id} journey complete - removing from simulation"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop passenger {self.component_id}: {e}")
            return False
    
    def mark_picked_up(self, pickup_time: datetime = None) -> None:
        """Mark passenger as picked up by vehicle."""
        self.is_picked_up = True
        self.pickup_satisfied = True
        self.journey.pickup_time = pickup_time or datetime.now()
        
        self.logger.info(
            f"Passenger {self.component_id} picked up at "
            f"({self.journey.pickup_lat:.6f}, {self.journey.pickup_lon:.6f})"
        )
    
    def mark_destination_reached(self, destination_time: datetime = None) -> None:
        """Mark passenger as having reached destination."""
        if not self.is_picked_up:
            self.logger.warning(
                f"Passenger {self.component_id} reached destination without being picked up"
            )
        
        self.destination_satisfied = True
        self.journey.destination_time = destination_time or datetime.now()
        
        self.logger.info(
            f"Passenger {self.component_id} reached destination at "
            f"({self.journey.destination_lat:.6f}, {self.journey.destination_lon:.6f})"
        )
        
        # Journey is complete when both pickup and destination are satisfied
        if self.pickup_satisfied and self.destination_satisfied:
            self.is_journey_complete = True
    
    def is_ready_for_deletion(self) -> bool:
        """Check if passenger journey is complete and ready for deletion."""
        return self.is_journey_complete and self.pickup_satisfied and self.destination_satisfied
    
    def get_journey_summary(self) -> dict:
        """Get summary of passenger's journey details."""
        return {
            'passenger_id': self.component_id,
            'passenger_type': self.passenger_type,
            'route_id': self.journey.route_id,
            'pickup_coords': (self.journey.pickup_lat, self.journey.pickup_lon),
            'destination_coords': (self.journey.destination_lat, self.journey.destination_lon),
            'journey_distance_km': self.journey.journey_distance_km,
            'pickup_time': self.journey.pickup_time,
            'destination_time': self.journey.destination_time,
            'is_picked_up': self.is_picked_up,
            'pickup_satisfied': self.pickup_satisfied,
            'destination_satisfied': self.destination_satisfied,
            'is_journey_complete': self.is_journey_complete
        }


# ============================================================================
# DISTRIBUTION MODEL PLUGIN ARCHITECTURE - NOW IN SEPARATE FILES
# ============================================================================
# Distribution models are now located in people_models/ directory:
# - people_models/base.py: IPeopleDistributionModel interface
# - people_models/poisson.py: PoissonDistributionModel implementation


# ============================================================================
# PEOPLE SIMULATOR ENGINE
# ============================================================================

class PeopleSimulator:
    """
    Core engine for continuous passenger generation and lifecycle management.
    
    The PeopleSimulator:
    - Uses pluggable distribution models for passenger generation
    - Continuously generates passengers throughout simulation lifecycle
    - Manages passenger lifecycle (creation, pickup, destination, deletion)
    - Provides real-time statistics and monitoring
    """
    
    def __init__(
        self,
        distribution_model: IPeopleDistributionModel,
        generation_interval: float = 10.0,
        cleanup_interval: float = 30.0
    ):
        """
        Initialize the people simulator.
        
        Args:
            distribution_model: Pluggable distribution model for passenger generation
            generation_interval: How often to generate new passengers (seconds)
            cleanup_interval: How often to cleanup completed passengers (seconds)
        """
        self.distribution_model = distribution_model
        self.generation_interval = generation_interval
        self.cleanup_interval = cleanup_interval
        
        self.active_passengers: Dict[str, Passenger] = {}
        self.completed_passengers: List[Dict] = []
        self.available_routes: List[str] = []
        
        self.is_running = False
        self.simulation_start_time = None
        self.generation_task = None
        self.cleanup_task = None
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Statistics
        self.stats = {
            'total_generated': 0,
            'total_completed': 0,
            'current_active': 0,
            'peak_active': 0,
            'average_journey_time': 0.0
        }
    
    def set_available_routes(self, routes: List[str]) -> None:
        """Set the available routes for passenger generation."""
        self.available_routes = routes
        self.logger.info(f"Available routes set: {routes}")
    
    def swap_distribution_model(self, new_model: IPeopleDistributionModel) -> None:
        """Swap the distribution model (plugin architecture)."""
        old_model_name = self.distribution_model.get_model_name()
        self.distribution_model = new_model
        new_model_name = new_model.get_model_name()
        
        self.logger.info(f"Distribution model swapped: {old_model_name} → {new_model_name}")
    
    async def start(self, simulation_duration: int = 3600) -> bool:
        """Start the people simulator."""
        if self.is_running:
            self.logger.warning("People simulator is already running")
            return False
        
        if not self.available_routes:
            self.logger.error("No available routes set - cannot start people simulator")
            return False
        
        try:
            self.is_running = True
            self.simulation_start_time = datetime.now()
            
            self.logger.info(
                f"Starting people simulator with {self.distribution_model.get_model_name()} "
                f"for {simulation_duration} seconds"
            )
            
            # Start background tasks
            self.generation_task = asyncio.create_task(
                self._passenger_generation_loop(simulation_duration)
            )
            self.cleanup_task = asyncio.create_task(
                self._passenger_cleanup_loop()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start people simulator: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """Stop the people simulator."""
        if not self.is_running:
            return True
        
        try:
            self.is_running = False
            
            # Cancel background tasks
            if self.generation_task:
                self.generation_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Clean up all active passengers
            for passenger in list(self.active_passengers.values()):
                await passenger.stop()
            
            self.logger.info("People simulator stopped")
            self._log_final_statistics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop people simulator: {e}")
            return False
    
    async def _passenger_generation_loop(self, simulation_duration: int) -> None:
        """Background task for continuous passenger generation."""
        try:
            while self.is_running:
                current_time = datetime.now()
                
                # Generate new passengers using distribution model
                new_passengers = await self.distribution_model.generate_passengers(
                    self.available_routes,
                    current_time,
                    simulation_duration
                )
                
                # Add passengers to active list and start them
                for passenger in new_passengers:
                    self.active_passengers[passenger.component_id] = passenger
                    await passenger.start()
                    self.stats['total_generated'] += 1
                
                # Update statistics
                self.stats['current_active'] = len(self.active_passengers)
                if self.stats['current_active'] > self.stats['peak_active']:
                    self.stats['peak_active'] = self.stats['current_active']
                
                # Wait for next generation cycle
                await asyncio.sleep(self.generation_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Passenger generation loop cancelled")
        except Exception as e:
            self.logger.error(f"Passenger generation loop error: {e}")
    
    async def _passenger_cleanup_loop(self) -> None:
        """Background task for cleaning up completed passengers."""
        try:
            while self.is_running:
                completed_ids = []
                
                # Find passengers ready for deletion
                for passenger_id, passenger in self.active_passengers.items():
                    if passenger.is_ready_for_deletion():
                        completed_ids.append(passenger_id)
                        
                        # Store journey summary for statistics
                        journey_summary = passenger.get_journey_summary()
                        self.completed_passengers.append(journey_summary)
                        self.stats['total_completed'] += 1
                
                # Remove completed passengers
                for passenger_id in completed_ids:
                    passenger = self.active_passengers.pop(passenger_id)
                    await passenger.stop()
                    self.logger.info(f"Passenger {passenger_id} journey completed and removed")
                
                # Update statistics
                self.stats['current_active'] = len(self.active_passengers)
                
                if completed_ids:
                    self.logger.info(
                        f"Cleaned up {len(completed_ids)} completed passengers. "
                        f"Active: {self.stats['current_active']}, "
                        f"Total completed: {self.stats['total_completed']}"
                    )
                
                # Wait for next cleanup cycle
                await asyncio.sleep(self.cleanup_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Passenger cleanup loop cancelled")
        except Exception as e:
            self.logger.error(f"Passenger cleanup loop error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current simulation statistics."""
        self.stats['current_active'] = len(self.active_passengers)
        return self.stats.copy()
    
    def get_active_passengers(self) -> List[Passenger]:
        """Get list of currently active passengers."""
        return list(self.active_passengers.values())
    
    def get_passenger_by_id(self, passenger_id: str) -> Optional[Passenger]:
        """Get specific passenger by ID."""
        return self.active_passengers.get(passenger_id)
    
    def _log_final_statistics(self) -> None:
        """Log final simulation statistics."""
        self.logger.info("=== PEOPLE SIMULATOR FINAL STATISTICS ===")
        self.logger.info(f"Total passengers generated: {self.stats['total_generated']}")
        self.logger.info(f"Total passengers completed: {self.stats['total_completed']}")
        self.logger.info(f"Peak concurrent passengers: {self.stats['peak_active']}")
        self.logger.info(f"Distribution model: {self.distribution_model.get_model_name()}")
        
        # Model parameters
        params = self.distribution_model.get_model_parameters()
        self.logger.info(f"Model parameters: {params}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_poisson_people_simulator(
    base_lambda: float = 2.0,
    generation_interval: float = 10.0
) -> PeopleSimulator:
    """
    Convenience function to create a PeopleSimulator with Poisson distribution model.
    
    Args:
        base_lambda: Base rate for passenger generation (passengers per minute)
        generation_interval: How often to generate passengers (seconds)
        
    Returns:
        Configured PeopleSimulator instance
    """
    distribution_model = PoissonDistributionModel(base_lambda=base_lambda)
    return PeopleSimulator(distribution_model, generation_interval)


def create_custom_people_simulator(
    distribution_model: IPeopleDistributionModel,
    generation_interval: float = 10.0
) -> PeopleSimulator:
    """
    Convenience function to create a PeopleSimulator with custom distribution model.
    
    Args:
        distribution_model: Custom distribution model implementation
        generation_interval: How often to generate passengers (seconds)
        
    Returns:
        Configured PeopleSimulator instance
    """
    return PeopleSimulator(distribution_model, generation_interval)