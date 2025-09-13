#!/usr/bin/env python3
"""
Agnostic People Simulation System

This system models passenger distribution based on:
- Peak times and real-world temporal patterns
- Route specifications
- Depot/hub designations
- Dynamic landuse analysis (format-agnostic)

The system is completely agnostic to landuse data format and can adapt to any
<country>_landuse.geojson file placed in passenger_analytics/location/
"""

import json
import math
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import random
from abc import ABC, abstractmethod

@dataclass
class PassengerProfile:
    """Individual passenger characteristics"""
    passenger_id: str
    origin_lat: float
    origin_lon: float
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    trip_purpose: str = "commute"
    time_flexibility: float = 0.3  # How flexible with timing (0=rigid, 1=very flexible)
    group_size: int = 1
    boarding_stop_id: Optional[str] = None
    alighting_stop_id: Optional[str] = None
    generation_time: Optional[datetime] = None

@dataclass
class RouteStop:
    """Stop along a route"""
    stop_id: str
    stop_name: str
    latitude: float
    longitude: float
    is_depot: bool = False
    is_hub: bool = False
    stop_type: str = "regular"  # regular, depot, hub, terminus

@dataclass
class RouteDefinition:
    """Complete route definition"""
    route_id: str
    route_name: str
    stops: List[RouteStop]
    direction: str = "forward"
    service_frequency_minutes: int = 15

@dataclass
class PeakTimePattern:
    """Defines peak time characteristics"""
    pattern_name: str
    start_hour: int
    end_hour: int
    intensity_multiplier: float
    passenger_flow_direction: str  # "to_depot", "from_depot", "balanced"

