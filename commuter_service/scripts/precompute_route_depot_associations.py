"""
Precompute Route-Depot Associations Script
==========================================

This script calculates spatial associations between routes and depots based on:
- Route START and END point locations (extracted from GeoJSON geometry)
- Depot locations (latitude, longitude from Strapi)
- Walking distance threshold: ~500 meters

Association Logic:
- Depots are bus stations/terminals where passengers wait
- A depot is associated with a route if the route's START or END point is within
  walking distance (~500m) of the depot location
- Each association records:
  - distance_from_route_m: Distance to nearest route endpoint
  - is_start_terminus: True if depot is within 500m of route START
  - is_end_terminus: True if depot is within 500m of route END
  - precomputed_at: Timestamp of calculation

Usage:
    python -m commuter_service.scripts.precompute_route_depot_associations
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from math import radians, cos, sin, asin, sqrt
import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
STRAPI_BASE_URL = "http://localhost:1337"
WALKING_DISTANCE_THRESHOLD_M = 500.0  # ~500 meters walking distance


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth (in meters).
    
    Args:
        lat1: Latitude of point 1 (degrees)
        lon1: Longitude of point 1 (degrees)
        lat2: Latitude of point 2 (degrees)
        lon2: Longitude of point 2 (degrees)
    
    Returns:
        Distance in meters
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    
    # Radius of Earth in meters
    r = 6371000
    return c * r


def extract_route_endpoints(geojson_data: dict) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
    """
    Extract START and END point coordinates from route GeoJSON data.
    
    Args:
        geojson_data: GeoJSON FeatureCollection with route geometry
    
    Returns:
        Tuple of (start_point, end_point) where each point is (lat, lon)
        Returns (None, None) if geometry cannot be extracted
    """
    try:
        if not geojson_data or 'features' not in geojson_data:
            return None, None
        
        features = geojson_data['features']
        if not features:
            return None, None
        
        # Get first feature's coordinates (route start)
        first_feature = features[0]
        first_coords = first_feature['geometry']['coordinates']
        if not first_coords:
            return None, None
        
        # First coordinate of first feature = START point
        # GeoJSON format: [longitude, latitude]
        start_lon, start_lat = first_coords[0]
        
        # Get last feature's coordinates (route end)
        last_feature = features[-1]
        last_coords = last_feature['geometry']['coordinates']
        if not last_coords:
            return None, None
        
        # Last coordinate of last feature = END point
        end_lon, end_lat = last_coords[-1]
        
        return (start_lat, start_lon), (end_lat, end_lon)
    
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to extract endpoints: {e}")
        return None, None


async def fetch_all_routes(client: httpx.AsyncClient) -> List[dict]:
    """Fetch all active routes from Strapi"""
    try:
        # First get the list of route IDs
        response = await client.get(
            f"{STRAPI_BASE_URL}/api/routes",
            params={
                "filters[is_active][$eq]": True,
                "pagination[pageSize]": 100,
                "fields[0]": "short_name",
                "fields[1]": "geojson_data"  # Explicitly request geojson_data
            }
        )
        response.raise_for_status()
        data = response.json()
        
        routes = []
        for item in data.get('data', []):
            attrs = item.get('attributes', item)
            geojson = attrs.get('geojson_data')
            
            # Debug logging
            if geojson:
                logger.debug(f"Route {attrs.get('short_name')} has geojson_data with {len(geojson.get('features', []))} features")
            else:
                logger.warning(f"Route {attrs.get('short_name')} (id={item['id']}) has NO geojson_data - skipping")
                continue  # Skip routes without geometry
            
            routes.append({
                'id': item['id'],
                'documentId': item.get('documentId'),
                'short_name': attrs.get('short_name', f"Route {item['id']}"),
                'geojson_data': geojson
            })
        
        logger.info(f"✓ Fetched {len(routes)} active routes with geometry")
        return routes
    
    except Exception as e:
        logger.error(f"✗ Failed to fetch routes: {e}")
        return []


async def fetch_all_depots(client: httpx.AsyncClient) -> List[dict]:
    """Fetch all active depots from Strapi"""
    try:
        response = await client.get(
            f"{STRAPI_BASE_URL}/api/depots",
            params={
                "filters[is_active][$eq]": True,
                "pagination[pageSize]": 100,
                "fields[0]": "name",
                "fields[1]": "latitude",
                "fields[2]": "longitude"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        depots = []
        for item in data.get('data', []):
            attrs = item.get('attributes', item)
            depots.append({
                'id': item['id'],
                'documentId': item.get('documentId'),
                'name': attrs.get('name', f"Depot {item['id']}"),
                'latitude': attrs.get('latitude'),
                'longitude': attrs.get('longitude')
            })
        
        logger.info(f"✓ Fetched {len(depots)} active depots")
        return depots
    
    except Exception as e:
        logger.error(f"✗ Failed to fetch depots: {e}")
        return []


async def delete_existing_associations(client: httpx.AsyncClient) -> int:
    """Delete all existing route-depot associations"""
    try:
        # Fetch all associations
        response = await client.get(
            f"{STRAPI_BASE_URL}/api/route-depots",
            params={"pagination[pageSize]": 1000}
        )
        response.raise_for_status()
        data = response.json()
        
        associations = data.get('data', [])
        deleted_count = 0
        
        for assoc in associations:
            document_id = assoc.get('documentId')
            if document_id:
                try:
                    await client.delete(f"{STRAPI_BASE_URL}/api/route-depots/{document_id}")
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete association {document_id}: {e}")
        
        logger.info(f"✓ Deleted {deleted_count} existing associations")
        return deleted_count
    
    except Exception as e:
        logger.error(f"✗ Failed to delete associations: {e}")
        return 0


async def create_association(
    client: httpx.AsyncClient,
    route_doc: str,
    depot_doc: str,
    depot_name: str,
    route_short_name: str,
    distance_m: float,
    is_start: bool,
    is_end: bool
) -> Optional[dict]:
    """Create a route-depot association record"""
    try:
        payload = {
            "data": {
                "route": route_doc,
                "depot": depot_doc,
                "distance_from_route_m": round(distance_m, 2),
                "is_start_terminus": is_start,
                "is_end_terminus": is_end,
                "precomputed_at": datetime.now(timezone.utc).isoformat(),
                "display_name": f"{depot_name} - {round(distance_m)}m",
                "depot_name": depot_name,
                "route_short_name": route_short_name
            }
        }
        
        response = await client.post(
            f"{STRAPI_BASE_URL}/api/route-depots",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        logger.error(f"✗ Failed to create association (route {route_doc}, depot {depot_doc}): {e}")
        return None


async def precompute_associations():
    """Main function to precompute all route-depot associations"""
    logger.info("=" * 80)
    logger.info("Route-Depot Association Precompute Script")
    logger.info("=" * 80)
    logger.info(f"Strapi URL: {STRAPI_BASE_URL}")
    logger.info(f"Walking distance threshold: {WALKING_DISTANCE_THRESHOLD_M}m")
    logger.info("")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Fetch all routes and depots
        logger.info("[STEP 1/4] Fetching routes and depots...")
        routes = await fetch_all_routes(client)
        depots = await fetch_all_depots(client)
        
        if not routes:
            logger.error("No routes found. Aborting.")
            return
        
        if not depots:
            logger.error("No depots found. Aborting.")
            return
        
        logger.info(f"Found {len(routes)} routes and {len(depots)} depots")
        logger.info("")
        
        # Step 2: Delete existing associations (idempotent)
        logger.info("[STEP 2/4] Deleting existing associations...")
        await delete_existing_associations(client)
        logger.info("")
        
        # Step 3: Calculate associations
        logger.info("[STEP 3/4] Calculating spatial associations...")
        associations_created = 0
        routes_with_endpoints = 0
        routes_without_endpoints = 0
        
        for route in routes:
            # Extract route endpoints
            start_point, end_point = extract_route_endpoints(route['geojson_data'])
            
            if not start_point or not end_point:
                logger.warning(f"Route {route['short_name']} (id={route['id']}): No endpoints found")
                routes_without_endpoints += 1
                continue
            
            routes_with_endpoints += 1
            start_lat, start_lon = start_point
            end_lat, end_lon = end_point
            
            logger.debug(f"Route {route['short_name']}: START=({start_lat:.6f}, {start_lon:.6f}), END=({end_lat:.6f}, {end_lon:.6f})")
            
            # Check each depot
            for depot in depots:
                if depot['latitude'] is None or depot['longitude'] is None:
                    logger.warning(f"Depot {depot.get('name', depot['id'])} has no coordinates - skipping")
                    continue
                
                depot_lat = depot['latitude']
                depot_lon = depot['longitude']
                
                # Calculate distances to both endpoints
                dist_to_start = haversine_distance(depot_lat, depot_lon, start_lat, start_lon)
                dist_to_end = haversine_distance(depot_lat, depot_lon, end_lat, end_lon)
                
                # Check if depot is within walking distance of either endpoint
                is_start_terminus = dist_to_start <= WALKING_DISTANCE_THRESHOLD_M
                is_end_terminus = dist_to_end <= WALKING_DISTANCE_THRESHOLD_M
                
                if is_start_terminus or is_end_terminus:
                    # Use the minimum distance
                    min_distance = min(dist_to_start, dist_to_end)
                    
                    # Create association
                    result = await create_association(
                        client,
                        route['documentId'],
                        depot['documentId'],
                        depot['name'],
                        route['short_name'],
                        min_distance,
                        is_start_terminus,
                        is_end_terminus
                    )
                    
                    if result:
                        associations_created += 1
                        logger.info(
                            f"✓ Association created: Route {route['short_name']} ↔ Depot {depot['name']} "
                            f"({min_distance:.1f}m, start={is_start_terminus}, end={is_end_terminus})"
                        )
        
        logger.info("")
        logger.info("[STEP 4/4] Summary")
        logger.info("=" * 80)
        logger.info(f"Total routes processed: {len(routes)}")
        logger.info(f"  - Routes with valid endpoints: {routes_with_endpoints}")
        logger.info(f"  - Routes without endpoints: {routes_without_endpoints}")
        logger.info(f"Total depots processed: {len(depots)}")
        logger.info(f"Associations created: {associations_created}")
        logger.info("=" * 80)
        logger.info("✅ Precompute complete!")


if __name__ == "__main__":
    asyncio.run(precompute_associations())
