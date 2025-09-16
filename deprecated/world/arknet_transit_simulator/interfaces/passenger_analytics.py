#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passenger Analytics Plugin Interface

Defines the interface for passenger rate modeling, location-specific analytics,
and real-world data integration plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class PassengerLocation:
    """Represents a specific location where passengers board/disembark."""
    location_id: str
    name: str
    latitude: float
    longitude: float
    location_type: str  # 'depot', 'stop', 'station', 'terminal'
    capacity: Optional[int] = None  # Max waiting passengers
    amenities: List[str] = None  # ['shelter', 'seating', 'digital_display']


@dataclass
class PassengerRateMetrics:
    """Passenger arrival and departure rate metrics."""
    location: PassengerLocation
    arrival_rate_peak: float  # passengers per hour
    arrival_rate_off_peak: float
    departure_rate_peak: float
    departure_rate_off_peak: float
    wait_time_avg: float  # minutes
    wait_time_peak: float
    demand_variance: float  # statistical variance in demand
    seasonal_factor: float  # multiplier for seasonal changes
    measurement_period: str  # 'daily', 'weekly', 'monthly'
    confidence_level: float  # 0.0-1.0


@dataclass
class PassengerDemandPattern:
    """Time-based passenger demand patterns."""
    location_id: str
    route_id: str
    time_period: str  # '06:00-09:00', 'morning_peak', etc.
    passenger_count: int
    boarding_rate: float  # passengers per minute
    alighting_rate: float
    load_factor: float  # occupancy percentage
    trip_purpose: str  # 'commute', 'leisure', 'shopping', 'school'
    direction: str  # 'inbound', 'outbound', 'bidirectional'


@dataclass
class RealWorldDataSource:
    """Configuration for external data sources."""
    source_id: str
    source_type: str  # 'gtfs', 'api', 'csv', 'json', 'database'
    connection_params: Dict[str, Any]
    data_format: str
    update_frequency: str  # 'realtime', 'hourly', 'daily'
    quality_score: float  # 0.0-1.0
    coverage_area: Optional[Tuple[float, float, float, float]] = None  # bbox


class PassengerAnalyticsPlugin(ABC):
    """Base interface for passenger analytics plugins."""
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Return the plugin name."""
        pass
    
    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """Return the plugin version."""
        pass
    
    @property
    @abstractmethod
    def supported_data_sources(self) -> List[str]:
        """Return list of supported data source types."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    def calculate_passenger_rates(self, 
                                location: PassengerLocation,
                                route_data: Dict[str, Any],
                                time_window: Tuple[datetime, datetime]) -> PassengerRateMetrics:
        """Calculate passenger arrival/departure rates for a specific location."""
        pass
    
    @abstractmethod
    def analyze_demand_patterns(self,
                              locations: List[PassengerLocation],
                              route_data: Dict[str, Any],
                              historical_data: Optional[Dict] = None) -> List[PassengerDemandPattern]:
        """Analyze passenger demand patterns across multiple locations."""
        pass
    
    @abstractmethod
    def predict_passenger_load(self,
                             origin: PassengerLocation,
                             destination: PassengerLocation,
                             departure_time: datetime,
                             route_data: Dict[str, Any]) -> Dict[str, float]:
        """Predict passenger load for specific origin-destination-time combination."""
        pass
    
    @abstractmethod
    def integrate_realworld_data(self,
                               data_source: RealWorldDataSource,
                               location_filter: Optional[List[str]] = None) -> bool:
        """Integrate data from external real-world sources."""
        pass
    
    @abstractmethod
    def export_analytics(self, 
                        format_type: str = 'json',
                        include_predictions: bool = True) -> str:
        """Export analytics data in specified format."""
        pass
    
    @abstractmethod
    def get_location_hotspots(self,
                            route_data: Dict[str, Any],
                            threshold: float = 0.7) -> List[Tuple[PassengerLocation, float]]:
        """Identify high-demand locations (hotspots) along routes."""
        pass


class LocationSpecificAnalytics(ABC):
    """Interface for location-specific passenger analytics."""
    
    @abstractmethod
    def calculate_walking_catchment(self,
                                  location: PassengerLocation,
                                  walking_radius_meters: int = 400) -> Dict[str, Any]:
        """Calculate the walking catchment area for a location."""
        pass
    
    @abstractmethod
    def analyze_passenger_flow(self,
                             location: PassengerLocation,
                             adjacent_locations: List[PassengerLocation],
                             time_period: str) -> Dict[str, float]:
        """Analyze passenger flow between locations."""
        pass
    
    @abstractmethod
    def optimize_service_frequency(self,
                                 locations: List[PassengerLocation],
                                 current_frequency: Dict[str, int],
                                 capacity_constraints: Dict[str, int]) -> Dict[str, int]:
        """Optimize service frequency based on passenger demand."""
        pass


class RealWorldDataIntegrator(ABC):
    """Interface for integrating real-world passenger data."""
    
    @abstractmethod
    def import_gtfs_data(self, gtfs_path: str) -> Dict[str, Any]:
        """Import GTFS (General Transit Feed Specification) data."""
        pass
    
    @abstractmethod
    def connect_transit_api(self, api_config: Dict[str, str]) -> bool:
        """Connect to real-time transit API."""
        pass
    
    @abstractmethod
    def import_csv_ridership(self, csv_path: str, mapping_config: Dict[str, str]) -> Dict[str, Any]:
        """Import ridership data from CSV files."""
        pass
    
    @abstractmethod
    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Validate the quality of imported data."""
        pass
    
    @abstractmethod
    def synchronize_with_source(self, source_id: str) -> bool:
        """Synchronize with external data source."""
        pass


# Plugin Registry
class PassengerAnalyticsRegistry:
    """Registry for managing passenger analytics plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, PassengerAnalyticsPlugin] = {}
        self._active_plugin: Optional[str] = None
    
    def register_plugin(self, plugin: PassengerAnalyticsPlugin) -> bool:
        """Register a new passenger analytics plugin."""
        try:
            plugin_name = plugin.plugin_name
            if plugin_name in self._plugins:
                print(f"⚠️ Plugin '{plugin_name}' already registered, replacing...")
            
            self._plugins[plugin_name] = plugin
            print(f"✅ Registered passenger analytics plugin: {plugin_name} v{plugin.plugin_version}")
            return True
        except Exception as e:
            print(f"❌ Failed to register plugin: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PassengerAnalyticsPlugin]:
        """Get a specific plugin by name."""
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins."""
        return list(self._plugins.keys())
    
    def set_active_plugin(self, plugin_name: str) -> bool:
        """Set the active plugin for passenger analytics."""
        if plugin_name in self._plugins:
            self._active_plugin = plugin_name
            return True
        return False
    
    def get_active_plugin(self) -> Optional[PassengerAnalyticsPlugin]:
        """Get the currently active plugin."""
        if self._active_plugin:
            return self._plugins.get(self._active_plugin)
        return None


# Global registry instance
passenger_analytics_registry = PassengerAnalyticsRegistry()