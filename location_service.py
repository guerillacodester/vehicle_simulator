"""
LocationService - Geofence and Location Awareness

Provides location-based services for vehicles and commuters:
- Check if vehicle is in assigned depot
- Check if point is in any geofence
- Find nearby POIs, places, and landmarks
- Get location name from coordinates
"""

import psycopg2
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}


class GeofenceType(Enum):
    """Types of geofences"""
    DEPOT = "depot"
    BOARDING_ZONE = "boarding_zone"
    SERVICE_AREA = "service_area"
    RESTRICTED = "restricted"
    PROXIMITY = "proximity"
    CUSTOM = "custom"


@dataclass
class GeofenceResult:
    """Result from geofence query"""
    geofence_id: str
    name: str
    type: str
    geometry_type: str
    distance_m: float
    
    def __repr__(self):
        return f"<Geofence {self.name} ({self.type}) @ {self.distance_m:.2f}m>"


@dataclass
class LocationInfo:
    """Complete location information"""
    latitude: float
    longitude: float
    geofences: List[GeofenceResult]
    nearest_poi: Optional[Dict]
    nearest_place: Optional[Dict]
    nearest_depot: Optional[Dict]
    location_description: str
    
    def __repr__(self):
        return f"<Location ({self.latitude:.6f}, {self.longitude:.6f}) - {self.location_description}>"


