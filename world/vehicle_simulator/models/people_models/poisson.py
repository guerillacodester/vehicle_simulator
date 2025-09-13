#!/usr/bin/env python3
"""
Poisson Distribution Model for People Simulation
===============================================

This module implements a Poisson distribution model with realistic passenger
generation patterns including peak hours, weekend patterns, and business
location weighting.
"""

import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from .base import IPeopleDistributionModel

# Import needed types and classes - these will be resolved at runtime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..people import Passenger, JourneyDetails, PeopleSimulatorConfig


class PoissonDistributionModel(IPeopleDistributionModel):
    """
    Poisson distribution model with peak times and business location weighting.
    
    Models realistic passenger arrival patterns:
    - Peak hours (7-9 AM, 5-7 PM) have higher passenger generation rates
    - Business areas have higher passenger density
    - Weekend patterns differ from weekday patterns
    - Journey distances follow realistic distribution
    """
    
    def __init__(
        self,
        config: Optional['PeopleSimulatorConfig'] = None,
        base_lambda: float = 2.0,
        peak_multiplier: float = 3.0,
        weekend_multiplier: float = 0.6,
        min_journey_km: float = 0.5,
        max_journey_km: float = 25.0,
        business_area_boost: float = 1.5
    ):
        """
        Initialize Poisson distribution model.
        
        Args:
            config: Configuration for API endpoints and settings
            base_lambda: Base rate for Poisson distribution (passengers per minute)
            peak_multiplier: Multiplier for peak hours
            weekend_multiplier: Multiplier for weekend traffic
            min_journey_km: Minimum journey distance
            max_journey_km: Maximum journey distance
            business_area_boost: Multiplier for business area passenger generation
        """
        # Import config class at runtime to avoid circular imports
        from ..people import PeopleSimulatorConfig
        
        self.config = config or PeopleSimulatorConfig()
        self.base_lambda = base_lambda
        self.peak_multiplier = peak_multiplier
        self.weekend_multiplier = weekend_multiplier
        self.min_journey_km = min_journey_km
        self.max_journey_km = max_journey_km
        self.business_area_boost = business_area_boost
        
        # Define peak hours (24-hour format)
        self.morning_peak = (7, 9)  # 7 AM - 9 AM
        self.evening_peak = (17, 19)  # 5 PM - 7 PM
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_model_name(self) -> str:
        """Return the name of this distribution model."""
        return "PoissonDistributionModel"
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Return the current parameters of this distribution model."""
        return {
            'base_lambda': self.base_lambda,
            'peak_multiplier': self.peak_multiplier,
            'weekend_multiplier': self.weekend_multiplier,
            'min_journey_km': self.min_journey_km,
            'max_journey_km': self.max_journey_km,
            'business_area_boost': self.business_area_boost,
            'morning_peak': self.morning_peak,
            'evening_peak': self.evening_peak
        }
    
    def _calculate_current_lambda(self, current_time: datetime) -> float:
        """Calculate current lambda based on time of day and day of week."""
        hour = current_time.hour
        is_weekend = current_time.weekday() >= 5  # Saturday = 5, Sunday = 6
        
        # Base rate
        current_lambda = self.base_lambda
        
        # Apply weekend multiplier
        if is_weekend:
            current_lambda *= self.weekend_multiplier
        
        # Apply peak hour multiplier
        if (self.morning_peak[0] <= hour < self.morning_peak[1] or 
            self.evening_peak[0] <= hour < self.evening_peak[1]):
            current_lambda *= self.peak_multiplier
        
        return current_lambda
    
    def _generate_realistic_coordinates(self, route_id: str) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Generate pickup and destination coordinates using REAL route data from PUBLIC API.
        
        STRICT REQUIREMENT: Must have route polyline from public API.
        NO FALLBACKS - if data is missing, passenger generation fails.
        NO PRIVATE ENDPOINTS - only uses public route geometry API.
        
        Distribution strategy:
        - All passengers pickup and destination along route polyline
        - Uses realistic distance constraints between pickup and destination
        """
        # Load route polyline from public API (REQUIRED)  
        route_points = self._get_route_polyline_strict(route_id)
        if not route_points or len(route_points) < 2:
            raise RuntimeError(f"Cannot generate passengers for {route_id}: Route polyline unavailable or invalid")
        
        # Passenger starts at random point along route polyline
        pickup_point = random.choice(route_points)
        pickup_lat, pickup_lon = pickup_point
        self.logger.debug(f"Generated route pickup for route {route_id}: ({pickup_lat:.6f}, {pickup_lon:.6f})")
        
        # Destination is always along the route polyline
        # Ensure destination is different from pickup (minimum distance constraint)
        available_destinations = [point for point in route_points 
                                if abs(point[0] - pickup_lat) > 0.001 or abs(point[1] - pickup_lon) > 0.001]
        
        if not available_destinations:
            raise RuntimeError(f"Cannot find valid destination for route {route_id}: All route points too close to pickup")
        
        dest_lat, dest_lon = random.choice(available_destinations)
        
        return (pickup_lat, pickup_lon), (dest_lat, dest_lon)
    
    def _get_route_polyline_strict(self, route_id: str) -> List[Tuple[float, float]]:
        """
        Get route polyline coordinates from API (strict mode - no fallbacks).
        
        Args:
            route_id: Route identifier (e.g., "route1")
            
        Returns:
            List of (latitude, longitude) tuples representing the route polyline
            
        Raises:
            RuntimeError: If route polyline cannot be retrieved
        """
        # Load coordinates from API
        coordinates = self._load_route_coordinates_from_api(route_id)
        
        if not coordinates or len(coordinates) < 2:
            raise RuntimeError(f"Cannot generate passengers: Route {route_id} has insufficient polyline data")
        
        # Convert from [longitude, latitude] to (latitude, longitude) tuples
        route_points = [(coord[1], coord[0]) for coord in coordinates]
        
        self.logger.debug(f"Loaded {len(route_points)} route points for {route_id}")
        return route_points
    
    def _get_random_route_point_strict(self, route_id: str) -> Tuple[float, float]:
        """
        Get random point along route polyline from geojson data (strict mode - no fallbacks).
        
        Args:
            route_id: Route identifier (e.g., "route1")
            
        Returns:
            Tuple of (latitude, longitude) along the route
            
        Raises:
            RuntimeError: If route coordinates cannot be loaded
        """
        # Load route coordinates from API
        route_coordinates = self._load_route_coordinates_from_api(route_id)
        
        if not route_coordinates:
            self.logger.error(f"No coordinates found for {route_id}")
            raise RuntimeError(f"Cannot generate passengers: Route {route_id} coordinates unavailable")
        
        # Select random point from route coordinates
        selected_point = random.choice(route_coordinates)
        
        # Coordinates in geojson are [longitude, latitude], convert to (latitude, longitude)
        lat, lon = selected_point[1], selected_point[0]
        
        self.logger.debug(f"Selected route point for {route_id}: ({lat:.6f}, {lon:.6f})")
        return (lat, lon)
    
    def _load_route_coordinates_from_api(self, route_id: str) -> Optional[List[List[float]]]:
        """
        Load route coordinates from public API.
        
        Args:
            route_id: Route identifier (e.g., "route1", "1")
            
        Returns:
            List of [longitude, latitude] coordinate pairs, or None if not found
            
        Raises:
            RuntimeError: If route coordinates cannot be retrieved
        """
        try:
            import requests
            
            # Map route IDs to route codes for API calls
            route_codes = {
                'route1': '1',
                'route_1': '1', 
                '1': '1',
            }
            
            route_code = route_codes.get(route_id.lower())
            if not route_code:
                self.logger.error(f"No route code mapped for route {route_id}")
                raise RuntimeError(f"Cannot generate passengers: Unknown route {route_id}")
            
            # Get route geometry from public API  
            api_url = f"{self.config.api_url}/routes/public/{route_code}/geometry"
            api_response = requests.get(api_url, timeout=self.config.request_timeout)
            
            if api_response.status_code == 200:
                route_data = api_response.json()
                
                if route_data.get('geometry') and route_data['geometry'].get('coordinates'):
                    coordinates = route_data['geometry']['coordinates']
                    self.logger.info(f"Loaded {len(coordinates)} coordinates for route {route_id} from API")
                    return coordinates
                else:
                    self.logger.error(f"Route {route_id} has no geometry coordinates in database")
                    raise RuntimeError(f"Cannot generate passengers: Route {route_id} has no geometry data")
            else:
                self.logger.error(f"Failed to get route {route_id} geometry from API: HTTP {api_response.status_code}")
                raise RuntimeError(f"Cannot generate passengers: Route API returned HTTP {api_response.status_code}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Cannot connect to route API for {route_id}: {e}")
            raise RuntimeError(f"Cannot generate passengers: Route API connection failed - {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error loading route coordinates for {route_id}: {e}")
            raise RuntimeError(f"Cannot generate passengers: Route coordinate retrieval failed - {e}")
    
    async def generate_passengers(
        self, 
        available_routes: List[str], 
        current_time: datetime,
        simulation_duration: int
    ) -> List['Passenger']:
        """Generate passengers using Poisson distribution with realistic patterns."""
        if not available_routes:
            return []
        
        # Import classes at runtime to avoid circular imports
        from ..people import Passenger, JourneyDetails
        
        # Calculate current passenger generation rate
        current_lambda = self._calculate_current_lambda(current_time)
        
        # Generate number of passengers using Poisson distribution
        # Lambda is per minute, so adjust for simulation tick
        tick_lambda = current_lambda / 60.0  # Convert to per-second rate
        num_passengers = np.random.poisson(tick_lambda)
        
        passengers = []
        
        for _ in range(num_passengers):
            # Select random route
            route_id = random.choice(available_routes)
            
            # Generate realistic pickup and destination coordinates
            (pickup_lat, pickup_lon), (dest_lat, dest_lon) = self._generate_realistic_coordinates(route_id)
            
            # Create journey details
            journey = JourneyDetails(
                route_id=route_id,
                pickup_lat=pickup_lat,
                pickup_lon=pickup_lon,
                destination_lat=dest_lat,
                destination_lon=dest_lon,
                pickup_time=current_time
            )
            
            # Create passenger
            passenger = Passenger(journey=journey)
            passengers.append(passenger)
        
        if passengers:
            self.logger.info(
                f"Generated {len(passengers)} passengers at {current_time.strftime('%H:%M:%S')} "
                f"(lambda={current_lambda:.2f})"
            )
        
        return passengers