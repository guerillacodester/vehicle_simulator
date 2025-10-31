"""
Analytics API - Reporting, statistics, and data visualization
Advanced analysis and aggregations (Separation of Concerns)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import configparser
from pathlib import Path
import httpx

from services.postgis_client import postgis_client

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Load Strapi URL from config
config = configparser.ConfigParser()
config_path = Path(__file__).parent.parent.parent / "config.ini"
config.read(config_path, encoding='utf-8')
STRAPI_URL = config.get('infrastructure', 'strapi_url', fallback='http://localhost:1337')


@router.get("/density-heatmap", summary="Get building density heatmap")
async def get_density_heatmap(
    grid_size_meters: int = Query(1000, ge=100, le=5000, description="Grid cell size"),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180)
) -> Dict[str, Any]:
    """
    Generate a heatmap of building density across a geographic area.
    
    Returns grid cells with building counts for visualization.
    """
    start_time = time.time()
    
    try:
        # Simplified grid-based heatmap
        # Convert grid_size_meters to degrees (approximate at equator: 1deg ≈ 111km)
        grid_size_deg = grid_size_meters / 111320.0
        
        query = """
            WITH grid AS (
                SELECT 
                    lat,
                    lat + $5::numeric AS lat_end,
                    lon,
                    lon + $5::numeric AS lon_end
                FROM (
                    SELECT 
                        generate_series($3::numeric, $4::numeric, $5::numeric) AS lat
                ) lats
                CROSS JOIN (
                    SELECT 
                        generate_series($1::numeric, $2::numeric, $5::numeric) AS lon
                ) lons
            )
            SELECT 
                g.lat AS lat_start,
                g.lat_end,
                g.lon AS lon_start,
                g.lon_end,
                COUNT(b.id) AS building_count
            FROM grid g
            LEFT JOIN buildings b ON 
                ST_Contains(
                    ST_MakeEnvelope(g.lon, g.lat, g.lon_end, g.lat_end, 4326),
                    b.geom
                )
            GROUP BY g.lat, g.lat_end, g.lon, g.lon_end
            HAVING COUNT(b.id) > 0
            ORDER BY building_count DESC
            LIMIT 1000
        """
        
        result = await postgis_client.execute_query(
            query, min_lon, max_lon, min_lat, max_lat, grid_size_deg
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'grid_size_meters': grid_size_meters,
            'bounds': {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lon': min_lon,
                'max_lon': max_lon
            },
            'cells': result,
            'cell_count': len(result),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {str(e)}")


@router.get("/route-coverage", summary="Analyze route coverage overlap")
async def get_route_coverage_analysis(
    buffer_meters: int = Query(500, ge=100, le=2000, description="Route coverage buffer")
) -> Dict[str, Any]:
    """
    Analyze route coverage and identify overlapping service areas.
    
    Shows which areas are served by multiple routes.
    """
    start_time = time.time()
    
    try:
        # Get all routes from Strapi
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{STRAPI_URL}/api/routes",
                params={"pagination[pageSize]": 1000}
            )
            routes_data = response.json()
            routes = routes_data.get('data', [])
        
        # Analyze coverage for each route
        coverage_analysis = []
        total_area = 0
        
        for route in routes:
            route_id = route['id']
            attrs = route['attributes']
            doc_id = attrs.get('documentId') or attrs.get('document_id')
            
            if not doc_id:
                continue
            
            # Calculate coverage area
            query = """
                WITH route_geom AS (
                    SELECT geom FROM highways WHERE document_id = $1 LIMIT 1
                )
                SELECT 
                    ST_Area(ST_Buffer(geom::geography, $2)) AS coverage_area_sq_meters
                FROM route_geom
            """
            
            try:
                result = await postgis_client.execute_query(query, doc_id, buffer_meters)
                if result:
                    area = result[0]['coverage_area_sq_meters']
                    total_area += area
                    
                    coverage_analysis.append({
                        'route_id': route_id,
                        'short_name': attrs.get('route_short_name'),
                        'long_name': attrs.get('route_long_name'),
                        'coverage_area_sq_meters': area,
                        'coverage_area_sq_km': round(area / 1_000_000, 2)
                    })
            except:
                continue
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'buffer_meters': buffer_meters,
            'routes_analyzed': len(coverage_analysis),
            'total_coverage_sq_km': round(total_area / 1_000_000, 2),
            'routes': coverage_analysis,
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coverage analysis failed: {str(e)}")


@router.get("/depot-service-areas", summary="Analyze depot service area overlap")
async def get_depot_service_areas(
    radius_meters: int = Query(1000, ge=100, le=5000, description="Depot service radius")
) -> Dict[str, Any]:
    """
    Analyze depot service areas and identify overlapping catchments.
    
    Shows which areas are served by multiple depots.
    """
    start_time = time.time()
    
    try:
        # Get all depots from Strapi
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{STRAPI_URL}/api/depots",
                params={"pagination[pageSize]": 1000}
            )
            depots_data = response.json()
            depots = depots_data.get('data', [])
        
        # Analyze service area for each depot
        service_areas = []
        total_area = 0
        
        for depot in depots:
            depot_id = depot['id']
            attrs = depot['attributes']
            location = attrs.get('location')
            
            if not location or not location.get('coordinates'):
                continue
            
            lon = location['coordinates'][0]
            lat = location['coordinates'][1]
            
            # Calculate service area
            area_sq_meters = 3.14159 * (radius_meters ** 2)  # Circle area
            total_area += area_sq_meters
            
            # Get building count
            try:
                buildings = await postgis_client.get_buildings_near_depot(
                    latitude=lat,
                    longitude=lon,
                    radius_meters=radius_meters,
                    limit=10000
                )
                building_count = len(buildings)
            except:
                building_count = 0
            
            service_areas.append({
                'depot_id': depot_id,
                'name': attrs.get('name'),
                'latitude': lat,
                'longitude': lon,
                'service_area_sq_meters': area_sq_meters,
                'service_area_sq_km': round(area_sq_meters / 1_000_000, 2),
                'building_count': building_count,
                'buildings_per_sq_km': round(building_count / (area_sq_meters / 1_000_000), 2) if area_sq_meters > 0 else 0
            })
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'radius_meters': radius_meters,
            'depots_analyzed': len(service_areas),
            'total_coverage_sq_km': round(total_area / 1_000_000, 2),
            'depots': service_areas,
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service area analysis failed: {str(e)}")


@router.get("/population-distribution", summary="Get population distribution by region")
async def get_population_distribution() -> Dict[str, Any]:
    """
    Estimate population distribution based on building density.
    
    Uses building count as a proxy for population.
    """
    start_time = time.time()
    
    try:
        # Get building count by region
        query = """
            SELECT 
                r.document_id,
                r.name,
                r.admin_level_id,
                COUNT(b.id) AS building_count,
                r.area_sq_km::float AS area_sq_km,
                COUNT(b.id)::float / NULLIF(r.area_sq_km::float, 0) AS buildings_per_sq_km
            FROM regions r
            LEFT JOIN buildings b ON ST_Contains(r.geom, b.geom)
            WHERE r.area_sq_km IS NOT NULL AND r.area_sq_km > 0
            GROUP BY r.document_id, r.name, r.admin_level_id, r.area_sq_km
            HAVING COUNT(b.id) > 0
            ORDER BY building_count DESC
        """
        
        result = await postgis_client.execute_query(query)
        
        # Calculate estimated population (assuming avg 3 people per building)
        PEOPLE_PER_BUILDING = 3
        
        distribution = []
        total_buildings = 0
        
        for region in result:
            building_count = region['building_count']
            estimated_pop = building_count * PEOPLE_PER_BUILDING
            total_buildings += building_count
            area_sq_km = float(region['area_sq_km'])
            
            distribution.append({
                'region_id': region['document_id'],
                'region_name': region['name'],
                'admin_level': region['admin_level_id'],
                'building_count': building_count,
                'area_sq_km': round(area_sq_km, 2),
                'buildings_per_sq_km': round(float(region['buildings_per_sq_km']), 2),
                'estimated_population': estimated_pop,
                'population_density_per_sq_km': round(estimated_pop / area_sq_km, 2) if area_sq_km > 0 else 0
            })
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'regions': distribution,
            'total_buildings': total_buildings,
            'estimated_total_population': total_buildings * PEOPLE_PER_BUILDING,
            'assumption': f'{PEOPLE_PER_BUILDING} people per building',
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Population distribution query failed: {str(e)}")


@router.get("/transport-demand", summary="Estimate transport demand")
async def get_transport_demand_estimate(
    passengers_per_building_per_hour: float = Query(0.05, ge=0.001, le=1.0)
) -> Dict[str, Any]:
    """
    Estimate transport demand based on building density and routes.
    
    Calculates expected passenger demand across the system.
    """
    start_time = time.time()
    
    try:
        # Get all routes from Strapi
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{STRAPI_URL}/api/routes",
                params={"pagination[pageSize]": 1000}
            )
            routes_data = response.json()
            routes = routes_data.get('data', [])
        
        route_demand = []
        total_demand = 0
        
        for route in routes:
            route_id = route['id']
            attrs = route['attributes']
            doc_id = attrs.get('documentId') or attrs.get('document_id')
            
            if not doc_id:
                continue
            
            # Get buildings along route
            try:
                buildings = await postgis_client.get_buildings_near_route(
                    route_id=doc_id,
                    buffer_meters=100,
                    limit=10000
                )
                
                building_count = len(buildings)
                demand_per_hour = building_count * passengers_per_building_per_hour
                total_demand += demand_per_hour
                
                route_demand.append({
                    'route_id': route_id,
                    'short_name': attrs.get('route_short_name'),
                    'long_name': attrs.get('route_long_name'),
                    'building_count': building_count,
                    'estimated_demand_per_hour': round(demand_per_hour, 1),
                    'estimated_demand_per_day': round(demand_per_hour * 12, 1)  # Assume 12 hours operation
                })
            except:
                continue
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'routes_analyzed': len(route_demand),
            'total_demand_per_hour': round(total_demand, 1),
            'total_demand_per_day': round(total_demand * 12, 1),
            'parameter': f'{passengers_per_building_per_hour} passengers per building per hour',
            'routes': route_demand,
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demand estimation failed: {str(e)}")
