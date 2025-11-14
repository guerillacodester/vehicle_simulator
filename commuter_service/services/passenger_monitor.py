"""
Passenger State Monitor

Real-time monitoring of passenger state changes.

Detects changes made by external processes (vehicles, mobile apps, etc.)
and broadcasts events to WebSocket clients.

Monitoring Strategy:
1. Poll Strapi API for changes (efficient with updatedAt filter)
2. Compare states with in-memory cache
3. Detect state transitions
4. Broadcast events to subscribed clients

Production considerations:
- Configurable poll interval (default: 2 seconds)
- Efficient queries using updatedAt timestamps
- Memory-efficient caching (only track active passengers)
- Automatic cleanup of completed passengers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from dataclasses import dataclass, field

import httpx

from commuter_service.domain.models.passenger_state import (
    PassengerStatus,
    calculate_passenger_state,
    PassengerStateChange
)


logger = logging.getLogger(__name__)


@dataclass
class PassengerSnapshot:
    """Cached snapshot of passenger state"""
    passenger_id: str
    document_id: str
    status: PassengerStatus
    spawned_at: Optional[datetime]
    boarded_at: Optional[datetime]
    alighted_at: Optional[datetime]
    vehicle_id: Optional[str]
    route_id: Optional[str]
    updated_at: datetime
    last_checked: datetime = field(default_factory=datetime.utcnow)


class PassengerMonitor:
    """
    Real-time passenger state monitor.
    
    Detects external changes to passenger states and broadcasts events.
    """
    
    def __init__(
        self,
        strapi_url: str,
        poll_interval: float = 2.0,
        cleanup_after_hours: int = 24
    ):
        """
        Initialize passenger monitor.
        
        Args:
            strapi_url: Strapi API base URL
            poll_interval: Seconds between polls (default: 2.0)
            cleanup_after_hours: Remove alighted passengers after N hours (default: 24)
        """
        self.strapi_url = strapi_url.rstrip("/")
        self.poll_interval = poll_interval
        self.cleanup_after_hours = cleanup_after_hours
        
        # In-memory cache of passenger states
        self.passenger_cache: Dict[str, PassengerSnapshot] = {}
        
        # Track which routes clients are monitoring
        self.monitored_routes: Set[str] = set()
        
        # Monitoring state
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'total_changes_detected': 0,
            'state_transitions': 0,
            'external_updates': 0,
            'last_poll': None,
            'cached_passengers': 0
        }
        
        logger.info(f"🔍 PassengerMonitor initialized (poll={poll_interval}s)")
    
    async def start(self):
        """Start the monitoring service"""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("🚀 PassengerMonitor started")
    
    async def stop(self):
        """Stop the monitoring service"""
        if not self.running:
            return
        
        self.running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️  PassengerMonitor stopped")
    
    def add_monitored_route(self, route_id: str):
        """Add a route to monitor (when clients subscribe)"""
        self.monitored_routes.add(route_id)
        logger.info(f"📡 Monitoring route: {route_id} (total: {len(self.monitored_routes)})")
    
    def remove_monitored_route(self, route_id: str):
        """Remove a route from monitoring"""
        self.monitored_routes.discard(route_id)
        logger.info(f"🔕 Stopped monitoring route: {route_id}")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("🔄 Monitor loop started")
        
        while self.running:
            try:
                await self._check_for_changes()
                self.stats['last_poll'] = datetime.utcnow()
                
                # Cleanup old passengers
                await self._cleanup_old_passengers()
                
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"❌ Monitor loop error: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
    
    async def _check_for_changes(self):
        """Check for passenger state changes"""
        if not self.monitored_routes:
            return  # No routes being monitored, skip
        
        # Calculate cutoff time (only check recently updated)
        cutoff = datetime.utcnow() - timedelta(seconds=self.poll_interval * 3)
        
        # Query passengers updated since last check
        async with httpx.AsyncClient(timeout=10.0) as client:
            for route_id in self.monitored_routes:
                try:
                    params = {
                        "filters[route_id][$eq]": route_id,
                        "filters[updatedAt][$gte]": cutoff.isoformat() + "Z",
                        "pagination[pageSize]": 100
                    }
                    
                    response = await client.get(
                        f"{self.strapi_url}/api/active-passengers",
                        params=params
                    )
                    response.raise_for_status()
                    
                    passengers = response.json().get("data", [])
                    
                    # Check each passenger for changes
                    for p in passengers:
                        await self._process_passenger_update(p)
                
                except Exception as e:
                    logger.error(f"Error checking route {route_id}: {e}")
    
    async def _process_passenger_update(self, passenger_data: dict):
        """Process a single passenger update and detect changes"""
        passenger_id = passenger_data.get("passenger_id")
        document_id = passenger_data.get("documentId")
        
        # Calculate current state from timestamps
        current_state = calculate_passenger_state(
            spawned_at=passenger_data.get("spawned_at"),
            boarded_at=passenger_data.get("boarded_at"),
            alighted_at=passenger_data.get("alighted_at"),
            status=passenger_data.get("status")
        )
        
        # Get cached snapshot
        cached = self.passenger_cache.get(passenger_id)
        
        if not cached:
            # New passenger - add to cache
            self.passenger_cache[passenger_id] = PassengerSnapshot(
                passenger_id=passenger_id,
                document_id=document_id,
                status=current_state,
                spawned_at=passenger_data.get("spawned_at"),
                boarded_at=passenger_data.get("boarded_at"),
                alighted_at=passenger_data.get("alighted_at"),
                vehicle_id=passenger_data.get("vehicle_id"),
                route_id=passenger_data.get("route_id"),
                updated_at=datetime.fromisoformat(passenger_data.get("updatedAt").replace("Z", "+00:00"))
            )
            logger.debug(f"📝 Cached new passenger: {passenger_id} ({current_state})")
            return
        
        # Check for state change
        if cached.status != current_state:
            # STATE TRANSITION DETECTED!
            self.stats['state_transitions'] += 1
            
            logger.info(
                f"🔄 State change detected: {passenger_id} "
                f"{cached.status} → {current_state}"
            )
            
            # Emit state change event
            await self._emit_state_change(
                passenger_id=passenger_id,
                previous_state=cached.status,
                new_state=current_state,
                passenger_data=passenger_data
            )
        
        # Check for field changes (external updates)
        changed_fields = []
        
        if cached.boarded_at != passenger_data.get("boarded_at"):
            changed_fields.append("boarded_at")
        if cached.alighted_at != passenger_data.get("alighted_at"):
            changed_fields.append("alighted_at")
        if cached.vehicle_id != passenger_data.get("vehicle_id"):
            changed_fields.append("vehicle_id")
        
        if changed_fields:
            self.stats['external_updates'] += 1
            logger.info(
                f"📝 External update detected: {passenger_id} "
                f"fields={changed_fields}"
            )
        
        # Update cache
        cached.status = current_state
        cached.boarded_at = passenger_data.get("boarded_at")
        cached.alighted_at = passenger_data.get("alighted_at")
        cached.vehicle_id = passenger_data.get("vehicle_id")
        cached.updated_at = datetime.fromisoformat(passenger_data.get("updatedAt").replace("Z", "+00:00"))
        cached.last_checked = datetime.utcnow()
        
        self.stats['total_changes_detected'] += 1
    
    async def _emit_state_change(
        self,
        passenger_id: str,
        previous_state: PassengerStatus,
        new_state: PassengerStatus,
        passenger_data: dict
    ):
        """Emit state change event to WebSocket clients"""
        try:
            # Import dynamically to avoid circular imports
            from commuter_service.interfaces.http.commuter_manifest import emit_passenger_event
            
            # Map state to event type
            event_type_map = {
                PassengerStatus.BOARDED: "boarded",
                PassengerStatus.ALIGHTED: "alighted",
                PassengerStatus.CANCELLED: "cancelled"
            }
            
            event_type = event_type_map.get(new_state, "state_changed")
            
            event_data = {
                "passenger_id": passenger_id,
                "route_id": passenger_data.get("route_id"),
                "previous_state": previous_state.value,
                "new_state": new_state.value,
                "vehicle_id": passenger_data.get("vehicle_id"),
                "latitude": passenger_data.get("latitude"),
                "longitude": passenger_data.get("longitude"),
                "external_trigger": True  # Changed by external process
            }
            
            if new_state == PassengerStatus.BOARDED:
                event_data["boarded_at"] = passenger_data.get("boarded_at")
            elif new_state == PassengerStatus.ALIGHTED:
                event_data["alighted_at"] = passenger_data.get("alighted_at")
            
            # Broadcast event
            await emit_passenger_event(
                event_type,
                event_data,
                route_id=passenger_data.get("route_id")
            )
            
        except Exception as e:
            logger.error(f"Failed to emit state change event: {e}")
    
    async def _cleanup_old_passengers(self):
        """Remove alighted passengers from cache after configured time"""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=self.cleanup_after_hours)
        
        to_remove = []
        
        for passenger_id, snapshot in self.passenger_cache.items():
            # Remove if alighted and old
            if (snapshot.status == PassengerStatus.ALIGHTED and
                snapshot.alighted_at and
                snapshot.alighted_at < cutoff):
                to_remove.append(passenger_id)
        
        for passenger_id in to_remove:
            del self.passenger_cache[passenger_id]
        
        if to_remove:
            logger.info(f"🗑️  Cleaned up {len(to_remove)} old passengers")
        
        self.stats['cached_passengers'] = len(self.passenger_cache)
    
    def get_stats(self) -> dict:
        """Get monitoring statistics"""
        return {
            **self.stats,
            'monitored_routes': len(self.monitored_routes),
            'cached_passengers': len(self.passenger_cache),
            'running': self.running
        }


# Global monitor instance
_monitor: Optional[PassengerMonitor] = None


def get_monitor() -> PassengerMonitor:
    """Get or create the global passenger monitor"""
    global _monitor
    
    if _monitor is None:
        from commuter_service.infrastructure.config import get_config
        config = get_config()
        
        _monitor = PassengerMonitor(
            strapi_url=config.infrastructure.strapi_url,
            poll_interval=2.0  # 2 second polls
        )
    
    return _monitor
