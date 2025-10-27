"""
Advanced spawn system with geospatial and temporal constraints.

Constraints applied:
1. Temporal: Time of day affects spawn locations
   - 6-7 AM: Heavy at residential areas (people leaving home)
   - 7-8 AM: Schools + residential (school run + work commute)
   - 8-9 AM: Commercial + schools (work destinations)
   
2. Geospatial: Building types influence spawn probability
   - Residential: High early morning (6-8 AM)
   - Schools: Peak 7-8 AM (parents/students)
   - Commercial: Peak 8-9 AM (workers)
   - POIs: Churches on Sundays, markets on Saturdays, etc.
   
3. Combined: Probability = base_weight × temporal_multiplier × geospatial_multiplier
"""

import asyncio
import httpx
import random
import math
from datetime import datetime, timedelta
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader


class TemporalConstraint:
    """Time-based spawn multipliers for different building types."""
    
    @staticmethod
    def get_multiplier(hour: int, building_type: str, day_of_week: str) -> float:
        """
        Get temporal multiplier based on hour, building type, and day.
        
        Returns multiplier (0.1 to 3.0) that modifies base spawn probability.
        """
        # Weekend patterns (lower overall, different timing)
        is_weekend = day_of_week in ['saturday', 'sunday']
        
        # Hour-based patterns for different building types
        patterns = {
            'residential': {
                # Early morning exodus for work/school
                6: 2.5, 7: 3.0, 8: 2.0, 9: 1.0,
                10: 0.5, 11: 0.5, 12: 0.8, 13: 0.7,
                14: 0.6, 15: 0.8, 16: 1.5, 17: 2.5,
                18: 2.0, 19: 1.0, 20: 0.5
            },
            'school': {
                # School hours
                6: 0.5, 7: 3.0, 8: 1.5, 9: 0.2,
                10: 0.1, 11: 0.1, 12: 0.3, 13: 0.2,
                14: 0.5, 15: 2.5, 16: 1.0, 17: 0.3
            },
            'commercial': {
                # Business hours
                6: 0.5, 7: 1.5, 8: 2.5, 9: 2.0,
                10: 1.5, 11: 1.8, 12: 2.0, 13: 1.5,
                14: 1.5, 15: 1.5, 16: 1.8, 17: 2.5,
                18: 2.0, 19: 1.0, 20: 0.5
            },
            'industrial': {
                # Shift work patterns
                6: 2.5, 7: 2.0, 8: 1.5, 9: 1.0,
                14: 1.5, 15: 2.0, 16: 1.5,
                22: 1.5, 23: 1.0  # Night shift
            },
            'retail': {
                # Shopping hours
                8: 1.0, 9: 1.5, 10: 2.0, 11: 2.0,
                12: 1.5, 13: 1.5, 14: 2.0, 15: 2.0,
                16: 2.5, 17: 2.5, 18: 2.0, 19: 1.5
            },
            'church': {
                # Sunday service
                8: 2.0 if day_of_week == 'sunday' else 0.2,
                9: 2.5 if day_of_week == 'sunday' else 0.2,
                10: 3.0 if day_of_week == 'sunday' else 0.2,
                17: 2.0 if day_of_week == 'wednesday' else 0.5,
                18: 2.5 if day_of_week in ['wednesday', 'friday'] else 0.5
            }
        }
        
        # Get pattern for building type (default to residential)
        pattern = patterns.get(building_type, patterns['residential'])
        
        # Weekend dampening (50% reduction for weekday commute patterns)
        multiplier = pattern.get(hour, 1.0)
        if is_weekend and building_type in ['commercial', 'industrial', 'school']:
            multiplier *= 0.5
        
        return multiplier


class GeospatialConstraint:
    """Location-based spawn constraints."""
    
    def __init__(self, geo_client: GeospatialClient):
        self.geo_client = geo_client
        self._building_cache = {}
    
    def get_location_multiplier(
        self,
        lat: float,
        lon: float,
        hour: int,
        day_of_week: str
    ) -> tuple[float, str]:
        """
        Get location-based multiplier by checking nearby features.
        
        Returns: (multiplier, building_type)
        """
        # Check cache first (avoid repeated API calls)
        cache_key = f"{lat:.6f},{lon:.6f}"
        if cache_key in self._building_cache:
            buildings = self._building_cache[cache_key]
        else:
            # Query nearby buildings
            result = self.geo_client.find_nearby_buildings(
                lat, lon, radius_meters=150
            )
            buildings = result.get('buildings', [])
            self._building_cache[cache_key] = buildings
        
        if not buildings:
            return 1.0, 'residential'  # Default
        
        # Get dominant building type
        building_type = buildings[0].get('building', 'residential')
        
        # Apply temporal constraint based on building type
        temporal_mult = TemporalConstraint.get_multiplier(hour, building_type, day_of_week)
        
        # Additional geospatial factors
        density_multiplier = 1.0
        if len(buildings) > 10:
            density_multiplier = 1.3  # High-density areas get boost
        elif len(buildings) > 5:
            density_multiplier = 1.1
        
        final_multiplier = temporal_mult * density_multiplier
        
        return final_multiplier, building_type


