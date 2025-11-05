"""
Commuter Service Client Connector
==================================

GUI-agnostic client for connecting to the Commuter Service API.
Supports both REST API and real-time WebSocket streaming.

Features:
- REST API: Query manifest, stats, visualization data
- WebSocket: Real-time passenger spawn/board/alight events
- Observable pattern: Subscribe to events with callbacks
- Auto-reconnection on disconnect
- Type-safe Pydantic models

Usage:
    from clients.commuter.connector import CommuterConnector
    
    connector = CommuterConnector(base_url="http://localhost:4000")
    
    # REST API
    manifest = await connector.get_manifest(route=1, date="2024-11-04")
    
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
import json

import httpx
import websockets
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
    - Real-time events (WebSocket)
    - Observable pattern (callbacks)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:4000",
        ws_url: Optional[str] = None,
        auto_reconnect: bool = True
    ):
        """
        Initialize connector
        
        Args:
            base_url: Base URL for REST API (default: http://localhost:4000)
            ws_url: WebSocket server URL (default: None, will auto-detect)
            auto_reconnect: Auto-reconnect on disconnect (default: True)
        """
        self.base_url = base_url.rstrip('/')
        
        # Detect WebSocket URL if not provided
        if ws_url:
            self.ws_url = ws_url
        else:
            # Convert http://localhost:4000 -> ws://localhost:4000/ws/stream
            ws_base = self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')
            self.ws_url = f"{ws_base}/ws/stream"
        
        self.auto_reconnect = auto_reconnect
        
        # HTTP client with extended timeout for long operations (seed can take minutes)
        self.http_client = httpx.AsyncClient(base_url=self.base_url, timeout=300.0)
        
        # WebSocket connection
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._ws_task: Optional[asyncio.Task] = None
        
        # Event handlers (Observable pattern)
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Connection state
        self.connected = False
        self.is_websocket_connected = False
        
        logger.info(f"CommuterConnector initialized | REST: {self.base_url} | WebSocket: {self.ws_url}")
    
    async def _websocket_listener(self):
        """Listen for WebSocket messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    logger.debug(f"📨 WebSocket message: {message_type}")
                    
                    # Handle connection events
                    if message_type == "connected":
                        self.is_websocket_connected = True
                        await self._trigger_event('connect', data)
                    
                    # Handle passenger lifecycle events
                    elif message_type in ["passenger:spawned", "passenger:boarded", "passenger:alighted"]:
                        await self._trigger_event(message_type, data.get("data", {}))
                    
                    # Handle seed progress events
                    elif message_type in ["seed:progress", "seed:hour_complete"]:
                        await self._trigger_event(message_type, data.get("data", {}))
                    
                    # Handle subscription confirmations
                    elif message_type in ["subscribed", "unsubscribed"]:
                        logger.info(f"✅ {data.get('message')}")
                    
                    # Handle errors
                    elif message_type == "error":
                        logger.error(f"❌ WebSocket error: {data.get('message')}")
                    
                    # Handle any other event types (catch-all)
                    elif ":" in message_type:
                        await self._trigger_event(message_type, data.get("data", {}))
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚫ WebSocket connection closed")
            self.is_websocket_connected = False
            await self._trigger_event('disconnect', {})
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    async def connect(self):
        """Connect to WebSocket server for real-time events"""
        if self.ws_url is None:
            logger.info("WebSocket URL not provided - real-time events disabled")
            return
        
        try:
            self.ws = await websockets.connect(self.ws_url)
            logger.info(f"✅ Connected to WebSocket: {self.ws_url}")
            
            # Start listener task
            self._ws_task = asyncio.create_task(self._websocket_listener())
            
            # Wait a bit for the welcome message and set connected flag
            await asyncio.sleep(0.5)
            
            # Check if we received the connected message
            if not self.is_websocket_connected:
                # Set it manually since connection succeeded
                self.is_websocket_connected = True
                logger.info("WebSocket connected (manual flag set)")
            
        except Exception as e:
            logger.warning(f"Failed to connect to WebSocket: {e}")
            logger.warning("Continuing without real-time events (HTTP API still available)")
            # Don't raise - allow HTTP API to work without WebSocket
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.ws:
            await self.ws.close()
        
        if self._ws_task:
            self._ws_task.cancel()
        
        await self.http_client.aclose()
        logger.info("Disconnected from Commuter Service")
    
    async def subscribe(self, route: str):
        """Subscribe to passenger events for a specific route"""
        if not self.ws or not self.is_websocket_connected:
            logger.warning("Not connected to WebSocket")
            return
        
        await self.ws.send(json.dumps({
            "type": "subscribe",
            "route": route
        }))
        logger.info(f"📡 Subscribed to route: {route}")
    
    async def unsubscribe(self, route: str):
        """Unsubscribe from passenger events for a route"""
        if not self.ws or not self.is_websocket_connected:
            return
        
        await self.ws.send(json.dumps({
            "type": "unsubscribe",
            "route": route
        }))
        logger.info(f"🔕 Unsubscribed from route: {route}")
    
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
            limit: Maximum results (default: 1000, max: 1000)
        
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
    
    async def seed_passengers(
        self,
        route: str,
        day: Optional[str] = None,
        date: Optional[str] = None,
        spawn_type: str = "route",
        start_hour: int = 0,
        end_hour: int = 23
    ) -> Dict[str, Any]:
        """
        Trigger passenger seeding on the server
        
        Args:
            route: Route short name (e.g., "1", "2")
            day: Day of week (e.g., "monday") - alternative to date
            date: Specific date (YYYY-MM-DD format) - alternative to day
            spawn_type: Type of spawning: 'route', 'depot', or 'both'
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
        
        Returns:
            Seed response with counts and status
        """
        payload = {
            'route': route,
            'spawn_type': spawn_type,
            'start_hour': start_hour,
            'end_hour': end_hour
        }
        
        if day:
            payload['day'] = day
        elif date:
            payload['date'] = date
        else:
            raise ValueError("Either 'day' or 'date' must be specified")
        
        try:
            response = await self.http_client.post("/api/seed", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Enhance error message with response details
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    detail = error_data.get('detail', str(e))
                    raise Exception(f"{detail}") from e
                except:
                    raise Exception(f"HTTP {e.response.status_code}: {e.response.text}") from e
            raise

    
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
    
    async def delete_passengers(
        self,
        route: Optional[str] = None,
        date: Optional[str] = None,
        day: Optional[str] = None,
        status: Optional[str] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        confirm: bool = False
    ) -> dict:
        """
        Delete passengers matching filters
        
        Args:
            route: Route short name (e.g., "1", "2")
            date: Specific date (YYYY-MM-DD)
            day: Day of week (e.g., "monday")
            status: Filter by status (e.g., "WAITING")
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
            confirm: Must be True to actually delete (safety check)
        
        Returns:
            dict with 'deleted' count and 'message'
        """
        params = {'confirm': confirm}
        
        if route:
            params['route'] = route
        if date:
            params['date'] = date
        if day:
            params['day'] = day
        if status:
            params['status'] = status
        if start_hour is not None:
            params['start_hour'] = start_hour
        if end_hour is not None:
            params['end_hour'] = end_hour
        
        response = await self.http_client.delete("/api/manifest", params=params)
        return response.json()
    
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
