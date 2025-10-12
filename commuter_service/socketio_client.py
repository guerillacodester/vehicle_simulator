"""
Socket.IO Client for Python Services

This module provides a Socket.IO client for Python services to connect
to the Strapi Socket.IO hub and participate in real-time event communication.

Services:
- Commuter Service: Spawns commuters, manages reservoirs
- Vehicle Conductor: Queries commuters, coordinates boarding
- Depot Manager: Manages queues, triggers departures
"""

import socketio
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json


class CommuterDirection(Enum):
    """Travel direction"""
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class ReservoirType(Enum):
    """Reservoir type"""
    DEPOT = "depot"
    ROUTE = "route"


class ServiceType(Enum):
    """Service identifier"""
    COMMUTER_SERVICE = "commuter-service"
    VEHICLE_CONDUCTOR = "vehicle-conductor"
    DEPOT_MANAGER = "depot-manager"
    SIMULATOR = "simulator"


@dataclass
class SocketIOMessage:
    """Standardized message format"""
    id: str
    type: str
    timestamp: str
    source: str
    data: Dict[str, Any]
    target: Optional[str | List[str]] = None
    correlationId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class EventTypes:
    """Event type constants"""
    # Commuter Service Events
    COMMUTER_SPAWNED = "commuter:spawned"
    COMMUTER_PICKED_UP = "commuter:picked_up"
    COMMUTER_DROPPED_OFF = "commuter:dropped_off"
    COMMUTER_EXPIRED = "commuter:expired"
    
    # Vehicle Query Events
    QUERY_COMMUTERS = "vehicle:query_commuters"
    COMMUTERS_FOUND = "vehicle:commuters_found"
    NO_COMMUTERS_FOUND = "vehicle:no_commuters"
    
    # Depot Queue Events
    DEPOT_QUEUE_JOIN = "depot:queue_join"
    DEPOT_QUEUE_UPDATE = "depot:queue_update"
    DEPOT_VEHICLE_DEPART = "depot:vehicle_depart"
    DEPOT_SEATS_FILLED = "depot:seats_filled"
    
    # System Events
    SERVICE_CONNECTED = "system:service_connected"
    SERVICE_DISCONNECTED = "system:service_disconnected"
    HEALTH_CHECK = "system:health_check"
    ERROR = "system:error"


