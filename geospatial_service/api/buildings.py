"""
Buildings API - Dedicated building queries and density analysis
All building-related operations (Single Responsibility Principle)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from services.postgis_client import postgis_client

router = APIRouter(prefix="/buildings", tags=["Buildings"])


class Building(BaseModel):
    """Building model"""
    building_id: int
    document_id: str
    latitude: float
    longitude: float
    distance_meters: Optional[float] = None


@router.get("/at-point", summary="Get buildings near a point")
async def get_buildings_at_point(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: int = Query(500, ge=10, le=5000, description="Search radius in meters"),
    limit: int = Query(5000, ge=1, le=10000, description="Maximum buildings to return")
) -> Dict[str, Any]:
    """
    Get all buildings within radius of a point.
    
    Essential for catchment area analysis.
    """
    start_time = time.time()
    
    try:
        buildings_data = await postgis_client.get_buildings_near_depot(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'query_point': {
                'latitude': latitude,
                'longitude': longitude
            },
            'radius_meters': radius_meters,
            'buildings': buildings_data,
            'count': len(buildings_data),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Buildings query failed: {str(e)}")


@router.post("/along-route", summary="Get buildings along a route")
async def get_buildings_along_route(
    request_data: Dict[str, Any],
    buffer_meters: int = Query(100, ge=10, le=1000, description="Buffer around route in meters"),
    limit: int = Query(5000, ge=1, le=10000, description="Maximum buildings to return")
) -> Dict[str, Any]:
    """
    Get all buildings within buffer distance of a route.
    
    Request body can contain either:
    - {"route_id": "document_id"} - for Strapi route
    - {"route_geojson": {"type": "LineString", "coordinates": [...]}} - for custom route
    
    Essential for route-based passenger spawning.
    """
    start_time = time.time()
    
    route_id = request_data.get('route_id')
    route_geojson = request_data.get('route_geojson')
    
    if not route_id and not route_geojson:
        raise HTTPException(status_code=400, detail="Either route_id or route_geojson is required")
    
    try:
        if route_id:
            # Use existing method for Strapi routes
            buildings_data = await postgis_client.get_buildings_near_route(
                route_id=route_id,
                buffer_meters=buffer_meters,
                limit=limit
            )
        else:
            # For custom GeoJSON route, query buildings along the linestring
            coords = route_geojson.get('coordinates', [])
            if not coords:
                raise HTTPException(status_code=400, detail="Invalid GeoJSON: no coordinates")
            
            # Convert coords to WKT LineString
            wkt_coords = ', '.join([f"{lon} {lat}" for lon, lat in coords])
            
            query = """
                SELECT 
                    id,
                    document_id,
                    ST_Y(ST_Centroid(geom)) AS latitude,
                    ST_X(ST_Centroid(geom)) AS longitude,
                    ST_Distance(
                        ST_SetSRID(ST_GeomFromText($1), 4326)::geography,
                        geom::geography
                    ) AS distance_meters
                FROM buildings
                WHERE ST_DWithin(
                    ST_SetSRID(ST_GeomFromText($1), 4326)::geography,
                    geom::geography,
                    $2
                )
                ORDER BY distance_meters ASC
                LIMIT $3
            """
            
            buildings_data = await postgis_client.execute_query(
                query, f"LINESTRING({wkt_coords})", buffer_meters, limit
            )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'route_id': route_id,
            'buffer_meters': buffer_meters,
            'buildings': buildings_data,
            'count': len(buildings_data),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route buildings query failed: {str(e)}")



@router.post("/in-polygon", summary="Get buildings inside a polygon")
async def get_buildings_in_polygon(
    polygon_data: Dict[str, Any],
    limit: int = Query(10000, ge=1, le=50000, description="Maximum buildings to return")
) -> Dict[str, Any]:
    """
    Get all buildings inside a polygon boundary.
    
    Useful for zone-based analysis.
    
    Request body should contain:
    {
        "coordinates": [[lon, lat], [lon, lat], ...]
    }
    """
    start_time = time.time()
    
    polygon_coords = polygon_data.get('coordinates', [])
    
    if not polygon_coords or len(polygon_coords) < 3:
        raise HTTPException(status_code=400, detail="Polygon must have at least 3 coordinates")
    
    try:
        # Build polygon WKT from coordinates
        # Coordinates should be [[lon, lat], [lon, lat], ...]
        if not polygon_coords[0] == polygon_coords[-1]:
            # Close the polygon if not already closed
            polygon_coords.append(polygon_coords[0])
        
        # Build WKT string
        coords_wkt = ", ".join([f"{coord[0]} {coord[1]}" for coord in polygon_coords])
        polygon_wkt = f"POLYGON(({coords_wkt}))"
        
        query = """
            SELECT 
                b.id as building_id,
                b.document_id,
                ST_Y(ST_Centroid(b.geom)) as latitude,
                ST_X(ST_Centroid(b.geom)) as longitude
            FROM buildings b
            WHERE ST_Contains(
                ST_GeomFromText($1, 4326),
                b.geom
            )
            LIMIT $2
        """
        
        buildings_data = await postgis_client.execute_query(query, polygon_wkt, limit)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'polygon_vertices': len(polygon_coords),
            'buildings': buildings_data,
            'count': len(buildings_data),
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polygon buildings query failed: {str(e)}")


@router.get("/density/{region_id}", summary="Get building density in region")
async def get_building_density(region_id: str) -> Dict[str, Any]:
    """
    Calculate building density within a region.
    
    Returns:
    - Total building count
    - Region area
    - Buildings per square kilometer
    """
    start_time = time.time()
    
    try:
        # Query region geometry and count buildings
        query = """
            WITH region_area AS (
                SELECT 
                    geom,
                    ST_Area(geom::geography) AS area_square_meters
                FROM regions
                WHERE document_id = $1
                LIMIT 1
            )
            SELECT 
                COUNT(b.id) as building_count,
                r.area_square_meters,
                r.area_square_meters / 1000000.0 AS area_square_km,
                COUNT(b.id) / (r.area_square_meters / 1000000.0) AS buildings_per_sq_km
            FROM region_area r
            LEFT JOIN buildings b ON ST_Contains(r.geom, b.geom)
            GROUP BY r.area_square_meters
        """
        
        result = await postgis_client.execute_query(query, region_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Region {region_id} not found")
        
        latency_ms = (time.time() - start_time) * 1000
        
        density_data = result[0]
        
        return {
            'region_id': region_id,
            'building_count': density_data['building_count'],
            'area_square_meters': density_data['area_square_meters'],
            'area_square_km': round(density_data['area_square_km'], 2),
            'buildings_per_sq_km': round(density_data['buildings_per_sq_km'], 2),
            'latency_ms': round(latency_ms, 2)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Density calculation failed: {str(e)}")


@router.get("/count", summary="Get total building count")
async def get_building_count(
    region_id: Optional[str] = Query(None, description="Optional region filter"),
) -> Dict[str, Any]:
    """
    Get total count of buildings.
    
    Optionally filter by region.
    """
    start_time = time.time()
    
    try:
        if region_id:
            # Count buildings in specific region
            query = """
                WITH region_geom AS (
                    SELECT geom FROM regions WHERE document_id = $1 LIMIT 1
                )
                SELECT COUNT(b.id) as building_count
                FROM buildings b, region_geom r
                WHERE ST_Contains(r.geom, b.geom)
            """
            result = await postgis_client.execute_query(query, region_id)
        else:
            # Count all buildings
            query = "SELECT COUNT(*) as building_count FROM buildings"
            result = await postgis_client.execute_query(query)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'building_count': result[0]['building_count'],
            'region_id': region_id,
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Building count query failed: {str(e)}")


@router.get("/stats", summary="Get building statistics")
async def get_building_stats() -> Dict[str, Any]:
    """
    Get comprehensive building statistics.
    
    Returns:
    - Total count
    - Distribution by type (if available)
    - Geographic extent
    """
    start_time = time.time()
    
    try:
        # Get overall stats
        query = """
            SELECT 
                COUNT(*) as total_buildings,
                ST_XMin(ST_Extent(geom)) as min_lon,
                ST_XMax(ST_Extent(geom)) as max_lon,
                ST_YMin(ST_Extent(geom)) as min_lat,
                ST_YMax(ST_Extent(geom)) as max_lat
            FROM buildings
        """
        
        result = await postgis_client.execute_query(query)
        
        if not result:
            raise HTTPException(status_code=500, detail="Stats query failed")
        
        stats = result[0]
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'total_buildings': stats['total_buildings'],
            'geographic_extent': {
                'min_latitude': stats['min_lat'],
                'max_latitude': stats['max_lat'],
                'min_longitude': stats['min_lon'],
                'max_longitude': stats['max_lon']
            },
            'latency_ms': round(latency_ms, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


@router.post("/batch-at-points", summary="Get buildings near multiple points")
async def get_buildings_batch(
    batch_data: Dict[str, Any],
    radius_meters: int = Query(500, ge=10, le=5000),
    limit_per_point: int = Query(1000, ge=1, le=5000)
) -> Dict[str, Any]:
    """
    Get buildings near multiple points in a single request.
    
    Efficient batch operation for multiple catchment queries.
    
    Request body should contain:
    {
        "points": [{"lat": 13.1, "lon": -59.6}, ...]
    }
    """
    start_time = time.time()
    
    points = batch_data.get('points', [])
    
    if not points:
        raise HTTPException(status_code=400, detail="No points provided")
    
    results = []
    
    for point in points:
        try:
            buildings_data = await postgis_client.get_buildings_near_depot(
                latitude=point['lat'],
                longitude=point['lon'],
                radius_meters=radius_meters,
                limit=limit_per_point
            )
            
            results.append({
                'point': point,
                'buildings': buildings_data,
                'count': len(buildings_data),
                'success': True
            })
        except Exception as e:
            results.append({
                'point': point,
                'error': str(e),
                'success': False
            })
    
    latency_ms = (time.time() - start_time) * 1000
    
    return {
        'points_queried': len(points),
        'radius_meters': radius_meters,
        'results': results,
        'latency_ms': round(latency_ms, 2)
    }