class LanduseAnalyzer:
    """Agnostic landuse data analyzer - adapts to any GeoJSON format"""
    
    def __init__(self):
        self.landuse_cache = {}
        self.analysis_cache = {}
    
    def load_landuse_data(self, country_code: str) -> Optional[Dict]:
        """Load landuse data for a country"""
        landuse_path = Path("passenger_analytics/location") / f"{country_code}_landuse.geojson"
        
        if not landuse_path.exists():
            print(f"⚠️ No landuse data found for {country_code} at {landuse_path}")
            return None
        
        try:
            with open(landuse_path, 'r') as f:
                data = json.load(f)
                self.landuse_cache[country_code] = data
                return data
        except Exception as e:
            print(f"❌ Error loading landuse data: {e}")
            return None
    
    def analyze_landuse_properties(self, landuse_data: Dict) -> Dict[str, Any]:
        """Analyze landuse data to understand its structure and extract patterns"""
        if not landuse_data or 'features' not in landuse_data:
            return {}
        
        analysis = {
            'total_features': len(landuse_data['features']),
            'property_types': {},
            'landuse_categories': {},
            'density_indicators': {},
            'passenger_generation_potential': {}
        }
        
        # Analyze all properties to understand the data structure
        all_properties = set()
        landuse_values = set()
        
        for feature in landuse_data['features']:
            props = feature.get('properties', {})
            
            # Collect all property keys
            all_properties.update(props.keys())
            
            # Extract landuse/category information (agnostic approach)
            for key, value in props.items():
                if value and isinstance(value, str):
                    # Look for landuse-like properties
                    if any(keyword in key.lower() for keyword in ['landuse', 'category', 'type', 'class']):
                        landuse_values.add(value)
                        if key not in analysis['landuse_categories']:
                            analysis['landuse_categories'][key] = {}
                        if value not in analysis['landuse_categories'][key]:
                            analysis['landuse_categories'][key][value] = 0
                        analysis['landuse_categories'][key][value] += 1
        
        analysis['available_properties'] = list(all_properties)
        analysis['detected_landuse_values'] = list(landuse_values)
        
        # Infer passenger generation potential from property names and values
        self._infer_passenger_generation_patterns(analysis)
        
        return analysis
    
    def _infer_passenger_generation_patterns(self, analysis: Dict):
        """Infer passenger generation patterns from landuse categories"""
        # High passenger generation keywords
        high_generation = ['residential', 'commercial', 'retail', 'office', 'school', 'university', 
                          'hospital', 'apartments', 'housing', 'shopping', 'market']
        
        # Medium passenger generation keywords  
        medium_generation = ['industrial', 'warehouse', 'factory', 'business', 'mixed',
                           'institutional', 'government', 'civic']
        
        # Low passenger generation keywords
        low_generation = ['farmland', 'agricultural', 'forest', 'park', 'grass', 'vacant',
                         'water', 'quarry', 'cemetery']
        
        generation_potential = {}
        
        for category_key, values in analysis['landuse_categories'].items():
            for value, count in values.items():
                value_lower = value.lower()
                
                # Classify passenger generation potential
                if any(keyword in value_lower for keyword in high_generation):
                    potential = 'high'
                    multiplier = 2.5
                elif any(keyword in value_lower for keyword in medium_generation):
                    potential = 'medium' 
                    multiplier = 1.5
                elif any(keyword in value_lower for keyword in low_generation):
                    potential = 'low'
                    multiplier = 0.5
                else:
                    potential = 'unknown'
                    multiplier = 1.0
                
                generation_potential[value] = {
                    'potential': potential,
                    'multiplier': multiplier,
                    'count': count,
                    'category_key': category_key
                }
        
        analysis['passenger_generation_potential'] = generation_potential
    
    def get_landuse_influence_at_location(self, latitude: float, longitude: float, 
                                        country_code: str, radius_m: float = 500) -> Dict:
        """Get landuse influence at a specific location"""
        landuse_data = self.landuse_cache.get(country_code)
        if not landuse_data:
            landuse_data = self.load_landuse_data(country_code)
        
        if not landuse_data:
            return {'total_influence': 1.0, 'influences': []}
        
        influences = []
        total_influence = 1.0
        
        for feature in landuse_data['features']:
            # Calculate distance to feature
            centroid_lat, centroid_lon = self._get_feature_centroid(feature)
            distance_m = self._haversine_distance(latitude, longitude, centroid_lat, centroid_lon)
            
            if distance_m <= radius_m:
                # Get landuse properties
                props = feature.get('properties', {})
                landuse_influence = self._extract_landuse_influence(props, distance_m, radius_m)
                
                if landuse_influence['influence'] > 0:
                    influences.append(landuse_influence)
                    total_influence += landuse_influence['influence'] * 0.1  # Scale influence
        
        return {
            'total_influence': min(total_influence, 5.0),  # Cap maximum influence
            'influences': influences,
            'location': {'lat': latitude, 'lon': longitude, 'radius_m': radius_m}
        }
    
    def _extract_landuse_influence(self, properties: Dict, distance_m: float, radius_m: float) -> Dict:
        """Extract influence from landuse properties (agnostic)"""
        influence = 0.0
        landuse_type = "unknown"
        passenger_potential = 1.0
        
        # Look for any property that might indicate landuse
        for key, value in properties.items():
            if value and isinstance(value, str):
                if any(keyword in key.lower() for keyword in ['landuse', 'category', 'type', 'class']):
                    landuse_type = value
                    
                    # Get passenger generation potential
                    analysis = self.analysis_cache.get('current_analysis', {})
                    gen_potential = analysis.get('passenger_generation_potential', {})
                    
                    if value in gen_potential:
                        passenger_potential = gen_potential[value]['multiplier']
                    
                    break
        
        # Calculate distance decay factor
        distance_factor = max(0.1, 1.0 - (distance_m / radius_m))
        
        # Calculate influence
        influence = passenger_potential * distance_factor
        
        return {
            'landuse_type': landuse_type,
            'influence': influence,
            'distance_m': distance_m,
            'distance_factor': distance_factor,
            'passenger_potential': passenger_potential,
            'properties': properties
        }
    
    def _get_feature_centroid(self, feature: Dict) -> Tuple[float, float]:
        """Calculate centroid of a geographic feature"""
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates', [])
        
        if not coordinates:
            return 0.0, 0.0
        
        # Handle different geometry types
        geom_type = geometry.get('type', '')
        
        if geom_type == 'Point':
            return coordinates[1], coordinates[0]  # lat, lon
        elif geom_type == 'Polygon':
            coords = coordinates[0]  # Outer ring
        elif geom_type == 'MultiPolygon':
            coords = coordinates[0][0]  # First polygon, outer ring
        else:
            coords = coordinates
        
        # Calculate centroid
        if coords and len(coords) > 0:
            lats = [coord[1] for coord in coords if len(coord) >= 2]
            lons = [coord[0] for coord in coords if len(coord) >= 2]
            
            if lats and lons:
                return sum(lats) / len(lats), sum(lons) / len(lons)
        
        return 0.0, 0.0
    
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