class SocketIOClient:
    """
    Socket.IO client for Python services
    
    Example:
        ```python
        client = SocketIOClient(
            url="http://localhost:1337",
            namespace="/depot-reservoir",
            service_type=ServiceType.COMMUTER_SERVICE
        )
        
        await client.connect()
        await client.emit_message(EventTypes.COMMUTER_SPAWNED, commuter_data)
        await client.disconnect()
        ```
    """
    
    def __init__(
        self,
        url: str = "http://localhost:1337",
        namespace: str = "/depot-reservoir",
        service_type: ServiceType = ServiceType.COMMUTER_SERVICE,
        logger: Optional[logging.Logger] = None
    ):
        self.url = url
        self.namespace = namespace
        self.service_type = service_type
        self.logger = logger or logging.getLogger(__name__)
        
        # Create Socket.IO client
        self.sio = socketio.AsyncClient(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=0,  # Infinite
            reconnection_delay=1,
            reconnection_delay_max=5,
        )
        
        # Message handlers
        self.handlers: Dict[str, List[Callable]] = {}
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "connected_at": None,
        }
        
        # Set up default event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up default Socket.IO event handlers"""
        
        @self.sio.event(namespace=self.namespace)
        async def connect():
            self.stats["connected_at"] = datetime.now().isoformat()
            self.logger.info(
                f"Connected to Socket.IO server: {self.url}{self.namespace}"
            )
        
        @self.sio.event(namespace=self.namespace)
        async def disconnect():
            self.logger.info(
                f"Disconnected from Socket.IO server: {self.url}{self.namespace}"
            )
        
        @self.sio.event(namespace=self.namespace)
        async def connect_error(data):
            self.stats["errors"] += 1
            self.logger.error(f"Connection error: {data}")
        
        @self.sio.event(namespace=self.namespace)
        async def message(data: Dict[str, Any]):
            """Handle incoming messages"""
            self.stats["messages_received"] += 1
            
            try:
                # Validate message format
                if not self._validate_message(data):
                    self.logger.warning(f"Invalid message format: {data}")
                    return
                
                message_type = data.get("type")
                self.logger.debug(
                    f"Received message: {message_type} from {data.get('source')}"
                )
                
                # Call registered handlers
                if message_type in self.handlers:
                    for handler in self.handlers[message_type]:
                        try:
                            await handler(data)
                        except Exception as e:
                            self.logger.error(
                                f"Error in handler for {message_type}: {e}"
                            )
                            self.stats["errors"] += 1
                            
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
                self.stats["errors"] += 1
        
        @self.sio.event(namespace=self.namespace)
        async def error(data: Dict[str, Any]):
            """Handle error messages"""
            self.stats["errors"] += 1
            self.logger.error(f"Server error: {data}")
    
    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate message structure"""
        required_fields = ["id", "type", "timestamp", "source", "data"]
        return all(field in message for field in required_fields)
    
    def _create_message(
        self,
        message_type: str,
        data: Dict[str, Any],
        target: Optional[str | List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> SocketIOMessage:
        """Create a standardized message"""
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}_{id(data)}"
        
        return SocketIOMessage(
            id=message_id,
            type=message_type,
            timestamp=datetime.now().isoformat(),
            source=self.service_type.value,
            data=data,
            target=target,
            correlationId=correlation_id
        )
    
    async def connect(self):
        """Connect to Socket.IO server"""
        try:
            self.logger.info(f"Connecting to {self.url}{self.namespace}...")
            await self.sio.connect(
                self.url,
                namespaces=[self.namespace],
                transports=['websocket', 'polling']
            )
            self.logger.info("Connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Socket.IO server"""
        try:
            await self.sio.disconnect()
            self.logger.info("Disconnected successfully")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    async def emit_message(
        self,
        message_type: str,
        data: Dict[str, Any],
        target: Optional[str | List[str]] = None,
        correlation_id: Optional[str] = None
    ):
        """Emit a message to the server"""
        try:
            message = self._create_message(message_type, data, target, correlation_id)
            await self.sio.emit('message', message.to_dict(), namespace=self.namespace)
            self.stats["messages_sent"] += 1
            
            self.logger.debug(
                f"Sent message: {message_type} (target: {target or 'broadcast'})"
            )
        except Exception as e:
            self.logger.error(f"Failed to emit message: {e}")
            self.stats["errors"] += 1
            raise
    
    def on(self, message_type: str, handler: Callable):
        """Register a message handler"""
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
        self.logger.debug(f"Registered handler for {message_type}")
    
    def off(self, message_type: str, handler: Optional[Callable] = None):
        """Unregister a message handler"""
        if message_type in self.handlers:
            if handler:
                self.handlers[message_type].remove(handler)
            else:
                del self.handlers[message_type]
            self.logger.debug(f"Unregistered handler for {message_type}")
    
    async def wait_for_response(
        self,
        correlation_id: str,
        expected_type: str,
        timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """Wait for a specific response message"""
        response_data = None
        response_event = asyncio.Event()
        
        async def response_handler(message: Dict[str, Any]):
            nonlocal response_data
            if message.get("correlationId") == correlation_id:
                response_data = message
                response_event.set()
        
        # Register temporary handler
        self.on(expected_type, response_handler)
        
        try:
            # Wait for response with timeout
            await asyncio.wait_for(response_event.wait(), timeout=timeout)
            return response_data
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Timeout waiting for response (correlation_id: {correlation_id})"
            )
            return None
        finally:
            # Cleanup handler
            self.off(expected_type, response_handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            **self.stats,
            "connected": self.sio.connected,
            "namespace": self.namespace,
            "service_type": self.service_type.value,
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            correlation_id = f"health_{int(datetime.now().timestamp() * 1000)}"
            
            # Send health check request
            await self.sio.emit(
                'health-check',
                {'correlationId': correlation_id},
                namespace='/system-events'
            )
            
            # Wait for response
            response = await self.wait_for_response(
                correlation_id,
                EventTypes.HEALTH_CHECK,
                timeout=3.0
            )
            
            if response:
                return response.get('data', {})
            else:
                return {"status": "timeout", "error": "Health check timeout"}
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}


# Convenience functions for common namespaces
def create_depot_client(
    url: str = "http://localhost:1337",
    service_type: ServiceType = ServiceType.COMMUTER_SERVICE
) -> SocketIOClient:
    """Create a client for the depot reservoir namespace"""
    return SocketIOClient(url, "/depot-reservoir", service_type)


def create_route_client(
    url: str = "http://localhost:1337",
    service_type: ServiceType = ServiceType.COMMUTER_SERVICE
) -> SocketIOClient:
    """Create a client for the route reservoir namespace"""
    return SocketIOClient(url, "/route-reservoir", service_type)


def create_vehicle_client(
    url: str = "http://localhost:1337",
    service_type: ServiceType = ServiceType.VEHICLE_CONDUCTOR
) -> SocketIOClient:
    """Create a client for the vehicle events namespace"""
    return SocketIOClient(url, "/vehicle-events", service_type)


def create_system_client(
    url: str = "http://localhost:1337",
    service_type: ServiceType = ServiceType.SIMULATOR
) -> SocketIOClient:
    """Create a client for the system events namespace"""
    return SocketIOClient(url, "/system-events", service_type)
