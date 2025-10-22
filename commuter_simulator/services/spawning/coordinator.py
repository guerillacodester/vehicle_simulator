"""
Spawning Coordinator - Automatic Passenger Generation

Manages background task for automatic passenger spawning using the plugin system.
Coordinates spawn generation, processing, and delivery to reservoirs.

Ported from commuter_service/spawning_coordinator.py with plugin system integration.
"""

import asyncio
import logging
from typing import Callable, Awaitable, Optional, List, Dict, Any
from datetime import datetime

from commuter_simulator.core.domain.spawning_plugin import PluginRegistry, SpawnContext, SpawnRequest


class SpawningCoordinator:
    """
    Manages background task for automatic passenger spawning using plugins.
    
    Coordinates with PluginRegistry to generate spawn requests from multiple
    sources (statistical models, historical data, etc.) and delegates actual
    spawning to callback functions.
    
    Example:
        # Setup plugin registry
        registry = PluginRegistry(api_client)
        registry.register_plugin(poisson_plugin)
        await registry.initialize_all()
        
        # Define spawn callback
        async def handle_spawn(spawn_request: SpawnRequest):
            # Process spawn request
            await reservoir.spawn_commuter(
                location=spawn_request.spawn_location,
                destination=spawn_request.destination_location,
                route_id=spawn_request.route_id
            )
        
        # Create and start coordinator
        coordinator = SpawningCoordinator(
            plugin_registry=registry,
            spawn_interval=30.0,
            on_spawn_callback=handle_spawn
        )
        
        await coordinator.start()
        # Coordinator runs in background
        await coordinator.stop()
    """
    
    def __init__(
        self,
        plugin_registry: PluginRegistry,
        spawn_interval: float = 30.0,
        time_window_minutes: int = 5,
        spawn_context: SpawnContext = SpawnContext.DEPOT,
        on_spawn_callback: Optional[Callable[[SpawnRequest], Awaitable[None]]] = None,
        on_batch_callback: Optional[Callable[[List[SpawnRequest]], Awaitable[None]]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize spawning coordinator.
        
        Args:
            plugin_registry: PluginRegistry with initialized plugins
            spawn_interval: How often to generate spawns (seconds)
            time_window_minutes: Time window for spawn generation
            spawn_context: Default spawn context (DEPOT, ROUTE, ZONE)
            on_spawn_callback: Async function called for each spawn request
            on_batch_callback: Async function called with batch of spawn requests
            logger: Logger instance (optional)
        """
        self.plugin_registry = plugin_registry
        self.spawn_interval = spawn_interval
        self.time_window_minutes = time_window_minutes
        self.spawn_context = spawn_context
        self.on_spawn_callback = on_spawn_callback
        self.on_batch_callback = on_batch_callback
        self.logger = logger or logging.getLogger(__name__)
        
        # State tracking
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.total_spawned = 0
        self.total_failed = 0
        self.last_spawn_time: Optional[datetime] = None
        
        # Performance metrics
        self.spawn_cycles = 0
        self.average_spawns_per_cycle = 0.0
    
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
            f"window={self.time_window_minutes}min, "
            f"context={self.spawn_context.value}"
        )
    
    async def stop(self):
        """Stop the spawning background task gracefully."""
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
            f"✅ SpawningCoordinator stopped: "
            f"{self.total_spawned} spawned, {self.total_failed} failed, "
            f"{self.spawn_cycles} cycles, "
            f"avg {self.average_spawns_per_cycle:.1f} per cycle"
        )
    
    def is_running(self) -> bool:
        """Check if spawning coordinator is currently running"""
        return self.running
    
    async def generate_and_process_spawns(
        self,
        current_time: Optional[datetime] = None,
        context: Optional[SpawnContext] = None,
        **kwargs
    ) -> int:
        """
        Generate spawn requests and process them (single cycle).
        
        Args:
            current_time: Current time for spawn generation (defaults to now)
            context: Spawn context override (uses default if None)
            **kwargs: Additional context-specific parameters
        
        Returns:
            Number of spawn requests generated and processed
        """
        if current_time is None:
            current_time = datetime.now()
        
        if context is None:
            context = self.spawn_context
        
        try:
            # Generate spawn requests from all active plugins
            spawn_requests = await self.plugin_registry.generate_spawns(
                current_time=current_time,
                time_window_minutes=self.time_window_minutes,
                context=context,
                **kwargs
            )
            
            if not spawn_requests:
                self.logger.debug(f"No spawn requests generated for cycle at {current_time.isoformat()}")
                return 0
            
            self.logger.info(
                f"[SPAWN_GEN] Generated {len(spawn_requests)} spawn requests "
                f"for hour {current_time.hour}, context={context.value}"
            )
            
            # Process spawn requests
            processed_count = 0
            failed_count = 0
            
            # Batch callback (if provided)
            if self.on_batch_callback:
                try:
                    await self.on_batch_callback(spawn_requests)
                    processed_count = len(spawn_requests)
                except Exception as e:
                    self.logger.error(f"Batch callback failed: {e}")
                    failed_count = len(spawn_requests)
            
            # Individual callbacks (if provided and no batch callback)
            elif self.on_spawn_callback:
                for spawn_request in spawn_requests:
                    try:
                        await self.on_spawn_callback(spawn_request)
                        processed_count += 1
                    except Exception as e:
                        self.logger.error(
                            f"Failed to process spawn request {spawn_request.passenger_id}: {e}"
                        )
                        failed_count += 1
            else:
                # No callbacks - just count as processed
                processed_count = len(spawn_requests)
                self.logger.warning("No spawn callbacks configured - requests not processed")
            
            # Update statistics
            self.total_spawned += processed_count
            self.total_failed += failed_count
            self.last_spawn_time = current_time
            self.spawn_cycles += 1
            self.average_spawns_per_cycle = self.total_spawned / self.spawn_cycles
            
            if processed_count > 0:
                self.logger.info(
                    f"✅ Processed {processed_count} spawns, {failed_count} failed"
                )
            
            return processed_count
        
        except Exception as e:
            self.logger.error(f"Error in spawn generation cycle: {e}", exc_info=True)
            return 0
    
    async def _spawning_loop(self):
        """
        Main spawning loop - runs in background task.
        
        Generates spawns at configured intervals until stopped.
        """
        self.logger.info("Spawning loop started")
        
        try:
            while self.running:
                cycle_start_time = datetime.now()
                
                # Generate and process spawns
                await self.generate_and_process_spawns(current_time=cycle_start_time)
                
                # Wait for next cycle
                await asyncio.sleep(self.spawn_interval)
        
        except asyncio.CancelledError:
            self.logger.info("Spawning loop cancelled")
        except Exception as e:
            self.logger.error(f"Spawning loop error: {e}", exc_info=True)
        finally:
            self.running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get spawning coordinator statistics"""
        return {
            'running': self.running,
            'total_spawned': self.total_spawned,
            'total_failed': self.total_failed,
            'spawn_cycles': self.spawn_cycles,
            'average_spawns_per_cycle': self.average_spawns_per_cycle,
            'last_spawn_time': self.last_spawn_time.isoformat() if self.last_spawn_time else None,
            'spawn_interval': self.spawn_interval,
            'time_window_minutes': self.time_window_minutes,
            'spawn_context': self.spawn_context.value,
            'plugin_stats': self.plugin_registry.get_stats()
        }
    
    def set_spawn_interval(self, interval: float):
        """Update spawn interval (takes effect next cycle)"""
        old_interval = self.spawn_interval
        self.spawn_interval = interval
        self.logger.info(f"Spawn interval updated: {old_interval}s → {interval}s")
    
    def set_spawn_context(self, context: SpawnContext):
        """Update spawn context (takes effect next cycle)"""
        old_context = self.spawn_context
        self.spawn_context = context
        self.logger.info(f"Spawn context updated: {old_context.value} → {context.value}")
    
    async def trigger_immediate_spawn(
        self,
        context: Optional[SpawnContext] = None,
        **kwargs
    ) -> int:
        """
        Trigger an immediate spawn cycle (outside of regular interval).
        
        Useful for testing or manual spawn generation.
        
        Returns:
            Number of spawns generated
        """
        self.logger.info("⚡ Triggering immediate spawn cycle")
        return await self.generate_and_process_spawns(
            current_time=datetime.now(),
            context=context,
            **kwargs
        )


class MultiContextCoordinator:
    """
    Manages multiple spawning coordinators for different contexts.
    
    Allows simultaneous spawning at depots, along routes, and in zones
    with different configurations for each context.
    
    Example:
        coordinator = MultiContextCoordinator(plugin_registry)
        
        # Configure depot spawning
        coordinator.add_context(
            SpawnContext.DEPOT,
            spawn_interval=60.0,
            callback=handle_depot_spawn
        )
        
        # Configure route spawning
        coordinator.add_context(
            SpawnContext.ROUTE,
            spawn_interval=120.0,
            callback=handle_route_spawn
        )
        
        await coordinator.start_all()
    """
    
    def __init__(self, plugin_registry: PluginRegistry, logger: Optional[logging.Logger] = None):
        self.plugin_registry = plugin_registry
        self.logger = logger or logging.getLogger(__name__)
        self.coordinators: Dict[SpawnContext, SpawningCoordinator] = {}
    
    def add_context(
        self,
        context: SpawnContext,
        spawn_interval: float = 30.0,
        time_window_minutes: int = 5,
        callback: Optional[Callable[[SpawnRequest], Awaitable[None]]] = None,
        batch_callback: Optional[Callable[[List[SpawnRequest]], Awaitable[None]]] = None
    ):
        """Add a spawning coordinator for a specific context"""
        if context in self.coordinators:
            self.logger.warning(f"Context {context.value} already exists, replacing")
        
        coordinator = SpawningCoordinator(
            plugin_registry=self.plugin_registry,
            spawn_interval=spawn_interval,
            time_window_minutes=time_window_minutes,
            spawn_context=context,
            on_spawn_callback=callback,
            on_batch_callback=batch_callback,
            logger=self.logger
        )
        
        self.coordinators[context] = coordinator
        self.logger.info(f"Added coordinator for context: {context.value}")
    
    def remove_context(self, context: SpawnContext):
        """Remove a spawning coordinator"""
        if context in self.coordinators:
            del self.coordinators[context]
            self.logger.info(f"Removed coordinator for context: {context.value}")
    
    async def start_all(self):
        """Start all coordinators"""
        self.logger.info(f"Starting {len(self.coordinators)} coordinators...")
        
        for context, coordinator in self.coordinators.items():
            try:
                await coordinator.start()
            except Exception as e:
                self.logger.error(f"Failed to start coordinator for {context.value}: {e}")
    
    async def stop_all(self):
        """Stop all coordinators"""
        self.logger.info(f"Stopping {len(self.coordinators)} coordinators...")
        
        for context, coordinator in self.coordinators.items():
            try:
                await coordinator.stop()
            except Exception as e:
                self.logger.error(f"Failed to stop coordinator for {context.value}: {e}")
    
    async def start_context(self, context: SpawnContext):
        """Start a specific coordinator"""
        if context in self.coordinators:
            await self.coordinators[context].start()
    
    async def stop_context(self, context: SpawnContext):
        """Stop a specific coordinator"""
        if context in self.coordinators:
            await self.coordinators[context].stop()
    
    def get_coordinator(self, context: SpawnContext) -> Optional[SpawningCoordinator]:
        """Get coordinator for a specific context"""
        return self.coordinators.get(context)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all coordinators"""
        return {
            'total_coordinators': len(self.coordinators),
            'contexts': {
                context.value: coordinator.get_stats()
                for context, coordinator in self.coordinators.items()
            }
        }
