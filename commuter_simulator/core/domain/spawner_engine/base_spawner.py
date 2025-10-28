"""
Spawner Interface - Abstract base for all spawner implementations.
Defines the contract for generating commuters (passengers).

Spawners are responsible for:
1. Generating commuter/passenger objects based on spatial/temporal rules
2. Pushing generated commuters to a reservoir
3. Tracking spawn statistics for monitoring

Spawners are NOT responsible for:
- Persistence (handled by reservoirs/repositories)
- Movement/simulation (handled by vehicle simulator)
- Pickup/dropoff logic (handled by conductor)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SpawnRequest:
    """Request to spawn a single commuter/passenger"""
    passenger_id: str
    spawn_location: tuple  # (lat, lon)
    destination_location: tuple  # (lat, lon)
    route_id: str
    spawn_time: datetime
    spawn_context: str  # "ROUTE", "DEPOT", etc
    priority: float = 1.0
    generation_method: str = "unknown"


class ReservoirInterface(ABC):
    """Abstract interface for storing spawned commuters"""
    
    @abstractmethod
    async def push(self, spawn_request: SpawnRequest) -> str:
        """
        Store a spawned commuter in the reservoir.
        
        Args:
            spawn_request: SpawnRequest object with passenger details
            
        Returns:
            str: Unique passenger ID in reservoir
        """
        pass
    
    @abstractmethod
    async def push_batch(self, spawn_requests: List[SpawnRequest]) -> tuple:
        """
        Store multiple spawned commuters concurrently.
        
        Args:
            spawn_requests: List of SpawnRequest objects
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        pass
    
    @abstractmethod
    async def available(self, route_id: str = None, limit: int = 100) -> List[Dict]:
        """
        Get available (waiting) commuters.
        
        Args:
            route_id: Optional filter by route
            limit: Maximum number to return
            
        Returns:
            List of available commuter dicts
        """
        pass
    
    @abstractmethod
    async def mark_picked_up(self, passenger_id: str) -> bool:
        """
        Mark commuter as picked up by vehicle.
        
        Args:
            passenger_id: Passenger to mark
            
        Returns:
            True if successful
        """
        pass


class SpawnerInterface(ABC):
    """
    Abstract base class for all spawner implementations.
    
    Defines the contract that RouteSpawner, DepotSpawner, ZoneSpawner, etc must implement.
    """
    
    def __init__(self, reservoir: ReservoirInterface, config: Dict[str, Any]):
        """
        Initialize spawner.
        
        Args:
            reservoir: Where spawned passengers are stored
            config: Configuration dict for this spawner
        """
        self.reservoir = reservoir
        self.config = config
        self.spawn_count = 0
        self.spawn_errors = 0
    
    @abstractmethod
    async def spawn(self, current_time: datetime, time_window_minutes: int = 60) -> List[SpawnRequest]:
        """
        Generate passengers for the specified time window.
        
        Must be implemented by subclasses (RouteSpawner, DepotSpawner, etc).
        
        Args:
            current_time: Current simulation time
            time_window_minutes: How many minutes to spawn for
            
        Returns:
            List of SpawnRequest objects (not yet persisted)
        """
        pass
    
    async def spawn_and_store(self, current_time: datetime, time_window_minutes: int = 60) -> int:
        """
        Generate passengers AND store in reservoir (template method pattern).
        
        This is the main entry point for spawning. It:
        1. Calls spawn() to generate requests
        2. Stores them via reservoir.push_batch()
        3. Tracks statistics
        
        Args:
            current_time: Current simulation time
            time_window_minutes: How many minutes to spawn for
            
        Returns:
            Number of successfully spawned passengers
        """
        try:
            # Generate spawn requests
            spawn_requests = await self.spawn(current_time, time_window_minutes)
            
            if not spawn_requests:
                return 0
            
            # Store via reservoir
            if self.reservoir:
                successful, failed = await self.reservoir.push_batch(spawn_requests)
                self.spawn_count += successful
                self.spawn_errors += failed
                return successful
            else:
                # No reservoir, just track generates
                self.spawn_count += len(spawn_requests)
                return len(spawn_requests)
                
        except Exception as e:
            self.spawn_errors += 1
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get spawner statistics"""
        return {
            "total_spawned": self.spawn_count,
            "total_errors": self.spawn_errors,
            "success_rate": (
                self.spawn_count / (self.spawn_count + self.spawn_errors)
                if (self.spawn_count + self.spawn_errors) > 0 else 0.0
            )
        }
