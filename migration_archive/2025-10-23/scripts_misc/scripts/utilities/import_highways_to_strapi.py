"""
Import Barbados Highway GeoJSON to Strapi Database
Imports highways and shapes in GTFS-compatible normalized structure:
- highways table (highway metadata)
- shapes table (geometry points)
- highway_shapes table (links highways to shapes)
"""

import json
import httpx
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Configuration
STRAPI_URL = "http://localhost:1337/api"
STRAPI_TOKEN = ""  # Add your token or use public endpoint
GEOJSON_FILE = Path(__file__).parent / "commuter_service" / "geojson_data" / "barbados_highway.json"
COUNTRY_CODE = "BRB"  # Barbados

# Stats
stats = {
    "total_features": 0,
    "highways_created": 0,
    "shapes_created": 0,
    "highway_shapes_created": 0,
    "errors": 0
}


async def get_country_id(client: httpx.AsyncClient) -> int:
    """Get Barbados country ID"""
    response = await client.get(f"{STRAPI_URL}/countries", params={"filters[code][$eq]": COUNTRY_CODE})
    data = response.json()
    
    if not data.get('data'):
        print(f"❌ Country {COUNTRY_CODE} not found!")
        raise ValueError(f"Country {COUNTRY_CODE} must exist in database")
    
    country_id = data['data'][0]['id']
    print(f"✅ Found country: {data['data'][0]['name']} (ID: {country_id})")
    return country_id


def parse_highway_feature(feature: Dict, index: int) -> Dict:
    """Parse a highway feature from GeoJSON"""
    properties = feature.get('properties', {})
    geometry = feature.get('geometry', {})
    
    # Extract highway name (may be null for unnamed roads)
    name = properties.get('name') or f"Highway {index}"
    
    # Determine highway type from OSM data
    highway_type = properties.get('highway', 'other')
    
    # Map OSM highway types to our enumeration
    type_mapping = {
        'motorway': 'motorway',
        'trunk': 'trunk',
        'primary': 'primary',
        'secondary': 'secondary',
        'tertiary': 'tertiary',
        'residential': 'residential',
        'service': 'service',
        'unclassified': 'unclassified',
        'track': 'track',
        'path': 'path',
        'footway': 'footway',
        'cycleway': 'cycleway',
        'steps': 'steps',
        'pedestrian': 'pedestrian',
        'living_street': 'living_street',
    }
    
    highway_type = type_mapping.get(highway_type, 'other')
    
    return {
        'name': name,
        'highway_type': highway_type,
        'osm_id': properties.get('osm_id', ''),
        'full_id': properties.get('full_id', ''),
        'ref': properties.get('ref', ''),
        'surface': properties.get('surface'),
        'lanes': properties.get('lanes'),
        'maxspeed': properties.get('maxspeed'),
        'oneway': properties.get('oneway') == 'yes',
        'is_active': True,
        'geometry': geometry
    }


def create_shape_points(geometry: Dict, shape_id: str) -> List[Dict]:
    """Convert LineString geometry to shape points"""
    coordinates = geometry.get('coordinates', [])
    shape_points = []
    
    cumulative_distance = 0.0
    
    for seq, coord in enumerate(coordinates):
        lon, lat = coord[0], coord[1]
        
        # Calculate distance traveled (simple Euclidean for now)
        if seq > 0:
            prev_lon, prev_lat = coordinates[seq-1][0], coordinates[seq-1][1]
            # Rough distance calculation (not precise, but sufficient for ordering)
            cumulative_distance += ((lon - prev_lon)**2 + (lat - prev_lat)**2)**0.5
        
        shape_points.append({
            'shape_id': shape_id,
            'shape_pt_lat': lat,
            'shape_pt_lon': lon,
            'shape_pt_sequence': seq,
            'shape_dist_traveled': round(cumulative_distance, 6),
            'is_active': True
        })
    
    return shape_points


