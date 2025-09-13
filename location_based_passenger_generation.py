"""
Enhanced Passenger Generation with Location Names

This module extends the passenger simulation to generate passengers from 
actual locations around the route using location names GeoJSON data.
"""

import json
import geopandas as gpd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import math
from pathlib import Path

class LocationBasedPassengerGenerator:
    """
    Generates passengers from actual locations around transit routes
    using location names GeoJSON data
    """
    
    def __init__(self, location_names_gdf: gpd.GeoDataFrame, route_stops_gdf: gpd.GeoDataFrame):
        self.location_names_gdf = location_names_gdf
        self.route_stops_gdf = route_stops_gdf
        self.location_cache = {}
        self.passenger_generation_rates = {}
        
        # Analyze location types for passenger generation potential
        self._analyze_location_types()
        self._calculate_stop_catchment_areas()
    
    def _analyze_location_types(self):
        """Analyze location names to determine passenger generation potential"""
        
        # Location type keywords and their passenger generation rates (passengers/hour/location)
        location_patterns = {
            # High generation locations
            'residential': {
                'keywords': ['house', 'home', 'residence', 'apartment', 'estate', 'village', 'settlement', 'community'],
                'base_rate': 2.5,  # passengers per hour per location
                'peak_multiplier': 3.0
            },
            'commercial': {
                'keywords': ['shop', 'store', 'market', 'mall', 'plaza', 'centre', 'center', 'business'],
                'base_rate': 8.0,
                'peak_multiplier': 2.5
            },
            'educational': {
                'keywords': ['school', 'college', 'university', 'academy', 'institute', 'campus'],
                'base_rate': 15.0,
                'peak_multiplier': 4.0
            },
            'healthcare': {
                'keywords': ['hospital', 'clinic', 'medical', 'health', 'doctor', 'pharmacy'],
                'base_rate': 6.0,
                'peak_multiplier': 1.8
            },
            'government': {
                'keywords': ['government', 'office', 'ministry', 'court', 'police', 'fire', 'post'],
                'base_rate': 4.0,
                'peak_multiplier': 2.2
            },
            'religious': {
                'keywords': ['church', 'temple', 'mosque', 'synagogue', 'cathedral', 'chapel'],
                'base_rate': 3.0,
                'peak_multiplier': 1.5
            },
            'recreation': {
                'keywords': ['park', 'beach', 'sports', 'gym', 'club', 'bar', 'restaurant', 'hotel'],
                'base_rate': 4.5,
                'peak_multiplier': 1.8
            },
            # Medium generation locations
            'industrial': {
                'keywords': ['factory', 'warehouse', 'industrial', 'plant', 'works', 'yard'],
                'base_rate': 3.5,
                'peak_multiplier': 2.8
            },
            'transport': {
                'keywords': ['station', 'terminal', 'airport', 'port', 'depot', 'garage'],
                'base_rate': 12.0,
                'peak_multiplier': 3.5
            },
            # Low generation locations
            'agricultural': {
                'keywords': ['farm', 'plantation', 'field', 'agriculture', 'crop', 'livestock'],
                'base_rate': 0.8,
                'peak_multiplier': 1.2
            },
            'natural': {
                'keywords': ['hill', 'mountain', 'river', 'pond', 'forest', 'wood', 'nature'],
                'base_rate': 0.3,
                'peak_multiplier': 1.0
            }
        }
        
        # Classify each location
        for idx, location in self.location_names_gdf.iterrows():
            location_name = str(location.get('name', '')).lower()
            
            # Default classification
            classification = {
                'type': 'unknown',
                'base_rate': 1.0,
                'peak_multiplier': 1.5,
                'confidence': 0.0
            }
            
            # Find best matching pattern
            best_match = None
            best_score = 0
            
            for location_type, pattern in location_patterns.items():
                score = 0
                for keyword in pattern['keywords']:
                    if keyword in location_name:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = location_type
            
            if best_match and best_score > 0:
                pattern = location_patterns[best_match]
                classification = {
                    'type': best_match,
                    'base_rate': pattern['base_rate'],
                    'peak_multiplier': pattern['peak_multiplier'],
                    'confidence': min(best_score / 3.0, 1.0)  # Normalize confidence
                }
            
            self.passenger_generation_rates[idx] = classification
    
    def _calculate_stop_catchment_areas(self):
        """Calculate which locations are within walking distance of each stop"""
        self.stop_catchments = {}
        
        for stop_idx, stop in self.route_stops_gdf.iterrows():
            stop_id = stop.get('stop_id', f'stop_{stop_idx}')
            stop_geom = stop.geometry
            
            # Find locations within walking distance (typically 400-800m)
            walking_distance_m = 600  # 600 meters = ~7 minute walk
            
            # Create buffer around stop
            stop_buffer = stop_geom.buffer(walking_distance_m / 111000)  # Rough conversion to degrees
            
            catchment_locations = []
            for loc_idx, location in self.location_names_gdf.iterrows():
                if stop_buffer.contains(location.geometry) or stop_buffer.intersects(location.geometry):
                    distance_m = self._calculate_distance(stop_geom, location.geometry)
                    
                    # Distance decay factor (closer locations generate more passengers)
                    distance_factor = max(0.2, 1.0 - (distance_m / walking_distance_m))
                    
                    catchment_locations.append({
                        'location_idx': loc_idx,
                        'name': location.get('name', f'Location_{loc_idx}'),
                        'distance_m': distance_m,
                        'distance_factor': distance_factor,
                        'generation_rate': self.passenger_generation_rates.get(loc_idx, {}),
                        'coordinates': (location.geometry.y, location.geometry.x)
                    })
            
            self.stop_catchments[stop_id] = catchment_locations
    
    def _calculate_distance(self, geom1, geom2) -> float:
        """Calculate distance between two geometries in meters"""
        # Simple haversine distance calculation
        lat1, lon1 = geom1.y, geom1.x
        lat2, lon2 = geom2.y, geom2.x
        
        R = 6371000  # Earth's radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def generate_passengers_from_locations(self, stop_id: str, current_time: datetime, 
                                         generation_duration_seconds: int = 30) -> List[Dict]:
        """
        Generate passengers from actual locations around a specific stop
        
        Args:
            stop_id: ID of the transit stop
            current_time: Current simulation time
            generation_duration_seconds: Time period for generation
            
        Returns:
            List of passenger records with origin location details
        """
        if stop_id not in self.stop_catchments:
            return []
        
        passengers = []
        catchment_locations = self.stop_catchments[stop_id]
        
        # Determine peak time multiplier
        hour = current_time.hour
        peak_multiplier = self._get_peak_multiplier(hour)
        
        for location_data in catchment_locations:
            generation_rate = location_data['generation_rate']
            
            if not generation_rate:
                continue
            
            # Calculate passengers for this location
            base_rate = generation_rate.get('base_rate', 1.0)
            location_peak_multiplier = generation_rate.get('peak_multiplier', 1.5)
            distance_factor = location_data['distance_factor']
            confidence = generation_rate.get('confidence', 0.5)
            
            # Total generation rate (passengers per hour)
            hourly_rate = base_rate * peak_multiplier * location_peak_multiplier * distance_factor * confidence
            
            # Scale to generation period
            period_rate = hourly_rate * (generation_duration_seconds / 3600)
            
            # Poisson distribution for realistic passenger generation
            passenger_count = np.random.poisson(period_rate)
            
            # Generate passenger records
            for _ in range(passenger_count):
                passenger = {
                    'passenger_id': f"pax_{len(passengers)}_{current_time.strftime('%H%M%S')}",
                    'origin_location_name': location_data['name'],
                    'origin_coordinates': location_data['coordinates'],
                    'boarding_stop_id': stop_id,
                    'boarding_time': current_time,
                    'walk_distance_m': location_data['distance_m'],
                    'walk_time_minutes': location_data['distance_m'] / 80,  # 80m/min walking speed
                    'location_type': generation_rate.get('type', 'unknown'),
                    'trip_purpose': self._infer_trip_purpose(generation_rate.get('type', 'unknown'), hour),
                    'group_size': self._generate_group_size(generation_rate.get('type', 'unknown')),
                    'generation_confidence': confidence
                }
                passengers.append(passenger)
        
        return passengers
    
    def _get_peak_multiplier(self, hour: int) -> float:
        """Get peak time multiplier based on hour"""
        if 7 <= hour <= 9:  # Morning rush
            return 3.5
        elif 17 <= hour <= 19:  # Evening rush
            return 3.0
        elif 15 <= hour <= 16:  # School hours
            return 2.0
        elif 10 <= hour <= 14:  # Midday
            return 1.2
        elif 20 <= hour <= 22:  # Evening leisure
            return 1.5
        else:  # Night/early morning
            return 0.3
    
    def _infer_trip_purpose(self, location_type: str, hour: int) -> str:
        """Infer trip purpose based on location type and time"""
        if 6 <= hour <= 9:
            if location_type in ['residential']:
                return 'work_commute'
            elif location_type in ['educational']:
                return 'education'
            else:
                return 'work_commute'
        elif 15 <= hour <= 17:
            if location_type in ['educational']:
                return 'education'
            elif location_type in ['commercial', 'recreational']:
                return 'shopping_leisure'
            else:
                return 'work_commute'
        elif 17 <= hour <= 19:
            return 'home_commute'
        elif 20 <= hour <= 23:
            return 'leisure'
        else:
            return 'other'
    
    def _generate_group_size(self, location_type: str) -> int:
        """Generate realistic group sizes based on location type"""
        if location_type in ['residential']:
            # Families more likely
            return np.random.choice([1, 2, 3, 4], p=[0.4, 0.3, 0.2, 0.1])
        elif location_type in ['educational']:
            # Students often travel alone or in pairs
            return np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        elif location_type in ['commercial', 'recreational']:
            # Mix of solo and group travelers
            return np.random.choice([1, 2, 3, 4], p=[0.5, 0.3, 0.15, 0.05])
        else:
            # Default distribution
            return np.random.choice([1, 2], p=[0.7, 0.3])
    
    def get_catchment_summary(self, stop_id: str) -> Dict:
        """Get summary of locations in catchment area of a stop"""
        if stop_id not in self.stop_catchments:
            return {}
        
        catchment = self.stop_catchments[stop_id]
        
        summary = {
            'total_locations': len(catchment),
            'location_types': {},
            'average_distance_m': 0,
            'total_generation_potential': 0
        }
        
        if not catchment:
            return summary
        
        distances = []
        for location in catchment:
            distances.append(location['distance_m'])
            
            loc_type = location['generation_rate'].get('type', 'unknown')
            if loc_type not in summary['location_types']:
                summary['location_types'][loc_type] = 0
            summary['location_types'][loc_type] += 1
            
            base_rate = location['generation_rate'].get('base_rate', 0)
            distance_factor = location['distance_factor']
            confidence = location['generation_rate'].get('confidence', 0)
            summary['total_generation_potential'] += base_rate * distance_factor * confidence
        
        summary['average_distance_m'] = np.mean(distances)
        
        return summary