class PeakTimeModelingSystem:
    """Models passenger distribution based on peak times and real-world patterns"""
    
    def __init__(self):
        self.peak_patterns = self._initialize_peak_patterns()
    
    def _initialize_peak_patterns(self) -> List[PeakTimePattern]:
        """Initialize standard peak time patterns"""
        return [
            PeakTimePattern("morning_commute", 6, 9, 3.5, "to_depot"),
            PeakTimePattern("midday_moderate", 10, 14, 1.2, "balanced"),
            PeakTimePattern("afternoon_school", 15, 16, 2.0, "from_depot"),
            PeakTimePattern("evening_commute", 17, 19, 3.0, "from_depot"),
            PeakTimePattern("evening_leisure", 20, 22, 1.5, "balanced"),
            PeakTimePattern("night_minimal", 23, 5, 0.3, "balanced")
        ]
    
    def get_current_peak_pattern(self, current_time: datetime) -> PeakTimePattern:
        """Get the current peak pattern based on time"""
        current_hour = current_time.hour
        
        for pattern in self.peak_patterns:
            if pattern.start_hour <= pattern.end_hour:
                # Normal range (e.g., 6-9)
                if pattern.start_hour <= current_hour <= pattern.end_hour:
                    return pattern
            else:
                # Overnight range (e.g., 23-5)
                if current_hour >= pattern.start_hour or current_hour <= pattern.end_hour:
                    return pattern
        
        # Default to moderate pattern
        return PeakTimePattern("default", current_hour, current_hour, 1.0, "balanced")
    
    def calculate_passenger_generation_rate(self, current_time: datetime, 
                                          base_rate: float, 
                                          location_influence: float = 1.0) -> float:
        """Calculate passenger generation rate based on time and location"""
        peak_pattern = self.get_current_peak_pattern(current_time)
        
        # Apply peak time multiplier
        time_adjusted_rate = base_rate * peak_pattern.intensity_multiplier
        
        # Apply location influence
        final_rate = time_adjusted_rate * location_influence
        
        # Add some random variation (±20%)
        variation = random.uniform(0.8, 1.2)
        
        return final_rate * variation

