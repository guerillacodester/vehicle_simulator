"""
Socket.IO Connection Manager for Fleet API
------------------------------------------
Provides real-time monitoring of fleet_manager API status using Socket.IO.
Maintains connection state and notifies subscribers of API availability changes.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Any, Callable, Set, Optional
from datetime import datetime
import socketio

logger = logging.getLogger(__name__)


class APIConnectionStatus:
    """Represents the current API connection status"""
    
    def __init__(self):
        self.is_connected = False
        self.response_time: Optional[float] = None
        self.error: Optional[str] = None
        self.last_checked = datetime.now()
        self.server_status = 'unknown'
        self.reconnect_attempts = 0

    def update_connected(self, response_time: float = None):
        """Update status to connected"""
        self.is_connected = True
        self.response_time = response_time
        self.error = None
        self.last_checked = datetime.now()
        self.server_status = 'online'
        self.reconnect_attempts = 0

    def update_disconnected(self, error: str = None):
        """Update status to disconnected"""
        self.is_connected = False
        self.response_time = None
        self.error = error
        self.last_checked = datetime.now()
        self.server_status = 'offline'

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary"""
        return {
            'is_connected': self.is_connected,
            'response_time': self.response_time,
            'error': self.error,
            'last_checked': self.last_checked.isoformat(),
            'server_status': self.server_status,
            'reconnect_attempts': self.reconnect_attempts
        }


