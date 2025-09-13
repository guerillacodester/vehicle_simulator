#!/usr/bin/env python3
"""
Concept for integrating landuse data into passenger generation model.
This shows how landuse polygons could enhance the existing Route 1 model.
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class LanduseInfluence:
    """Defines how different landuse types affect passenger generation"""
    landuse_type: str
    passenger_multiplier: float
    peak_factor: float  # How much this affects peak vs off-peak
    boarding_ratio: float  # Ratio of boarding to alighting
    radius_of_influence_m: float
    time_patterns: Dict[str, float]  # Hour-based multipliers

class LanduseEnhancedPassengerModel:
    """Enhanced passenger model that incorporates landuse data"""
    
    def __init__(self):
        self.landuse_influences = self._initialize_landuse_influences()
        self.current_model = None
        self.landuse_data = None
    
    def _initialize_landuse_influences(self) -> Dict[str, LanduseInfluence]:
        """Define how different landuse types affect passenger generation"""
        return {
            'residential': LanduseInfluence(
                landuse_type='residential',
                passenger_multiplier=2.5,  # High passenger generation
                peak_factor=3.0,  # Much higher in morning/evening peaks
                boarding_ratio=0.8,  # More boarding than alighting in morning
                radius_of_influence_m=400,
                time_patterns={
                    '06:00': 1.5, '07:00': 3.0, '08:00': 2.5,  # Morning peak
                    '17:00': 2.0, '18:00': 2.5, '19:00': 1.8,  # Evening peak
                    'default': 1.0
                }
            ),
            'industrial': LanduseInfluence(
                landuse_type='industrial',
                passenger_multiplier=1.8,
                peak_factor=2.0,  # Shift changes affect peaks
                boarding_ratio=0.3,  # More alighting (work destination)
                radius_of_influence_m=600,  # Larger influence radius
                time_patterns={
                    '06:00': 1.2, '07:00': 2.5, '15:00': 2.0, '16:00': 2.8,  # Shift patterns
                    'default': 1.0
                }
            ),
            'commercial': LanduseInfluence(
                landuse_type='commercial',
                passenger_multiplier=2.0,
                peak_factor=1.5,
                boarding_ratio=0.4,  # Mixed boarding/alighting
                radius_of_influence_m=300,
                time_patterns={
                    '09:00': 1.5, '12:00': 1.8, '17:00': 1.6,  # Business hours
                    'default': 1.0
                }
            ),
            'educational': LanduseInfluence(
                landuse_type='educational',
                passenger_multiplier=3.0,  # Very high generation
                peak_factor=4.0,  # Extreme peaks during class times
                boarding_ratio=0.6,
                radius_of_influence_m=500,
                time_patterns={
                    '07:00': 3.5, '08:00': 4.0,  # School start
                    '15:00': 3.8, '16:00': 4.2,  # School end
                    'default': 0.5  # Very low outside school hours
                }
            ),
            'grass': LanduseInfluence(
                landuse_type='grass',
                passenger_multiplier=0.3,  # Low generation
                peak_factor=0.8,  # Less peak variation
                boarding_ratio=0.5,
                radius_of_influence_m=200,
                time_patterns={'default': 1.0}
            ),
            'farmland': LanduseInfluence(
                landuse_type='farmland',
                passenger_multiplier=0.1,  # Very low
                peak_factor=0.5,
                boarding_ratio=0.5,
                radius_of_influence_m=800,  # Large but sparse influence
                time_patterns={'default': 1.0}
            ),
            'quarry': LanduseInfluence(
                landuse_type='quarry',
                passenger_multiplier=1.2,
                peak_factor=1.8,  # Shift-based work
                boarding_ratio=0.2,  # Mostly alighting (work destination)
                radius_of_influence_m=400,
                time_patterns={
                    '06:00': 2.0, '07:00': 2.5, '15:00': 1.8, '16:00': 2.2,
                    'default': 0.8
                }
            )
        }
    
    def calculate_landuse_influence_for_stop(self, stop_coordinates: Tuple[float, float], 
                                           landuse_polygons: List[Dict],
                                           time_hour: Optional[str] = None) -> Dict[str, float]:
        """
        Calculate how nearby landuse affects passenger generation at a stop.
        
        Args:
            stop_coordinates: (longitude, latitude) of the stop
            landuse_polygons: List of GeoJSON-like landuse features
            time_hour: Hour string like '07:00' for time-based adjustments
        
        Returns:
            Dictionary with influence factors for boarding/alighting rates
        """
        total_boarding_multiplier = 1.0
        total_alighting_multiplier = 1.0
        landuse_breakdown = {}
        
        stop_lon, stop_lat = stop_coordinates
        
        for polygon in landuse_polygons:
            landuse_type = polygon.get('properties', {}).get('landuse')
            if not landuse_type or landuse_type not in self.landuse_influences:
                continue
            
            influence = self.landuse_influences[landuse_type]
            
            # Calculate distance from stop to polygon centroid
            centroid_lon, centroid_lat = self._calculate_polygon_centroid(polygon)
            distance_m = self._haversine_distance(stop_lat, stop_lon, centroid_lat, centroid_lon)
            
            # Check if within influence radius
            if distance_m <= influence.radius_of_influence_m:
                # Apply distance decay
                distance_factor = max(0.1, 1.0 - (distance_m / influence.radius_of_influence_m))
                
                # Apply time-based multiplier
                time_multiplier = influence.time_patterns.get(time_hour, 
                                                           influence.time_patterns.get('default', 1.0))
                
                # Calculate polygon area influence (larger areas have more influence)
                area_factor = min(2.0, self._calculate_polygon_area_factor(polygon))
                
                # Combine all factors
                base_influence = (influence.passenger_multiplier * 
                                distance_factor * 
                                time_multiplier * 
                                area_factor)
                
                # Apply to boarding vs alighting
                boarding_influence = base_influence * influence.boarding_ratio
                alighting_influence = base_influence * (1 - influence.boarding_ratio)
                
                total_boarding_multiplier += boarding_influence * 0.1  # Scale down to reasonable levels
                total_alighting_multiplier += alighting_influence * 0.1
                
                landuse_breakdown[f"{landuse_type}_{distance_m:.0f}m"] = {
                    'boarding_influence': boarding_influence,
                    'alighting_influence': alighting_influence,
                    'distance_m': distance_m,
                    'area_factor': area_factor
                }
        
        return {
            'boarding_multiplier': total_boarding_multiplier,
            'alighting_multiplier': total_alighting_multiplier,
            'landuse_breakdown': landuse_breakdown
        }
    
    def _calculate_polygon_centroid(self, polygon: Dict) -> Tuple[float, float]:
        """Calculate the centroid of a polygon"""
        coordinates = polygon['geometry']['coordinates']
        
        # Handle MultiPolygon vs Polygon
        if polygon['geometry']['type'] == 'MultiPolygon':
            # Use first polygon for simplicity
            coords = coordinates[0][0]
        else:
            coords = coordinates[0]
        
        # Simple centroid calculation
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        
        return sum(lons) / len(lons), sum(lats) / len(lats)
    
    def _calculate_polygon_area_factor(self, polygon: Dict) -> float:
        """Calculate area-based influence factor"""
        # Simplified area calculation - in reality would use proper geographic area
        coordinates = polygon['geometry']['coordinates']
        
        if polygon['geometry']['type'] == 'MultiPolygon':
            coords = coordinates[0][0]
        else:
            coords = coordinates[0]
        
        # Simple bounding box area as proxy
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        
        lon_span = max(lons) - min(lons)
        lat_span = max(lats) - min(lats)
        
        # Convert to rough area factor (larger = more influence)
        area_factor = math.sqrt(lon_span * lat_span) * 10000  # Scale to reasonable range
        return min(3.0, max(0.5, area_factor))  # Clamp between 0.5 and 3.0
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def enhance_existing_model(self, current_model_path: str, landuse_data_path: str) -> Dict:
        """
        Enhance the existing passenger model with landuse data.
        
        This would:
        1. Load current model (extracted_route_1_model.json)
        2. Load landuse data (landuse.geojson) 
        3. For each stop, calculate landuse influences
        4. Adjust passenger rates based on nearby landuse
        5. Return enhanced model
        """
        
        # Load current model
        with open(current_model_path, 'r') as f:
            current_model = json.load(f)
        
        # Load landuse data
        with open(landuse_data_path, 'r') as f:
            landuse_data = json.load(f)
        
        # Enhance each location in the model
        enhanced_locations = {}
        
        for location_id, location_data in current_model['locations'].items():
            # Get stop coordinates (would need to be added to model or looked up)
            stop_coords = self._get_stop_coordinates(location_id)
            
            if stop_coords:
                # Calculate landuse influences
                influences = self.calculate_landuse_influence_for_stop(
                    stop_coords, 
                    landuse_data['features']
                )
                
                # Apply influences to passenger rates
                enhanced_location = self._apply_landuse_influences(location_data, influences)
                enhanced_locations[location_id] = enhanced_location
            else:
                enhanced_locations[location_id] = location_data
        
        # Create enhanced model
        enhanced_model = current_model.copy()
        enhanced_model['locations'] = enhanced_locations
        enhanced_model['landuse_integration'] = {
            'enabled': True,
            'landuse_data_source': landuse_data_path,
            'integration_date': '2025-09-13',
            'influence_types': list(self.landuse_influences.keys())
        }
        
        return enhanced_model
    
    def _get_stop_coordinates(self, location_id: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a stop - would be looked up from stops database"""
        # Example coordinates - in reality would come from stops data
        coordinates = {
            'BRIDGETOWN_TERMINAL': (-59.6198, 13.1067),  # Central Bridgetown
            'DEPOT_MAIN': (-59.6462136, 13.2809774),     # Actual depot coordinates
            'UNIVERSITY_MAIN': (-59.6240, 13.1340)       # Near University area
        }
        return coordinates.get(location_id)
    
    def _apply_landuse_influences(self, location_data: Dict, influences: Dict) -> Dict:
        """Apply landuse influences to location passenger rates"""
        enhanced_location = location_data.copy()
        
        # Apply multipliers to passenger rates
        boarding_mult = influences['boarding_multiplier']
        alighting_mult = influences['alighting_multiplier']
        
        # Update peak hours rates
        if 'passenger_rates' in enhanced_location and 'peak_hours' in enhanced_location['passenger_rates']:
            peak_rates = enhanced_location['passenger_rates']['peak_hours']
            
            if 'boarding' in peak_rates:
                peak_rates['boarding']['rate_per_hour'] *= boarding_mult
            
            if 'alighting' in peak_rates:
                peak_rates['alighting']['rate_per_hour'] *= alighting_mult
        
        # Add landuse analysis
        enhanced_location['landuse_analysis'] = {
            'boarding_multiplier': boarding_mult,
            'alighting_multiplier': alighting_mult,
            'nearby_landuse': influences['landuse_breakdown']
        }
        
        return enhanced_location