class AgnosticPeopleSimulationSystem:
    """Main people simulation system - agnostic to landuse data format"""
    
    def __init__(self, country_code: str = "barbados"):
        self.country_code = country_code
        self.landuse_analyzer = LanduseAnalyzer()
        self.peak_time_system = PeakTimeModelingSystem()
        self.active_passengers = {}
        self.generation_stats = {
            'total_generated': 0,
            'generation_rate_history': [],
            'peak_patterns_used': []
        }
        
        # Load and analyze landuse data
        self._initialize_landuse_analysis()
    
    def _initialize_landuse_analysis(self):
        """Initialize landuse analysis for the country"""
        print(f"🌍 Initializing landuse analysis for {self.country_code}...")
        
        landuse_data = self.landuse_analyzer.load_landuse_data(self.country_code)
        if landuse_data:
            analysis = self.landuse_analyzer.analyze_landuse_properties(landuse_data)
            self.landuse_analyzer.analysis_cache['current_analysis'] = analysis
            
            print(f"✅ Loaded {analysis['total_features']} landuse features")
            print(f"📊 Detected landuse categories: {len(analysis['detected_landuse_values'])}")
            
            # Show passenger generation potential
            gen_potential = analysis.get('passenger_generation_potential', {})
            high_gen = [k for k, v in gen_potential.items() if v['potential'] == 'high']
            medium_gen = [k for k, v in gen_potential.items() if v['potential'] == 'medium']
            
            if high_gen:
                print(f"🚀 High passenger generation areas: {', '.join(high_gen[:5])}")
            if medium_gen:
                print(f"🔄 Medium passenger generation areas: {', '.join(medium_gen[:5])}")
        else:
            print(f"⚠️ Using default passenger generation patterns (no landuse data)")
    
    def generate_passengers_for_route(self, route: RouteDefinition, 
                                    current_time: datetime,
                                    generation_duration_minutes: int = 15) -> List[PassengerProfile]:
        """Generate passengers for a specific route"""
        generated_passengers = []
        
        print(f"\n🚌 Generating passengers for Route {route.route_id} at {current_time.strftime('%H:%M')}")
        
        for stop in route.stops:
            # Get landuse influence at this stop
            landuse_influence = self.landuse_analyzer.get_landuse_influence_at_location(
                stop.latitude, stop.longitude, self.country_code
            )
            
            # Determine base passenger rate based on stop type
            base_rate = self._get_base_passenger_rate(stop)
            
            # Calculate actual generation rate
            generation_rate = self.peak_time_system.calculate_passenger_generation_rate(
                current_time, base_rate, landuse_influence['total_influence']
            )
            
            # Generate passengers for this time period
            passengers_count = max(0, int(generation_rate * (generation_duration_minutes / 60)))
            
            # Add some Poisson variation for realism
            if passengers_count > 0:
                passengers_count = max(0, int(random.gauss(passengers_count, math.sqrt(passengers_count))))
            
            # Generate individual passengers
            stop_passengers = self._generate_passengers_at_stop(
                stop, passengers_count, current_time, route
            )
            
            generated_passengers.extend(stop_passengers)
            
            if stop_passengers:
                print(f"  👥 {stop.stop_name}: {len(stop_passengers)} passengers "
                      f"(rate: {generation_rate:.1f}/hr, influence: {landuse_influence['total_influence']:.1f}x)")
        
        # Update statistics
        self.generation_stats['total_generated'] += len(generated_passengers)
        self.generation_stats['generation_rate_history'].append({
            'time': current_time,
            'route_id': route.route_id,
            'passengers_generated': len(generated_passengers)
        })
        
        return generated_passengers
    
    def _get_base_passenger_rate(self, stop: RouteStop) -> float:
        """Get base passenger generation rate based on stop type"""
        if stop.is_depot:
            return 80.0  # High rate for depots - transport workers, connecting passengers
        elif stop.is_hub:
            return 120.0  # Very high rate for hubs - transfer point
        elif stop.stop_type == "terminus":
            return 60.0  # High rate for terminals
        else:
            return 25.0  # Standard rate for regular stops
    
    def _generate_passengers_at_stop(self, stop: RouteStop, passenger_count: int,
                                   current_time: datetime, route: RouteDefinition) -> List[PassengerProfile]:
        """Generate individual passengers at a specific stop"""
        passengers = []
        
        for i in range(passenger_count):
            # Determine trip characteristics based on stop type and time
            trip_purpose = self._determine_trip_purpose(stop, current_time)
            group_size = self._determine_group_size(trip_purpose)
            
            # Create passenger profile
            passenger = PassengerProfile(
                passenger_id=f"{stop.stop_id}_{current_time.strftime('%H%M%S')}_{i:03d}",
                origin_lat=stop.latitude + random.uniform(-0.001, 0.001),  # Small variation
                origin_lon=stop.longitude + random.uniform(-0.001, 0.001),
                trip_purpose=trip_purpose,
                group_size=group_size,
                boarding_stop_id=stop.stop_id,
                generation_time=current_time
            )
            
            # Determine destination based on depot/hub logic
            passenger = self._assign_destination(passenger, stop, route, current_time)
            
            passengers.append(passenger)
        
        return passengers
    
    def _determine_trip_purpose(self, stop: RouteStop, current_time: datetime) -> str:
        """Determine trip purpose based on stop type and time"""
        hour = current_time.hour
        
        if stop.is_depot:
            if 5 <= hour <= 8:
                return "work_commute"
            elif 16 <= hour <= 19:
                return "return_commute"
            else:
                return "work_related"
        elif stop.is_hub:
            return "transfer"
        elif 6 <= hour <= 9:
            return "work_commute"
        elif 15 <= hour <= 16:
            return "school"
        elif 17 <= hour <= 19:
            return "return_commute"
        elif 20 <= hour <= 22:
            return "leisure"
        else:
            return "other"
    
    def _determine_group_size(self, trip_purpose: str) -> int:
        """Determine group size based on trip purpose"""
        if trip_purpose == "leisure":
            return random.choices([1, 2, 3, 4], weights=[0.3, 0.5, 0.15, 0.05])[0]
        elif trip_purpose == "school":
            return random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        else:
            return random.choices([1, 2], weights=[0.8, 0.2])[0]
    
    def _assign_destination(self, passenger: PassengerProfile, origin_stop: RouteStop,
                          route: RouteDefinition, current_time: datetime) -> PassengerProfile:
        """Assign destination based on depot/hub logic and time patterns"""
        peak_pattern = self.peak_time_system.get_current_peak_pattern(current_time)
        
        # Special logic for depot/hub stops
        if origin_stop.is_depot:
            if peak_pattern.passenger_flow_direction == "from_depot":
                # Peak times: depot workers going home/to city
                destination_stops = [s for s in route.stops if not s.is_depot and not s.is_hub]
            else:
                # Off-peak: various destinations including other depots/hubs
                destination_stops = [s for s in route.stops if s.stop_id != origin_stop.stop_id]
        elif origin_stop.is_hub:
            # Hubs distribute to all directions
            destination_stops = [s for s in route.stops if s.stop_id != origin_stop.stop_id]
        else:
            # Regular stops
            if peak_pattern.passenger_flow_direction == "to_depot":
                # Morning commute: toward depots/hubs/work areas
                destination_stops = [s for s in route.stops if s.is_depot or s.is_hub]
                if not destination_stops:
                    destination_stops = route.stops[-3:]  # Last few stops if no depot/hub
            elif peak_pattern.passenger_flow_direction == "from_depot":
                # Evening commute: away from work areas
                destination_stops = [s for s in route.stops if not s.is_depot and not s.is_hub]
            else:
                # Balanced: any destination
                destination_stops = [s for s in route.stops if s.stop_id != origin_stop.stop_id]
        
        if destination_stops:
            dest_stop = random.choice(destination_stops)
            passenger.destination_lat = dest_stop.latitude
            passenger.destination_lon = dest_stop.longitude
            passenger.alighting_stop_id = dest_stop.stop_id
        
        return passenger
    
    async def start_real_time_generation(self, route: RouteDefinition, 
                                       generation_interval_seconds: int = 30):
        """Start real-time passenger generation for a route"""
        print(f"\n🕐 Starting real-time passenger generation for Route {route.route_id}")
        print(f"⏱️ Generation interval: {generation_interval_seconds} seconds")
        print("Press Ctrl+C to stop...\n")
        
        try:
            while True:
                current_time = datetime.now()
                
                # Generate passengers
                passengers = self.generate_passengers_for_route(
                    route, current_time, 
                    generation_duration_minutes=generation_interval_seconds/60
                )
                
                # Store active passengers
                for passenger in passengers:
                    self.active_passengers[passenger.passenger_id] = passenger
                
                # Show summary
                if passengers:
                    print(f"✅ Generated {len(passengers)} passengers at {current_time.strftime('%H:%M:%S')}")
                    print(f"📊 Total active passengers: {len(self.active_passengers)}")
                
                # Wait for next generation cycle
                await asyncio.sleep(generation_interval_seconds)
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Stopping real-time generation. Total generated: {self.generation_stats['total_generated']}")