def create_location_enhanced_demo(location_names_geojson_path: str, route_stops_geojson_path: str):
    """
    Create a demonstration of location-based passenger generation
    
    Args:
        location_names_geojson_path: Path to GeoJSON with location names
        route_stops_geojson_path: Path to GeoJSON with route stops
    """
    
    # Load the GeoJSON data
    location_names_gdf = gpd.read_file(location_names_geojson_path)
    route_stops_gdf = gpd.read_file(route_stops_geojson_path)
    
    # Initialize the location-based generator
    generator = LocationBasedPassengerGenerator(location_names_gdf, route_stops_gdf)
    
    print("🌍 LOCATION-BASED PASSENGER GENERATION DEMO")
    print("=" * 50)
    
    # Show catchment analysis for each stop
    for stop_idx, stop in route_stops_gdf.iterrows():
        stop_id = stop.get('stop_id', f'stop_{stop_idx}')
        stop_name = stop.get('stop_name', stop_id)
        
        summary = generator.get_catchment_summary(stop_id)
        
        print(f"\n📍 {stop_name} ({stop_id})")
        print(f"   🏠 Catchment locations: {summary['total_locations']}")
        print(f"   📏 Average distance: {summary['average_distance_m']:.0f}m")
        print(f"   📊 Generation potential: {summary['total_generation_potential']:.1f} pax/hr")
        
        if summary['location_types']:
            print(f"   🏢 Location types:")
            for loc_type, count in sorted(summary['location_types'].items(), key=lambda x: x[1], reverse=True):
                print(f"      {loc_type}: {count} locations")
    
    # Generate passengers for morning rush hour
    print(f"\n🕐 MORNING RUSH HOUR GENERATION (8:00 AM)")
    print("-" * 40)
    
    morning_time = datetime.now().replace(hour=8, minute=0, second=0)
    
    for stop_idx, stop in route_stops_gdf.iterrows():
        stop_id = stop.get('stop_id', f'stop_{stop_idx}')
        stop_name = stop.get('stop_name', stop_id)
        
        passengers = generator.generate_passengers_from_locations(stop_id, morning_time, 60)
        
        print(f"\n📍 {stop_name}: {len(passengers)} passengers")
        
        if passengers:
            # Show origin location distribution
            origins = {}
            trip_purposes = {}
            
            for passenger in passengers[:5]:  # Show first 5
                origin = passenger['origin_location_name']
                purpose = passenger['trip_purpose']
                
                origins[origin] = origins.get(origin, 0) + 1
                trip_purposes[purpose] = trip_purposes.get(purpose, 0) + 1
                
                print(f"   👤 From {origin} ({passenger['walk_distance_m']:.0f}m walk)")
            
            if len(passengers) > 5:
                print(f"   ... and {len(passengers) - 5} more passengers")
            
            print(f"   🎯 Trip purposes: {dict(trip_purposes)}")
    
    return generator

if __name__ == "__main__":
    # Example usage - you would provide actual GeoJSON file paths
    print("📋 To use this system, provide:")
    print("  1. Location names GeoJSON (places, landmarks, buildings)")
    print("  2. Route stops GeoJSON (bus stops along the route)")
    print("\nExample structure for location names GeoJSON:")
    print('{')
    print('  "type": "FeatureCollection",')
    print('  "features": [')
    print('    {')
    print('      "type": "Feature",')
    print('      "properties": {')
    print('        "name": "Bridgetown Hospital",')
    print('        "amenity": "hospital"')
    print('      },')
    print('      "geometry": {')
    print('        "type": "Point",')
    print('        "coordinates": [-59.6198, 13.1067]')
    print('      }')
    print('    }')
    print('  ]')
    print('}')