def demonstrate_landuse_integration():
    """Demonstrate how landuse data would enhance the passenger model"""
    
    print("🏘️ LANDUSE-ENHANCED PASSENGER MODEL CONCEPT")
    print("=" * 60)
    
    model = LanduseEnhancedPassengerModel()
    
    # Show landuse influence definitions
    print("\n📊 LANDUSE INFLUENCE FACTORS:")
    for landuse_type, influence in model.landuse_influences.items():
        print(f"\n{landuse_type.upper()}:")
        print(f"  • Passenger Multiplier: {influence.passenger_multiplier}x")
        print(f"  • Peak Factor: {influence.peak_factor}x")
        print(f"  • Boarding Ratio: {influence.boarding_ratio}")
        print(f"  • Influence Radius: {influence.radius_of_influence_m}m")
    
    # Simulate landuse analysis for a stop
    print(f"\n🚏 EXAMPLE: DEPOT_MAIN STOP ANALYSIS")
    print("-" * 40)
    
    # Example landuse polygons near depot
    example_landuse = [
        {
            'properties': {'landuse': 'industrial'},
            'geometry': {
                'type': 'Polygon',
                'coordinates': [[[-59.646, 13.280], [-59.647, 13.280], [-59.647, 13.281], [-59.646, 13.281], [-59.646, 13.280]]]
            }
        },
        {
            'properties': {'landuse': 'residential'},
            'geometry': {
                'type': 'Polygon', 
                'coordinates': [[[-59.645, 13.279], [-59.646, 13.279], [-59.646, 13.280], [-59.645, 13.280], [-59.645, 13.279]]]
            }
        }
    ]
    
    # Calculate influences
    depot_coords = (-59.6462136, 13.2809774)
    influences = model.calculate_landuse_influence_for_stop(depot_coords, example_landuse, '07:00')
    
    print(f"Boarding Multiplier: {influences['boarding_multiplier']:.2f}x")
    print(f"Alighting Multiplier: {influences['alighting_multiplier']:.2f}x")
    
    print("\n🔍 NEARBY LANDUSE BREAKDOWN:")
    for landuse_id, data in influences['landuse_breakdown'].items():
        print(f"  • {landuse_id}")
        print(f"    - Boarding influence: {data['boarding_influence']:.2f}")
        print(f"    - Alighting influence: {data['alighting_influence']:.2f}")
        print(f"    - Distance: {data['distance_m']:.0f}m")
    
    print(f"\n✨ ENHANCED MODEL BENEFITS:")
    print("  • More accurate passenger predictions based on land development")
    print("  • Time-sensitive adjustments (rush hour vs off-peak)")
    print("  • Differentiated boarding/alighting patterns")
    print("  • Distance decay effects from landuse influence")
    print("  • Adaptable to urban development changes")


if __name__ == "__main__":
    demonstrate_landuse_integration()