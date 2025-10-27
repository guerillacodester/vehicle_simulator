"""
Depot Spawning System
---------------------
Manages vehicle creation and departure scheduling from a depot.

This module provides a lightweight depot abstraction for initializing vehicles
and scheduling their departures. Vehicles are created with a route ID and
departure time, and the depot tracks their state.

Design principles:
- Independent of GPS/networking (no side effects on creation)
- Simple data model: Depot holds Vehicle list, schedules departures
- No async/await complexity; caller manages task scheduling
- Integrates with vehicle_simulator.py test harness

Classes:
  - Vehicle: Represents a single vehicle with ID, route, capacity, state
  - Depot: Manages fleet initialization and departure scheduling
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VehicleState(Enum):
    """Vehicle lifecycle states."""
    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
    DEPARTED = "DEPARTED"
    RETURNING = "RETURNING"
    IDLE = "IDLE"


@dataclass
class Vehicle:
    """
    Represents a single vehicle.
    
    Attributes:
        vehicle_id: Unique identifier (e.g., "VHCL_001")
        route_id: Route this vehicle is assigned to
        capacity: Max passenger count
        departure_time: When vehicle departs from depot (datetime or None)
        state: Current lifecycle state
        pickup_count: Total pickups this vehicle has made
    """
    vehicle_id: str
    route_id: str
    capacity: int = 50
    departure_time: Optional[datetime] = None
    state: VehicleState = field(default=VehicleState.CREATED)
    pickup_count: int = 0
    
    def __repr__(self) -> str:
        return (
            f"Vehicle(id={self.vehicle_id}, route={self.route_id}, "
            f"depart={self.departure_time}, state={self.state.value}, "
            f"pickups={self.pickup_count})"
        )


class Depot:
    """
    Manages vehicle fleet initialization and departure scheduling.
    
    Methods:
      - add_vehicle(vehicle): Add a vehicle to the depot fleet
      - schedule_departure(vehicle_id, time): Set vehicle departure time
      - get_departures(time_window): Query vehicles departing in a time range
      - get_vehicle(vehicle_id): Retrieve a vehicle by ID
      - get_all_vehicles(): Return all vehicles
      - mark_departed(vehicle_id): Update vehicle state to DEPARTED
    """
    
    def __init__(self, name: str, location: str = "main_depot"):
        """
        Initialize a depot.
        
        Args:
            name: Depot name (e.g., "Downtown Depot")
            location: Geographic location or zone (e.g., "downtown")
        """
        self.name = name
        self.location = location
        self.vehicles: Dict[str, Vehicle] = {}
        self.created_at = datetime.now()
        logger.info(f"Depot '{name}' created at {self.location}")
    
    def add_vehicle(self, vehicle: Vehicle) -> None:
        """
        Add a vehicle to the depot fleet.
        
        Args:
            vehicle: Vehicle instance to add
            
        Raises:
            ValueError: If vehicle ID already exists
        """
        if vehicle.vehicle_id in self.vehicles:
            raise ValueError(
                f"Vehicle {vehicle.vehicle_id} already exists in depot {self.name}"
            )
        self.vehicles[vehicle.vehicle_id] = vehicle
        logger.info(
            f"Added {vehicle} to depot {self.name} "
            f"({len(self.vehicles)} total vehicles)"
        )
    
    def schedule_departure(self, vehicle_id: str, departure_time: datetime) -> None:
        """
        Schedule a vehicle departure.
        
        Args:
            vehicle_id: ID of the vehicle to schedule
            departure_time: DateTime when vehicle should depart
            
        Raises:
            KeyError: If vehicle_id not found
        """
        vehicle = self.vehicles[vehicle_id]
        vehicle.departure_time = departure_time
        vehicle.state = VehicleState.SCHEDULED
        logger.info(
            f"Scheduled {vehicle_id} to depart at {departure_time.isoformat()}"
        )
    
    def get_departures(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Vehicle]:
        """
        Get all vehicles scheduled to depart within a time window.
        
        Args:
            start_time: Start of window (inclusive)
            end_time: End of window (inclusive)
            
        Returns:
            List of Vehicle objects with departure_time in [start_time, end_time]
        """
        departures = [
            v for v in self.vehicles.values()
            if v.departure_time and start_time <= v.departure_time <= end_time
        ]
        departures.sort(key=lambda v: v.departure_time)  # type: ignore
        return departures
    
    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get a single vehicle by ID."""
        return self.vehicles.get(vehicle_id)
    
    def get_all_vehicles(self) -> List[Vehicle]:
        """Return all vehicles in depot."""
        return list(self.vehicles.values())
    
    def mark_departed(self, vehicle_id: str) -> None:
        """
        Update vehicle state to DEPARTED.
        
        Args:
            vehicle_id: ID of the vehicle that departed
            
        Raises:
            KeyError: If vehicle_id not found
        """
        vehicle = self.vehicles[vehicle_id]
        vehicle.state = VehicleState.DEPARTED
        logger.info(f"Vehicle {vehicle_id} marked as departed")
    
    def increment_pickups(self, vehicle_id: str, count: int = 1) -> None:
        """
        Increment pickup count for a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            count: Number of pickups to add (default 1)
            
        Raises:
            KeyError: If vehicle_id not found
        """
        vehicle = self.vehicles[vehicle_id]
        vehicle.pickup_count += count
        logger.debug(f"Vehicle {vehicle_id} pickup count: {vehicle.pickup_count}")
    
    def summary(self) -> str:
        """Return a summary of depot state."""
        scheduled = sum(1 for v in self.vehicles.values() if v.state == VehicleState.SCHEDULED)
        departed = sum(1 for v in self.vehicles.values() if v.state == VehicleState.DEPARTED)
        total_pickups = sum(v.pickup_count for v in self.vehicles.values())
        
        return (
            f"Depot '{self.name}' ({self.location}): "
            f"{len(self.vehicles)} vehicles, "
            f"{scheduled} scheduled, {departed} departed, "
            f"{total_pickups} total pickups"
        )


def create_standard_depot(
    name: str = "Main Depot",
    num_vehicles: int = 4,
    route_id: str = "gg3pv3z19hhm117v9xth5ezq",
    start_time: datetime = None,
    interval_minutes: int = 20,
) -> Depot:
    """
    Create a depot with N vehicles on a standard schedule.
    
    Convenience function for testing. Creates vehicles with IDs VHCL_001, VHCL_002, etc.,
    and schedules departures at intervals starting from start_time.
    
    Args:
        name: Depot name
        num_vehicles: Number of vehicles to create
        route_id: Route ID all vehicles will service
        start_time: First departure time (default: now + 5 min)
        interval_minutes: Minutes between departures
        
    Returns:
        Depot with initialized and scheduled vehicles
    """
    if start_time is None:
        start_time = datetime.now() + timedelta(minutes=5)
    
    depot = Depot(name)
    
    for i in range(num_vehicles):
        vehicle_id = f"VHCL_{i+1:03d}"
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            route_id=route_id,
            capacity=50
        )
        depot.add_vehicle(vehicle)
        
        departure = start_time + timedelta(minutes=interval_minutes * i)
        depot.schedule_departure(vehicle_id, departure)
    
    logger.info(f"Created standard depot with {num_vehicles} vehicles")
    return depot
