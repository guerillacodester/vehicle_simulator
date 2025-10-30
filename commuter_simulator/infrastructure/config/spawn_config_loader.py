"""
Spawn Configuration Loader
---------------------------
Loads and caches spawn-config data from the Fleet API for data-driven commuter spawning.

The spawn-config content type stores:
- Building weights (residential, commercial, office, etc.)
- POI weights (bus_station, marketplace, hospital, etc.)
- Landuse weights (residential, commercial, industrial, etc.)
- Hourly spawn rates (24-hour patterns: 0.1-2.8 multipliers)
- Day-of-week multipliers (weekday vs weekend patterns)
- Distribution parameters (Poisson lambda, spawn radius, max spawns)

Mental Model:
    final_spawn_probability = weight × peak_multiplier × hourly_rate × day_multiplier

Usage:
    loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    config = await loader.get_config_by_country("Barbados")
    
    # Get current hourly rate based on simulation time
    hourly_rate = loader.get_hourly_rate(config, current_hour=8)  # 2.8x for morning peak
    
    # Get building weight by type
    building_weight = loader.get_building_weight(config, "residential")  # e.g., 3.5
    
    # Get POI weight by type
    poi_weight = loader.get_poi_weight(config, "bus_station")  # e.g., 5.0
    
    # Get day multiplier
    day_mult = loader.get_day_multiplier(config, "monday")  # 1.0 for weekdays
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SpawnConfigLoader:
    """
    Loads spawn configuration from Fleet API and caches it for efficient access.
    
    Spawn configs are cached for 1 hour by default to reduce API calls while
    allowing updates to propagate reasonably quickly.
    """
    
    def __init__(
        self, 
        api_base_url: str = "http://localhost:1337/api",
        cache_ttl_seconds: int = 3600,  # 1 hour default
        timeout_seconds: float = 10.0
    ):
        """
        Initialize the spawn config loader.
        
        Args:
            api_base_url: Base URL for the Fleet API (default: localhost:1337)
            cache_ttl_seconds: Cache time-to-live in seconds (default: 3600 = 1 hour)
            timeout_seconds: HTTP request timeout (default: 10 seconds)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.timeout = timeout_seconds
        
        # Cache: {country_name: (config_data, timestamp)}
        self._cache: Dict[str, tuple[Dict[str, Any], datetime]] = {}
        
        logger.info(
            f"SpawnConfigLoader initialized | API: {self.api_base_url} | "
            f"Cache TTL: {cache_ttl_seconds}s"
        )
    
    async def get_config_by_country(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        Get spawn configuration for a specific country.
        
        First checks cache. If cache is expired or missing, fetches from API
        and caches the result.
        
        Args:
            country_name: Name of the country (e.g., "Barbados")
            
        Returns:
            Spawn config dictionary with all components, or None if not found
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Check cache first
        if country_name in self._cache:
            config, timestamp = self._cache[country_name]
            age = datetime.now() - timestamp
            
            if age < self.cache_ttl:
                logger.debug(f"Cache HIT for {country_name} (age: {age.total_seconds():.1f}s)")
                return config
            else:
                logger.debug(f"Cache EXPIRED for {country_name} (age: {age.total_seconds():.1f}s)")
        
        # Cache miss or expired - fetch from API
        logger.info(f"Fetching spawn config for country: {country_name}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Query spawn-config filtered by country name with full population
            # API endpoint: GET /api/spawn-configs?filters[country][name][$eq]=Barbados&populate=*
            url = f"{self.api_base_url}/spawn-configs"
            params = {
                "filters[country][name][$eq]": country_name,
                "populate": "*"  # Populate all components + country relation
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract first result (should be only one due to oneToOne country relationship)
            if not data.get("data") or len(data["data"]) == 0:
                logger.warning(f"No spawn config found for country: {country_name}")
                return None
            
            config = data["data"][0]
            
            # Validate required fields
            if not self._validate_config(config):
                logger.error(f"Invalid spawn config structure for {country_name}")
                return None
            
            # Cache the result
            self._cache[country_name] = (config, datetime.now())
            logger.info(
                f"Loaded spawn config for {country_name} | "
                f"Buildings: {len(config.get('building_weights', []))} | "
                f"POIs: {len(config.get('poi_weights', []))} | "
                f"Landuse: {len(config.get('landuse_weights', []))}"
            )
            
            return config
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate that config has required structure.
        
        Args:
            config: Config dictionary from API
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "building_weights",
            "poi_weights", 
            "landuse_weights",
            "hourly_spawn_rates",
            "day_multipliers",
            "distribution_params"
        ]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate we have 24 hourly rates
        if len(config.get("hourly_spawn_rates", [])) != 24:
            logger.error(
                f"Expected 24 hourly_spawn_rates, got {len(config.get('hourly_spawn_rates', []))}"
            )
            return False
        
        # Validate we have 7 day multipliers
        if len(config.get("day_multipliers", [])) != 7:
            logger.error(
                f"Expected 7 day_multipliers, got {len(config.get('day_multipliers', []))}"
            )
            return False
        
        return True
    
    def get_hourly_rate(
        self, 
        config: Dict[str, Any], 
        current_hour: int
    ) -> float:
        """
        Get the spawn rate multiplier for a specific hour.
        
        Args:
            config: Spawn config from get_config_by_country()
            current_hour: Hour of day (0-23)
            
        Returns:
            Hourly spawn rate multiplier (e.g., 2.8 for morning peak)
            
        Raises:
            ValueError: If hour is out of range or config is invalid
        """
        if not 0 <= current_hour <= 23:
            raise ValueError(f"Hour must be 0-23, got {current_hour}")
        
        hourly_rates = config.get("hourly_spawn_rates", [])
        if len(hourly_rates) != 24:
            raise ValueError(f"Invalid config: expected 24 hourly rates, got {len(hourly_rates)}")
        
        # Find the pattern for this hour
        # hourly_rates is a list of dicts: [{hour: 0, spawn_rate: 0.2, ...}, ...]
        for pattern in hourly_rates:
            if pattern.get("hour") == current_hour:
                rate = pattern.get("spawn_rate", 1.0)
                logger.debug(f"Hourly rate for hour {current_hour}: {rate}")
                return rate
        
        # Fallback if hour not found (shouldn't happen with valid config)
        logger.warning(f"Hour {current_hour} not found in config, defaulting to 1.0")
        return 1.0
    
    def get_building_weight(
        self, 
        config: Dict[str, Any], 
        building_type: str,
        apply_peak_multiplier: bool = True
    ) -> float:
        """
        Get the spawn weight for a specific building type.
        
        Args:
            config: Spawn config from get_config_by_country()
            building_type: OSM building type (e.g., "residential", "commercial")
            apply_peak_multiplier: If True, multiply weight by peak_multiplier
            
        Returns:
            Building weight (e.g., 3.5), or 0 if type not found or inactive
        """
        building_weights = config.get("building_weights", [])
        
        for bw in building_weights:
            if bw.get("building_type") == building_type and bw.get("is_active", False):
                base_weight = bw.get("weight", 1.0)
                
                if apply_peak_multiplier:
                    peak_mult = bw.get("peak_multiplier", 1.0)
                    final_weight = base_weight * peak_mult
                    logger.debug(
                        f"Building '{building_type}': weight={base_weight} × "
                        f"peak={peak_mult} = {final_weight}"
                    )
                    return final_weight
                else:
                    return base_weight
        
        # Type not found or inactive
        logger.debug(f"Building type '{building_type}' not found or inactive, weight=0")
        return 0.0
    
    def get_poi_weight(
        self, 
        config: Dict[str, Any], 
        poi_type: str,
        apply_peak_multiplier: bool = True
    ) -> float:
        """
        Get the spawn weight for a specific POI type.
        
        Args:
            config: Spawn config from get_config_by_country()
            poi_type: OSM POI type (e.g., "bus_station", "marketplace")
            apply_peak_multiplier: If True, multiply weight by peak_multiplier
            
        Returns:
            POI weight (e.g., 5.0), or 0 if type not found or inactive
        """
        poi_weights = config.get("poi_weights", [])
        
        for pw in poi_weights:
            if pw.get("poi_type") == poi_type and pw.get("is_active", False):
                base_weight = pw.get("weight", 1.0)
                
                if apply_peak_multiplier:
                    peak_mult = pw.get("peak_multiplier", 1.0)
                    final_weight = base_weight * peak_mult
                    logger.debug(
                        f"POI '{poi_type}': weight={base_weight} × "
                        f"peak={peak_mult} = {final_weight}"
                    )
                    return final_weight
                else:
                    return base_weight
        
        # Type not found or inactive
        logger.debug(f"POI type '{poi_type}' not found or inactive, weight=0")
        return 0.0
    
    def get_landuse_weight(
        self, 
        config: Dict[str, Any], 
        landuse_type: str,
        apply_peak_multiplier: bool = True
    ) -> float:
        """
        Get the spawn weight for a specific landuse type.
        
        Args:
            config: Spawn config from get_config_by_country()
            landuse_type: OSM landuse type (e.g., "residential", "commercial")
            apply_peak_multiplier: If True, multiply weight by peak_multiplier
            
        Returns:
            Landuse weight (e.g., 2.0), or 0 if type not found or inactive
        """
        landuse_weights = config.get("landuse_weights", [])
        
        for lw in landuse_weights:
            if lw.get("landuse_type") == landuse_type and lw.get("is_active", False):
                base_weight = lw.get("weight", 1.0)
                
                if apply_peak_multiplier:
                    peak_mult = lw.get("peak_multiplier", 1.0)
                    final_weight = base_weight * peak_mult
                    logger.debug(
                        f"Landuse '{landuse_type}': weight={base_weight} × "
                        f"peak={peak_mult} = {final_weight}"
                    )
                    return final_weight
                else:
                    return base_weight
        
        # Type not found or inactive
        logger.debug(f"Landuse type '{landuse_type}' not found or inactive, weight=0")
        return 0.0
    
    def get_day_multiplier(
        self, 
        config: Dict[str, Any], 
        day_of_week: str
    ) -> float:
        """
        Get the day-of-week multiplier.
        
        Args:
            config: Spawn config from get_config_by_country()
            day_of_week: Day name (lowercase: "monday", "tuesday", etc.)
            
        Returns:
            Day multiplier (e.g., 1.0 for weekdays, 0.7 for Saturday, 0.5 for Sunday)
        """
        day_multipliers = config.get("day_multipliers", [])
        
        for dm in day_multipliers:
            if dm.get("day_of_week", "").lower() == day_of_week.lower():
                multiplier = dm.get("multiplier", 1.0)
                logger.debug(f"Day multiplier for {day_of_week}: {multiplier}")
                return multiplier
        
        # Fallback if day not found
        logger.warning(f"Day '{day_of_week}' not found in config, defaulting to 1.0")
        return 1.0
    
    def get_distribution_params(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get ALL distribution parameters for spawning (database is source of truth).
        
        Args:
            config: Spawn config from get_config_by_country()
            
        Returns:
            Dictionary with ALL spawn configuration keys:
                - passengers_per_building_per_hour: Spatial density factor (e.g., 0.3)
                - spawn_radius_meters: Search radius for buildings (e.g., 800)
                - min_trip_distance_meters: Minimum trip distance (e.g., 250)
                - trip_distance_mean_meters: Mean of trip distance normal dist (e.g., 2000)
                - trip_distance_std_meters: Std dev of trip distance dist (e.g., 1000)
                - max_trip_distance_ratio: Max trip as ratio of remaining route (e.g., 0.95)
                - min_spawn_interval_seconds: Minimum time between spawns (e.g., 45)
        """
        dist_params_list = config.get("distribution_params", [])
        
        if not dist_params_list or len(dist_params_list) == 0:
            logger.error("CRITICAL: No distribution_params found in spawn config - using emergency defaults")
            return {
                "passengers_per_building_per_hour": 0.3,
                "spawn_radius_meters": 800,
                "min_trip_distance_meters": 250,
                "trip_distance_mean_meters": 2000,
                "trip_distance_std_meters": 1000,
                "max_trip_distance_ratio": 0.95,
                "min_spawn_interval_seconds": 45
            }
        
        # Take first entry (should be only one due to max:1 constraint)
        params = dist_params_list[0]
        
        # Extract all parameters from database (NO hardcoded values in code)
        return {
            "passengers_per_building_per_hour": params.get("passengers_per_building_per_hour"),
            "spawn_radius_meters": params.get("spawn_radius_meters"),
            "min_trip_distance_meters": params.get("min_trip_distance_meters"),
            "trip_distance_mean_meters": params.get("trip_distance_mean_meters"),
            "trip_distance_std_meters": params.get("trip_distance_std_meters"),
            "max_trip_distance_ratio": params.get("max_trip_distance_ratio"),
            "min_spawn_interval_seconds": params.get("min_spawn_interval_seconds")
        }
    
    def calculate_spawn_probability(
        self,
        config: Dict[str, Any],
        feature_weight: float,
        current_hour: int,
        day_of_week: str
    ) -> float:
        """
        Calculate final spawn probability using the mental model:
        
            final_spawn_probability = weight × hourly_rate × day_multiplier
        
        Note: peak_multiplier is already applied in get_*_weight() methods.
        
        Args:
            config: Spawn config from get_config_by_country()
            feature_weight: Already-calculated feature weight (building/POI/landuse)
            current_hour: Hour of day (0-23)
            day_of_week: Day name (lowercase)
            
        Returns:
            Final spawn probability multiplier (e.g., 7.84 = 2.8 × 2.8 × 1.0)
        """
        hourly_rate = self.get_hourly_rate(config, current_hour)
        day_mult = self.get_day_multiplier(config, day_of_week)
        
        final_prob = feature_weight * hourly_rate * day_mult
        
        logger.debug(
            f"Spawn probability: {feature_weight} × {hourly_rate} × {day_mult} = {final_prob}"
        )
        
        return final_prob
    
    def clear_cache(self, country_name: Optional[str] = None):
        """
        Clear cached spawn configs.
        
        Args:
            country_name: If provided, clear only this country's cache.
                         If None, clear entire cache.
        """
        if country_name:
            if country_name in self._cache:
                del self._cache[country_name]
                logger.info(f"Cleared cache for {country_name}")
        else:
            self._cache.clear()
            logger.info("Cleared entire spawn config cache")


# Example usage
async def example_usage():
    """Example of how to use SpawnConfigLoader"""
    
    loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    
    # Load config for Barbados
    config = await loader.get_config_by_country("Barbados")
    
    if not config:
        print("Config not found!")
        return
    
    print(f"\n=== Spawn Config: {config.get('name')} ===")
    print(f"Description: {config.get('description')}")
    print(f"Active: {config.get('is_active')}")
    
    # Get distribution params
    dist_params = loader.get_distribution_params(config)
    print(f"\nPoisson Lambda: {dist_params['poisson_lambda']}")
    print(f"Max Spawns/Cycle: {dist_params['max_spawns_per_cycle']}")
    print(f"Spawn Radius: {dist_params['spawn_radius_meters']}m")
    
    # Example: Morning rush hour on Monday
    current_hour = 8  # 8 AM
    day = "monday"
    
    # Get hourly rate
    hourly_rate = loader.get_hourly_rate(config, current_hour)
    print(f"\nHourly rate at {current_hour}:00 = {hourly_rate}")
    
    # Get day multiplier
    day_mult = loader.get_day_multiplier(config, day)
    print(f"Day multiplier for {day} = {day_mult}")
    
    # Get building weights
    print("\n=== Building Weights (with peak multipliers) ===")
    for btype in ["residential", "commercial", "office", "school"]:
        weight = loader.get_building_weight(config, btype, apply_peak_multiplier=True)
        if weight > 0:
            print(f"{btype}: {weight}")
    
    # Calculate final spawn probability for residential building
    residential_weight = loader.get_building_weight(config, "residential")
    final_prob = loader.calculate_spawn_probability(
        config, residential_weight, current_hour, day
    )
    print(f"\nFinal spawn probability (residential, Mon 8am): {final_prob}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
