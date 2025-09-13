"""
Source-Agnostic Telemetry Interface
----------------------------------
Abstract interface that allows any data source (simulated, serial, network, file, etc.)
to feed telemetry data into the GPS device buffer system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import threading
import time


class ITelemetrySource(ABC):
    """
    Abstract interface for any telemetry data source.
    Implementations can be simulation, serial GPS, network feeds, files, etc.
    """
    
    @abstractmethod
    def start(self) -> bool:
        """
        Start the telemetry source.
        Returns True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the telemetry source."""
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the source is currently running."""
        pass
    
    @abstractmethod
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest telemetry data.
        Returns None if no data available.
        
        Expected format:
        {
            "lat": float,
            "lon": float, 
            "speed": float,
            "heading": float,
            "route": str,
            "vehicle_reg": str,
            "driver_id": str,
            "driver_name": {"first": str, "last": str},
            "ts": str (ISO format),
            # Any additional custom fields
        }
        """
        pass


class TelemetryManager:
    """
    Manages telemetry data flow from any source to GPS device buffers.
    Source-agnostic - works with simulation, real GPS, network feeds, etc.
    """
    
    def __init__(self):
        self.sources: List[ITelemetrySource] = []
        self.buffers: List[Any] = []  # RxTx buffers from GPS devices
        self.running = False
        self.manager_thread = None
        self.update_interval = 0.5  # Default 500ms
        
    def add_source(self, source: ITelemetrySource) -> None:
        """Add a telemetry data source."""
        self.sources.append(source)
        
    def add_buffer(self, buffer) -> None:
        """Add a GPS device buffer to receive data."""
        self.buffers.append(buffer)
        
    def set_update_interval(self, interval: float) -> None:
        """Set how often to poll sources for data (seconds)."""
        self.update_interval = interval
        
    def start(self) -> bool:
        """Start all sources and begin data flow management."""
        try:
            # Start all sources
            for source in self.sources:
                if not source.start():
                    print(f"⚠️ Failed to start source: {source.__class__.__name__}")
                    
            self.running = True
            self.manager_thread = threading.Thread(target=self._manage_data_flow, daemon=True)
            self.manager_thread.start()
            
            print(f"📡 Telemetry Manager started with {len(self.sources)} sources")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start telemetry manager: {e}")
            return False
            
    def _manage_data_flow(self) -> None:
        """Main loop - poll sources and distribute to buffers."""
        while self.running:
            try:
                # Collect data from all active sources
                for source in self.sources:
                    if source.is_running():
                        data = source.get_latest_data()
                        if data:
                            # Distribute to all buffers
                            self._distribute_data(data)
                            
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"⚠️ Data flow error: {e}")
                time.sleep(1.0)
                
    def _distribute_data(self, data: Dict[str, Any]) -> None:
        """Send data to all registered buffers."""
        for buffer in self.buffers:
            try:
                buffer.write(data)
            except Exception as e:
                print(f"⚠️ Buffer write failed: {e}")
                
    def stop(self) -> None:
        """Stop all sources and data flow."""
        self.running = False
        
        for source in self.sources:
            try:
                source.stop()
            except Exception as e:
                print(f"⚠️ Error stopping source: {e}")
                
        print("🛑 Telemetry Manager stopped")
        
    def get_status(self) -> Dict[str, Any]:
        """Get current status of manager and sources."""
        return {
            "running": self.running,
            "sources": [
                {
                    "type": source.__class__.__name__,
                    "running": source.is_running()
                }
                for source in self.sources
            ],
            "buffers_count": len(self.buffers),
            "update_interval": self.update_interval
        }


class TelemetrySourceBase(ITelemetrySource):
    """
    Base implementation with common functionality.
    Concrete sources can inherit from this.
    """
    
    def __init__(self, source_id: str = "unknown"):
        self.source_id = source_id
        self.running = False
        self.last_data: Optional[Dict[str, Any]] = None
        self.data_lock = threading.Lock()
        
    def is_running(self) -> bool:
        return self.running
        
    def _update_data(self, new_data: Dict[str, Any]) -> None:
        """Thread-safe data update."""
        with self.data_lock:
            # Ensure standard fields exist
            standardized_data = self._standardize_data(new_data)
            self.last_data = standardized_data
            
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get latest data (thread-safe)."""
        with self.data_lock:
            return self.last_data.copy() if self.last_data else None
            
    def _standardize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure data has all required fields with defaults."""
        standardized = {
            "lat": float(data.get("lat", 0.0)),
            "lon": float(data.get("lon", 0.0)),
            "speed": float(data.get("speed", 0.0)),
            "heading": float(data.get("heading", 0.0)),
            "route": str(data.get("route", "unknown")),
            "vehicle_reg": str(data.get("vehicle_reg", self.source_id)),
            "driver_id": str(data.get("driver_id", f"drv-{self.source_id}")),
            "driver_name": data.get("driver_name", {"first": "Unknown", "last": "Driver"}),
            "ts": data.get("ts", datetime.now(timezone.utc).isoformat()),
        }
        
        # Include any additional fields
        for key, value in data.items():
            if key not in standardized:
                standardized[key] = value
                
        return standardized