class SocketIOAPIMonitor:
    """
    Real-time API monitoring using Socket.IO connection to fleet_manager API.
    Provides connection status updates and automatic reconnection.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url.rstrip('/')
        self.socket: Optional[socketio.SimpleClient] = None
        self.status = APIConnectionStatus()
        
        # Callback management
        self.status_callbacks: Set[Callable[[APIConnectionStatus], None]] = set()
        
        # Connection management
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 2.0
        self.ping_interval = 30.0  # Ping every 30 seconds
        
        logger.info(f"Socket.IO API monitor initialized for: {self.server_url}")

    def add_status_callback(self, callback: Callable[[APIConnectionStatus], None]):
        """Add callback for status change notifications"""
        self.status_callbacks.add(callback)
        logger.debug(f"Added status callback: {callback.__name__}")

    def remove_status_callback(self, callback: Callable[[APIConnectionStatus], None]):
        """Remove status callback"""
        self.status_callbacks.discard(callback)
        logger.debug(f"Removed status callback: {callback.__name__}")

    def _notify_status_change(self):
        """Notify all callbacks of status change"""
        for callback in self.status_callbacks:
            try:
                callback(self.status)
            except Exception as e:
                logger.error(f"Error in status callback {callback.__name__}: {e}")

    def start_monitoring(self):
        """Start real-time API monitoring"""
        if self.is_monitoring:
            logger.warning("API monitoring already started")
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Socket.IO API monitoring started")

    def stop_monitoring(self):
        """Stop API monitoring"""
        self.is_monitoring = False
        
        if self.socket:
            try:
                self.socket.disconnect()
                logger.info("Socket.IO connection closed")
            except Exception as e:
                logger.warning(f"Error closing socket connection: {e}")
            finally:
                self.socket = None
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Socket.IO API monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting Socket.IO monitoring loop")
        
        while self.is_monitoring:
            try:
                if not self.socket or not self.socket.connected:
                    self._attempt_connection()
                else:
                    self._send_ping()
                
                # Wait before next iteration
                time.sleep(self.ping_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.status.update_disconnected(f"Monitor loop error: {e}")
                self._notify_status_change()
                time.sleep(self.reconnect_delay)

    def _attempt_connection(self):
        """Attempt to establish Socket.IO connection"""
        try:
            logger.info(f"Attempting Socket.IO connection to {self.server_url}")
            
            # Create new socket client
            self.socket = socketio.SimpleClient(
                logger=False,  # Disable socketio logging
                engineio_logger=False
            )
            
            # Connect with timeout
            start_time = time.time()
            self.socket.connect(
                self.server_url,
                transports=['websocket', 'polling'],
                wait_timeout=5
            )
            
            # Calculate connection time
            connection_time = time.time() - start_time
            
            # Setup event handlers
            self._setup_event_handlers()
            
            # Update status
            self.status.update_connected(connection_time)
            self._notify_status_change()
            
            logger.info(f"✅ Socket.IO connected in {connection_time:.2f}s")
            
        except Exception as e:
            self.status.reconnect_attempts += 1
            error_msg = f"Connection failed: {e}"
            
            if self.status.reconnect_attempts >= self.max_reconnect_attempts:
                error_msg += f" (max attempts {self.max_reconnect_attempts} reached)"
                logger.error(f"❌ Socket.IO connection failed permanently: {e}")
            else:
                logger.warning(f"⚠️ Socket.IO connection failed (attempt {self.status.reconnect_attempts}): {e}")
            
            self.status.update_disconnected(error_msg)
            self._notify_status_change()
            
            # Clean up failed socket
            if self.socket:
                try:
                    self.socket.disconnect()
                except:
                    pass
                self.socket = None

    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers using SimpleClient approach"""
        if not self.socket:
            return
            
        try:
            # SimpleClient doesn't support @socket.event decorators
            # We need to manually receive events in the monitoring loop
            logger.debug("Event handlers setup complete for SimpleClient")
            
        except Exception as e:
            logger.warning(f"Failed to setup event handlers: {e}")

    def _send_ping(self):
        """Send ping to test connection"""
        if not self.socket or not self.socket.connected:
            return
            
        try:
            self._ping_start_time = time.time()
            self.socket.emit('ping', {'timestamp': self._ping_start_time})
            
            # Try to receive events (SimpleClient approach)
            try:
                # Listen for pong response with timeout
                event = self.socket.receive(timeout=2)
                if event and len(event) >= 2:
                    event_name, event_data = event[0], event[1] if len(event) > 1 else {}
                    
                    if event_name == 'pong':
                        response_time = time.time() - self._ping_start_time
                        self.status.response_time = response_time
                        self.status.last_checked = datetime.now()
                        logger.debug(f"Ping response: {response_time:.3f}s")
                    elif event_name == 'connection_status':
                        if event_data.get('status') == 'connected':
                            self.status.server_status = event_data.get('server', 'online')
                        logger.debug(f"Received connection_status: {event_data}")
                        
            except Exception as e:
                # Timeout or no response is normal
                logger.debug(f"No ping response received: {e}")
            
            logger.debug("Sent ping to API")
            
        except Exception as e:
            logger.warning(f"Failed to send ping: {e}")
            self.status.update_disconnected(f"Ping failed: {e}")
            self._notify_status_change()

    def get_status(self) -> APIConnectionStatus:
        """Get current connection status"""
        return self.status

    def is_api_available(self) -> bool:
        """Check if API is currently available"""
        return self.status.is_connected and self.status.server_status == 'online'

    def force_reconnect(self):
        """Force a reconnection attempt"""
        logger.info("Forcing Socket.IO reconnection")
        
        # Disconnect current socket
        if self.socket:
            try:
                self.socket.disconnect()
            except:
                pass
            self.socket = None
        
        # Reset reconnect attempts
        self.status.reconnect_attempts = 0
        
        # Attempt immediate reconnection
        if self.is_monitoring:
            self._attempt_connection()

    def send_custom_event(self, event: str, data: Dict[str, Any]):
        """Send custom event to API (for future extensions)"""
        if not self.socket or not self.socket.connected:
            logger.warning(f"Cannot send event {event}: not connected")
            return False
            
        try:
            self.socket.emit(event, data)
            logger.debug(f"Sent custom event: {event}")
            return True
        except Exception as e:
            logger.error(f"Failed to send event {event}: {e}")
            return False


# Singleton instance for application-wide use
_api_monitor: Optional[SocketIOAPIMonitor] = None

def get_api_monitor(server_url: str = "http://localhost:8000") -> SocketIOAPIMonitor:
    """Get singleton API monitor instance"""
    global _api_monitor
    
    if _api_monitor is None:
        _api_monitor = SocketIOAPIMonitor(server_url)
    
    return _api_monitor

def start_api_monitoring(server_url: str = "http://localhost:8000") -> SocketIOAPIMonitor:
    """Start API monitoring and return monitor instance"""
    monitor = get_api_monitor(server_url)
    monitor.start_monitoring()
    return monitor

def stop_api_monitoring():
    """Stop API monitoring"""
    global _api_monitor
    
    if _api_monitor:
        _api_monitor.stop_monitoring()
        _api_monitor = None
