"""
Reverse Geocoding Tool - Find Location Info from Lat/Lon
Enter any coordinate and get nearby POIs, Places, Depots, and Geofences
"""

import psycopg2
import requests
from typing import List, Dict, Optional
import sys

STRAPI_URL = "http://localhost:1337/api"
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

class ReverseGeocoder:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
    
    def find_nearest_poi(self, lat: float, lon: float, limit: int = 5, max_distance_m: float = 5000) -> List[Dict]:
        """Find nearest POIs using PostGIS"""
        query = """
            SELECT 
                name,
                poi_type,
                amenity,
                latitude,
                longitude,
                ST_Distance(
                    ST_MakePoint(longitude, latitude)::geography,
                    ST_MakePoint(%s, %s)::geography
                ) as distance_meters
            FROM pois
            WHERE is_active = true
            AND ST_DWithin(
                ST_MakePoint(longitude, latitude)::geography,
                ST_MakePoint(%s, %s)::geography,
                %s
            )
            ORDER BY distance_meters ASC
            LIMIT %s
        """
        
        self.cursor.execute(query, (lon, lat, lon, lat, max_distance_m, limit))
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'name': row[0],
                'type': row[1],
                'amenity': row[2],
                'latitude': row[3],
                'longitude': row[4],
                'distance_m': round(row[5], 2)
            })
        return results
    
    def find_nearest_place(self, lat: float, lon: float, limit: int = 5, max_distance_m: float = 5000) -> List[Dict]:
        """Find nearest Places using PostGIS"""
        query = """
            SELECT 
                name,
                place_type,
                latitude,
                longitude,
                population,
                importance,
                ST_Distance(
                    ST_MakePoint(longitude, latitude)::geography,
                    ST_MakePoint(%s, %s)::geography
                ) as distance_meters
            FROM places
            WHERE is_active = true
            AND ST_DWithin(
                ST_MakePoint(longitude, latitude)::geography,
                ST_MakePoint(%s, %s)::geography,
                %s
            )
            ORDER BY distance_meters ASC
            LIMIT %s
        """
        
        self.cursor.execute(query, (lon, lat, lon, lat, max_distance_m, limit))
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'name': row[0],
                'place_type': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'population': row[4],
                'importance': row[5],
                'distance_m': round(row[6], 2)
            })
        return results
    
    def find_nearest_depot(self, lat: float, lon: float, limit: int = 5, max_distance_m: float = 10000) -> List[Dict]:
        """Find nearest Depots using PostGIS"""
        query = """
            SELECT 
                depot_id,
                name,
                address,
                latitude,
                longitude,
                capacity,
                is_active,
                ST_Distance(
                    ST_MakePoint(longitude, latitude)::geography,
                    ST_MakePoint(%s, %s)::geography
                ) as distance_meters
            FROM depots
            WHERE is_active = true
            AND ST_DWithin(
                ST_MakePoint(longitude, latitude)::geography,
                ST_MakePoint(%s, %s)::geography,
                %s
            )
            ORDER BY distance_meters ASC
            LIMIT %s
        """
        
        self.cursor.execute(query, (lon, lat, lon, lat, max_distance_m, limit))
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'depot_id': row[0],
                'name': row[1],
                'address': row[2],
                'latitude': row[3],
                'longitude': row[4],
                'capacity': row[5],
                'is_active': row[6],
                'distance_m': round(row[7], 2)
            })
        return results
    
    def find_geofences_at_location(self, lat: float, lon: float) -> List[Dict]:
        """Find which geofences contain this point"""
        query = """
            SELECT * FROM check_point_in_geofences(%s, %s)
        """
        
        self.cursor.execute(query, (lat, lon))
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'geofence_id': row[0],
                'name': row[1],
                'type': row[2],
                'geometry_type': row[3],
                'distance_m': round(row[4], 2)
            })
        return results
    
    def reverse_geocode(self, lat: float, lon: float, max_distance_m: float = 5000) -> Dict:
        """
        Complete reverse geocoding - find everything near this coordinate
        
        Args:
            lat: Latitude
            lon: Longitude
            max_distance_m: Maximum search radius in meters (default 5km)
        
        Returns:
            Dict with nearest POIs, Places, Depots, and Geofences
        """
        
        print(f"\n{'='*80}")
        print(f"REVERSE GEOCODING: ({lat}, {lon})")
        print(f"{'='*80}")
        print(f"Search radius: {max_distance_m}m ({max_distance_m/1000:.1f}km)")
        
        # Find geofences (point is inside)
        print(f"\n🎯 Checking geofences (point containment)...")
        geofences = self.find_geofences_at_location(lat, lon)
        
        if geofences:
            print(f"   ✅ Inside {len(geofences)} geofence(s):")
            for gf in geofences:
                print(f"      • {gf['name']} ({gf['type']})")
                print(f"        ID: {gf['geofence_id']}, Geometry: {gf['geometry_type']}")
        else:
            print(f"   ℹ️  Not inside any geofence")
        
        # Find nearest POIs
        print(f"\n📍 Finding nearest POIs...")
        pois = self.find_nearest_poi(lat, lon, limit=5, max_distance_m=max_distance_m)
        
        if pois:
            print(f"   ✅ Found {len(pois)} POI(s) within {max_distance_m}m:")
            for i, poi in enumerate(pois, 1):
                print(f"      {i}. {poi['name']} ({poi['type']})")
                print(f"         Amenity: {poi['amenity']}")
                print(f"         Distance: {poi['distance_m']:.2f}m")
                print(f"         Location: ({poi['latitude']:.6f}, {poi['longitude']:.6f})")
        else:
            print(f"   ℹ️  No POIs found within {max_distance_m}m")
        
        # Find nearest Places
        print(f"\n🏘️  Finding nearest Places...")
        places = self.find_nearest_place(lat, lon, limit=5, max_distance_m=max_distance_m)
        
        if places:
            print(f"   ✅ Found {len(places)} Place(s) within {max_distance_m}m:")
            for i, place in enumerate(places, 1):
                print(f"      {i}. {place['name']} ({place['place_type']})")
                pop_str = f", Pop: {place['population']}" if place['population'] else ""
                imp_str = f", Importance: {place['importance']}" if place['importance'] else ""
                print(f"         Distance: {place['distance_m']:.2f}m{pop_str}{imp_str}")
                print(f"         Location: ({place['latitude']:.6f}, {place['longitude']:.6f})")
        else:
            print(f"   ℹ️  No Places found within {max_distance_m}m")
        
        # Find nearest Depots
        print(f"\n🚌 Finding nearest Depots...")
        depots = self.find_nearest_depot(lat, lon, limit=3, max_distance_m=max_distance_m)
        
        if depots:
            print(f"   ✅ Found {len(depots)} Depot(s) within {max_distance_m}m:")
            for i, depot in enumerate(depots, 1):
                print(f"      {i}. {depot['name']}")
                print(f"         ID: {depot['depot_id']}, Capacity: {depot['capacity']} vehicles")
                print(f"         Address: {depot['address']}")
                print(f"         Distance: {depot['distance_m']:.2f}m")
                print(f"         Location: ({depot['latitude']:.6f}, {depot['longitude']:.6f})")
        else:
            print(f"   ℹ️  No Depots found within {max_distance_m}m")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"📊 SUMMARY")
        print(f"{'='*80}")
        
        # Create location description
        location_name = "Unknown location"
        
        if geofences:
            location_name = f"Inside {geofences[0]['name']}"
        elif pois and pois[0]['distance_m'] < 100:
            location_name = f"At {pois[0]['name']}"
        elif pois and pois[0]['distance_m'] < 500:
            location_name = f"Near {pois[0]['name']} ({pois[0]['distance_m']:.0f}m away)"
        elif places:
            location_name = f"In {places[0]['name']} area ({places[0]['distance_m']:.0f}m from center)"
        
        print(f"📍 Location: {location_name}")
        print(f"🎯 Coordinates: ({lat}, {lon})")
        print(f"")
        print(f"Nearby features:")
        print(f"  • {len(geofences)} geofence(s) (inside)")
        print(f"  • {len(pois)} POI(s) within {max_distance_m}m")
        print(f"  • {len(places)} place(s) within {max_distance_m}m")
        print(f"  • {len(depots)} depot(s) within {max_distance_m}m")
        
        if pois:
            print(f"\n🏆 Closest feature: {pois[0]['name']} ({pois[0]['distance_m']:.2f}m)")
        
        print(f"\n{'='*80}")
        
        return {
            'coordinates': {'lat': lat, 'lon': lon},
            'location_description': location_name,
            'geofences': geofences,
            'pois': pois,
            'places': places,
            'depots': depots
        }
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()


