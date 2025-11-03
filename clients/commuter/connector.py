"""
Commuter Service Client Connector
==================================

GUI-agnostic client for connecting to the Commuter Service API.
Supports both REST API and real-time Socket.IO/SSE streaming.

Features:
- REST API: Query manifest, stats, visualization data
- Socket.IO: Real-time passenger spawn/board/alight events
- SSE Streaming: HTTP streaming fallback
- Observable pattern: Subscribe to events with callbacks
- Auto-reconnection on disconnect
- Type-safe Pydantic models

Usage:
    from clients.commuter.connector import CommuterConnector
    
    connector = CommuterConnector(base_url="http://localhost:4000")
    
    # REST API
    manifest = await connector.get_manifest(route=1, day="monday")
    
    # Real-time streaming
    def on_passenger_spawned(data):
        print(f"Passenger spawned: {data}")
    
    connector.on('passenger:spawned', on_passenger_spawned)
    await connector.connect()
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from enum import Enum

import httpx
import socketio
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# EVENT TYPES
# ============================================================================

class EventType(str, Enum):
    """Passenger lifecycle events"""
    SPAWNED = "passenger:spawned"
    BOARDED = "passenger:boarded"
    ALIGHTED = "passenger:alighted"
    CANCELLED = "passenger:cancelled"


# ============================================================================
# MODELS
# ============================================================================

class PassengerEvent(BaseModel):
    """Passenger lifecycle event"""
    event_type: str
    passenger_id: str
    route_id: str
    timestamp: datetime
    location: Optional[Dict[str, float]] = None  # {lat, lon}
    metadata: Optional[Dict[str, Any]] = None


class ManifestQuery(BaseModel):
    """Manifest query parameters"""
    route: Optional[str] = None
    day: Optional[str] = None
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
    limit: int = 1000


class ManifestResponse(BaseModel):
    """Manifest API response"""
    count: int = Field(..., description="Number of passengers returned")
    route_id: Optional[str] = Field(None, description="Route filter applied")
    depot_id: Optional[str] = Field(None, description="Depot filter applied")
    passengers: List[Dict[str, Any]] = Field(..., description="Enriched passenger data")
    ordered_by_route_position: bool = Field(..., description="Whether sorted by route position")


# ============================================================================
# COMMUTER CONNECTOR
# ============================================================================

class CommuterConnector:
    """
    GUI-agnostic client for Commuter Service API.
    
    Supports:
    - REST API (HTTP/HTTPS)
    - Real-time events (Socket.IO)
    - Observable pattern (callbacks)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:4000",
        socketio_url: Optional[str] = None,
        auto_reconnect: bool = True
    ):
        """
        Initialize connector
        
        Args:
            base_url: Base URL for REST API (default: http://localhost:4000)
            socketio_url: Socket.IO server URL (default: None, will try to detect)
            auto_reconnect: Auto-reconnect on disconnect (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.socketio_url = socketio_url or self._detect_socketio_url()
        self.auto_reconnect = auto_reconnect
        
        # HTTP client
        self.http_client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        
        # Socket.IO client
        self.sio = socketio.AsyncClient(reconnection=auto_reconnect)
        self._setup_socketio_handlers()
        
        # Event handlers (Observable pattern)
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Connection state
        self.connected = False
        self.is_socketio_connected = False
        
        logger.info(f"CommuterConnector initialized | REST: {self.base_url} | Socket.IO: {self.socketio_url}")
    
    def _detect_socketio_url(self) -> Optional[str]:
        """Detect Socket.IO server URL from REST API"""
        # Socket.IO server not implemented yet
        # Will be added in TIER 4.10
        return None
    
    def _setup_socketio_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect():
            self.connected = True
            self.is_socketio_connected = True
            logger.info("✅ Connected to Socket.IO server")
            await self._trigger_event('connect', {})
        
        @self.sio.event
        async def disconnect():
            self.connected = False
            self.is_socketio_connected = False
            logger.warning("⚫ Disconnected from Socket.IO server")
            await self._trigger_event('disconnect', {})
        
        @self.sio.on('passenger:spawned')
        async def on_passenger_spawned(data):
            logger.debug(f"📨 passenger:spawned: {data}")
            await self._trigger_event(EventType.SPAWNED, data)
        
        @self.sio.on('passenger:boarded')
        async def on_passenger_boarded(data):
            logger.debug(f"📨 passenger:boarded: {data}")
            await self._trigger_event(EventType.BOARDED, data)
        
        @self.sio.on('passenger:alighted')
        async def on_passenger_alighted(data):
            logger.debug(f"📨 passenger:alighted: {data}")
            await self._trigger_event(EventType.ALIGHTED, data)
        
        @self.sio.on('*')
        async def catch_all(event, data):
            """Catch all other events"""
            if event not in ['connect', 'disconnect', 'passenger:spawned', 'passenger:boarded', 'passenger:alighted']:
                logger.debug(f"📨 {event}: {data}")
                await self._trigger_event(event, data)
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    async def connect(self):
        """Connect to Socket.IO server for real-time events"""
        if self.socketio_url is None:
            logger.info("Socket.IO URL not provided - real-time events disabled")
            return
        
        try:
            await self.sio.connect(self.socketio_url)
            logger.info(f"Connected to Socket.IO: {self.socketio_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Socket.IO: {e}")
            logger.warning("Continuing without real-time events (HTTP API still available)")
            # Don't raise - allow HTTP API to work without Socket.IO
    
    async def disconnect(self):
        """Disconnect from Socket.IO server"""
        await self.sio.disconnect()
        await self.http_client.aclose()
        logger.info("Disconnected from Commuter Service")
    
    # ========================================================================
    # REST API
    # ========================================================================
    
    async def get_manifest(
        self,
        route: Optional[str] = None,
        day: Optional[str] = None,
        date: Optional[str] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        limit: int = 1000
    ) -> ManifestResponse:
        """
        Query passenger manifest
        
        Args:
            route: Route short name (e.g., "1", "2")
            day: Day of week (e.g., "monday") - DEPRECATED, use date instead
            date: Specific date (YYYY-MM-DD format)
            start_hour: Start hour (0-23) - requires date or day
            end_hour: End hour (0-23) - requires date or day
            limit: Maximum results (default: 100, max: 1000)
        
        Returns:
            ManifestResponse with passengers
        """
        params = {'limit': min(limit, 1000)}
        
        if route:
            params['route'] = route
        
        # Only apply date/time filters if explicitly provided
        if date:
            from datetime import datetime
            
            # Parse explicit date
            target_date = datetime.strptime(date, '%Y-%m-%d')
            
            # Set start/end times
            start_h = start_hour if start_hour is not None else 0
            end_h = end_hour if end_hour is not None else 23
            
            start_dt = target_date.replace(hour=start_h, minute=0, second=0, microsecond=0)
            end_dt = target_date.replace(hour=end_h, minute=59, second=59, microsecond=999999)
            
            params['start'] = start_dt.isoformat()
            params['end'] = end_dt.isoformat()
        
        # Note: 'day' parameter is ignored to avoid hardcoded dates
        # Users should use 'date' parameter with explicit YYYY-MM-DD format
        
        response = await self.http_client.get("/api/manifest", params=params)
        response.raise_for_status()
        
        return ManifestResponse(**response.json())
    
    async def get_barchart(
        self,
        route: Optional[str] = None,
        day: Optional[str] = None,
        start_hour: int = 0,
        end_hour: int = 23
    ) -> Dict[str, Any]:
        """Get barchart visualization data"""
        params = {
            'start_hour': start_hour,
            'end_hour': end_hour
        }
        if route:
            params['route'] = route
        if day:
            params['day'] = day
        
        response = await self.http_client.get("/api/manifest/visualization/barchart", params=params)
        response.raise_for_status()
        
        return response.json()
    
    async def get_stats(
        self,
        route: Optional[str] = None,
        day: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get passenger statistics"""
        params = {}
        if route:
            params['route'] = route
        if day:
            params['day'] = day
        
        response = await self.http_client.get("/api/manifest/stats", params=params)
        response.raise_for_status()
        
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        response = await self.http_client.get("/health")
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # EVENT STREAMING (Observable Pattern)
    # ========================================================================
    
    def on(self, event: str, callback: Callable):
        """
        Subscribe to event
        
        Args:
            event: Event name (e.g., 'passenger:spawned', EventType.SPAWNED)
            callback: Callback function (sync or async)
        
        Example:
            def on_spawned(data):
                print(f"Spawned: {data}")
            
            connector.on('passenger:spawned', on_spawned)
        """
        event_name = event.value if isinstance(event, EventType) else event
        
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        
        self._event_handlers[event_name].append(callback)
        logger.debug(f"Subscribed to event: {event_name}")
    
    def off(self, event: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from event
        
        Args:
            event: Event name
            callback: Specific callback to remove (if None, removes all)
        """
        event_name = event.value if isinstance(event, EventType) else event
        
        if event_name not in self._event_handlers:
            return
        
        if callback is None:
            # Remove all handlers for this event
            del self._event_handlers[event_name]
            logger.debug(f"Unsubscribed all handlers from: {event_name}")
        else:
            # Remove specific handler
            self._event_handlers[event_name].remove(callback)
            logger.debug(f"Unsubscribed handler from: {event_name}")
    
    async def _trigger_event(self, event: str, data: Any):
        """Trigger event callbacks"""
        event_name = event.value if isinstance(event, EventType) else event
        
        if event_name not in self._event_handlers:
            return
        
        for callback in self._event_handlers[event_name]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {e}")
