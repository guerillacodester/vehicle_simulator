"""
Fleet Management Client Connector
==================================

GUI-agnostic client for connecting to the Fleet Management API.
Supports both REST API and real-time WebSocket streaming.

Features:
- REST API: Query vehicles, conductors, health
- Control API: Start/stop engines, enable/disable boarding
- WebSocket: Real-time event streaming (engine, position, passengers)
- Observable pattern: Subscribe to events with callbacks
- Auto-reconnection on disconnect
- Type-safe Pydantic models

Usage:
    from clients.fleet.connector import FleetConnector
    
    connector = FleetConnector(base_url="http://localhost:5001")
    
    # REST API - Query state
    vehicles = await connector.get_vehicles()
    vehicle = await connector.get_vehicle("ZR102")
    
    # Control API - Issue commands
    result = await connector.start_engine("ZR102")
    result = await connector.enable_boarding("ZR102")
    result = await connector.trigger_boarding("ZR102")
    
    # Real-time streaming
    def on_engine_started(data):
        print(f"Engine started: {data}")
    
    connector.on('engine_started', on_engine_started)
    await connector.connect_websocket()
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from enum import Enum
import json

import httpx
import websockets

from .models import (
    VehicleState, VehicleListResponse,
    ConductorState, ConductorListResponse,
    CommandResult, HealthResponse, FleetEvent
)


logger = logging.getLogger(__name__)


# ============================================================================
# EVENT TYPES
# ============================================================================

class EventType(str, Enum):
    """Fleet event types"""
    ENGINE_STARTED = "engine_started"
    ENGINE_STOPPED = "engine_stopped"
    POSITION_UPDATE = "position_update"
    PASSENGER_BOARDED = "passenger_boarded"
    PASSENGER_ALIGHTED = "passenger_alighted"
    BOARDING_ENABLED = "boarding_enabled"
    BOARDING_DISABLED = "boarding_disabled"
    CONNECT = "connect"
    DISCONNECT = "disconnect"


# ============================================================================
# FLEET CONNECTOR
# ============================================================================

class FleetConnector:
    """
    GUI-agnostic client for Fleet Management API.
    
    Supports:
    - REST API (HTTP/HTTPS)
    - Control commands (POST)
    - Real-time events (WebSocket)
    - Observable pattern (callbacks)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:6000",
        ws_url: Optional[str] = None,
        auto_reconnect: bool = True
    ):
        """
        Initialize connector
        
        Args:
            base_url: Base URL for Host Server API (default: http://localhost:6000)
            ws_url: WebSocket server URL (default: None, will auto-detect)
            auto_reconnect: Auto-reconnect on disconnect (default: True)
        """
        self.base_url = base_url.rstrip('/')
        
        # Detect WebSocket URL if not provided
        if ws_url:
            self.ws_url = ws_url
        else:
            # Convert http://localhost:5001 -> ws://localhost:5001/ws/events
            ws_base = self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')
            self.ws_url = f"{ws_base}/ws/events"
        
        self.auto_reconnect = auto_reconnect
        
        # HTTP client with extended timeout
        self.http_client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        
        # WebSocket connection
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._ws_task: Optional[asyncio.Task] = None
        
        # Event handlers (Observable pattern)
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Connection state
        self.connected = False
        self.is_websocket_connected = False
        
        logger.info(f"FleetConnector initialized | REST: {self.base_url} | WebSocket: {self.ws_url}")
    
    # ========================================================================
    # EVENT HANDLING (Observable Pattern)
    # ========================================================================
    
    def on(self, event_type: str, callback: Callable):
        """
        Subscribe to an event
        
        Args:
            event_type: Event type (e.g., 'engine_started', 'position_update')
            callback: Callback function to invoke when event occurs
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(callback)
        logger.debug(f"📡 Subscribed to '{event_type}'")
    
    def off(self, event_type: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from an event
        
        Args:
            event_type: Event type
            callback: Specific callback to remove (if None, remove all)
        """
        if event_type not in self._event_handlers:
            return
        
        if callback is None:
            # Remove all handlers for this event
            del self._event_handlers[event_type]
        else:
            # Remove specific handler
            self._event_handlers[event_type] = [
                h for h in self._event_handlers[event_type] if h != callback
            ]
    
    async def _trigger_event(self, event_type: str, data: Any):
        """Trigger all callbacks for an event type"""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for '{event_type}': {e}")
    
    # ========================================================================
    # WEBSOCKET CONNECTION
    # ========================================================================
    
    async def _websocket_listener(self):
        """Listen for WebSocket messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    event_type = data.get("event_type")
                    
                    logger.debug(f"📨 WebSocket event: {event_type}")
                    
                    # Trigger event handlers
                    await self._trigger_event(event_type, data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚫ WebSocket connection closed")
            self.is_websocket_connected = False
            await self._trigger_event('disconnect', {})
            
            # Auto-reconnect if enabled
            if self.auto_reconnect:
                logger.info("🔄 Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
                await self.connect_websocket()
    
    async def connect_websocket(self):
        """Connect to WebSocket server for real-time events"""
        if self.ws_url is None:
            logger.info("WebSocket URL not provided - real-time events disabled")
            return
        
        try:
            logger.info(f"🔌 Connecting to WebSocket: {self.ws_url}")
            self.ws = await websockets.connect(self.ws_url)
            self.is_websocket_connected = True
            
            # Start listener task
            self._ws_task = asyncio.create_task(self._websocket_listener())
            
            logger.info("✅ WebSocket connected")
            await self._trigger_event('connect', {})
            
        except Exception as e:
            logger.error(f"❌ Failed to connect WebSocket: {e}")
            self.is_websocket_connected = False
    
    async def disconnect_websocket(self):
        """Disconnect from WebSocket server"""
        if self.ws:
            logger.info("🔌 Disconnecting WebSocket...")
            await self.ws.close()
            self.ws = None
            self.is_websocket_connected = False
        
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None
    
    # ========================================================================
    # REST API - HEALTH & STATUS
    # ========================================================================
    
    async def get_health(self) -> HealthResponse:
        """
        Get API health status
        
        Returns:
            HealthResponse with simulator status
        """
        response = await self.http_client.get("/health")
        response.raise_for_status()
        return HealthResponse(**response.json())
    
    async def get_websocket_status(self) -> Dict[str, Any]:
        """
        Get WebSocket connection statistics
        
        Returns:
            WebSocket status dict
        """
        response = await self.http_client.get("/ws/status")
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # REST API - VEHICLES
    # ========================================================================
    
    async def get_vehicles(self) -> List[VehicleState]:
        """
        Get all vehicles
        
        Returns:
            List of VehicleState objects
        """
        response = await self.http_client.get("/api/vehicles")
        response.raise_for_status()
        data = VehicleListResponse(**response.json())
        return data.drivers
    
    async def get_vehicle(self, vehicle_id: str) -> VehicleState:
        """
        Get specific vehicle by ID
        
        Args:
            vehicle_id: Vehicle registration code (e.g., "ZR102")
        
        Returns:
            VehicleState object
        """
        response = await self.http_client.get(f"/api/vehicles/{vehicle_id}")
        response.raise_for_status()
        return VehicleState(**response.json())
    
    # ========================================================================
    # REST API - CONDUCTORS
    # ========================================================================
    
    async def get_conductors(self) -> List[ConductorState]:
        """
        Get all conductors
        
        Returns:
            List of ConductorState objects
        """
        response = await self.http_client.get("/api/conductors")
        response.raise_for_status()
        data = ConductorListResponse(**response.json())
        return data.conductors
    
    async def get_conductor(self, vehicle_id: str) -> ConductorState:
        """
        Get conductor for specific vehicle
        
        Args:
            vehicle_id: Vehicle registration code
        
        Returns:
            ConductorState object
        """
        response = await self.http_client.get(f"/api/conductors/{vehicle_id}")
        response.raise_for_status()
        return ConductorState(**response.json())
    
    # ========================================================================
    # CONTROL API - ENGINE
    # ========================================================================
    
    async def start_engine(self, vehicle_id: str) -> CommandResult:
        """
        Start vehicle engine
        
        Args:
            vehicle_id: Vehicle registration code
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post(f"/api/vehicles/{vehicle_id}/start-engine")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    async def stop_engine(self, vehicle_id: str) -> CommandResult:
        """
        Stop vehicle engine
        
        Args:
            vehicle_id: Vehicle registration code
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post(f"/api/vehicles/{vehicle_id}/stop-engine")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    # ========================================================================
    # CONTROL API - BOARDING
    # ========================================================================
    
    async def enable_boarding(self, vehicle_id: str) -> CommandResult:
        """
        Enable passenger boarding for vehicle
        
        Args:
            vehicle_id: Vehicle registration code
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post(f"/api/vehicles/{vehicle_id}/enable-boarding")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    async def disable_boarding(self, vehicle_id: str) -> CommandResult:
        """
        Disable passenger boarding for vehicle
        
        Args:
            vehicle_id: Vehicle registration code
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post(f"/api/vehicles/{vehicle_id}/disable-boarding")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    async def trigger_boarding(self, vehicle_id: str) -> CommandResult:
        """
        Manually trigger passenger boarding check
        
        Args:
            vehicle_id: Vehicle registration code
        
        Returns:
            CommandResult with passengers_boarded count
        """
        response = await self.http_client.post(f"/api/vehicles/{vehicle_id}/trigger-boarding")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    # ========================================================================
    # SIMULATOR CONTROL
    # ========================================================================
    
    async def get_sim_status(self) -> Dict[str, Any]:
        """
        Get simulator status
        
        Returns:
            Dict with running status, sim_time, vehicle counts
        """
        response = await self.http_client.get("/api/sim/status")
        response.raise_for_status()
        return response.json()
    
    async def pause_sim(self) -> CommandResult:
        """
        Pause the simulator
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post("/api/sim/pause")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    async def resume_sim(self) -> CommandResult:
        """
        Resume the simulator
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post("/api/sim/resume")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    async def stop_sim(self) -> CommandResult:
        """
        Stop the simulator
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post("/api/sim/stop")
        response.raise_for_status()
        return CommandResult(**response.json())
    
    async def set_sim_time(self, sim_time: datetime) -> CommandResult:
        """
        Set simulation time
        
        Args:
            sim_time: New simulation datetime
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post(
            "/api/sim/set-time",
            json={"sim_time": sim_time.isoformat()}
        )
        response.raise_for_status()
        return CommandResult(**response.json())
    
    # ========================================================================
    # SERVICE MANAGEMENT (Host Server)
    # ========================================================================
    
    async def start_simulator_service(
        self,
        api_port: Optional[int] = None,
        sim_time: Optional[str] = None,
        enable_boarding_after: Optional[float] = None,
        data_api_url: Optional[str] = None
    ) -> CommandResult:
        """
        Start the simulator service
        
        Args:
            api_port: Override API port
            sim_time: Simulation time (ISO or HH:MM)
            enable_boarding_after: Auto-enable boarding delay
            data_api_url: Fleet data API URL (vehicles/drivers/routes source)
        
        Returns:
            CommandResult with success status
        """
        payload = {}
        if api_port:
            payload["api_port"] = api_port
        if sim_time:
            payload["sim_time"] = sim_time
        if enable_boarding_after:
            payload["enable_boarding_after"] = enable_boarding_after
        if data_api_url:
            payload["data_api_url"] = data_api_url
        
        response = await self.http_client.post(
            "/api/services/simulator/start",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    
    async def stop_simulator_service(self) -> CommandResult:
        """
        Stop the simulator service
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post("/api/services/simulator/stop")
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    
    async def restart_simulator_service(
        self,
        api_port: Optional[int] = None,
        sim_time: Optional[str] = None,
        enable_boarding_after: Optional[float] = None
    ) -> CommandResult:
        """
        Restart the simulator service
        
        Args:
            api_port: Override API port
            sim_time: Simulation time (ISO or HH:MM)
            enable_boarding_after: Auto-enable boarding delay
        
        Returns:
            CommandResult with success status
        """
        payload = {}
        if api_port:
            payload["api_port"] = api_port
        if sim_time:
            payload["sim_time"] = sim_time
        if enable_boarding_after:
            payload["enable_boarding_after"] = enable_boarding_after
        
        response = await self.http_client.post(
            "/api/services/simulator/restart",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    
    async def get_simulator_service_status(self) -> Dict[str, Any]:
        """
        Get simulator service status
        
        Returns:
            Dict with service status
        """
        response = await self.http_client.get("/api/services/simulator/status")
        response.raise_for_status()
        return response.json()
    
    async def get_all_services_status(self) -> Dict[str, Any]:
        """
        Get all services status
        
        Returns:
            Dict with all service statuses
        """
        response = await self.http_client.get("/api/services/status")
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # Multi-Service Control (Registry-based)
    # ========================================================================
    
    async def start_service(
        self,
        service_name: str,
        api_port: Optional[int] = None,
        sim_time: Optional[str] = None,
        enable_boarding_after: Optional[float] = None,
        data_api_url: Optional[str] = None
    ) -> CommandResult:
        """
        Start a specific service by name
        
        Args:
            service_name: Service name (simulator, gpscentcom, commuter_service, geospatial)
            api_port: Override API port (simulator only)
            sim_time: Simulation time (simulator only)
            enable_boarding_after: Auto-enable boarding delay (simulator only)
            data_api_url: Fleet data API URL (simulator only)
        
        Returns:
            CommandResult with success status
        """
        payload = {}
        if api_port:
            payload["api_port"] = api_port
        if sim_time:
            payload["sim_time"] = sim_time
        if enable_boarding_after:
            payload["enable_boarding_after"] = enable_boarding_after
        if data_api_url:
            payload["data_api_url"] = data_api_url
        
        response = await self.http_client.post(
            f"/api/services/{service_name}/start",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    
    async def stop_service(self, service_name: str) -> CommandResult:
        """
        Stop a specific service by name
        
        Args:
            service_name: Service name (simulator, gpscentcom, commuter_service, geospatial)
        
        Returns:
            CommandResult with success status
        """
        response = await self.http_client.post(f"/api/services/{service_name}/stop")
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    
    async def restart_service(
        self,
        service_name: str,
        api_port: Optional[int] = None,
        sim_time: Optional[str] = None,
        enable_boarding_after: Optional[float] = None,
        data_api_url: Optional[str] = None
    ) -> CommandResult:
        """
        Restart a specific service by name
        
        Args:
            service_name: Service name (simulator, gpscentcom, commuter_service, geospatial)
            api_port: Override API port (simulator only)
            sim_time: Simulation time (simulator only)
            enable_boarding_after: Auto-enable boarding delay (simulator only)
            data_api_url: Fleet data API URL (simulator only)
        
        Returns:
            CommandResult with success status
        """
        payload = {}
        if api_port:
            payload["api_port"] = api_port
        if sim_time:
            payload["sim_time"] = sim_time
        if enable_boarding_after:
            payload["enable_boarding_after"] = enable_boarding_after
        if data_api_url:
            payload["data_api_url"] = data_api_url
        
        response = await self.http_client.post(
            f"/api/services/{service_name}/restart",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get status of a specific service
        
        Args:
            service_name: Service name (simulator, gpscentcom, commuter_service, geospatial)
        
        Returns:
            Dict with service status
        """
        response = await self.http_client.get(f"/api/services/{service_name}/status")
        response.raise_for_status()
        return response.json()
    
    async def start_all_services(
        self,
        data_api_url: Optional[str] = None
    ) -> CommandResult:
        """
        Start all services in dependency order
        
        Args:
            data_api_url: Fleet data API URL (passed to simulator)
        
        Returns:
            CommandResult with success status and service results
        """
        payload = {}
        if data_api_url:
            payload["data_api_url"] = data_api_url
        
        response = await self.http_client.post(
            "/api/services/start-all",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    
    async def stop_all_services(self) -> CommandResult:
        """
        Stop all services in reverse dependency order
        
        Returns:
            CommandResult with success status and service results
        """
        response = await self.http_client.post("/api/services/stop-all")
        response.raise_for_status()
        result = response.json()
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
    # CLEANUP
    # ========================================================================
    
    async def close(self):
        """Close all connections"""
        await self.disconnect_websocket()
        await self.http_client.aclose()
        logger.info("FleetConnector closed")
