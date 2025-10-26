"""
PostGIS Client - Direct spatial queries to PostgreSQL
Optimized for performance with connection pooling
"""

import asyncpg
import time
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
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Convert to list of dicts
        result = [dict(row) for row in rows]
        
        return result
    
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
        query = """
            WITH nearby AS (
                SELECT 
                    name,
                    highway_type,
                    geom
                FROM highways
                WHERE ST_DWithin(
                    geom,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326),
                    $3 / 111320.0  -- Convert meters to degrees (approximate)
                )
                LIMIT 50  -- Get nearby candidates using index
            )
            SELECT 
                name,
                highway_type,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography
                ) as distance_meters
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
        query = """
            WITH nearby AS (
                SELECT 
                    name,
                    poi_type,
                    amenity,
                    geom
                FROM pois
                WHERE ST_DWithin(
                    geom,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326),
                    $3 / 111320.0  -- Convert meters to degrees (approximate)
                )
                LIMIT 50  -- Get nearby candidates using index
            )
            SELECT 
                name,
                poi_type,
                amenity,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography
                ) as distance_meters
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
                al.region_type
            FROM regions r
            JOIN admin_levels al ON r.admin_level_id = al.id
            WHERE ST_Contains(
                r.geom,
                ST_SetSRID(ST_MakePoint($2, $1), 4326)
            )
            ORDER BY al.admin_level ASC
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
        Returns: {id, document_id, name, landuse_type}
        """
        query = """
            SELECT 
                id,
                document_id,
                name,
                landuse_type
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
        query = """
            SELECT 
                b.id as building_id,
                b.document_id,
                b.latitude,
                b.longitude,
                ST_Distance(
                    b.geom::geography,
                    h.geom::geography
                ) as distance_meters
            FROM buildings b
            CROSS JOIN highways h
            WHERE h.document_id = $1
              AND ST_DWithin(
                b.geom::geography,
                h.geom::geography,
                $2
              )
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
        query = """
            WITH nearby AS (
                SELECT 
                    id,
                    document_id,
                    latitude,
                    longitude,
                    geom
                FROM buildings
                WHERE ST_DWithin(
                    geom,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326),
                    $3 / 111320.0  -- Convert meters to degrees (approximate)
                )
            )
            SELECT 
                id as building_id,
                document_id,
                latitude,
                longitude,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography
                ) as distance_meters
            FROM nearby
            WHERE ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography
            ) <= $3
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
