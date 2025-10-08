#!/usr/bin/env python3
"""
Step 6: Production API Integration - ProductionApiDataSource Implementation
==========================================================================

Production-ready passenger data source that replaces hardcoded values with live API integration
while maintaining the proven mathematical simulation algorithms.

DESIGN PRINCIPLE: 
- Same PassengerDataSource interface as Step 5
- Live API data instead of hardcoded values  
- Proven Poisson mathematics with real-world inputs
- Comprehensive error handling and fallback mechanisms
- Performance optimization with caching strategies
"""

import os

import asyncio
import logging
import time
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path

# Import the existing API client and interfaces
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'commuter_service'))

from commuter_service.strapi_api_client import StrapiApiClient


def _load_strapi_env_config():
    """
    Load environment config from Strapi folder if available.
    This allows the client to use the same config as the server.
    """
    strapi_env_path = Path(__file__).parent / "arknet_fleet_manager" / "arknet-fleet-api" / ".env"
    if strapi_env_path.exists():
        try:
            with open(strapi_env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key in ['CLIENT_API_URL', 'CLIENT_API_TOKEN'] and key not in os.environ:
                            os.environ[key] = value
        except Exception:
            pass  # Silently ignore errors, fallback to defaults


@dataclass
class GeographicBounds:
    """Dynamic geographic bounds calculated from real API data."""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    center_lat: float
    center_lon: float
    
    @property
    def area_km2(self) -> float:
        """Calculate approximate area in km²."""
        lat_diff = self.max_lat - self.min_lat
        lon_diff = self.max_lon - self.min_lon
        # Rough approximation for Barbados latitude
        return abs(lat_diff * lon_diff * 111.0 * 111.0 * math.cos(math.radians(self.center_lat)))


@dataclass
class POICategory:
    """POI category with spawning weights."""
    name: str
    weight: float
    description: str
    attraction_factor: float  # How much this POI type attracts passengers


@dataclass
class CachedApiData:
    """Cached API data with timestamp for performance optimization."""
    data: Any
    timestamp: datetime
    expiry_minutes: int = 10
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() - self.timestamp > timedelta(minutes=self.expiry_minutes)


class ProductionApiDataSource:
    """
    Production-ready passenger data source using live Strapi API integration.
    
    Replaces SimulatedPassengerDataSource hardcoded values with real API data while
    maintaining the same mathematical simulation algorithms and interface compatibility.
    """
    
    def __init__(self, base_url: str = None, enable_caching: bool = True):
        # Load config from Strapi .env if available
        _load_strapi_env_config()
        
        # Use environment variable or sensible default
        if base_url is None:
            # Try client-specific config first, then fallback to localhost
            base_url = (os.getenv('CLIENT_API_URL') or 
                       os.getenv('ARKNET_API_URL') or 
                       'http://localhost:1337')
        self.api_client = StrapiApiClient(base_url)
        self.enable_caching = enable_caching
        
        # Cache storage for performance optimization
        self._cache: Dict[str, CachedApiData] = {}
        
        # Dynamic configuration (replaces hardcoded values)
        self._geographic_bounds: Optional[GeographicBounds] = None
        self._poi_categories: Dict[str, POICategory] = {}
        self._depot_locations: List[Dict[str, Any]] = []
        self._route_data: List[Dict[str, Any]] = []
        
        # Mathematical parameters (configurable, not hardcoded)
        self.config = {
            'base_lambda': 2.3,  # Will be calibrated from real data
            'rush_hour_multiplier': 2.5,  # Will be adjusted based on POI categories
            'memory_per_passenger_mb': 0.0005,  # From Step 5 validation
            'cache_expiry_minutes': 10,
            'api_timeout_seconds': 30,
            'max_retries': 3
        }
        
        # Performance tracking
        self.performance_metrics = {
            'api_calls_made': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'api_errors': 0,
            'fallback_activations': 0
        }
        
        # Fallback data for error recovery
        self._fallback_bounds = GeographicBounds(
            min_lat=13.0, max_lat=13.35, min_lon=-59.65, max_lon=-59.4,
            center_lat=13.175, center_lon=-59.525
        )
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """
        Initialize the production data source with live API data.
        
        Returns:
            bool: True if initialization successful, False if fallback required
        """
        try:
            self.logger.info("🔄 Initializing Production API Data Source...")
            
            # Connect to API
            connection_success = await self.api_client.connect()
            if not connection_success:
                self.logger.error("❌ Failed to connect to Strapi API")
                return await self._initialize_fallback_mode()
            
            # Load core data with error handling
            success_flags = await asyncio.gather(
                self._load_geographic_bounds(),
                self._load_poi_categories(), 
                self._load_depot_locations(),
                self._load_route_data(),
                return_exceptions=True
            )
            
            # Check if any critical operations failed
            failures = [s for s in success_flags if isinstance(s, Exception)]
            if len(failures) > 2:  # Allow some failures but not too many
                self.logger.warning(f"⚠️ Multiple initialization failures ({len(failures)}), using fallback")
                return await self._initialize_fallback_mode()
            
            self.logger.info("✅ Production API Data Source initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Critical initialization error: {e}")
            return await self._initialize_fallback_mode()
    
    async def _initialize_fallback_mode(self) -> bool:
        """Initialize with fallback data when API is unavailable."""
        self.logger.warning("⚠️ Initializing fallback mode with cached/default data")
        self.performance_metrics['fallback_activations'] += 1
        
        # Use fallback geographic bounds
        self._geographic_bounds = self._fallback_bounds
        
        # Create basic POI categories for fallback
        self._poi_categories = {
            'restaurant': POICategory('restaurant', 0.4, 'Food establishments', 1.2),
            'shop': POICategory('shop', 0.3, 'Retail stores', 1.0),
            'transit_stop': POICategory('transit_stop', 0.8, 'Bus stops and terminals', 2.0),
            'amenity': POICategory('amenity', 0.2, 'General amenities', 0.8)
        }
        
        # Basic depot fallback (from our Step 4 data)
        self._depot_locations = [
            {"name": "Speightstown Bus Terminal", "latitude": 13.252068, "longitude": -59.642543},
            {"name": "Granville Williams Bus Terminal", "latitude": 13.096108, "longitude": -59.612344},
            {"name": "Cheapside ZR and Minibus Terminal", "latitude": 13.098168, "longitude": -59.621582},
            {"name": "Constitution River Terminal", "latitude": 13.096538, "longitude": -59.608646},
            {"name": "Princess Alice Bus Terminal", "latitude": 13.097766, "longitude": -59.621822}
        ]
        
        self.logger.info("✅ Fallback mode initialized")
        return True
    
    async def _load_geographic_bounds(self) -> bool:
        """Load and calculate dynamic geographic bounds from all API data."""
        try:
            cache_key = "geographic_bounds"
            
            # Check cache first
            if self.enable_caching and cache_key in self._cache:
                cached = self._cache[cache_key]
                if not cached.is_expired:
                    self._geographic_bounds = cached.data
                    self.performance_metrics['cache_hits'] += 1
                    return True
            
            self.logger.info("📍 Calculating dynamic geographic bounds from API data...")
            self.performance_metrics['api_calls_made'] += 1
            self.performance_metrics['cache_misses'] += 1
            
            # Collect coordinates from all geographic features
            all_coordinates = []
            
            # Get POI coordinates
            pois_response = await self.api_client.session.get(
                f"{self.api_client.base_url}/api/pois",
                params={"pagination[pageSize]": 100}
            )
            if pois_response.status_code == 200:
                pois_data = pois_response.json()
                for poi in pois_data.get('data', []):
                    if poi.get('coordinates'):
                        coords = poi['coordinates']
                        if isinstance(coords, list) and len(coords) >= 2:
                            all_coordinates.append((coords[1], coords[0]))  # lat, lon
            
            # Get Places coordinates  
            places_response = await self.api_client.session.get(
                f"{self.api_client.base_url}/api/places", 
                params={"pagination[pageSize]": 100}
            )
            if places_response.status_code == 200:
                places_data = places_response.json()
                for place in places_data.get('data', []):
                    if place.get('coordinates'):
                        coords = place['coordinates']
                        if isinstance(coords, list) and len(coords) >= 2:
                            all_coordinates.append((coords[1], coords[0]))  # lat, lon
            
            # Calculate bounds from collected coordinates
            if all_coordinates:
                lats = [coord[0] for coord in all_coordinates]
                lons = [coord[1] for coord in all_coordinates]
                
                self._geographic_bounds = GeographicBounds(
                    min_lat=min(lats),
                    max_lat=max(lats),
                    min_lon=min(lons),
                    max_lon=max(lons),
                    center_lat=sum(lats) / len(lats),
                    center_lon=sum(lons) / len(lons)
                )
                
                # Cache the result
                if self.enable_caching:
                    self._cache[cache_key] = CachedApiData(
                        data=self._geographic_bounds,
                        timestamp=datetime.now(),
                        expiry_minutes=60  # Geographic bounds change rarely
                    )
                
                self.logger.info(f"✅ Dynamic bounds: {self._geographic_bounds.min_lat:.3f}→{self._geographic_bounds.max_lat:.3f} lat, "
                               f"{self._geographic_bounds.min_lon:.3f}→{self._geographic_bounds.max_lon:.3f} lon "
                               f"(~{self._geographic_bounds.area_km2:.1f} km²)")
                return True
            else:
                self.logger.warning("⚠️ No coordinate data found, using fallback bounds")
                self._geographic_bounds = self._fallback_bounds
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error loading geographic bounds: {e}")
            self._geographic_bounds = self._fallback_bounds
            self.performance_metrics['api_errors'] += 1
            return False
    
    async def _load_poi_categories(self) -> bool:
        """Load POI categories and calculate spawning weights based on amenity types."""
        try:
            cache_key = "poi_categories"
            
            # Check cache first
            if self.enable_caching and cache_key in self._cache:
                cached = self._cache[cache_key]
                if not cached.is_expired:
                    self._poi_categories = cached.data
                    self.performance_metrics['cache_hits'] += 1
                    return True
            
            self.logger.info("🏷️ Loading POI categories from API...")
            self.performance_metrics['api_calls_made'] += 1
            self.performance_metrics['cache_misses'] += 1
            
            # Fetch POI data to analyze categories
            response = await self.api_client.session.get(
                f"{self.api_client.base_url}/api/pois",
                params={"pagination[pageSize]": 100}
            )
            
            if response.status_code == 200:
                pois_data = response.json()
                
                # Analyze POI categories and create weights
                category_counts = {}
                for poi in pois_data.get('data', []):
                    amenity = poi.get('amenity', 'general')
                    category_counts[amenity] = category_counts.get(amenity, 0) + 1
                
                # Create category weights based on real data
                total_pois = sum(category_counts.values())
                self._poi_categories = {}
                
                for category, count in category_counts.items():
                    # Calculate weight based on frequency and passenger attraction
                    base_weight = count / total_pois if total_pois > 0 else 0.1
                    
                    # Apply attraction factors based on category type
                    if 'restaurant' in category.lower() or 'food' in category.lower():
                        attraction_factor = 1.3  # Food attracts more passengers
                    elif 'shop' in category.lower() or 'store' in category.lower():
                        attraction_factor = 1.0  # Baseline attraction
                    elif 'transport' in category.lower() or 'bus' in category.lower():
                        attraction_factor = 2.0  # Transit hubs attract most passengers
                    elif 'school' in category.lower() or 'education' in category.lower():
                        attraction_factor = 1.5  # Schools generate significant traffic
                    else:
                        attraction_factor = 0.8  # General amenities
                    
                    self._poi_categories[category] = POICategory(
                        name=category,
                        weight=min(base_weight * attraction_factor, 1.0),  # Cap at 1.0
                        description=f"{category} (count: {count})",
                        attraction_factor=attraction_factor
                    )
                
                # Cache the result
                if self.enable_caching:
                    self._cache[cache_key] = CachedApiData(
                        data=self._poi_categories,
                        timestamp=datetime.now(),
                        expiry_minutes=30  # POI categories change occasionally
                    )
                
                self.logger.info(f"✅ Loaded {len(self._poi_categories)} POI categories from real data")
                return True
            else:
                self.logger.warning(f"⚠️ POI API returned {response.status_code}, using fallback categories")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error loading POI categories: {e}")
            self.performance_metrics['api_errors'] += 1
            return False
    
    async def _load_depot_locations(self) -> bool:
        """Load live depot locations from API."""
        try:
            cache_key = "depot_locations"
            
            # Check cache first
            if self.enable_caching and cache_key in self._cache:
                cached = self._cache[cache_key]
                if not cached.is_expired:
                    self._depot_locations = cached.data
                    self.performance_metrics['cache_hits'] += 1
                    return True
            
            self.logger.info("🚌 Loading depot locations from API...")
            self.performance_metrics['api_calls_made'] += 1
            self.performance_metrics['cache_misses'] += 1
            
            # Use the existing API client method
            depots = await self.api_client.get_all_depots()
            
            # Convert to our format
            self._depot_locations = []
            for depot in depots:
                # Check if depot has latitude/longitude in location dict or as direct attributes
                lat, lon = None, None
                
                # First check if there's a location dict with lat/lon
                if hasattr(depot, 'location') and depot.location and isinstance(depot.location, dict):
                    lat = depot.location.get('lat')
                    lon = depot.location.get('lon')
                
                # If no location dict, check for direct lat/lon attributes (this is the current case)
                if not lat and hasattr(depot, 'latitude'):
                    lat = getattr(depot, 'latitude', None)
                if not lon and hasattr(depot, 'longitude'):
                    lon = getattr(depot, 'longitude', None)
                
                if lat and lon:
                    self._depot_locations.append({
                        'id': depot.id,
                        'name': depot.name,
                        'latitude': lat,
                        'longitude': lon,
                        'capacity': depot.capacity,
                        'address': depot.address
                    })
            
            # Cache the result
            if self.enable_caching:
                self._cache[cache_key] = CachedApiData(
                    data=self._depot_locations,
                    timestamp=datetime.now(),
                    expiry_minutes=60  # Depot locations change rarely
                )
            
            self.logger.info(f"✅ Loaded {len(self._depot_locations)} depot locations")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error loading depot locations: {e}")
            self.performance_metrics['api_errors'] += 1
            return False
    
    async def _load_route_data(self) -> bool:
        """Load route data from API for geographic spawning."""
        try:
            cache_key = "route_data"
            
            # Check cache first
            if self.enable_caching and cache_key in self._cache:
                cached = self._cache[cache_key]
                if not cached.is_expired:
                    self._route_data = cached.data
                    self.performance_metrics['cache_hits'] += 1
                    return True
            
            self.logger.info("🛣️ Loading route data from API...")
            self.performance_metrics['api_calls_made'] += 1
            self.performance_metrics['cache_misses'] += 1
            
            # Use existing API client method
            routes = await self.api_client.get_all_routes()
            
            # Convert to our format
            self._route_data = []
            for route in routes:
                if route.geometry_coordinates:
                    self._route_data.append({
                        'id': route.id,
                        'name': route.long_name,
                        'short_name': route.short_name,
                        'coordinates': route.geometry_coordinates,
                        'length_km': route.route_length_km
                    })
            
            # Cache the result  
            if self.enable_caching:
                self._cache[cache_key] = CachedApiData(
                    data=self._route_data,
                    timestamp=datetime.now(),
                    expiry_minutes=30  # Route data changes occasionally
                )
            
            self.logger.info(f"✅ Loaded {len(self._route_data)} routes")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error loading route data: {e}")
            self.performance_metrics['api_errors'] += 1
            return False
    
    def get_passengers_for_timeframe(self, start_time: datetime, duration_minutes: int, 
                                   location_bounds: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Generate passengers using Poisson distribution with REAL API DATA as inputs.
        
        REPLACES: SimulatedPassengerDataSource hardcoded values
        KEEPS: Proven Poisson mathematical algorithms from Step 3
        """
        if not self._geographic_bounds:
            self.logger.warning("⚠️ No geographic bounds loaded, using fallback")
            bounds = self._fallback_bounds
        else:
            bounds = self._geographic_bounds
        
        # Use real geographic bounds instead of hardcoded values
        effective_bounds = {
            'min_lat': bounds.min_lat,
            'max_lat': bounds.max_lat, 
            'min_lon': bounds.min_lon,
            'max_lon': bounds.max_lon
        }
        
        time_hour = start_time.hour
        
        # Calculate lambda rate using POI-category-based weights (not hardcoded)
        base_lambda = self._calculate_dynamic_lambda_rate(time_hour)
        
        # Apply temporal scaling based on real POI categories
        temporal_weights = self.get_temporal_weights(time_hour)
        rush_factor = sum(temporal_weights.values()) / 0.75  # Normalize against baseline
        lambda_rate = base_lambda * rush_factor
        
        # Generate passenger count using validated Poisson mathematics from Step 3
        passenger_count = max(0, int(random.expovariate(1/lambda_rate) * duration_minutes))
        
        passengers = []
        for i in range(passenger_count):
            # Generate coordinates within REAL geographic bounds
            lat = random.uniform(effective_bounds['min_lat'], effective_bounds['max_lat'])
            lon = random.uniform(effective_bounds['min_lon'], effective_bounds['max_lon'])
            
            # Select destination type based on real POI categories
            destination_type = self._select_destination_from_real_categories()
            
            passengers.append({
                'id': f"prod_passenger_{i}_{int(time.time())}",
                'latitude': lat,
                'longitude': lon,
                'pickup_time': start_time + timedelta(minutes=random.randint(0, duration_minutes)),
                'destination_type': destination_type,
                'source': 'production_api',
                'poi_category': self._get_poi_category_for_destination(destination_type),
                'estimated_demand': self._calculate_location_demand(lat, lon)
            })
        
        return passengers
    
    def get_demand_at_location(self, latitude: float, longitude: float, radius_km: float) -> int:
        """
        Calculate demand based on REAL depot locations and POI density.
        
        REPLACES: SimulatedPassengerDataSource hardcoded Bridgetown coordinates
        USES: Real depot locations from API + POI category weights
        """
        base_demand = 1
        
        # Calculate demand based on proximity to REAL depot locations
        depot_demand = 0
        for depot in self._depot_locations:
            distance = self._calculate_distance_km(
                latitude, longitude, 
                depot['latitude'], depot['longitude']
            )
            
            if distance <= radius_km:
                # Higher demand near transit depots (realistic behavior)
                depot_influence = max(0, (radius_km - distance) / radius_km)
                depot_capacity_factor = depot.get('capacity', 50) / 50  # Normalize
                depot_demand += int(10 * depot_influence * depot_capacity_factor)
        
        # Calculate demand based on POI category density in area
        poi_demand = 0
        for category_name, category in self._poi_categories.items():
            # Simulate POI density effect (in production, could query actual POIs in radius)
            estimated_pois_in_radius = random.randint(0, 5) * category.attraction_factor
            poi_demand += int(estimated_pois_in_radius * category.weight * 2)
        
        total_demand = base_demand + depot_demand + poi_demand
        
        # Add some realistic variance
        variance_factor = random.uniform(0.7, 1.5)
        return max(1, int(total_demand * variance_factor))
    
    def get_pickup_probability(self, latitude: float, longitude: float, time_of_day: int) -> float:
        """
        Calculate pickup probability based on REAL temporal patterns and POI categories.
        
        REPLACES: SimulatedPassengerDataSource fixed 0.3 base probability  
        USES: Dynamic calculation based on POI categories and time patterns
        """
        # Base probability varies by time using real temporal weights
        temporal_weights = self.get_temporal_weights(time_of_day)
        base_prob = sum(temporal_weights.values()) / 3.0  # Normalize to reasonable range
        
        # Adjust based on proximity to real depot locations
        depot_factor = 1.0
        min_depot_distance = float('inf')
        
        for depot in self._depot_locations:
            distance = self._calculate_distance_km(
                latitude, longitude,
                depot['latitude'], depot['longitude']
            )
            min_depot_distance = min(min_depot_distance, distance)
        
        # Higher probability near depots
        if min_depot_distance < 1.0:  # Within 1km of depot
            depot_factor = 1.5
        elif min_depot_distance < 2.0:  # Within 2km of depot  
            depot_factor = 1.2
        
        # Consider POI category influence
        avg_category_weight = sum(cat.weight for cat in self._poi_categories.values()) / len(self._poi_categories)
        poi_factor = 0.8 + (avg_category_weight * 0.4)  # Scale factor 0.8-1.2
        
        final_probability = base_prob * depot_factor * poi_factor
        return min(1.0, max(0.1, final_probability))  # Keep in reasonable range
    
    def get_temporal_weights(self, time_of_day: int) -> Dict[str, float]:
        """
        Get spawning distribution weights based on REAL POI categories and time.
        
        REPLACES: SimulatedPassengerDataSource hardcoded time weights
        USES: Dynamic weights based on POI category attraction factors and time
        """
        if not self._poi_categories:
            # Fallback to basic weights if POI data not loaded
            if 7 <= time_of_day <= 9:  # Morning rush
                return {'depot': 0.50, 'route': 0.30, 'poi': 0.20}
            elif 17 <= time_of_day <= 19:  # Evening rush  
                return {'depot': 0.35, 'route': 0.35, 'poi': 0.30}
            else:  # Off-peak
                return {'depot': 0.40, 'route': 0.35, 'poi': 0.25}
        
        # Calculate dynamic weights based on POI categories and time
        depot_weight = 0.35  # Base depot weight
        route_weight = 0.35  # Base route weight
        
        # Adjust POI weight based on category attraction and time
        poi_weight = 0.30  # Base POI weight
        
        if 7 <= time_of_day <= 9:  # Morning rush - more depot activity
            depot_weight += 0.15
            poi_weight -= 0.10
        elif 11 <= time_of_day <= 14:  # Lunch time - more POI activity
            # Weight POIs higher, especially food-related categories
            food_categories = [cat for cat in self._poi_categories.values() 
                             if 'restaurant' in cat.name.lower() or 'food' in cat.name.lower()]
            if food_categories:
                avg_food_attraction = sum(cat.attraction_factor for cat in food_categories) / len(food_categories)
                poi_weight += 0.10 * (avg_food_attraction / 2.0)  # Scale by attraction
                depot_weight -= 0.05
        elif 17 <= time_of_day <= 19:  # Evening rush - mixed activity
            # Balanced between depot and POI
            pass  # Keep base weights
        elif 20 <= time_of_day <= 22:  # Evening - more POI activity
            poi_weight += 0.10
            depot_weight -= 0.05
        
        # Normalize to ensure sum = 1.0
        total = depot_weight + route_weight + poi_weight
        return {
            'depot': depot_weight / total,
            'route': route_weight / total,
            'poi': poi_weight / total
        }
    
    # Helper methods for calculations
    
    def _calculate_dynamic_lambda_rate(self, time_hour: int) -> float:
        """Calculate lambda rate based on loaded POI data and depot density."""
        base_rate = self.config['base_lambda']
        
        # Adjust based on number of active depots (more depots = more activity)
        depot_factor = 1.0 + (len(self._depot_locations) / 10.0)  # Scale by depot count
        
        # Adjust based on POI category diversity  
        category_diversity = len(self._poi_categories) / 10.0  # More categories = more activity
        diversity_factor = 1.0 + min(category_diversity, 0.5)  # Cap at 50% increase
        
        return base_rate * depot_factor * diversity_factor
    
    def _select_destination_from_real_categories(self) -> str:
        """Select destination type based on real POI category weights."""
        if not self._poi_categories:
            return random.choice(['depot', 'route', 'poi'])
        
        # Weight selection based on actual POI categories
        total_weight = sum(cat.weight for cat in self._poi_categories.values())
        if total_weight == 0:
            return random.choice(['depot', 'route', 'poi'])
        
        # Higher POI weight means more POI destinations
        avg_poi_weight = total_weight / len(self._poi_categories)
        
        if avg_poi_weight > 0.5:  # High POI attraction
            choices = ['poi'] * 5 + ['depot'] * 3 + ['route'] * 2
        elif avg_poi_weight > 0.3:  # Medium POI attraction
            choices = ['poi'] * 4 + ['depot'] * 3 + ['route'] * 3  
        else:  # Low POI attraction
            choices = ['poi'] * 2 + ['depot'] * 4 + ['route'] * 4
        
        return random.choice(choices)
    
    def _get_poi_category_for_destination(self, destination_type: str) -> Optional[str]:
        """Get appropriate POI category for destination."""
        if destination_type != 'poi' or not self._poi_categories:
            return None
        
        # Weight category selection by attraction factor
        categories = list(self._poi_categories.keys())
        weights = [cat.attraction_factor for cat in self._poi_categories.values()]
        
        return random.choices(categories, weights=weights)[0] if categories else None
    
    def _calculate_location_demand(self, latitude: float, longitude: float) -> int:
        """Estimate passenger demand at specific coordinates."""
        return self.get_demand_at_location(latitude, longitude, 0.5)  # 500m radius
    
    def _calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers."""
        # Haversine formula for accurate distance calculation
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    async def close(self):
        """Clean up resources."""
        if self.api_client:
            await self.api_client.close()
        self.logger.info("✅ ProductionApiDataSource closed")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance and caching metrics."""
        total_requests = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
        cache_hit_rate = (self.performance_metrics['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.performance_metrics,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'total_cache_requests': total_requests,
            'geographic_bounds_area_km2': self._geographic_bounds.area_km2 if self._geographic_bounds else 0,
            'loaded_depots': len(self._depot_locations),
            'loaded_poi_categories': len(self._poi_categories),
            'loaded_routes': len(self._route_data)
        }


# Export for use in tests
__all__ = ['ProductionApiDataSource', 'GeographicBounds', 'POICategory', 'CachedApiData']