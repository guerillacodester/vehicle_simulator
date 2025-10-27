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
    spawned_at: datetime
    latitude: float
    longitude: float
    destination_lat: float
    destination_lon: float
    destination_name: str
    route_id: Optional[str] = None
    depot_id: Optional[str] = None
    direction: str = "OUTBOUND"  # OUTBOUND, RETURN


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
    async def push_batch(self, spawn_requests: List[SpawnRequest]) -> List[str]:
        """
        Store multiple spawned commuters efficiently.
        
        Args:
            spawn_requests: List of SpawnRequest objects
            
        Returns:
            List[str]: Unique passenger IDs in reservoir
        """
        pass
    
    @abstractmethod
    async def available(self, limit: int = 100) -> List[SpawnRequest]:
        """Get available commuters (not yet picked up)"""
        pass


class SpawnerInterface(ABC):
    """
    Abstract base class for all spawner implementations.
    
    Spawners generate commuters based on spatial/temporal distribution rules
    and push them to a reservoir for consumption by the conductor.
    """
    
    def __init__(self, reservoir: ReservoirInterface, config: Dict[str, Any]):
        """
        Initialize spawner.
        
        Args:
            reservoir: Where to store spawned commuters (push-based)
            config: Configuration dict with spawner-specific parameters
        """
        self.reservoir = reservoir
        self.config = config
        self.spawn_count = 0
        self.spawn_errors = 0
    
    @abstractmethod
    async def spawn(self, current_time: datetime, time_window_minutes: int = 60) -> List[SpawnRequest]:
        """
        Generate commuters for a given time window.
        
        This method must be implemented by subclasses to define how commuters
        are generated (e.g., Poisson distribution for routes, uniform for depots).
        
        Args:
            current_time: Current simulation time
            time_window_minutes: Time window for spawning (default 60 min)
            
        Returns:
            List[SpawnRequest]: Generated commuter spawn requests
        """
        pass
    
    async def spawn_and_store(self, current_time: datetime, time_window_minutes: int = 60) -> List[str]:
        """
        Generate commuters AND push them to the reservoir.
        
        This template method handles the common flow:
        1. Call spawn() to generate commuters
        2. Push to reservoir
        3. Track statistics
        
        Args:
            current_time: Current simulation time
            time_window_minutes: Time window for spawning
            
        Returns:
            List[str]: Passenger IDs in reservoir
        """
        try:
            spawn_requests = await self.spawn(current_time, time_window_minutes)
            
            if not spawn_requests:
                return []
            
            # Push to reservoir (batch operation for efficiency)
            passenger_ids = await self.reservoir.push_batch(spawn_requests)
            
            self.spawn_count += len(spawn_requests)
            return passenger_ids
            
        except Exception as e:
            self.spawn_errors += 1
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get spawner statistics"""
        return {
            "spawn_count": self.spawn_count,
            "spawn_errors": self.spawn_errors,
            "error_rate": self.spawn_errors / max(1, self.spawn_count)
        }