class LocationService:
    """
    Geofence and location awareness service
    
    Usage:
        service = LocationService()
        
        # Check if vehicle is in depot
        if service.is_vehicle_in_assigned_depot('vehicle_123', 13.098, -59.621):
            print("Vehicle can start boarding!")
        
        # Get all geofences at location
        geofences = service.get_geofences_at_location(13.098, -59.621)
        
        # Get complete location info
        info = service.get_location_info(13.098, -59.621)
    """
    
    def __init__(self):
        """Initialize database connection"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        
        # Cache for depot assignments (vehicle_id -> depot_id)
        self._depot_assignments = {}
    
    def _get_vehicle_assigned_depot(self, vehicle_id: str) -> Optional[str]:
        """
        Get the depot assigned to a vehicle
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            depot_id if assigned, None otherwise
        """
        # Check cache first
        if vehicle_id in self._depot_assignments:
            return self._depot_assignments[vehicle_id]
        
        # Query database
        query = """
            SELECT assigned_depot_id
            FROM vehicles
            WHERE vehicle_id = %s
        """
        
        self.cursor.execute(query, (vehicle_id,))
        result = self.cursor.fetchone()
        
        if result:
            depot_id = result[0]
            self._depot_assignments[vehicle_id] = depot_id
            return depot_id
        
        return None
    
    def get_depot_at_location(self, lat: float, lon: float) -> Optional[str]:
        """
        Get the depot ID at a specific location (if inside depot geofence)
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            depot_id if inside depot geofence, None otherwise
        """
        # Get all depot geofences at this location
        geofences = self.get_geofences_at_location(lat, lon, types=[GeofenceType.DEPOT])
        
        if not geofences:
            return None
        
        # Extract depot_id from geofence_id
        # Format: "geofence-bgi_cheapside_03" → "BGI_CHEAPSIDE_03"
        geofence_id = geofences[0].geofence_id
        
        # Remove "geofence-" prefix and convert to uppercase
        depot_id = geofence_id.replace("geofence-", "").upper()
        
        return depot_id
    
    def is_vehicle_in_assigned_depot(self, vehicle_id: str, lat: float, lon: float) -> bool:
        """
        Check if vehicle is inside its assigned depot geofence
        
        This is the key method for determining if a vehicle can start boarding.
        
        Args:
            vehicle_id: Vehicle identifier
            lat: Current latitude
            lon: Current longitude
            
        Returns:
            True if vehicle is inside correct depot geofence, False otherwise
            
        Example:
            >>> service = LocationService()
            >>> # Vehicle at Cheapside depot coordinates
            >>> service.is_vehicle_in_assigned_depot('vehicle_123', 13.098168, -59.621582)
            True
        """
        # Get vehicle's assigned depot
        assigned_depot = self._get_vehicle_assigned_depot(vehicle_id)
        
        if not assigned_depot:
            return False
        
        # Get depot at current location
        current_depot = self.get_depot_at_location(lat, lon)
        
        if not current_depot:
            return False
        
        # Check if they match
        return assigned_depot.upper() == current_depot.upper()
    
    def get_geofences_at_location(
        self, 
        lat: float, 
        lon: float, 
        types: Optional[List[GeofenceType]] = None
    ) -> List[GeofenceResult]:
        """
        Get all geofences containing a point
        
        Args:
            lat: Latitude
            lon: Longitude
            types: Optional list of geofence types to filter (e.g., [GeofenceType.DEPOT])
            
        Returns:
            List of GeofenceResult objects
            
        Example:
            >>> service = LocationService()
            >>> geofences = service.get_geofences_at_location(13.098, -59.621, [GeofenceType.DEPOT])
            >>> for gf in geofences:
            ...     print(f"{gf.name}: {gf.distance_m}m")
        """
        # Convert enum types to strings
        if types:
            type_array = [t.value for t in types]
        else:
            type_array = None
        
        # Build query
        if type_array:
            query = "SELECT * FROM check_point_in_geofences(%s, %s, %s)"
            params = (lat, lon, type_array)
        else:
            query = "SELECT * FROM check_point_in_geofences(%s, %s)"
            params = (lat, lon)
        
        self.cursor.execute(query, params)
        
        results = []
        for row in self.cursor.fetchall():
            results.append(GeofenceResult(
                geofence_id=row[0],
                name=row[1],
                type=row[2],
                geometry_type=row[3],
                distance_m=round(row[4], 2)
            ))
        
        return results
    
    def is_in_any_depot(self, lat: float, lon: float) -> bool:
        """
        Check if location is inside ANY depot geofence
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if inside any depot, False otherwise
        """
        geofences = self.get_geofences_at_location(lat, lon, types=[GeofenceType.DEPOT])
        return len(geofences) > 0
    
    def is_in_boarding_zone(self, lat: float, lon: float) -> bool:
        """
        Check if location is inside any boarding zone geofence
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if inside boarding zone, False otherwise
        """
        geofences = self.get_geofences_at_location(lat, lon, types=[GeofenceType.BOARDING_ZONE])
        return len(geofences) > 0
    
    def get_nearest_poi(self, lat: float, lon: float, max_distance_m: float = 500) -> Optional[Dict]:
        """
        Get nearest POI within distance
        
        Args:
            lat: Latitude
            lon: Longitude
            max_distance_m: Maximum search radius in meters
            
        Returns:
            Dict with POI info or None
        """
        query = """
            SELECT 
                name,
                poi_type,
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
            LIMIT 1
        """
        
        self.cursor.execute(query, (lon, lat, lon, lat, max_distance_m))
        result = self.cursor.fetchone()
        
        if result:
            return {
                'name': result[0],
                'type': result[1],
                'latitude': result[2],
                'longitude': result[3],
                'distance_m': round(result[4], 2)
            }
        
        return None
    
    def get_nearest_place(self, lat: float, lon: float, max_distance_m: float = 1000) -> Optional[Dict]:
        """
        Get nearest place (street/locality) within distance
        
        Args:
            lat: Latitude
            lon: Longitude
            max_distance_m: Maximum search radius in meters
            
        Returns:
            Dict with place info or None
        """
        query = """
            SELECT 
                name,
                place_type,
                latitude,
                longitude,
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
            LIMIT 1
        """
        
        self.cursor.execute(query, (lon, lat, lon, lat, max_distance_m))
        result = self.cursor.fetchone()
        
        if result:
            return {
                'name': result[0],
                'place_type': result[1],
                'latitude': result[2],
                'longitude': result[3],
                'distance_m': round(result[4], 2)
            }
        
        return None
    
    def get_location_info(self, lat: float, lon: float) -> LocationInfo:
        """
        Get complete location information
        
        Combines geofences, POIs, places into single result
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            LocationInfo object with all details
        """
        # Get all geofences
        geofences = self.get_geofences_at_location(lat, lon)
        
        # Get nearest POI and place
        poi = self.get_nearest_poi(lat, lon, max_distance_m=500)
        place = self.get_nearest_place(lat, lon, max_distance_m=1000)
        
        # Create description
        if geofences:
            description = f"Inside {geofences[0].name}"
        elif poi and poi['distance_m'] < 100:
            description = f"At {poi['name']}"
        elif poi and poi['distance_m'] < 500:
            description = f"Near {poi['name']} ({poi['distance_m']:.0f}m)"
        elif place:
            description = f"In {place['name']} area"
        else:
            description = "Unknown location"
        
        return LocationInfo(
            latitude=lat,
            longitude=lon,
            geofences=geofences,
            nearest_poi=poi,
            nearest_place=place,
            nearest_depot=None,  # TODO: Add if needed
            location_description=description
        )
    
    def clear_cache(self):
        """Clear internal caches"""
        self._depot_assignments.clear()
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience functions for quick checks
def is_vehicle_in_depot(vehicle_id: str, lat: float, lon: float) -> bool:
    """Quick check if vehicle is in assigned depot"""
    with LocationService() as service:
        return service.is_vehicle_in_assigned_depot(vehicle_id, lat, lon)


def get_location_name(lat: float, lon: float) -> str:
    """Quick lookup of location name"""
    with LocationService() as service:
        info = service.get_location_info(lat, lon)
        return info.location_description


if __name__ == "__main__":
    # Example usage
    service = LocationService()
    
    print("="*80)
    print("LOCATION SERVICE EXAMPLES")
    print("="*80)
    
    # Test 1: Check if coordinates are in Cheapside depot
    lat, lon = 13.098168, -59.621582
    print(f"\n1. Testing Cheapside depot coordinates ({lat}, {lon}):")
    
    geofences = service.get_geofences_at_location(lat, lon)
    print(f"   Geofences: {len(geofences)}")
    for gf in geofences:
        print(f"   - {gf.name} ({gf.type})")
    
    depot_id = service.get_depot_at_location(lat, lon)
    print(f"   Depot ID: {depot_id}")
    
    # Test 2: Get location info
    print(f"\n2. Location info for Cheapside:")
    info = service.get_location_info(lat, lon)
    print(f"   Description: {info.location_description}")
    if info.nearest_poi:
        print(f"   Nearest POI: {info.nearest_poi['name']} ({info.nearest_poi['distance_m']:.2f}m)")
    
    # Test 3: Check random location (not in depot)
    lat2, lon2 = 13.200, -59.600
    print(f"\n3. Testing random location ({lat2}, {lon2}):")
    
    is_depot = service.is_in_any_depot(lat2, lon2)
    print(f"   In any depot: {is_depot}")
    
    info2 = service.get_location_info(lat2, lon2)
    print(f"   Description: {info2.location_description}")
    
    service.close()
    
    print("\n" + "="*80)
    print("✅ LocationService examples complete")
    print("="*80)
