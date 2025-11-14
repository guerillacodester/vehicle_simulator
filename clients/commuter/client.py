"""
Commuter Service Client
=======================

Pure business logic client with no UI dependencies.
Can be used from any interface (CLI, GUI, web, .NET via pythonnet).
"""

import requests
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
from datetime import datetime

from .models import (
    ManifestResponse,
    BarchartResponse,
    TableResponse,
    RouteMetrics,
    SeedRequest,
    SeedResponse,
    HealthResponse
)

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False


class CommuterClient:
    """
    Interface-agnostic commuter service client.
    
    Provides access to passenger manifest queries, visualization, and seeding.
    
    Example (Manifest Query):
        client = CommuterClient("http://localhost:4000")
        response = client.get_manifest(route="1", limit=100)
        print(f"Found {response.count} passengers")
    
    Example (Visualization):
        barchart = client.get_barchart(date="2024-11-04", route="1")
        print(f"Peak hour: {barchart.peak_hour}:00 ({barchart.max_count} passengers)")
    
    Example (Seeding):
        result = client.seed_passengers(route="1", day="monday", start_hour=7, end_hour=9)
        print(f"Created {result.passengers_created} passengers")
    
    Example (Auto-config):
        client = CommuterClient()  # Loads URL from config.ini
        manifest = client.get_manifest(route="1")
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize commuter client.
        
        Args:
            base_url: Base URL of commuter service. If None, loads from config.ini.
                     Defaults to "http://localhost:4000" if config unavailable.
        """
        if base_url is None:
            if _config_available:
                try:
                    config = get_config()
                    base_url = config.infrastructure.commuter_service_url
                except Exception:
                    base_url = "http://localhost:4000"  # Fallback
            else:
                base_url = "http://localhost:4000"  # Fallback
        
        self.base_url = base_url.rstrip('/')
    
    # ==================== Health ====================
    
    def health_check(self) -> HealthResponse:
        """
        Check service health.
        
        Returns:
            HealthResponse with status
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/health")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return HealthResponse.model_validate(response.json())
    
    # ==================== Manifest Queries ====================
    
    def get_manifest(
        self,
        route: Optional[str] = None,
        depot: Optional[str] = None,
        status: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        sort: str = "spawned_at:asc"
    ) -> ManifestResponse:
        """
        Get passenger manifest with filtering.
        
        Args:
            route: Filter by route_id
            depot: Filter by depot_id
            status: Filter by status (WAITING, BOARDED, etc.)
            start: Filter spawned_at >= ISO8601 timestamp
            end: Filter spawned_at <= ISO8601 timestamp
            limit: Max passengers to return (1-1000)
            sort: Sort order (default: spawned_at:asc)
        
        Returns:
            ManifestResponse with passengers
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/api/manifest")
        params = {
            "limit": limit,
            "sort": sort
        }
        if route:
            params["route"] = route
        if depot:
            params["depot"] = depot
        if status:
            params["status"] = status
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return ManifestResponse.model_validate(response.json())
    
    # ==================== Visualization ====================
    
    def get_barchart(
        self,
        date: str,
        route: Optional[str] = None,
        start_hour: int = 0,
        end_hour: int = 23
    ) -> BarchartResponse:
        """
        Get barchart visualization data.
        
        Args:
            date: Target date (YYYY-MM-DD)
            route: Filter by route short name (e.g., "1")
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
        
        Returns:
            BarchartResponse with hourly counts
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/api/manifest/visualization/barchart")
        params = {
            "date": date,
            "start_hour": start_hour,
            "end_hour": end_hour
        }
        if route:
            params["route"] = route
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return BarchartResponse.model_validate(response.json())
    
    def get_table(
        self,
        date: str,
        route: Optional[str] = None,
        start_hour: int = 0,
        end_hour: int = 23
    ) -> TableResponse:
        """
        Get table visualization with geocoded addresses.
        
        Args:
            date: Target date (YYYY-MM-DD)
            route: Filter by route short name (e.g., "1")
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
        
        Returns:
            TableResponse with enriched passenger data
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/api/manifest/visualization/table")
        params = {
            "date": date,
            "start_hour": start_hour,
            "end_hour": end_hour
        }
        if route:
            params["route"] = route
        
        response = requests.get(url, params=params, timeout=60)  # Longer timeout for geocoding
        response.raise_for_status()
        return TableResponse.model_validate(response.json())
    
    def get_stats(
        self,
        date: str,
        route: Optional[str] = None,
        start_hour: int = 0,
        end_hour: int = 23
    ) -> RouteMetrics:
        """
        Get summary statistics.
        
        Args:
            date: Target date (YYYY-MM-DD)
            route: Filter by route short name (e.g., "1")
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
        
        Returns:
            RouteMetrics with summary statistics
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/api/manifest/stats")
        params = {
            "date": date,
            "start_hour": start_hour,
            "end_hour": end_hour
        }
        if route:
            params["route"] = route
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return RouteMetrics.model_validate(response.json())
    
    # ==================== Seeding ====================
    
    def seed_passengers(
        self,
        route: str,
        day: Optional[str] = None,
        date: Optional[str] = None,
        start_hour: int = 0,
        end_hour: int = 23,
        spawn_type: str = "route"
    ) -> SeedResponse:
        """
        Seed passengers for a route (triggers spawning remotely).
        
        Note: This requires the /api/manifest/seed endpoint to be implemented.
        
        Args:
            route: Route short name (e.g., "1")
            day: Day of week (monday, tuesday, etc.) - alternative to date
            date: Specific date (YYYY-MM-DD) - alternative to day
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
            spawn_type: "route", "depot", or "both"
        
        Returns:
            SeedResponse with creation results
        
        Raises:
            requests.RequestException: If request fails
            NotImplementedError: If endpoint doesn't exist yet
        """
        url = urljoin(self.base_url, "/api/manifest/seed")
        
        seed_request = SeedRequest(
            route=route,
            day=day,
            date=date,
            start_hour=start_hour,
            end_hour=end_hour,
            spawn_type=spawn_type
        )
        
        response = requests.post(
            url,
            json=seed_request.model_dump(exclude_none=True),
            timeout=300  # 5 minutes for large seeding operations
        )
        
        if response.status_code == 404:
            raise NotImplementedError(
                "Seed endpoint not yet implemented. "
                "Use commuter_service/seed.py directly for now."
            )
        
        response.raise_for_status()
        return SeedResponse.model_validate(response.json())
    
    # ==================== Deletion ====================
    
    def delete_passengers(
        self,
        route: Optional[str] = None,
        depot: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete passengers matching filters.
        
        Args:
            route: Filter by route_id
            depot: Filter by depot_id
            status: Filter by status
            start_time: Filter spawned_at >= ISO8601 timestamp
            end_time: Filter spawned_at <= ISO8601 timestamp
        
        Returns:
            Dict with deleted_count and filters_applied
        
        Raises:
            requests.RequestException: If request fails
        """
        url = urljoin(self.base_url, "/api/manifest")
        params = {}
        if route:
            params["route"] = route
        if depot:
            params["depot"] = depot
        if status:
            params["status"] = status
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        
        response = requests.delete(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
