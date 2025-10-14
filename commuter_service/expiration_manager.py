"""
Expiration Manager - Background Commuter Expiration

This module manages automatic expiration of commuters who have waited too long.
Extracted from DepotReservoir and RouteReservoir to follow DRY principle.

Responsibilities:
- Background task to check for expired commuters
- Configurable check intervals and timeouts
- Callback-based expiration handling
- Graceful start/stop lifecycle

Used by:
- DepotReservoir
- RouteReservoir
"""

import asyncio
import logging
from typing import Callable, Awaitable, Optional, List, Any
from datetime import datetime, timedelta


class ExpirationManager:
    """
    Manages background task for expiring old commuters.
    
    Periodically checks a collection of commuters and calls a callback
    for each one that has exceeded the expiration timeout.
    
    Example:
        async def handle_expiration(commuter):
            # Remove commuter, update stats, emit event
            print(f"Commuter {commuter.person_id} expired!")
        
        manager = ExpirationManager(
            check_interval=30.0,      # Check every 30 seconds
            expiration_timeout=300.0,  # Expire after 5 minutes
            on_expire_callback=handle_expiration
        )
        
        await manager.start()
        # ... manager runs in background ...
        await manager.stop()
    """
    
    def __init__(
        self,
        check_interval: float = 10.0,
        expiration_timeout: float = 1800.0,  # 30 minutes default
        on_expire_callback: Optional[Callable[[Any], Awaitable[None]]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize expiration manager.
        
        Args:
            check_interval: How often to check for expirations (seconds)
            expiration_timeout: How long before commuters expire (seconds)
            on_expire_callback: Async function called for each expired commuter
            logger: Logger instance (optional)
        """
        self.check_interval = check_interval
        self.expiration_timeout = timedelta(seconds=expiration_timeout)
        self.on_expire_callback = on_expire_callback
        self.logger = logger or logging.getLogger(__name__)
        
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """
        Start the expiration background task.
        
        Raises:
            RuntimeError: If already running
        """
        if self.running:
            raise RuntimeError("ExpirationManager is already running")
        
        self.running = True
        self.task = asyncio.create_task(self._expiration_loop())
        self.logger.info(
            f"ExpirationManager started: "
            f"check_interval={self.check_interval}s, "
            f"timeout={self.expiration_timeout.total_seconds()}s"
        )
    
    async def stop(self):
        """
        Stop the expiration background task gracefully.
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
        
        self.logger.info("ExpirationManager stopped")
    
    def is_running(self) -> bool:
        """Check if expiration manager is currently running"""
        return self.running
    
    async def check_and_expire(
        self,
        commuters: dict,
        get_spawn_time: Optional[Callable[[Any], datetime]] = None
    ) -> List[str]:
        """
        Check commuters and expire old ones (single check, not a loop).
        
        Args:
            commuters: Dictionary of {commuter_id: commuter}
            get_spawn_time: Function to get spawn time from commuter
                          (defaults to commuter.spawn_time attribute)
        
        Returns:
            List of expired commuter IDs
        """
        now = datetime.now()
        expired_ids = []
        
        for commuter_id, commuter in commuters.items():
            # Get spawn time
            if get_spawn_time:
                spawn_time = get_spawn_time(commuter)
            else:
                spawn_time = getattr(commuter, 'spawn_time', None)
            
            if spawn_time is None:
                self.logger.warning(f"Commuter {commuter_id} has no spawn_time")
                continue
            
            # Check if expired
            age = now - spawn_time
            if age > self.expiration_timeout:
                expired_ids.append(commuter_id)
                
                # Call expiration callback if provided
                if self.on_expire_callback:
                    try:
                        await self.on_expire_callback(commuter)
                    except Exception as e:
                        self.logger.error(
                            f"Error in expiration callback for {commuter_id}: {e}"
                        )
        
        return expired_ids
    
    async def _expiration_loop(self):
        """
        Background task that periodically checks for expirations.
        
        Note: This requires the on_expire_callback to handle the actual
        expiration logic (remove from collections, update stats, etc.)
        """
        while self.running:
            try:
                await asyncio.sleep(self.check_interval)
                
                # Note: Subclasses or users should override this or use
                # check_and_expire() directly with their commuter collection
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in expiration loop: {e}")
        
        self.logger.debug("Expiration loop exited")
    
    def update_timeout(self, new_timeout: float):
        """
        Update expiration timeout (in seconds).
        
        Args:
            new_timeout: New timeout in seconds
        """
        self.expiration_timeout = timedelta(seconds=new_timeout)
        self.logger.info(f"Expiration timeout updated to {new_timeout}s")
    
    def update_check_interval(self, new_interval: float):
        """
        Update check interval (in seconds).
        
        Args:
            new_interval: New check interval in seconds
        """
        self.check_interval = new_interval
        self.logger.info(f"Check interval updated to {new_interval}s")


class ReservoirExpirationManager(ExpirationManager):
    """
    Specialized expiration manager for reservoirs with commuter collections.
    
    This extends ExpirationManager to work directly with reservoir
    commuter dictionaries.
    
    Example:
        async def on_expire(commuter_id, commuter):
            # Handle expiration
            await remove_commuter(commuter_id)
            stats.increment_expired()
        
        manager = ReservoirExpirationManager(
            get_commuters=lambda: reservoir.active_commuters,
            on_expire=on_expire
        )
        
        await manager.start()
    """
    
    def __init__(
        self,
        get_commuters: Callable[[], dict],
        on_expire: Callable[[str, Any], Awaitable[None]],
        check_interval: float = 10.0,
        expiration_timeout: float = 1800.0,
        get_spawn_time: Optional[Callable[[Any], datetime]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize reservoir expiration manager.
        
        Args:
            get_commuters: Function that returns {commuter_id: commuter} dict
            on_expire: Async function called with (commuter_id, commuter) for each expiration
            check_interval: How often to check (seconds)
            expiration_timeout: How long before expiration (seconds)
            get_spawn_time: Function to extract spawn time from commuter
            logger: Logger instance
        """
        # Use a wrapper callback that calls on_expire with commuter_id
        async def callback_wrapper(commuter):
            # Find commuter_id by searching the dict
            commuters = get_commuters()
            commuter_id = None
            for cid, c in commuters.items():
                if c is commuter:
                    commuter_id = cid
                    break
            
            if commuter_id:
                await on_expire(commuter_id, commuter)
        
        super().__init__(
            check_interval=check_interval,
            expiration_timeout=expiration_timeout,
            on_expire_callback=callback_wrapper,
            logger=logger
        )
        
        self.get_commuters = get_commuters
        self.get_spawn_time_func = get_spawn_time
    
    async def _expiration_loop(self):
        """Background task that checks commuters and expires old ones"""
        while self.running:
            try:
                await asyncio.sleep(self.check_interval)
                
                commuters = self.get_commuters()
                expired_ids = await self.check_and_expire(
                    commuters,
                    get_spawn_time=self.get_spawn_time_func
                )
                
                if expired_ids:
                    self.logger.info(f"Expired {len(expired_ids)} commuters")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in expiration loop: {e}")
