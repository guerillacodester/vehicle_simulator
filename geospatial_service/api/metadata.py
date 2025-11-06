"""
Metadata API - Service metadata and dataset information
System information and capabilities (Single Responsibility Principle)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time

from ..services.postgis_client import postgis_client

router = APIRouter(prefix="/meta", tags=["Metadata"])


@router.get("/stats", summary="Get database statistics")
async def get_database_stats() -> Dict[str, Any]:
    """
    Get comprehensive database statistics.
    
    Returns counts for all major feature types.
    """
    start_time = time.time()
    
    try:
        stats = await postgis_client.get_stats()
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'features': stats,
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


@router.get("/bounds", summary="Get geographic bounds of dataset")
async def get_geographic_bounds() -> Dict[str, Any]:
    """
    Get the geographic extent of the entire dataset.
    
    Returns bounding box coordinates.
    """
    start_time = time.time()
    
    try:
        # Get extent from buildings (most comprehensive dataset)
        query = """
            SELECT 
                ST_XMin(ST_Extent(geom)) as min_lon,
                ST_XMax(ST_Extent(geom)) as max_lon,
                ST_YMin(ST_Extent(geom)) as min_lat,
                ST_YMax(ST_Extent(geom)) as max_lat,
                ST_X(ST_Centroid(ST_Extent(geom))) as center_lon,
                ST_Y(ST_Centroid(ST_Extent(geom))) as center_lat
            FROM buildings
        """
        
        result = await postgis_client.execute_query(query)
        
        if not result:
            raise HTTPException(status_code=500, detail="Bounds query failed")
        
        bounds = result[0]
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'bounding_box': {
                'min_latitude': bounds['min_lat'],
                'max_latitude': bounds['max_lat'],
                'min_longitude': bounds['min_lon'],
                'max_longitude': bounds['max_lon']
            },
            'center': {
                'latitude': bounds['center_lat'],
                'longitude': bounds['center_lon']
            },
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bounds query failed: {str(e)}")


@router.get("/regions", summary="List all regions")
async def list_all_regions() -> Dict[str, Any]:
    """
    Get list of all administrative regions.
    
    Returns regions with their types and areas.
    """
    start_time = time.time()
    
    try:
        query = """
            SELECT 
                document_id,
                name,
                admin_level_id,
                area_sq_km,
                center_longitude AS center_lon,
                center_latitude AS center_lat
            FROM regions
            WHERE admin_level_id IS NOT NULL
            ORDER BY admin_level_id, name
        """
        
        result = await postgis_client.execute_query(query)
        
        # Group by admin level
        regions_by_level = {}
        for region in result:
            level = region['admin_level_id']
            if level not in regions_by_level:
                regions_by_level[level] = []
            
            regions_by_level[level].append({
                'document_id': region['document_id'],
                'name': region['name'],
                'area_sq_km': float(region['area_sq_km']) if region['area_sq_km'] else 0.0,
                'center': {
                    'latitude': float(region['center_lat']) if region['center_lat'] else 0.0,
                    'longitude': float(region['center_lon']) if region['center_lon'] else 0.0
                }
            })
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'total_regions': len(result),
            'by_admin_level': regions_by_level,
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regions query failed: {str(e)}")


@router.get("/tags", summary="Get available OSM tags")
async def get_available_tags() -> Dict[str, Any]:
    """
    Get summary of available OpenStreetMap tags in the dataset.
    
    Shows what types of features are available.
    """
    start_time = time.time()
    
    try:
        # Get highway types
        highway_query = """
            SELECT 
                highway_type,
                COUNT(*) as count
            FROM highways
            WHERE highway_type IS NOT NULL
            GROUP BY highway_type
            ORDER BY count DESC
        """
        
        # Get POI types
        poi_query = """
            SELECT 
                COALESCE(amenity, poi_type, 'other') as type,
                COUNT(*) as count
            FROM pois
            GROUP BY COALESCE(amenity, poi_type, 'other')
            ORDER BY count DESC
            LIMIT 50
        """
        
        # Get landuse types (use zone_type instead of landuse_type)
        landuse_query = """
            SELECT 
                zone_type,
                COUNT(*) as count
            FROM landuse_zones
            WHERE zone_type IS NOT NULL
            GROUP BY zone_type
            ORDER BY count DESC
        """
        
        highways = await postgis_client.execute_query(highway_query)
        pois = await postgis_client.execute_query(poi_query)
        landuse = await postgis_client.execute_query(landuse_query)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'highway_types': highways,
            'poi_types': pois,
            'landuse_types': landuse,
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tags query failed: {str(e)}")


@router.get("/version", summary="Get API version and capabilities")
async def get_version_info() -> Dict[str, Any]:
    """
    Get API version information and capabilities.
    
    Shows what features are available in this API.
    """
    return {
        'version': '2.0.0',
        'name': 'Geospatial Services API',
        'description': 'Production-grade geospatial query and analysis API',
        'capabilities': {
            'geocoding': {
                'reverse': True,
                'forward': False,
                'batch': True
            },
            'geofencing': {
                'point_in_polygon': True,
                'batch_check': True,
                'region_info': True
            },
            'routes': {
                'geometry': True,
                'buildings': True,
                'metrics': True,
                'coverage': True,
                'nearest': True,
                'list': True
            },
            'depots': {
                'catchment': True,
                'routes': True,
                'coverage': True,
                'nearest': True,
                'list': True
            },
            'buildings': {
                'at_point': True,
                'along_route': True,
                'in_polygon': True,
                'density': True,
                'stats': True,
                'batch': True
            },
            'spawn_analysis': {
                'depot_analysis': True,
                'route_analysis': True,
                'system_overview': True,
                'compare_scaling': True,
                'configuration': True
            },
            'analytics': {
                'density_heatmap': True,
                'route_coverage': True,
                'depot_service_areas': True,
                'population_distribution': True,
                'transport_demand': True
            },
            'metadata': {
                'stats': True,
                'bounds': True,
                'regions': True,
                'tags': True,
                'version': True
            }
        },
        'endpoints': {
            'geocoding': '/geocode',
            'geofencing': '/geofence',
            'routes': '/routes',
            'depots': '/depots',
            'buildings': '/buildings',
            'spawn_analysis': '/spawn',
            'analytics': '/analytics',
            'metadata': '/meta',
            'spatial': '/spatial',
            'documentation': '/docs'
        }
    }


@router.get("/health", summary="Health check with detailed status")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check.
    
    Tests database connectivity and returns system status.
    """
    start_time = time.time()
    
    try:
        # Test database
        stats = await postgis_client.get_stats()
        db_healthy = True
        db_error = None
    except Exception as e:
        db_healthy = False
        db_error = str(e)
        stats = None
    
    latency_ms = (time.time() - start_time) * 1000
    
    overall_healthy = db_healthy
    
    return {
        'status': 'healthy' if overall_healthy else 'unhealthy',
        'timestamp': time.time(),
        'components': {
            'database': {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'error': db_error,
                'features': stats if db_healthy else None
            },
            'api': {
                'status': 'healthy',
                'version': '2.0.0'
            }
        },
        'latency_ms': round(latency_ms, 2)
    }
