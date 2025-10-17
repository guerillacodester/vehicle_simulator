"""
Spawning Coordinator - Automatic Passenger Spawning

This module manages automatic background passenger spawning using Poisson distribution.
Extracted from DepotReservoir and RouteReservoir to follow DRY principle.

Responsibilities:
- Background task for periodic spawning
- Integration with PoissonGeoJSONSpawner
- Configurable spawn intervals
- Callback-based spawn handling
- Graceful start/stop lifecycle

Used by:
- DepotReservoir
- RouteReservoir
"""

import asyncio
import logging
from typing import Callable, Awaitable, Optional, List, Dict, Any
from datetime import datetime


class SpawningCoordinator:
    """
    Manages background task for automatic passenger spawning.
    
    Coordinates with PoissonGeoJSONSpawner to generate spawn requests
    and delegates actual spawning to a callback function.
    
    Example:
        async def handle_spawn(spawn_request):
            # Process spawn request
            await reservoir.spawn_commuter(
                depot_id=spawn_request['depot_id'],
                route_id=spawn_request['route_id'],
                destination=spawn_request['destination']
            )
        
        coordinator = SpawningCoordinator(
            spawner=poisson_spawner,
            spawn_interval=30.0,      # Every 30 seconds
            on_spawn_callback=handle_spawn
        )
        
        await coordinator.start()
        # ... coordinator runs in background ...
        await coordinator.stop()
    """
    
    def __init__(
        self,
        spawner: Any,  # PoissonGeoJSONSpawner instance
        spawn_interval: float = 30.0,
        time_window_minutes: float = 5.0,
        on_spawn_callback: Optional[Callable[[Dict], Awaitable[None]]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize spawning coordinator.
        
        Args:
            spawner: PoissonGeoJSONSpawner instance for generating spawn requests
            spawn_interval: How often to generate spawns (seconds)
            time_window_minutes: Time window for Poisson calculations
            on_spawn_callback: Async function called for each spawn request
            logger: Logger instance (optional)
        """
        self.spawner = spawner
        self.spawn_interval = spawn_interval
        self.time_window_minutes = time_window_minutes
        self.on_spawn_callback = on_spawn_callback
        self.logger = logger or logging.getLogger(__name__)
        
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.total_spawned = 0
        self.total_failed = 0
    
    async def start(self):
        """
        Start the spawning background task.
        
        Raises:
            RuntimeError: If already running
        """
        if self.running:
            raise RuntimeError("SpawningCoordinator is already running")
        
        self.running = True
        self.task = asyncio.create_task(self._spawning_loop())
        self.logger.info(
            f"🚀 SpawningCoordinator started: "
            f"interval={self.spawn_interval}s, "
            f"window={self.time_window_minutes}min"
        )
    
    async def stop(self):
        """
        Stop the spawning background task gracefully.
        """
        if not self.running:
            return
        
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        self.logger.info(
            f"SpawningCoordinator stopped: "
            f"{self.total_spawned} spawned, {self.total_failed} failed"
        )
    
    def is_running(self) -> bool:
        """Check if spawning coordinator is currently running"""
        return self.running
    
    async def generate_and_process_spawns(
        self,
        current_time: Optional[datetime] = None
    ) -> int:
        """
        Generate spawn requests and process them (single cycle).
        
        Args:
            current_time: Current time for spawn generation (defaults to now)
        
        Returns:
            Number of spawn requests generated
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            # Generate spawn requests from Poisson spawner
            spawn_requests = await self.spawner.generate_poisson_spawn_requests(
                current_time=current_time,
                time_window_minutes=self.time_window_minutes
            )
            
            self.logger.info(
                f"[SPAWN_GEN] Generated {len(spawn_requests)} spawn requests "
                f"for hour {current_time.hour}"
            )
            
            # Process each spawn request
            for request in spawn_requests:
                try:
                    if self.on_spawn_callback:
                        await self.on_spawn_callback(request)
                        self.total_spawned += 1
                except Exception as e:
                    self.total_failed += 1
                    self.logger.error(
                        f"Failed to process spawn request: {e}",
                        exc_info=True
                    )
            
            return len(spawn_requests)
            
        except Exception as e:
            self.logger.error(f"Error generating spawn requests: {e}")
            return 0
    
    async def _spawning_loop(self):
        """
        Background task that periodically generates spawn requests.
        """
        self.logger.info(
            "[SPAWNING_LOOP] Starting automatic passenger spawning loop "
            "(using GeoJSON population data)"
        )
        
        spawn_cycle_number = 0
        
        while self.running:
            try:
                spawn_cycle_number += 1
                self.logger.info(f"[SPAWNING_LOOP] Cycle {spawn_cycle_number}: Waiting {self.spawn_interval}s before next spawn...")
                
                # Wait before next spawn cycle
                await asyncio.sleep(self.spawn_interval)
                
                self.logger.info(f"[SPAWNING_LOOP] Cycle {spawn_cycle_number}: Generating spawns now...")
                
                # Generate and process spawns
                await self.generate_and_process_spawns()
                
                self.logger.info(f"[SPAWNING_LOOP] Cycle {spawn_cycle_number}: Completed")
                
            except asyncio.CancelledError:
                self.logger.info("[SPAWNING_LOOP] Loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"[SPAWNING_LOOP] Error in spawning loop: {e}", exc_info=True)
        
        self.logger.info("[SPAWNING_LOOP] Loop exited")
    
    def update_spawn_interval(self, new_interval: float):
        """
        Update spawn interval (in seconds).
        
        Args:
            new_interval: New spawn interval in seconds
        """
        self.spawn_interval = new_interval
        self.logger.info(f"Spawn interval updated to {new_interval}s")
    
    def update_time_window(self, new_window: float):
        """
        Update time window for Poisson calculations (in minutes).
        
        Args:
            new_window: New time window in minutes
        """
        self.time_window_minutes = new_window
        self.logger.info(f"Time window updated to {new_window}min")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get spawning statistics.
        
        Returns:
            Dictionary with spawning stats
        """
        return {
            "running": self.running,
            "spawn_interval": self.spawn_interval,
            "time_window_minutes": self.time_window_minutes,
            "total_spawned": self.total_spawned,
            "total_failed": self.total_failed,
            "success_rate": (
                self.total_spawned / (self.total_spawned + self.total_failed)
                if (self.total_spawned + self.total_failed) > 0
                else 0.0
            )
        }
    
    def reset_stats(self):
        """Reset spawning statistics"""
        self.total_spawned = 0
        self.total_failed = 0
