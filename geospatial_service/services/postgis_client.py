"""
PostGIS Client - Direct spatial queries to PostgreSQL
Optimized for performance with connection pooling
"""

import asyncpg
import time
import decimal
from typing import List, Dict, Optional, Tuple, Any
from config.database import db_config


class PostGISClient:
    """PostGIS spatial query client with connection pooling"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize connection pool"""
        if self.pool is None:
            self.pool = await db_config.get_pool(min_size=5, max_size=20)
            print("✅ PostGIS connection pool initialized (5-20 connections)")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("✅ PostGIS connection pool closed")
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts"""
        if not self.pool:
            await self.connect()
        
        start_time = time.time()
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Convert to list of dicts and normalize Decimal -> float for JSON/pydantic
            result = []
            for row in rows:
                d = dict(row)
                for k, v in d.items():
                    if isinstance(v, decimal.Decimal):
                        try:
                            d[k] = float(v)
                        except Exception:
                            d[k] = float(str(v))
                result.append(d)
            
            return result
        except Exception as e:
            print(f"❌ SQL Error: {e}")
            print(f"Query: {query}")
            print(f"Args: {args}")
            raise
    
    # ============================================================================
    # REVERSE GEOCODING QUERIES
    # ============================================================================
    
    async def find_nearest_highway(
        self, 
        latitude: float, 
        longitude: float, 
        radius_meters: int = 500
    ) -> Optional[Dict[str, Any]]:
        """
        Find nearest highway within radius using ST_DWithin
        Returns: {name, highway_type, distance_meters}
        Optimized: Uses geometry index first, then computes geography distance
        """
        # Use a quick bbox (degrees) filter to leverage GiST index, then compute
        # accurate distances in metres using geography for ordering.
        # Convert meters to degrees approximately; longitude scale adjusted by cos(lat).
        query = """
            WITH params AS (
                SELECT
                    $1::double precision AS lat,
                    $2::double precision AS lon,
                    $3::double precision AS meters,
                    ($3::double precision / 111320.0) AS deg_lat,
                    ($3::double precision / (111320.0 * GREATEST(cos(radians($1::double precision)), 0.0001))) AS deg_lon
            ), nearby AS (
                SELECT h.name, h.highway_type, h.geom
                FROM highways h, params p
                WHERE h.geom && ST_MakeEnvelope(p.lon - p.deg_lon, p.lat - p.deg_lat, p.lon + p.deg_lon, p.lat + p.deg_lat, 4326)
            )
            SELECT name, highway_type,
                ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint((SELECT lon FROM params), (SELECT lat FROM params)), 4326)::geography) AS distance_meters
            FROM nearby
            ORDER BY distance_meters ASC
            LIMIT 1
        """
        
        results = await self.execute_query(query, latitude, longitude, radius_meters)
        return results[0] if results else None
    
    async def find_nearest_poi(
        self, 
        latitude: float, 
        longitude: float, 
        radius_meters: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """
        Find nearest POI within radius using ST_DWithin
        Returns: {name, poi_type, amenity, distance_meters}
        Optimized: Uses geometry index first, then computes geography distance
        """
        # Similar pattern: bbox filter then accurate geography distance
        query = """
            WITH params AS (
                SELECT
                    $1::double precision AS lat,
                    $2::double precision AS lon,
                    $3::double precision AS meters,
                    ($3::double precision / 111320.0) AS deg_lat,
                    ($3::double precision / (111320.0 * GREATEST(cos(radians($1::double precision)), 0.0001))) AS deg_lon
            ), nearby AS (
                SELECT p.name, p.poi_type, p.amenity, p.geom
                FROM pois p, params prm
                WHERE p.geom && ST_MakeEnvelope(prm.lon - prm.deg_lon, prm.lat - prm.deg_lat, prm.lon + prm.deg_lon, prm.lat + prm.deg_lat, 4326)
            )
            SELECT name, poi_type, amenity,
                ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint((SELECT lon FROM params), (SELECT lat FROM params)), 4326)::geography) AS distance_meters
            FROM nearby
            ORDER BY distance_meters ASC
            LIMIT 1
        """
        
        results = await self.execute_query(query, latitude, longitude, radius_meters)
        return results[0] if results else None
    
    # ============================================================================
    # GEOFENCE QUERIES
    # ============================================================================
    
    async def check_geofence_region(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Check if point is inside any region using ST_Contains
        Returns: {id, document_id, name, region_type}
        """
        query = """
            SELECT 
                r.id,
                r.document_id,
                r.name,
                'parish' as region_type
            FROM regions r
            WHERE ST_Contains(
                r.geom,
                ST_SetSRID(ST_MakePoint($2, $1), 4326)
            )
            LIMIT 1
        """
        
        results = await self.execute_query(query, latitude, longitude)
        return results[0] if results else None
    
    async def check_geofence_landuse(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Check if point is inside any landuse zone using ST_Contains
        Returns: {id, document_id, name, zone_type}
        """
        query = """
            SELECT 
                id,
                document_id,
                name,
                zone_type
            FROM landuse_zones
            WHERE ST_Contains(
                geom,
                ST_SetSRID(ST_MakePoint($2, $1), 4326)
            )
            LIMIT 1
        """
        
        results = await self.execute_query(query, latitude, longitude)
        return results[0] if results else None
    
    # ============================================================================
    # ROUTE BUILDINGS QUERY
    # ============================================================================
    
    async def get_buildings_near_route(
        self, 
        route_id: str,
        buffer_meters: int = 500,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get buildings within buffer distance of a route (highway)
        Returns: [{building_id, latitude, longitude, distance_meters}]
        """
        # Use highway geom bbox to prefilter buildings, then compute accurate distances
        query = """
            WITH highway_geom AS (
                SELECT geom FROM highways WHERE document_id = $1 LIMIT 1
            ), hparams AS (
                SELECT ST_Envelope(h.geom) AS env, h.geom AS geom FROM highway_geom h
            )
            SELECT 
                b.id as building_id,
                b.document_id,
                ST_Y(ST_Centroid(b.geom)) as latitude,
                ST_X(ST_Centroid(b.geom)) as longitude,
                ST_Distance(b.geom::geography, (SELECT geom FROM highway_geom)::geography) as distance_meters
            FROM buildings b, highway_geom hg
            WHERE b.geom && ST_Envelope(hg.geom)
              AND ST_DWithin(b.geom::geography, hg.geom::geography, $2)
            ORDER BY distance_meters ASC
            LIMIT $3
        """
        
        return await self.execute_query(query, route_id, buffer_meters, limit)
    
    # ============================================================================
    # DEPOT CATCHMENT QUERY
    # ============================================================================
    
    async def get_buildings_near_depot(
        self, 
        latitude: float,
        longitude: float,
        radius_meters: int = 1000,
        limit: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Get all buildings within radius of depot point
        Returns: [{building_id, latitude, longitude, distance_meters}]
        Optimized: Uses geometry index for fast spatial query
        """
        # Prefilter with bbox to use GiST index, then compute exact geography distance
        query = """
            WITH params AS (
                SELECT
                    $1::double precision AS lat,
                    $2::double precision AS lon,
                    $3::double precision AS meters,
                    ($3::double precision / 111320.0) AS deg_lat,
                    ($3::double precision / (111320.0 * GREATEST(cos(radians($1::double precision)), 0.0001))) AS deg_lon
            ), nearby AS (
                SELECT id, document_id, ST_Centroid(geom) AS centroid
                FROM buildings b, params p
                WHERE b.geom && ST_MakeEnvelope(p.lon - p.deg_lon, p.lat - p.deg_lat, p.lon + p.deg_lon, p.lat + p.deg_lat, 4326)
            )
            SELECT id AS building_id, document_id,
                ST_Y(centroid) AS latitude,
                ST_X(centroid) AS longitude,
                ST_Distance(centroid::geography, ST_SetSRID(ST_MakePoint((SELECT lon FROM params), (SELECT lat FROM params)), 4326)::geography) AS distance_meters
            FROM nearby
            WHERE ST_Distance(centroid::geography, ST_SetSRID(ST_MakePoint((SELECT lon FROM params), (SELECT lat FROM params)), 4326)::geography) <= (SELECT meters FROM params)
            ORDER BY distance_meters ASC
            LIMIT $4
        """
        
        return await self.execute_query(query, latitude, longitude, radius_meters, limit)
    
    # ============================================================================
    # STATISTICS
    # ============================================================================
    
    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        queries = {
            "buildings": "SELECT COUNT(*) as count FROM buildings",
            "highways": "SELECT COUNT(*) as count FROM highways",
            "pois": "SELECT COUNT(*) as count FROM pois",
            "landuse_zones": "SELECT COUNT(*) as count FROM landuse_zones",
            "regions": "SELECT COUNT(*) as count FROM regions"
        }
        
        stats = {}
        for key, query in queries.items():
            results = await self.execute_query(query)
            stats[key] = results[0]["count"] if results else 0
        
        return stats


# Global instance
postgis_client = PostGISClient()
