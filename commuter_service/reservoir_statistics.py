"""
Reservoir Statistics - Shared Statistics Tracking

This module provides thread-safe statistics tracking for reservoirs.
Extracted from DepotReservoir and RouteReservoir to follow DRY principle.

Responsibilities:
- Track spawned/picked_up/expired counts
- Thread-safe increment operations
- Statistics reporting and logging
- Uptime tracking

Used by:
- DepotReservoir
- RouteReservoir
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ReservoirStatistics:
    """
    Thread-safe statistics tracker for commuter reservoirs.
    
    Tracks key metrics:
    - total_spawned: Number of commuters spawned
    - total_picked_up: Number of commuters picked up by vehicles
    - total_expired: Number of commuters that timed out
    - waiting: Current number waiting (calculated)
    
    Example:
        stats = ReservoirStatistics(name="Depot_Speightstown")
        
        # Track events
        await stats.increment_spawned()
        await stats.increment_picked_up()
        
        # Get current stats
        current = await stats.get_stats()
        # → {"spawned": 1, "picked_up": 1, "expired": 0, "waiting": 0}
        
        # Log stats
        await stats.log_stats(logger)
    """
    
    name: str  # Identifier for logging (e.g., "Depot_Speightstown", "Route_1A")
    total_spawned: int = 0
    total_picked_up: int = 0
    total_expired: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    
    async def increment_spawned(self, count: int = 1):
        """
        Increment spawned counter (thread-safe).
        
        Args:
            count: Number to increment by (default: 1)
        """
        async with self._lock:
            self.total_spawned += count
    
    async def increment_picked_up(self, count: int = 1):
        """
        Increment picked_up counter (thread-safe).
        
        Args:
            count: Number to increment by (default: 1)
        """
        async with self._lock:
            self.total_picked_up += count
    
    async def increment_expired(self, count: int = 1):
        """
        Increment expired counter (thread-safe).
        
        Args:
            count: Number to increment by (default: 1)
        """
        async with self._lock:
            self.total_expired += count
    
    async def get_stats(self, waiting_count: Optional[int] = None) -> Dict:
        """
        Get current statistics snapshot (thread-safe).
        
        Args:
            waiting_count: Current number waiting (if known)
            
        Returns:
            Dictionary with all statistics
        """
        async with self._lock:
            stats = {
                "name": self.name,
                "total_spawned": self.total_spawned,
                "total_picked_up": self.total_picked_up,
                "total_expired": self.total_expired,
                "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
            }
            
            # Calculate or use provided waiting count
            if waiting_count is not None:
                stats["waiting_count"] = waiting_count
            else:
                # Calculate from totals
                stats["waiting_count"] = (
                    self.total_spawned - self.total_picked_up - self.total_expired
                )
            
            return stats
    
    async def log_stats(
        self,
        logger: logging.Logger,
        waiting_count: Optional[int] = None,
        level: int = logging.INFO
    ):
        """
        Log current statistics.
        
        Args:
            logger: Logger instance to use
            waiting_count: Current number waiting (if known)
            level: Logging level (default: INFO)
        """
        stats = await self.get_stats(waiting_count)
        
        logger.log(
            level,
            f"{self.name} Stats: "
            f"{stats['total_spawned']} spawned, "
            f"{stats['total_picked_up']} picked up, "
            f"{stats['total_expired']} expired, "
            f"{stats['waiting_count']} waiting | "
            f"Uptime: {stats['uptime_seconds']:.1f}s"
        )
    
    async def reset(self):
        """
        Reset all counters to zero (thread-safe).
        
        Useful for testing or restarting tracking.
        """
        async with self._lock:
            self.total_spawned = 0
            self.total_picked_up = 0
            self.total_expired = 0
            self.created_at = datetime.now()
    
    def get_stats_sync(self, waiting_count: Optional[int] = None) -> Dict:
        """
        Get statistics synchronously (non-async version).
        
        WARNING: Not thread-safe! Use only when async is not available.
        
        Args:
            waiting_count: Current number waiting (if known)
            
        Returns:
            Dictionary with all statistics
        """
        stats = {
            "name": self.name,
            "total_spawned": self.total_spawned,
            "total_picked_up": self.total_picked_up,
            "total_expired": self.total_expired,
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
        }
        
        if waiting_count is not None:
            stats["waiting_count"] = waiting_count
        else:
            stats["waiting_count"] = (
                self.total_spawned - self.total_picked_up - self.total_expired
            )
        
        return stats
    
    def increment_spawned_sync(self, count: int = 1):
        """Synchronous version of increment_spawned (not thread-safe)"""
        self.total_spawned += count
    
    def increment_picked_up_sync(self, count: int = 1):
        """Synchronous version of increment_picked_up (not thread-safe)"""
        self.total_picked_up += count
    
    def increment_expired_sync(self, count: int = 1):
        """Synchronous version of increment_expired (not thread-safe)"""
        self.total_expired += count