async def create_highway(client: httpx.AsyncClient, highway_data: Dict, country_id: int) -> int:
    """Create highway record"""
    payload = {
        'data': {
            'name': highway_data['name'],
            'highway_type': highway_data['highway_type'],
            'osm_id': highway_data['osm_id'],
            'full_id': highway_data['full_id'],
            'ref': highway_data['ref'],
            'surface': highway_data['surface'],
            'lanes': highway_data['lanes'],
            'maxspeed': highway_data['maxspeed'],
            'oneway': highway_data['oneway'],
            'is_active': highway_data['is_active'],
            'country': country_id
        }
    }
    
    response = await client.post(f"{STRAPI_URL}/highways", json=payload)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create highway: {highway_data['name']}")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
        stats['errors'] += 1
        return None
    
    result = response.json()
    highway_id = result['data']['id']
    stats['highways_created'] += 1
    return highway_id


async def create_shape_batch(client: httpx.AsyncClient, shape_points: List[Dict]) -> bool:
    """Create shape points in batch"""
    for point in shape_points:
        payload = {'data': point}
        response = await client.post(f"{STRAPI_URL}/shapes", json=payload)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create shape point")
            stats['errors'] += 1
            return False
        
        stats['shapes_created'] += 1
    
    return True


async def link_highway_to_shape(client: httpx.AsyncClient, highway_id: int, shape_id: str) -> bool:
    """Create highway_shape link"""
    payload = {
        'data': {
            'highway_id': str(highway_id),
            'shape_id': shape_id,
            'is_default': True,
            'is_active': True
        }
    }
    
    response = await client.post(f"{STRAPI_URL}/highway-shapes", json=payload)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to link highway {highway_id} to shape {shape_id}")
        stats['errors'] += 1
        return False
    
    stats['highway_shapes_created'] += 1
    return True


async def import_highways():
    """Main import function"""
    print("=" * 80)
    print("🛣️  HIGHWAY GEOJSON IMPORT")
    print("=" * 80)
    print(f"Source: {GEOJSON_FILE}")
    print(f"Target: {STRAPI_URL}")
    print("")
    
    # Load GeoJSON
    print("📂 Loading GeoJSON file...")
    with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    features = geojson_data.get('features', [])
    stats['total_features'] = len(features)
    print(f"✅ Loaded {len(features)} highway features")
    print("")
    
    # Setup HTTP client
    headers = {}
    if STRAPI_TOKEN:
        headers['Authorization'] = f'Bearer {STRAPI_TOKEN}'
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        # Get country ID
        country_id = await get_country_id(client)
        print("")
        
        # Process each highway feature
        print("🚀 Importing highways...")
        for idx, feature in enumerate(features, 1):
            if idx % 100 == 0:
                print(f"   Progress: {idx}/{len(features)} ({idx/len(features)*100:.1f}%)")
            
            try:
                # Parse highway data
                highway_data = parse_highway_feature(feature, idx)
                
                # Create highway
                highway_id = await create_highway(client, highway_data, country_id)
                if not highway_id:
                    continue
                
                # Create shape ID (unique per highway)
                shape_id = f"highway_{highway_id}"
                
                # Create shape points
                shape_points = create_shape_points(highway_data['geometry'], shape_id)
                if not await create_shape_batch(client, shape_points):
                    continue
                
                # Link highway to shape
                await link_highway_to_shape(client, highway_id, shape_id)
                
            except Exception as e:
                print(f"❌ Error processing feature {idx}: {e}")
                stats['errors'] += 1
                continue
    
    # Print summary
    print("")
    print("=" * 80)
    print("📊 IMPORT SUMMARY")
    print("=" * 80)
    print(f"Total features processed: {stats['total_features']}")
    print(f"Highways created: {stats['highways_created']}")
    print(f"Shape points created: {stats['shapes_created']}")
    print(f"Highway-shape links created: {stats['highway_shapes_created']}")
    print(f"Errors: {stats['errors']}")
    print("=" * 80)
    
    if stats['errors'] > 0:
        print("⚠️  Import completed with errors")
    else:
        print("✅ Import completed successfully!")


if __name__ == "__main__":
    asyncio.run(import_highways())
