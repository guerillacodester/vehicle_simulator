#!/usr/bin/env python3
"""
Consolidated Passenger Modeler v2.0.0
=====================================

Complete passenger modeling system that combines:
1. GPS location consolidation with bearing-based naming
2. Plugin-based statistical distribution modeling (Poisson, Gaussian, etc.)
3. Multi-threaded processing for performance
4. Comprehensive statistical reporting
5. Direct output to passenger_simulator v3 format

Processes GeoJSON data files according to config.ini settings and applies
specified model plugin distribution to generate passengers around each point.
"""

import json
import logging
import configparser
import math
import concurrent.futures
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime
import threading
import time
import sys

# Add utils and plugins to path
sys.path.append(str(Path(__file__).parent))
from utils import ConfigManager, PluginLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Version constant
CONSOLIDATED_PASSENGER_MODELER_VERSION = "2.0.0"

@dataclass
class ConsolidatedLocation:
    """Represents a consolidated location with merged nearby points and passenger modeling"""
    id: str
    name: str
    latitude: float
    longitude: float
    location_type: str
    source_priority: int
    merged_count: int
    base_passenger_capacity: int
    statistical_passenger_capacity: int
    hourly_patterns: Dict[int, float]
    daily_patterns: Dict[str, float]
    amenity_weights: Dict[str, float]
    source_data: List[Dict[str, Any]]

class ThreadSafeCounter:
    """Thread-safe counter for progress tracking"""
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
            return self._value
    
    @property
    def value(self):
        with self._lock:
            return self._value