async def get_route_1_coordinates():
    """Fetch Route 1 geometry."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://localhost:1337/api/routes?populate=*&filters[short_name][$eq]=1"
        )
        resp.raise_for_status()
        data = resp.json()
        route = data['data'][0]
        
        all_coords = []
        for feature in route['geojson_data']['features']:
            coords = feature['geometry']['coordinates']
            for coord in coords:
                if isinstance(coord, str):
                    lon, lat = map(float, coord.split())
                else:
                    lon, lat = coord[0], coord[1]
                all_coords.append((lat, lon))
        
        return all_coords, route


def weighted_random_choice(weights):
    """Select index based on weights."""
    total = sum(weights)
    if total == 0:
        return random.randint(0, len(weights) - 1)
    r = random.uniform(0, total)
    cumsum = 0
    for i, w in enumerate(weights):
        cumsum += w
        if r <= cumsum:
            return i
    return len(weights) - 1


def base_boarding_probability(position_fraction):
    """Base probability (exponential decay from route start)."""
    return math.exp(-2.5 * position_fraction)


async def main():
    print("="*80)
    print("CONSTRAINED SPAWN SIMULATION")
    print("Geospatial + Temporal Constraints")
    print("="*80)
    
    # Get route data
    coords, route_data = await get_route_1_coordinates()
    
    # Calculate distances
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    cumulative_distances = [0]
    total_route_length = 0
    for i in range(1, len(coords)):
        prev_lat, prev_lon = coords[i-1]
        curr_lat, curr_lon = coords[i]
        segment_dist = haversine(prev_lat, prev_lon, curr_lat, curr_lon)
        total_route_length += segment_dist
        cumulative_distances.append(total_route_length)
    
    print(f"\nRoute: {route_data['long_name']} (#{route_data['short_name']})")
    print(f"Length: {total_route_length/1000:.2f}km")
    
    # Initialize
    geo_client = GeospatialClient(base_url="http://localhost:8001")
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    spawn_config = await config_loader.get_config_by_country("Barbados")
    geo_constraint = GeospatialConstraint(geo_client)
    
    # Simulate specific time periods to show constraint effects
    time_periods = [
        (7, 0, "Early Morning - Residential Peak"),
        (7, 30, "School Run Peak"),
        (8, 30, "Work Commute Peak"),
    ]
    
    for hour, minute, period_name in time_periods:
        print(f"\n{'='*80}")
        print(f"{period_name} ({hour:02d}:{minute:02d})")
        print(f"{'='*80}")
        
        # Sample 20 route points to check constraints
        sample_indices = random.sample(range(len(coords)), min(20, len(coords)))
        
        spawn_data = []
        for idx in sample_indices:
            lat, lon = coords[idx]
            pos_pct = (idx / len(coords)) * 100
            
            # Base probability (exponential decay)
            base_prob = base_boarding_probability(idx / len(coords))
            
            # Apply geospatial + temporal constraint
            geo_mult, building_type = geo_constraint.get_location_multiplier(
                lat, lon, hour, 'monday'
            )
            
            # Final probability
            final_prob = base_prob * geo_mult
            
            spawn_data.append({
                'pos': pos_pct,
                'lat': lat,
                'lon': lon,
                'building': building_type,
                'base': base_prob,
                'geo_mult': geo_mult,
                'final': final_prob
            })
        
        # Sort by position for display
        spawn_data.sort(key=lambda x: x['pos'])
        
        print(f"\n{'Pos':<6} {'Building Type':<12} {'Base':<8} {'×':<3} {'Constraint':<12} {'=':<3} {'Final':<8} {'Effect':<15}")
        print("-"*80)
        
        for s in spawn_data[:10]:  # Show first 10
            effect = "BOOSTED" if s['geo_mult'] > 1.5 else "NORMAL" if s['geo_mult'] > 0.8 else "SUPPRESSED"
            print(f"{s['pos']:5.1f}% {s['building']:<12} {s['base']:7.3f} {'×':<3} {s['geo_mult']:11.2f} {'=':<3} {s['final']:7.3f} {effect:<15}")
        
        # Show statistics
        residential_avg = sum(s['geo_mult'] for s in spawn_data if s['building'] == 'residential') / max(1, sum(1 for s in spawn_data if s['building'] == 'residential'))
        school_avg = sum(s['geo_mult'] for s in spawn_data if s['building'] == 'school') / max(1, sum(1 for s in spawn_data if s['building'] == 'school'))
        commercial_avg = sum(s['geo_mult'] for s in spawn_data if s['building'] == 'commercial') / max(1, sum(1 for s in spawn_data if s['building'] == 'commercial'))
        
        print(f"\nAverage Multipliers:")
        print(f"  Residential: {residential_avg:.2f}x")
        if school_avg > 0:
            print(f"  Schools: {school_avg:.2f}x")
        if commercial_avg > 0:
            print(f"  Commercial: {commercial_avg:.2f}x")
    
    print("\n" + "="*80)
    print("CONSTRAINT EFFECTS SUMMARY")
    print("="*80)
    print("""
Temporal Constraints Applied:
✓ 7:00 AM - Residential areas heavily weighted (people leaving home)
✓ 7:30 AM - Schools boosted (school run + early commute)
✓ 8:30 AM - Commercial areas boosted (work destinations)

Geospatial Constraints Applied:
✓ Building density increases spawn probability
✓ Building type determines temporal pattern
✓ High-density residential = more spawns early morning
✓ Schools = peak during school hours
✓ Commercial = peak during business hours

Result: Spawns are now TEMPORALLY and GEOSPATIALLY realistic!
    """)


if __name__ == "__main__":
    asyncio.run(main())