def create_example_route() -> RouteDefinition:
    """Create an example route with depot and hub designations"""
    stops = [
        RouteStop("DEPOT_MAIN", "Main Depot", 13.2809774, -59.6462136, is_depot=True),
        RouteStop("BRIDGETOWN_HUB", "Bridgetown Hub", 13.1067, -59.6198, is_hub=True),
        RouteStop("UNIVERSITY_STOP", "University", 13.1340, -59.6240),
        RouteStop("COMMERCIAL_AREA", "Commercial District", 13.1200, -59.6100),
        RouteStop("RESIDENTIAL_ZONE", "Residential Area", 13.1400, -59.6000),
        RouteStop("INDUSTRIAL_PARK", "Industrial Park", 13.1500, -59.5900)
    ]
    
    return RouteDefinition(
        route_id="ROUTE_1",
        route_name="Main Route with Depot",
        stops=stops,
        service_frequency_minutes=15
    )

async def demonstrate_agnostic_people_simulation():
    """Demonstrate the agnostic people simulation system"""
    print("🎯 AGNOSTIC PEOPLE SIMULATION SYSTEM")
    print("=" * 60)
    
    # Initialize system (will try to load barbados_landuse.geojson)
    sim_system = AgnosticPeopleSimulationSystem("barbados")
    
    # Create example route
    route = create_example_route()
    
    print(f"\n🗺️ ROUTE DEFINITION:")
    print(f"Route: {route.route_name} ({route.route_id})")
    for stop in route.stops:
        stop_type = "🏢 DEPOT" if stop.is_depot else "🔄 HUB" if stop.is_hub else "🚏 STOP"
        print(f"  {stop_type} {stop.stop_name}")
    
    # Generate passengers for current time
    current_time = datetime.now()
    passengers = sim_system.generate_passengers_for_route(route, current_time)
    
    print(f"\n📈 GENERATION SUMMARY:")
    print(f"Total passengers generated: {len(passengers)}")
    
    if passengers:
        print(f"\n👥 SAMPLE PASSENGERS:")
        for i, passenger in enumerate(passengers[:5]):  # Show first 5
            print(f"  {i+1}. {passenger.passenger_id}")
            print(f"     Trip: {passenger.boarding_stop_id} → {passenger.alighting_stop_id}")
            print(f"     Purpose: {passenger.trip_purpose}, Group: {passenger.group_size}")
    
    # Ask if user wants real-time simulation
    print(f"\n🚀 Real-time simulation available!")
    print("This system will:")
    print("• Generate passengers every 30 seconds")
    print("• Adapt to current time and peak patterns")
    print("• Use landuse data if available")
    print("• Handle depot/hub passenger flows")
    
    return sim_system, route

if __name__ == "__main__":
    asyncio.run(demonstrate_agnostic_people_simulation())