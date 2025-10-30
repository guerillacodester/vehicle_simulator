"""
Core GPS telemetry client.

Pure business logic with no UI dependencies.
Can be used from any interface (CLI, GUI, web, .NET via pythonnet).
"""

import requests
import json
import threading
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from .models import Vehicle, AnalyticsResponse, HealthResponse
from .observers import ObservableClient


class GPSTelemetryClient(ObservableClient):
    """
    Interface-agnostic GPS telemetry client.
    
    Provides both synchronous (HTTP polling) and asynchronous (SSE streaming)
    methods for consuming telemetry data.
    
    Can be used directly or through observers for event-driven architectures.
    
    Example (Synchronous):
        client = GPSTelemetryClient("http://localhost:8000")
        vehicles = client.get_all_devices()
        for v in vehicles:
            print(f"{v.deviceId}: {v.lat}, {v.lon}")
    
    Example (Streaming with Observer):
        class MyObserver(TelemetryObserver):
            def on_vehicle_update(self, vehicle):
                print(f"Update: {vehicle.deviceId}")
        
        client = GPSTelemetryClient("http://localhost:8000")
        client.add_observer(MyObserver())
        client.start_stream()  # Non-blocking
    
    Example (Streaming with Callback):
        def on_update(vehicle):
            print(f"Update: {vehicle.deviceId}")
        
        client = GPSTelemetryClient("http://localhost:8000")
        client.add_observer(CallbackObserver(on_vehicle_update=on_update))
        client.start_stream()
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", api_prefix: str = "/gps"):
        """
        Initialize GPS telemetry client.
        
        Args:
            base_url: Base URL of GPS server (e.g., "http://localhost:8000")
            api_prefix: API prefix (e.g., "/gps" for unified services, "" for standalone)
        """
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.api_prefix = api_prefix.rstrip('/')
        self._stream_thread: Optional[threading.Thread] = None
        self._stream_active = False
    
    # ==================== Synchronous HTTP Methods ====================
    
    def get_all_devices(self) -> List[Vehicle]:
        """
        Get all active devices (HTTP polling).
        
        Returns:
            List of Vehicle objects with current telemetry
        
        Raises:
            requests.RequestException: If HTTP request fails
        """
        url = urljoin(self.base_url, f"{self.api_prefix}/devices")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [Vehicle.model_validate(item) for item in data]
    
    def get_device(self, device_id: str) -> Optional[Vehicle]:
        """
        Get specific device by ID (HTTP polling).
        
        Args:
            device_id: Device identifier (e.g., "GPS-ZR102")
        
        Returns:
            Vehicle object if found, None if not found
        
        Raises:
            requests.RequestException: If HTTP request fails (except 404)
        """
        url = urljoin(self.base_url, f"{self.api_prefix}/device/{device_id}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return Vehicle.model_validate(response.json())
    
    def get_route_devices(self, route_code: str) -> List[Vehicle]:
        """
        Get all devices on a specific route (HTTP polling).
        
        Args:
            route_code: Route identifier (e.g., "1", "2A")
        
        Returns:
            List of Vehicle objects on the route
        
        Raises:
            requests.RequestException: If HTTP request fails
        """
        url = urljoin(self.base_url, f"{self.api_prefix}/route/{route_code}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [Vehicle.model_validate(item) for item in data]
    
    def get_analytics(self) -> AnalyticsResponse:
        """
        Get fleet analytics (HTTP polling).
        
        Returns:
            AnalyticsResponse with per-route statistics
        
        Raises:
            requests.RequestException: If HTTP request fails
        """
        url = urljoin(self.base_url, f"{self.api_prefix}/analytics")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return AnalyticsResponse.model_validate(response.json())
    
    def get_health(self) -> HealthResponse:
        """
        Get server health status (HTTP polling).
        
        Returns:
            HealthResponse with server status
        
        Raises:
            requests.RequestException: If HTTP request fails
        """
        url = urljoin(self.base_url, f"{self.api_prefix}/health")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return HealthResponse.model_validate(response.json())
    
    # ==================== Streaming Methods (SSE) ====================
    
    def start_stream(
        self,
        device_id: Optional[str] = None,
        route_code: Optional[str] = None,
        blocking: bool = False
    ) -> None:
        """
        Start SSE telemetry stream (notifies observers on updates).
        
        Args:
            device_id: Filter to specific device (optional)
            route_code: Filter to specific route (optional)
            blocking: If True, blocks until stream ends. If False, runs in background thread.
        
        Example (Non-blocking):
            client.add_observer(my_observer)
            client.start_stream()  # Returns immediately
            # Do other work...
            client.stop_stream()  # Stop when done
        
        Example (Blocking):
            client.add_observer(my_observer)
            client.start_stream(blocking=True)  # Blocks until Ctrl+C or error
        """
        if self._stream_active:
            raise RuntimeError("Stream already active. Call stop_stream() first.")
        
        self._stream_active = True
        
        if blocking:
            self._run_stream(device_id, route_code)
        else:
            self._stream_thread = threading.Thread(
                target=self._run_stream,
                args=(device_id, route_code),
                daemon=True
            )
            self._stream_thread.start()
    
    def stop_stream(self) -> None:
        """
        Stop SSE telemetry stream.
        
        If stream is running in background thread, this will signal it to stop.
        """
        self._stream_active = False
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=5)
        self._notify_disconnected()
    
    def is_streaming(self) -> bool:
        """Check if stream is currently active."""
        return self._stream_active
    
    def _run_stream(self, device_id: Optional[str], route_code: Optional[str]) -> None:
        """
        Internal method to run SSE stream.
        
        Notifies observers of updates. Runs until stop_stream() called or error occurs.
        """
        params: Dict[str, str] = {}
        if device_id:
            params['device_id'] = device_id
        if route_code:
            params['route_code'] = route_code
        
        url = urljoin(self.base_url, f"{self.api_prefix}/stream")
        
        try:
            response = requests.get(url, params=params, stream=True, timeout=None)
            response.raise_for_status()
            
            self._notify_connected()
            
            for line in response.iter_lines():
                if not self._stream_active:
                    break
                
                if line.startswith(b'data:'):
                    try:
                        data = line[5:].decode('utf-8').strip()
                        vehicle = Vehicle.model_validate_json(data)
                        self._notify_vehicle_update(vehicle)
                    except Exception as e:
                        self._notify_error(e)
        
        except Exception as e:
            self._notify_error(e)
        
        finally:
            self._stream_active = False
            self._notify_disconnected()
    
    # ==================== Utility Methods ====================
    
    def test_connection(self) -> bool:
        """
        Test if server is reachable.
        
        Returns:
            True if server responds to health check, False otherwise
        """
        try:
            self.get_health()
            return True
        except Exception:
            return False