def main():
    """Interactive reverse geocoding tool"""
    
    geocoder = ReverseGeocoder()
    
    print("\n" + "="*80)
    print("🌍 REVERSE GEOCODING TOOL")
    print("="*80)
    print("Enter coordinates to find nearby POIs, Places, Depots, and Geofences")
    print("Type 'quit' or 'exit' to stop")
    print("")
    
    # Example coordinates for testing
    examples = [
        (13.098168, -59.621582, "Cheapside Terminal (inside depot geofence)"),
        (13.096108, -59.612344, "Fairchild Street Terminal"),
        (13.095, -59.615, "Downtown Bridgetown"),
        (13.252068, -59.642543, "Speightstown"),
    ]
    
    print("Example coordinates to try:")
    for lat, lon, desc in examples:
        print(f"  • {lat}, {lon}  →  {desc}")
    print("")
    
    while True:
        try:
            # Get user input
            user_input = input("Enter coordinates (lat, lon) or 'quit': ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Parse input
            if ',' in user_input:
                parts = user_input.split(',')
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
            else:
                print("❌ Invalid format. Use: lat, lon (e.g., 13.098, -59.621)")
                continue
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                print("❌ Invalid coordinates. Lat must be -90 to 90, Lon must be -180 to 180")
                continue
            
            # Optional: custom search radius
            radius_input = input("Search radius in meters (default 5000, press Enter to skip): ").strip()
            max_distance = float(radius_input) if radius_input else 5000
            
            # Reverse geocode
            result = geocoder.reverse_geocode(lat, lon, max_distance_m=max_distance)
            
            print("\n" + "-"*80)
            print("Press Enter to search again, or type 'quit' to exit")
            print("-"*80 + "\n")
            
        except ValueError as e:
            print(f"❌ Error parsing input: {e}")
            print("   Use format: lat, lon (e.g., 13.098, -59.621)")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    geocoder.close()


if __name__ == "__main__":
    # If coordinates provided as command line args, use those
    if len(sys.argv) == 3:
        try:
            lat = float(sys.argv[1])
            lon = float(sys.argv[2])
            geocoder = ReverseGeocoder()
            geocoder.reverse_geocode(lat, lon)
            geocoder.close()
        except ValueError:
            print("Usage: python reverse_geocode.py <latitude> <longitude>")
            print("Example: python reverse_geocode.py 13.098 -59.621")
    else:
        # Interactive mode
        main()
