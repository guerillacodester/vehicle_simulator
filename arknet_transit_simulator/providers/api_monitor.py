"""
API Monitor Stub
================
Simple stub implementation for API monitoring functionality.
"""

import logging
from enum import Enum
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

class APIConnectionStatus(Enum):
    """API connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert status to dictionary."""
        return {"status": self.value}

class SocketIOAPIMonitor:
    """Simple API monitor stub for Fleet Manager connectivity."""
    
    def __init__(self, server_url: str):
        """Initialize API monitor."""
        self.server_url = server_url
        self.status = APIConnectionStatus.DISCONNECTED
        self.callbacks = []
        self.monitoring = False
        
    def add_status_callback(self, callback: Callable[[APIConnectionStatus], None]):
        """Add a callback for status changes."""
        self.callbacks.append(callback)
        
    def start_monitoring(self):
        """Start monitoring API connectivity."""
        logger.info(f"[APIMonitor] Starting monitoring for {self.server_url}")
        self.monitoring = True
        self.status = APIConnectionStatus.CONNECTED
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(self.status)
            except Exception as e:
                logger.error(f"[APIMonitor] Callback error: {e}")
                
    def stop_monitoring(self):
        """Stop monitoring API connectivity."""
        logger.info("[APIMonitor] Stopping monitoring")
        self.monitoring = False
        self.status = APIConnectionStatus.DISCONNECTED
        
    def is_api_available(self) -> bool:
        """Check if API is available."""
        return self.status == APIConnectionStatus.CONNECTED
        
    def get_status(self) -> APIConnectionStatus:
        """Get current connection status."""
        return self.status
        
    def force_reconnect(self):
        """Force a reconnection attempt."""
        logger.info("[APIMonitor] Force reconnect requested")
        if self.monitoring:
            self.status = APIConnectionStatus.CONNECTED
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(self.status)
                except Exception as e:
                    logger.error(f"[APIMonitor] Callback error: {e}")