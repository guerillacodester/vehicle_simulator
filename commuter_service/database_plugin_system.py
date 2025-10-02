"""
Database-First Passenger Plugin System
=====================================

API-driven plugin system that reads country configurations from Strapi database
instead of file-based plugins. This allows users to modify passenger behavior
through the admin interface without touching code files.

Architecture:
- Countries: Loaded from /api/countries endpoint
- Plugin Configs: Stored as Strapi content types (passenger-plugin-configs)
- Cultural Models: API-configurable behavioral patterns
- GeoJSON Data: Uploadable via Strapi media library
- Real-time Updates: Changes via API affect simulation immediately
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
import json

class DatabaseCountryPlugin:
    """Database-driven country plugin that reads config from Strapi API"""
    
    def __init__(self, strapi_base_url: str = "http://localhost:1337"):
        self.strapi_url = strapi_base_url
        self.country_data: Dict[str, Any] = {}
        self.plugin_config: Dict[str, Any] = {}
        self.cultural_patterns: Dict[str, Any] = {}
        self.country_code: str = ""
        self.country_name: str = ""
        
    async def load_country_plugin(self, country_code: str) -> bool:
        """
        Load country plugin configuration from Strapi database
        
        Args:
            country_code: Country code (e.g., 'BB', 'JM', 'TT')
            
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                # Load country basic info
                country_info = await self._load_country_info(client, country_code)
                if not country_info:
                    return False
                
                # Load plugin configuration
                plugin_config = await self._load_plugin_config(client, country_code)
                if not plugin_config:
                    # Create default config if none exists
                    plugin_config = await self._create_default_plugin_config(client, country_code)
                
                # Load cultural patterns
                cultural_patterns = await self._load_cultural_patterns(client, country_code)
                if not cultural_patterns:
                    # Create default cultural patterns if none exist
                    cultural_patterns = await self._create_default_cultural_patterns(client, country_code)
                
                # Store loaded data
                self.country_data = country_info
                self.plugin_config = plugin_config
                self.cultural_patterns = cultural_patterns
                self.country_code = country_code
                self.country_name = country_info.get('name', country_code)
                
                logging.info(f"✅ Loaded database plugin for {self.country_name} ({country_code})")
                return True
                
        except Exception as e:
            logging.error(f"❌ Failed to load country plugin {country_code}: {e}")
            return False
    
    async def _load_country_info(self, client: httpx.AsyncClient, country_code: str) -> Optional[Dict]:
        """Load basic country information from countries table"""
        try:
            response = await client.get(
                f"{self.strapi_url}/api/countries",
                params={"filters[code][$eq]": country_code}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                country = data['data'][0]
                return {
                    'id': country['id'],
                    'country_id': country['country_id'],
                    'name': country['name'],
                    'code': country['code'],
                    'currency': country.get('currency'),
                    'timezone': country.get('timezone'),
                    'is_active': country.get('is_active', True)
                }
            return None
            
        except Exception as e:
            logging.error(f"Failed to load country info for {country_code}: {e}")
            return None
    
    async def _load_plugin_config(self, client: httpx.AsyncClient, country_code: str) -> Optional[Dict]:
        """Load plugin configuration from passenger-plugin-configs table"""
        try:
            response = await client.get(
                f"{self.strapi_url}/api/passenger-plugin-configs",
                params={"filters[country_code][$eq]": country_code}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                config = data['data'][0]
                return {
                    'id': config['id'],
                    'country_code': config['country_code'],
                    'base_spawn_rate': config.get('base_spawn_rate', 0.15),
                    'rush_hour_multiplier': config.get('rush_hour_multiplier', 2.5),
                    'off_peak_multiplier': config.get('off_peak_multiplier', 0.8),
                    'weekend_multiplier': config.get('weekend_multiplier', 0.4),
                    'walking_distance_meters': config.get('walking_distance_meters', 80),
                    'generation_interval_seconds': config.get('generation_interval_seconds', 60),
                    'passenger_demand_multiplier': config.get('passenger_demand_multiplier', 1.0),
                    'trip_purposes': config.get('trip_purposes', {}),
                    'time_patterns': config.get('time_patterns', {}),
                    'is_enabled': config.get('is_enabled', True)
                }
            return None
            
        except Exception as e:
            logging.error(f"Failed to load plugin config for {country_code}: {e}")
            return None
    
    async def _load_cultural_patterns(self, client: httpx.AsyncClient, country_code: str) -> Optional[Dict]:
        """Load cultural patterns from passenger-cultural-patterns table"""
        try:
            response = await client.get(
                f"{self.strapi_url}/api/passenger-cultural-patterns",
                params={"filters[country_code][$eq]": country_code}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                patterns = data['data'][0]
                return {
                    'id': patterns['id'],
                    'country_code': patterns['country_code'],
                    'work_patterns': patterns.get('work_patterns', {}),
                    'social_patterns': patterns.get('social_patterns', {}),
                    'cultural_events': patterns.get('cultural_events', {}),
                    'location_modifiers': patterns.get('location_modifiers', {}),
                    'time_modifiers': patterns.get('time_modifiers', {}),
                    'is_active': patterns.get('is_active', True)
                }
            return None
            
        except Exception as e:
            logging.error(f"Failed to load cultural patterns for {country_code}: {e}")
            return None
    
    async def _create_default_plugin_config(self, client: httpx.AsyncClient, country_code: str) -> Dict:
        """Create default plugin configuration for country"""
        default_config = {
            'country_code': country_code,
            'base_spawn_rate': 0.15,
            'rush_hour_multiplier': 2.5,
            'off_peak_multiplier': 0.8,
            'weekend_multiplier': 0.4,
            'walking_distance_meters': 80,
            'generation_interval_seconds': 60,
            'passenger_demand_multiplier': 1.0,
            'trip_purposes': {
                'work': 0.35,
                'school': 0.15,
                'shopping': 0.20,
                'medical': 0.08,
                'recreation': 0.12,
                'social': 0.10
            },
            'time_patterns': {
                'morning_rush_start': '06:30',
                'morning_rush_end': '09:00',
                'evening_rush_start': '16:00',
                'evening_rush_end': '18:30',
                'work_start': '08:00',
                'work_end': '17:00'
            },
            'is_enabled': True
        }
        
        try:
            response = await client.post(
                f"{self.strapi_url}/api/passenger-plugin-configs",
                json={"data": default_config}
            )
            response.raise_for_status()
            created = response.json()
            logging.info(f"✅ Created default plugin config for {country_code}")
            return created.get('data', default_config)
            
        except Exception as e:
            logging.warning(f"Failed to create default plugin config for {country_code}: {e}")
            return default_config
    
    async def _create_default_cultural_patterns(self, client: httpx.AsyncClient, country_code: str) -> Dict:
        """Create default cultural patterns for country"""
        default_patterns = {
            'country_code': country_code,
            'work_patterns': {
                'standard_start': '08:00',
                'standard_end': '17:00',
                'lunch_time': '12:00',
                'lunch_duration': 60  # minutes
            },
            'social_patterns': {
                'church_time_sunday': '09:00',
                'market_day_saturday': '08:00',
                'beach_weekend_peak': '14:00',
                'after_work_socializing': '17:30'
            },
            'cultural_events': {
                # Default empty - to be configured by users
            },
            'location_modifiers': {
                'residential': {'morning': 2.0, 'evening': 1.8, 'midday': 0.8},
                'commercial': {'morning': 1.2, 'evening': 1.5, 'midday': 1.8},
                'business': {'morning': 2.5, 'evening': 2.0, 'midday': 1.2},
                'tourist': {'morning': 1.4, 'evening': 1.8, 'midday': 1.6}
            },
            'time_modifiers': {
                'rush_hour_peak': 2.5,
                'lunch_peak': 1.8,
                'evening_social': 1.2,
                'night_minimal': 0.3,
                'weekend_leisure': 1.5
            },
            'is_active': True
        }
        
        try:
            response = await client.post(
                f"{self.strapi_url}/api/passenger-cultural-patterns",
                json={"data": default_patterns}
            )
            response.raise_for_status()
            created = response.json()
            logging.info(f"✅ Created default cultural patterns for {country_code}")
            return created.get('data', default_patterns)
            
        except Exception as e:
            logging.warning(f"Failed to create default cultural patterns for {country_code}: {e}")
            return default_patterns
    
    def get_spawn_rate_modifier(self, current_time: datetime, location_type: str = "general") -> float:
        """Calculate spawn rate modifier based on database-stored patterns"""
        if not self.cultural_patterns:
            return 1.0
        
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # Get time-based modifier
        time_modifiers = self.cultural_patterns.get('time_modifiers', {})
        
        # Morning rush (6:30-9:00)
        if 6.5 <= hour + current_time.minute/60.0 <= 9.0:
            base_modifier = time_modifiers.get('rush_hour_peak', 2.5)
        # Lunch time (12:00-13:00)
        elif 12 <= hour <= 13:
            base_modifier = time_modifiers.get('lunch_peak', 1.8)
        # Evening rush (16:00-18:30)
        elif 16 <= hour <= 18.5:
            base_modifier = time_modifiers.get('rush_hour_peak', 2.5) * 0.8  # Slightly lower than morning
        # Evening social (18:30-22:00)
        elif 18.5 <= hour <= 22:
            base_modifier = time_modifiers.get('evening_social', 1.2)
        # Night minimal (22:00-6:30)
        elif hour >= 22 or hour <= 6.5:
            base_modifier = time_modifiers.get('night_minimal', 0.3)
        else:
            base_modifier = 1.0
        
        # Apply weekend modifier
        if weekday >= 5:  # Weekend
            base_modifier *= self.plugin_config.get('weekend_multiplier', 0.4)
        
        # Apply location-specific modifier
        location_modifiers = self.cultural_patterns.get('location_modifiers', {})
        location_modifier = 1.0
        
        if location_type in location_modifiers:
            time_of_day = 'morning' if 6 <= hour <= 12 else 'evening' if 16 <= hour <= 20 else 'midday'
            location_modifier = location_modifiers[location_type].get(time_of_day, 1.0)
        
        return base_modifier * location_modifier
    
    def get_trip_purpose_distribution(self, current_time: datetime, origin_type: str) -> Dict[str, float]:
        """Get trip purpose distribution from database configuration"""
        base_purposes = self.plugin_config.get('trip_purposes', {
            'work': 0.35,
            'school': 0.15,
            'shopping': 0.20,
            'medical': 0.08,
            'recreation': 0.12,
            'social': 0.10
        })
        
        # Adjust based on time of day
        hour = current_time.hour
        weekday = current_time.weekday()
        
        if weekday < 5:  # Weekdays
            if 6 <= hour <= 9:  # Morning rush
                base_purposes = {
                    'work': 0.60,
                    'school': 0.25,
                    'shopping': 0.05,
                    'medical': 0.03,
                    'recreation': 0.02,
                    'social': 0.05
                }
            elif 15 <= hour <= 17:  # School ending
                base_purposes = {
                    'work': 0.20,
                    'school': 0.40,
                    'shopping': 0.15,
                    'medical': 0.10,
                    'recreation': 0.10,
                    'social': 0.05
                }
        else:  # Weekends
            base_purposes = {
                'work': 0.10,
                'school': 0.02,
                'shopping': 0.35,
                'medical': 0.08,
                'recreation': 0.30,
                'social': 0.15
            }
        
        return base_purposes
    
    def get_cultural_metadata(self) -> Dict[str, Any]:
        """Return cultural metadata from database"""
        return {
            'country_code': self.country_code,
            'country_name': self.country_name,
            'country_data': self.country_data,
            'plugin_config': self.plugin_config,
            'cultural_patterns': self.cultural_patterns,
            'timezone': self.country_data.get('timezone'),
            'currency': self.country_data.get('currency'),
            'is_active': self.country_data.get('is_active'),
            'api_driven': True
        }


class DatabasePluginManager:
    """Manages database-driven country plugins"""
    
    def __init__(self, strapi_base_url: str = "http://localhost:1337"):
        self.strapi_url = strapi_base_url
        self.current_plugin: Optional[DatabaseCountryPlugin] = None
        self.current_country: Optional[str] = None
        self.available_countries_cache: Dict[str, str] = {}
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl_minutes = 5  # Cache for 5 minutes
    
    async def get_available_countries(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get available countries from Strapi database with caching"""
        now = datetime.now()
        
        # Use cache if available and not expired
        if (not force_refresh and self.available_countries_cache and 
            self.cache_timestamp and 
            (now - self.cache_timestamp).total_seconds() < self.cache_ttl_minutes * 60):
            return self.available_countries_cache
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.strapi_url}/api/countries",
                    params={"filters[is_active][$eq]": True, "pagination[pageSize]": 100}
                )
                response.raise_for_status()
                data = response.json()
                
                countries = {}
                for country in data.get('data', []):
                    code = country.get('code')
                    name = country.get('name')
                    if code and name:
                        countries[code.lower()] = name
                
                # Update cache
                self.available_countries_cache = countries
                self.cache_timestamp = now
                
                logging.info(f"✅ Loaded {len(countries)} countries from database")
                return countries
                
        except Exception as e:
            logging.error(f"❌ Failed to load countries from database: {e}")
            return self.available_countries_cache  # Return cached version if available
    
    async def set_country(self, country_code: str) -> bool:
        """Set the active country plugin"""
        try:
            plugin = DatabaseCountryPlugin(self.strapi_url)
            success = await plugin.load_country_plugin(country_code.upper())
            
            if success:
                self.current_plugin = plugin
                self.current_country = country_code.upper()
                logging.info(f"✅ Set active country to: {country_code}")
                return True
            else:
                logging.error(f"❌ Failed to set country to: {country_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error setting country {country_code}: {e}")
            return False
    
    def get_current_plugin(self) -> Optional[DatabaseCountryPlugin]:
        """Get the currently active plugin"""
        return self.current_plugin
    
    def get_spawn_rate_modifier(self, current_time: datetime, location_type: str = "general") -> float:
        """Get spawn rate modifier from current plugin"""
        if self.current_plugin:
            return self.current_plugin.get_spawn_rate_modifier(current_time, location_type)
        return 1.0
    
    def get_trip_purpose_distribution(self, current_time: datetime, origin_type: str) -> Dict[str, float]:
        """Get trip purpose distribution from current plugin"""
        if self.current_plugin:
            return self.current_plugin.get_trip_purpose_distribution(current_time, origin_type)
        
        # Default fallback
        return {
            'work': 0.40,
            'school': 0.15,
            'shopping': 0.20,
            'medical': 0.10,
            'recreation': 0.10,
            'social': 0.05
        }


# Global database plugin manager
_db_plugin_manager: Optional[DatabasePluginManager] = None

async def get_database_plugin_manager(strapi_url: str = "http://localhost:1337") -> DatabasePluginManager:
    """Get global database plugin manager instance"""
    global _db_plugin_manager
    if _db_plugin_manager is None:
        _db_plugin_manager = DatabasePluginManager(strapi_url)
    return _db_plugin_manager