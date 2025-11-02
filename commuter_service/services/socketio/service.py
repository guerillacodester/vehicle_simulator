"""
Socket.IO Service - Real-time event communication
=================================================

Single source of truth for Socket.IO communication in the commuter simulator.
"""

import socketio
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ServiceType(Enum):
    """Service identifier"""
    COMMUTER_SERVICE = "commuter-service"
    VEHICLE_CONDUCTOR = "vehicle-conductor"
    DEPOT_MANAGER = "depot-manager"
    SIMULATOR = "simulator"


class EventTypes:
    """Event type constants"""
    # Commuter Events
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
    
    # System Events
    SERVICE_CONNECTED = "system:service_connected"
    SERVICE_DISCONNECTED = "system:service_disconnected"
    HEALTH_CHECK = "system:health_check"
    ERROR = "system:error"


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
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class SocketIOService:
    """
    Socket.IO communication service
    
    Usage:
        service = SocketIOService(
            url="http://localhost:1337",
            namespace="/depot-reservoir",
            service_type=ServiceType.COMMUTER_SERVICE
        )
        
        await service.connect()
        await service.emit(EventTypes.COMMUTER_SPAWNED, commuter_data)
        await service.disconnect()
    """
    
    def __init__(
        self,
        url: str = "http://localhost:1337",
        namespace: str = "/depot-reservoir",
        service_type: ServiceType = ServiceType.COMMUTER_SERVICE
    ):
        self.url = url
        self.namespace = namespace
        self.service_type = service_type
        self.logger = logging.getLogger(__name__)
        
        self.sio = socketio.AsyncClient(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1,
            reconnection_delay_max=5,
        )
        
        self.handlers: Dict[str, List[Callable]] = {}
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "connected_at": None,
        }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up Socket.IO event handlers"""
        
        @self.sio.event(namespace=self.namespace)
        async def connect():
            self.stats["connected_at"] = datetime.now().isoformat()
            self.logger.info(f"✓ Connected to {self.url}{self.namespace}")
        
        @self.sio.event(namespace=self.namespace)
        async def disconnect():
            self.logger.info(f"✓ Disconnected from {self.url}{self.namespace}")
        
        @self.sio.event(namespace=self.namespace)
        async def connect_error(data):
            self.stats["errors"] += 1
            self.logger.error(f"✗ Connection error: {data}")
        
        @self.sio.event(namespace=self.namespace)
        async def message(data: Dict[str, Any]):
            self.stats["messages_received"] += 1
            
            try:
                message_type = data.get("type")
                
                if message_type in self.handlers:
                    for handler in self.handlers[message_type]:
                        try:
                            await handler(data)
                        except Exception as e:
                            self.logger.error(f"✗ Handler error for {message_type}: {e}")
                            self.stats["errors"] += 1
                            
            except Exception as e:
                self.logger.error(f"✗ Error processing message: {e}")
                self.stats["errors"] += 1
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def connect(self):
        """Connect to Socket.IO server"""
        try:
            self.logger.info(f"Connecting to {self.url}{self.namespace}...")
            await self.sio.connect(
                self.url,
                namespaces=[self.namespace],
                transports=['websocket', 'polling']
            )
        except Exception as e:
            self.logger.error(f"✗ Connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from server"""
        try:
            await self.sio.disconnect()
            self.logger.info("Disconnected successfully")
        except Exception as e:
            self.logger.error(f"✗ Disconnect error: {e}")
    
    async def emit(
        self,
        event_type: str,
        data: Dict[str, Any],
        target: Optional[str | List[str]] = None
    ):
        """Emit message to server"""
        try:
            message = SocketIOMessage(
                id=f"msg_{int(datetime.now().timestamp() * 1000)}",
                type=event_type,
                timestamp=datetime.now().isoformat(),
                source=self.service_type.value,
                data=data,
                target=target
            )
            
            await self.sio.emit('message', message.to_dict(), namespace=self.namespace)
            self.stats["messages_sent"] += 1
            
        except Exception as e:
            self.logger.error(f"✗ Emit error: {e}")
            self.stats["errors"] += 1
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return self.stats.copy()