class ConsolidatedPassengerModeler:
    """Complete passenger modeling system with location consolidation and statistical modeling"""
    
    def __init__(self, config_path: str = "config.ini", num_threads: int = None):
        """Initialize with configuration file and threading settings"""
        # Load configuration
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Initialize config manager and plugin system
        self.config_manager = ConfigManager(config_path)
        
        # Threading configuration
        self.num_threads = num_threads or min(8, (threading.active_count() or 1) + 4)
        logger.info(f"Using {self.num_threads} threads for processing")
        
        # Extract configuration settings
        self.walking_distance_meters = int(self.config['processing']['walking_distance_meters'])
        self.region = self.config['environment']['region']
        self.coordinate_system = self.config['environment']['coordinate_system']
        
        # Parse naming priorities
        self.naming_priorities = {}
        priority_section = self.config['naming_priority']
        for key, value in priority_section.items():
            priority_num = int(key.split('_')[1])
            self.naming_priorities[value] = priority_num
        
        # Parse data file paths
        self.data_files = {}
        for key, value in self.config['data'].items():
            if value:  # Only include non-empty paths
                self.data_files[key] = value
                
        # Model configuration
        self.model_type = self.config['model']['type']
        
        # Initialize plugin system
        current_dir = Path(__file__).parent
        plugins_dir = current_dir / 'plugins'
        configs_dir = plugins_dir / 'configs'
        
        self.plugin_loader = PluginLoader(str(plugins_dir), str(configs_dir), self.config_manager)
        self.statistical_model = self.plugin_loader.create_model(self.model_type)
        
        if not self.statistical_model:
            raise ValueError(f"Failed to load statistical model: {self.model_type}")
        
        # Cache for named locations (for bearing calculations)
        self.named_locations = []
        
        logger.info(f"Initialized ConsolidatedPassengerModeler:")
        logger.info(f"  Walking distance: {self.walking_distance_meters}m")
        logger.info(f"  Region: {self.region}")
        logger.info(f"  Model type: {self.model_type}")
        logger.info(f"  Data files: {list(self.data_files.keys())}")
        logger.info(f"  Naming priorities: {self.naming_priorities}")
        logger.info(f"  Statistical model: {type(self.statistical_model).__name__}")

    def load_geojson_data(self) -> Dict[str, List[Dict]]:
        """Load all GeoJSON files using multithreading"""
        all_features = {}
        
        def load_file(data_type_and_path):
            data_type, file_path = data_type_and_path
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                features = []
                for feature in geojson_data.get('features', []):
                    # Extract coordinates based on geometry type
                    geometry = feature.get('geometry', {})
                    coordinates = self._extract_coordinates(geometry)
                    
                    if coordinates:
                        processed_feature = {
                            'coordinates': coordinates,
                            'properties': feature.get('properties', {}),
                            'geometry_type': geometry.get('type'),
                            'source_type': data_type,
                            'original_feature': feature
                        }
                        features.append(processed_feature)
                        
                        # Collect named locations for bearing calculations
                        name = self._extract_name(processed_feature)
                        if name and name.strip():
                            self.named_locations.append({
                                'name': name.strip(),
                                'coordinates': coordinates,
                                'source_type': data_type
                            })
                
                logger.info(f"Loaded {len(features)} features from {data_type}")
                return data_type, features
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                return data_type, []
        
        # Load files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(load_file, item) for item in self.data_files.items()]
            
            for future in concurrent.futures.as_completed(futures):
                data_type, features = future.result()
                all_features[data_type] = features
        
        logger.info(f"Collected {len(self.named_locations)} named locations for bearing calculations")
        return all_features

    def _extract_coordinates(self, geometry: Dict) -> Optional[Tuple[float, float]]:
        """Extract representative coordinates from various geometry types"""
        geom_type = geometry.get('type')
        coords = geometry.get('coordinates', [])
        
        if not coords:
            return None
            
        try:
            if geom_type == 'Point':
                return tuple(coords)
            elif geom_type in ['LineString', 'MultiPoint']:
                # Use centroid of linestring or first point of multipoint
                if geom_type == 'LineString':
                    # Calculate centroid of linestring
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    return (sum(lons) / len(lons), sum(lats) / len(lats))
                else:  # MultiPoint
                    return tuple(coords[0])
            elif geom_type in ['Polygon', 'MultiPolygon']:
                # Calculate centroid of polygon
                if geom_type == 'Polygon':
                    exterior_coords = coords[0]
                else:  # MultiPolygon
                    exterior_coords = coords[0][0]
                
                # Simple centroid calculation
                lons = [c[0] for c in exterior_coords]
                lats = [c[1] for c in exterior_coords]
                return (sum(lons) / len(lons), sum(lats) / len(lats))
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Error extracting coordinates from {geom_type}: {e}")
            return None
        
        return None

    def cluster_nearby_locations_threaded(self, all_features: Dict[str, List[Dict]]) -> List[List[Dict]]:
        """Conservative clustering - only merge truly nearby points of compatible types"""
        # Flatten all features with coordinates
        all_points = []
        for data_type, features in all_features.items():
            for feature in features:
                if feature['coordinates']:
                    all_points.append(feature)
        
        if not all_points:
            return []
        
        logger.info(f"Starting conservative clustering of {len(all_points)} points...")
        start_time = time.time()
        
        # Conservative clustering - much smaller distance threshold and type compatibility
        clusters = []
        used_indices = set()
        
        # Use a smaller effective distance for clustering to preserve more locations
        effective_distance = min(50, self.walking_distance_meters // 3)  # Much more conservative
        
        for i, point in enumerate(all_points):
            if i in used_indices:
                continue
                
            cluster = [point]
            point_lat, point_lon = point['coordinates'][1], point['coordinates'][0]
            point_type = point['source_type']
            
            # Only merge with very nearby points of compatible types
            for j, other_point in enumerate(all_points):
                if i != j and j not in used_indices:
                    other_lat, other_lon = other_point['coordinates'][1], other_point['coordinates'][0]
                    other_type = other_point['source_type']
                    
                    distance = self._calculate_distance_meters(point_lat, point_lon, other_lat, other_lon)
                    
                    # Very conservative merging rules:
                    # 1. Must be within very small distance (50m max)
                    # 2. Only merge compatible types
                    # 3. Limit cluster size to prevent over-aggregation
                    
                    should_merge = False
                    
                    if distance <= effective_distance and len(cluster) < 3:  # Max 3 points per cluster
                        # Compatible type merging rules
                        if point_type == other_type:  # Same type - can merge
                            should_merge = True
                        elif point_type in ['landuse', 'names'] and other_type in ['landuse', 'names']:  # Geographic features
                            should_merge = True
                        elif distance <= 25:  # Very close points can merge regardless of type
                            should_merge = True
                    
                    if should_merge:
                        cluster.append(other_point)
                        used_indices.add(j)
            
            clusters.append(cluster)
            used_indices.add(i)
        
        end_time = time.time()
        avg_cluster_size = len(all_points) / len(clusters) if clusters else 0
        reduction_ratio = len(all_points) / len(clusters) if clusters else 1
        
        logger.info(f"Conservative clustering: {len(all_points)} points -> {len(clusters)} clusters")
        logger.info(f"Average cluster size: {avg_cluster_size:.1f}")
        logger.info(f"Reduction ratio: {reduction_ratio:.1f}:1 (target: 2-3:1)")
        logger.info(f"Clustering completed in {end_time - start_time:.2f} seconds")
        
        return clusters

    def consolidate_cluster_with_statistical_modeling(self, cluster: List[Dict]) -> ConsolidatedLocation:
        """Consolidate a cluster with full statistical passenger modeling"""
        if not cluster:
            raise ValueError("Empty cluster provided")
        
        # Calculate centroid coordinates
        lons = [point['coordinates'][0] for point in cluster]
        lats = [point['coordinates'][1] for point in cluster]
        centroid_lon = sum(lons) / len(lons)
        centroid_lat = sum(lats) / len(lats)
        
        # Determine the best name and type based on priorities
        best_name, location_type, source_priority = self._select_best_name_with_bearing(
            cluster, centroid_lat, centroid_lon)
        
        # Generate unique ID
        location_id = f"CONS_{hash(f'{centroid_lat}_{centroid_lon}') & 0x7FFFFFFF:08x}"
        
        # Calculate base passenger capacity
        base_capacity = self._calculate_base_passenger_capacity(cluster)
        
        # Apply statistical modeling for passenger generation
        statistical_capacity, hourly_patterns, daily_patterns, amenity_weights = self._apply_statistical_modeling(
            cluster, base_capacity, centroid_lat, centroid_lon, location_type)
        
        return ConsolidatedLocation(
            id=location_id,
            name=best_name,
            latitude=centroid_lat,
            longitude=centroid_lon,
            location_type=location_type,
            source_priority=source_priority,
            merged_count=len(cluster),
            base_passenger_capacity=base_capacity,
            statistical_passenger_capacity=statistical_capacity,
            hourly_patterns=hourly_patterns,
            daily_patterns=daily_patterns,
            amenity_weights=amenity_weights,
            source_data=cluster
        )

    def _apply_statistical_modeling(self, cluster: List[Dict], base_capacity: int, 
                                  lat: float, lon: float, location_type: str) -> Tuple[int, Dict, Dict, Dict]:
        """Apply statistical model to generate realistic passenger patterns"""
        
        # Get model parameters and patterns
        model_params = self.statistical_model.get_model_parameters()
        time_patterns = self.statistical_model.get_time_patterns()
        amenity_weights = self.statistical_model.get_amenity_weights()
        
        # Determine amenity type from cluster features
        cluster_amenity_types = []
        for feature in cluster:
            props = feature.get('properties', {})
            amenity = props.get('amenity')
            if amenity:
                cluster_amenity_types.append(amenity)
        
        # Calculate location-specific multiplier based on amenity types
        location_multiplier = 1.0
        if cluster_amenity_types:
            # Use average weight of present amenity types
            weights = [amenity_weights.get(amenity, 1.0) for amenity in cluster_amenity_types]
            location_multiplier = sum(weights) / len(weights) if weights else 1.0
        
        # Apply statistical model to base capacity
        if hasattr(self.statistical_model, 'calculate_passenger_capacity'):
            statistical_capacity = self.statistical_model.calculate_passenger_capacity(
                base_capacity, location_type, cluster_amenity_types)
        else:
            # Fallback calculation using Poisson or similar distribution
            base_lambda = model_params.get('base_lambda', 5.0)
            statistical_capacity = max(1, int(np.random.poisson(base_lambda * location_multiplier)))
        
        # Generate hourly patterns (store multipliers, not final capacity)
        hourly_patterns = {}
        for hour in range(24):
            if hasattr(self.statistical_model, 'get_time_multiplier'):
                multiplier = self.statistical_model.get_time_multiplier(hour)
            else:
                # Use time patterns from model - find the pattern that includes this hour
                multiplier = 1.0
                for pattern_name, pattern in time_patterns.items():
                    if hour in pattern.get('hours', []):
                        multiplier = pattern.get('multiplier', 1.0)
                        break
            hourly_patterns[hour] = multiplier  # Store just the multiplier, not multiplied capacity
        
        # Generate daily patterns (store multipliers, not final capacity)
        daily_patterns = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if hasattr(self.statistical_model, 'get_daily_multiplier'):
                multiplier = self.statistical_model.get_daily_multiplier(day)
            else:
                multiplier = time_patterns.get('daily_distribution', {}).get(day, 1.0)
            daily_patterns[day] = multiplier  # Store just the multiplier, not multiplied capacity
        
        return statistical_capacity, hourly_patterns, daily_patterns, amenity_weights

    def _calculate_base_passenger_capacity(self, cluster: List[Dict]) -> int:
        """Calculate base passenger generation capacity based on cluster characteristics"""
        base_capacity = 1  # Minimal base for realistic Caribbean ridership (was 10, then 3)
        
        # Capacity modifiers based on source types  
        type_multipliers = {
            'busstops': 2.0,      # Bus stops generate more passengers (reduced from 2.5)
            'amenities': 1.5,      # Amenities attract passengers (reduced from 1.8)
            'highway': 1.2,        # Highway features moderate passenger generation (reduced from 1.3)
            'names': 1.1,          # Named places slight boost (unchanged)
            'landuse': 1.0         # Base capacity for land use (unchanged)
        }
        
        total_capacity = 0
        for feature in cluster:
            source_type = feature.get('source_type', 'unknown')
            multiplier = type_multipliers.get(source_type, 1.0)
            total_capacity += base_capacity * multiplier
        
        return max(int(total_capacity), 1)  # Minimum 1 passenger capacity (was 5)

    def _select_best_name_with_bearing(self, cluster: List[Dict], 
                                     centroid_lat: float, centroid_lon: float) -> Tuple[str, str, int]:
        """Select the best name from cluster, using bearing-based naming for unnamed locations"""
        # Group features by source type
        by_source = defaultdict(list)
        for feature in cluster:
            by_source[feature['source_type']].append(feature)
        
        # Check each priority level for named features
        for source_type, priority in sorted(self.naming_priorities.items(), key=lambda x: x[1]):
            if source_type in by_source:
                # Look for features with names in this priority level
                for feature in by_source[source_type]:
                    name = self._extract_name(feature)
                    if name and name.strip():
                        return name.strip(), source_type, priority
        
        # If no named features found, use bearing-based naming
        if self.named_locations:
            closest_named = self._find_closest_named_location(centroid_lat, centroid_lon)
            if closest_named:
                distance = self._calculate_distance_meters(
                    centroid_lat, centroid_lon,
                    closest_named['coordinates'][1], closest_named['coordinates'][0]
                )
                bearing = self._calculate_bearing(
                    centroid_lat, centroid_lon,
                    closest_named['coordinates'][1], closest_named['coordinates'][0]
                )
                
                # Format: "150m NE of Church Street"
                name = f"{distance:.0f}m {bearing} of {closest_named['name']}"
                
                # Use the highest priority source type present
                if by_source:
                    best_source = min(by_source.keys(), 
                                    key=lambda x: self.naming_priorities.get(x, 999))
                    return name, best_source, self.naming_priorities.get(best_source, 999)
        
        # Fallback to NONDESCRIPT
        return "NONDESCRIPT", "unknown", 999

    def _find_closest_named_location(self, lat: float, lon: float) -> Optional[Dict]:
        """Find the closest named location for bearing calculation"""
        if not self.named_locations:
            return None
        
        closest_location = None
        min_distance = float('inf')
        
        for named_location in self.named_locations:
            named_lat = named_location['coordinates'][1]
            named_lon = named_location['coordinates'][0]
            distance = self._calculate_distance_meters(lat, lon, named_lat, named_lon)
            
            if distance < min_distance:
                min_distance = distance
                closest_location = named_location
        
        return closest_location

    def _extract_name(self, feature: Dict) -> Optional[str]:
        """Extract name from feature properties"""
        properties = feature.get('properties', {})
        
        # Try various name fields in order of preference
        name_fields = ['name', 'stop_name', 'amenity', 'building', 'shop', 'highway']
        
        for field in name_fields:
            if field in properties and properties[field]:
                value = str(properties[field]).strip()
                if value and value.lower() not in ['null', 'none', '']:
                    return value
        
        return None

    def _calculate_distance_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> str:
        """Calculate bearing from point 1 to point 2 and return compass direction"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(delta_lon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        bearing_deg = (bearing_deg + 360) % 360
        
        # Convert to 16-point compass
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        
        index = round(bearing_deg / 22.5) % 16
        return directions[index]

    def process_locations_with_statistical_modeling(self) -> List[ConsolidatedLocation]:
        """Main processing pipeline with location consolidation and statistical modeling"""
        logger.info("Starting consolidated passenger modeling process...")
        start_time = time.time()
        
        # Load all GeoJSON data
        all_features = self.load_geojson_data()
        load_time = time.time()
        logger.info(f"Data loading completed in {load_time - start_time:.2f} seconds")
        
        # Cluster nearby locations
        clusters = self.cluster_nearby_locations_threaded(all_features)
        cluster_time = time.time()
        logger.info(f"Clustering completed in {cluster_time - load_time:.2f} seconds")
        
        # Consolidate clusters with statistical modeling
        logger.info(f"Starting statistical modeling for {len(clusters)} clusters...")
        
        counter = ThreadSafeCounter()
        consolidated_locations = []
        
        def consolidate_cluster_worker(cluster):
            location = self.consolidate_cluster_with_statistical_modeling(cluster)
            count = counter.increment()
            if count % 1000 == 0:
                logger.info(f"Processed {count}/{len(clusters)} clusters...")
            return location
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(consolidate_cluster_worker, cluster) for cluster in clusters]
            
            for future in concurrent.futures.as_completed(futures):
                location = future.result()
                consolidated_locations.append(location)
        
        consolidation_time = time.time()
        logger.info(f"Statistical modeling completed in {consolidation_time - cluster_time:.2f} seconds")
        logger.info(f"Total processing time: {consolidation_time - start_time:.2f} seconds")
        logger.info(f"Successfully processed {len(consolidated_locations)} locations with statistical modeling")
        
        return consolidated_locations

    def generate_comprehensive_model(self, output_name: str = "barbados_v4_statistical") -> Dict[str, Any]:
        """Generate the complete passenger model with statistical analysis"""
        
        # Process all locations
        consolidated_locations = self.process_locations_with_statistical_modeling()
        
        # Generate comprehensive statistics
        model_statistics = self._generate_model_statistics(consolidated_locations)
        
        # Create passenger_simulator v3 compatible format
        v3_format = self._convert_to_v3_format(consolidated_locations)
        
        # Add statistical analysis
        v3_format["statistical_analysis"] = model_statistics
        v3_format["plugin_info"] = {
            "model_type": self.model_type,
            "plugin_name": type(self.statistical_model).__name__,
            "model_parameters": self.statistical_model.get_model_parameters(),
            "distribution_statistics": self.statistical_model.get_distribution_statistics()
        }
        
        # Save the model
        output_dir = Path(__file__).parent / "models" / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{output_name}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(v3_format, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved comprehensive model to: {output_file}")
        
        return v3_format

    def _generate_model_statistics(self, locations: List[ConsolidatedLocation]) -> Dict[str, Any]:
        """Generate comprehensive statistical analysis of the model"""
        
        total_base_capacity = sum(loc.base_passenger_capacity for loc in locations)
        total_statistical_capacity = sum(loc.statistical_passenger_capacity for loc in locations)
        
        # Analyze by location type
        by_type = defaultdict(list)
        for loc in locations:
            by_type[loc.location_type].append(loc)
        
        type_analysis = {}
        for loc_type, type_locations in by_type.items():
            type_analysis[loc_type] = {
                "count": len(type_locations),
                "base_capacity": sum(loc.base_passenger_capacity for loc in type_locations),
                "statistical_capacity": sum(loc.statistical_passenger_capacity for loc in type_locations),
                "avg_merged": sum(loc.merged_count for loc in type_locations) / len(type_locations),
                "capacity_enhancement": sum(loc.statistical_passenger_capacity - loc.base_passenger_capacity for loc in type_locations)
            }
        
        # Analyze hourly patterns
        hourly_totals = defaultdict(float)
        for loc in locations:
            for hour, capacity in loc.hourly_patterns.items():
                hourly_totals[hour] += capacity
        
        # Analyze daily patterns
        daily_totals = defaultdict(float)
        for loc in locations:
            for day, capacity in loc.daily_patterns.items():
                daily_totals[day] += capacity
        
        # Peak analysis
        peak_hour = max(hourly_totals.items(), key=lambda x: x[1])
        peak_day = max(daily_totals.items(), key=lambda x: x[1])
        
        return {
            "overview": {
                "total_locations": len(locations),
                "total_base_capacity": total_base_capacity,
                "total_statistical_capacity": total_statistical_capacity,
                "capacity_enhancement": total_statistical_capacity - total_base_capacity,
                "enhancement_percentage": ((total_statistical_capacity - total_base_capacity) / total_base_capacity * 100) if total_base_capacity > 0 else 0,
                "average_capacity_per_location": total_statistical_capacity / len(locations) if locations else 0
            },
            "by_location_type": type_analysis,
            "temporal_patterns": {
                "peak_hour": {"hour": peak_hour[0], "capacity": peak_hour[1]},
                "peak_day": {"day": peak_day[0], "capacity": peak_day[1]},
                "hourly_distribution": dict(hourly_totals),
                "daily_distribution": dict(daily_totals)
            },
            "naming_analysis": {
                "named_locations": len([loc for loc in locations if not loc.name.startswith("NONDESCRIPT")]),
                "bearing_based": len([loc for loc in locations if "m " in loc.name and " of " in loc.name]),
                "nondescript": len([loc for loc in locations if loc.name.startswith("NONDESCRIPT")])
            }
        }

    def _convert_to_v3_format(self, locations: List[ConsolidatedLocation]) -> Dict[str, Any]:
        """Convert consolidated locations to passenger_simulator v3 format"""
        
        v3_model = {
            "metadata": {
                "model_version": "v4.0.0_statistical_consolidated",
                "region": self.region,
                "coordinate_system": self.coordinate_system,
                "generation_date": datetime.now().strftime("%Y-%m-%d"),
                "total_locations": len(locations),
                "walking_distance_meters": self.walking_distance_meters,
                "statistical_modeling": True,
                "model_type": self.model_type,
                "threading_enabled": True,
                "num_threads_used": self.num_threads
            },
            "bus_stops": {},
            "amenities": {},
            "streets": {},
            "places": {}
        }
        
        # Categorize locations
        counters = {"bus_stops": 0, "amenities": 0, "streets": 0, "places": 0}
        
        for location in locations:
            # Create standardized entry with statistical data
            entry = {
                "stop_id": location.id,
                "stop_name": location.name,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "location_type": location.location_type,
                "passenger_capacity": location.statistical_passenger_capacity,  # Use statistical capacity
                "base_capacity": location.base_passenger_capacity,
                "merged_count": location.merged_count,
                "source_priority": location.source_priority,
                "hourly_patterns": location.hourly_patterns,
                "daily_patterns": location.daily_patterns,
                "amenity_weights": location.amenity_weights
            }
            
            # Categorize into appropriate section
            if location.location_type == "busstops":
                category = "bus_stops"
                prefix = "BUS"
            elif location.location_type == "amenities":
                category = "amenities"
                prefix = "AME"
            elif location.location_type in ["highway", "names"]:
                category = "streets"
                prefix = "STR"
            else:
                category = "places"
                prefix = "PLC"
            
            key = f"{prefix}_{counters[category]:04d}"
            v3_model[category][key] = entry
            counters[category] += 1
        
        # Update metadata with counts
        for category, count in counters.items():
            v3_model["metadata"][f"{category}_count"] = count
        
        return v3_model

    def print_comprehensive_summary(self, model_data: Dict[str, Any]):
        """Print detailed summary statistics"""
        print("\n" + "="*80)
        print("🚀 CONSOLIDATED PASSENGER MODELER v2.0.0 - STATISTICAL")
        print("="*80)
        
        metadata = model_data["metadata"]
        stats = model_data.get("statistical_analysis", {})
        plugin_info = model_data.get("plugin_info", {})
        
        print(f"⚡ Processing Performance:")
        print(f"   Threads used: {metadata.get('num_threads_used', 'N/A')}")
        print(f"   Statistical modeling: {metadata.get('statistical_modeling', False)}")
        print(f"   Model type: {plugin_info.get('model_type', 'Unknown').upper()}")
        print(f"   Plugin: {plugin_info.get('plugin_name', 'Unknown')}")
        
        overview = stats.get("overview", {})
        print(f"\n📊 Statistical Analysis:")
        print(f"   Total locations: {overview.get('total_locations', 0):,}")
        print(f"   Base capacity: {overview.get('total_base_capacity', 0):,}")
        print(f"   Statistical capacity: {overview.get('total_statistical_capacity', 0):,}")
        print(f"   Enhancement: +{overview.get('capacity_enhancement', 0):,} ({overview.get('enhancement_percentage', 0):.1f}%)")
        print(f"   Average per location: {overview.get('average_capacity_per_location', 0):.1f}")
        
        # Location type breakdown
        by_type = stats.get("by_location_type", {})
        print(f"\n📍 Locations by Type:")
        for loc_type, type_stats in by_type.items():
            print(f"   {loc_type:<12}: {type_stats.get('count', 0):4d} locations, "
                  f"capacity {type_stats.get('statistical_capacity', 0):6,}, "
                  f"enhanced +{type_stats.get('capacity_enhancement', 0):4,}")
        
        # Temporal patterns
        temporal = stats.get("temporal_patterns", {})
        peak_hour = temporal.get("peak_hour", {})
        peak_day = temporal.get("peak_day", {})
        
        print(f"\n🕐 Temporal Patterns:")
        print(f"   Peak hour: {peak_hour.get('hour', 'N/A')}:00 ({peak_hour.get('capacity', 0):,.0f} capacity)")
        print(f"   Peak day: {peak_day.get('day', 'N/A').title()} ({peak_day.get('capacity', 0):,.0f} capacity)")
        
        # Naming analysis
        naming = stats.get("naming_analysis", {})
        print(f"\n🏷️  Enhanced Naming Results:")
        total_locs = overview.get('total_locations', 1)
        named_pct = (naming.get('named_locations', 0) / total_locs * 100) if total_locs > 0 else 0
        bearing_pct = (naming.get('bearing_based', 0) / total_locs * 100) if total_locs > 0 else 0
        nondescript_pct = (naming.get('nondescript', 0) / total_locs * 100) if total_locs > 0 else 0
        
        print(f"   Named locations: {naming.get('named_locations', 0)} ({named_pct:.1f}%)")
        print(f"   Bearing-based: {naming.get('bearing_based', 0)} ({bearing_pct:.1f}%)")
        print(f"   Nondescript: {naming.get('nondescript', 0)} ({nondescript_pct:.1f}%)")
        print(f"   Total usefully named: {naming.get('named_locations', 0) + naming.get('bearing_based', 0)} ({named_pct + bearing_pct:.1f}%)")
        
        # Model parameters
        model_params = plugin_info.get("model_parameters", {})
        if model_params:
            print(f"\n⚙️  Statistical Model Parameters:")
            for param, value in model_params.items():
                print(f"   {param}: {value}")
        
        print(f"\n💾 Model file: models/generated/barbados_v4_statistical.json")
        print("✅ Statistical passenger modeling completed successfully!")
        
        print(f"\n🔗 Integration Instructions:")
        print("1. Copy models/generated/barbados_v4_statistical.json to:")
        print("   world/arknet_transit_simulator/passenger_simulator/models/")
        print("2. Update time_smeared_service.py to use barbados_v4_statistical.json")
        print("3. Test with: python simulate_passengers.py 1 8")


def main():
    """Main function to run the consolidated passenger modeler"""
    try:
        # Initialize the modeler
        modeler = ConsolidatedPassengerModeler()
        
        # Generate the complete model
        model_data = modeler.generate_comprehensive_model()
        
        # Print comprehensive summary
        modeler.print_comprehensive_summary(model_data)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in consolidated passenger modeling: {e}")
        print(f"\n❌ Consolidated passenger modeling failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())