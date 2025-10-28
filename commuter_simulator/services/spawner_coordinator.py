"""
Spawner Coordinator - Orchestrates multiple spawners with individual enable/disable control.

Responsibilities:
1. Manages collection of spawner instances (RouteSpawner, DepotSpawner, etc.)
2. Respects enable/disable flags for each spawner type
3. Runs enabled spawners concurrently using asyncio.gather
4. Provides unified logging and error handling
5. Tracks aggregate statistics across all spawners

Does NOT:
- Create spawner instances (that's the entrypoint's job)
- Manage reservoirs (spawners own their reservoirs)
- Handle persistence (that's the reservoir's job)
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from commuter_simulator.core.domain.spawner_engine import SpawnerInterface


class SpawnerCoordinator:
    """
    Orchestrates multiple spawners with individual enable/disable control.
    
    Example usage:
        coordinator = SpawnerCoordinator(
            spawners=[route_spawner, depot_spawner],
            config={'enable_routespawner': True, 'enable_depotspawner': False}
        )
        await coordinator.start()
    """
    
    def __init__(self, spawners: List[SpawnerInterface], config: Dict[str, Any]):
        """
        Initialize coordinator with spawners and configuration.
        
        Args:
            spawners: List of spawner instances (RouteSpawner, DepotSpawner, etc.)
            config: Configuration dict with enable flags:
                - enable_routespawner: bool (default True)
                - enable_depotspawner: bool (default True)
                - spawn_interval_seconds: int (default 60)
                - continuous_mode: bool (default False - run once then exit)
        """
        self.spawners = spawners
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._running = False
    
    async def start(self, current_time: datetime = None, time_window_minutes: int = 60):
        """
        Start spawning process (single iteration or continuous loop).
        
        Args:
            current_time: Simulation time (default: datetime.utcnow())
            time_window_minutes: Time window for spawning (default: 60)
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Filter enabled spawners
        enabled_spawners = self._get_enabled_spawners()
        
        if not enabled_spawners:
            self.logger.warning("⚠️  No spawners enabled! Check configuration.")
            return
        
        # Check if continuous mode
        continuous_mode = self.config.get('continuous_mode', False)
        spawn_interval = self.config.get('spawn_interval_seconds', 60)
        
        if continuous_mode:
            self.logger.info(f"🔄 Starting continuous spawning (interval: {spawn_interval}s)...")
            await self._run_continuous(enabled_spawners, time_window_minutes, spawn_interval)
        else:
            self.logger.info(f"▶️  Running single spawn cycle...")
            await self._run_single_cycle(enabled_spawners, current_time, time_window_minutes)
    
    def _get_enabled_spawners(self) -> List[SpawnerInterface]:
        """Filter spawners based on enable flags in config"""
        enabled = []
        
        for spawner in self.spawners:
            spawner_name = spawner.__class__.__name__
            enable_key = f'enable_{spawner_name.lower()}'
            is_enabled = self.config.get(enable_key, True)  # Default: enabled
            
            if is_enabled:
                enabled.append(spawner)
                self.logger.info(f"✅ {spawner_name} ENABLED")
            else:
                self.logger.info(f"⏭️  {spawner_name} DISABLED (skipping)")
        
        return enabled
    
    async def _run_single_cycle(
        self, 
        enabled_spawners: List[SpawnerInterface],
        current_time: datetime,
        time_window_minutes: int
    ):
        """Run a single spawn cycle for all enabled spawners"""
        self.logger.info(
            f"🚀 Starting spawn cycle for {len(enabled_spawners)} spawner(s) "
            f"at {current_time.strftime('%H:%M:%S')}"
        )
        
        try:
            # Run all enabled spawners concurrently
            tasks = [
                spawner.spawn_and_store(
                    current_time=current_time,
                    time_window_minutes=time_window_minutes
                )
                for spawner in enabled_spawners
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            total_spawned = 0
            errors = 0
            
            for i, result in enumerate(results):
                spawner_name = enabled_spawners[i].__class__.__name__
                
                if isinstance(result, Exception):
                    self.logger.error(f"❌ {spawner_name} failed: {result}")
                    errors += 1
                else:
                    self.logger.info(f"✅ {spawner_name} spawned {result} passengers")
                    total_spawned += result
            
            self.logger.info(
                f"📊 Spawn cycle complete: {total_spawned} total passengers, {errors} errors"
            )
            
            # Print aggregate stats
            await self._log_aggregate_stats()
            
        except Exception as e:
            self.logger.error(f"❌ Error in spawn cycle: {e}", exc_info=True)
    
    async def _run_continuous(
        self,
        enabled_spawners: List[SpawnerInterface],
        time_window_minutes: int,
        interval_seconds: int
    ):
        """Run spawning continuously with interval"""
        self._running = True
        
        try:
            while self._running:
                current_time = datetime.utcnow()
                await self._run_single_cycle(enabled_spawners, current_time, time_window_minutes)
                
                self.logger.info(f"⏱️  Sleeping for {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️  Received shutdown signal")
            self._running = False
        except Exception as e:
            self.logger.error(f"❌ Error in continuous loop: {e}", exc_info=True)
            self._running = False
    
    async def _log_aggregate_stats(self):
        """Log aggregate statistics across all spawners"""
        total_spawned = 0
        total_errors = 0
        
        for spawner in self.spawners:
            stats = spawner.get_stats()
            total_spawned += stats.get('total_spawned', 0)
            total_errors += stats.get('total_errors', 0)
        
        success_rate = (
            total_spawned / (total_spawned + total_errors) * 100
            if (total_spawned + total_errors) > 0 else 0.0
        )
        
        self.logger.info(
            f"📈 Aggregate Stats: {total_spawned} spawned, "
            f"{total_errors} errors, {success_rate:.1f}% success rate"
        )
    
    def stop(self):
        """Stop continuous spawning"""
        self.logger.info("🛑 Stopping spawner coordinator...")
        self._running = False
