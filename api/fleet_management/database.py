"""
Fleet Management Database Service
===============================
Database operations for fleet management
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

from config.database import get_ssh_tunnel, get_db_config
from models import Base, Vehicle, Route, Stop, Timetable, RouteStop

logger = logging.getLogger(__name__)

class FleetDatabaseService:
    """Database service for fleet management operations"""
    
    def __init__(self):
        self.tunnel = None
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection with SSH tunnel"""
        if self._initialized:
            return
            
        try:
            logger.info("🔌 Initializing database connection...")
            
            # Start SSH tunnel
            self.tunnel = get_ssh_tunnel()
            self.tunnel.start()
            logger.info(f"🚇 SSH tunnel established on port {self.tunnel.local_bind_port}")
            
            # Create database engine
            db_config = get_db_config(self.tunnel)
            connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
            
            self.engine = create_engine(connection_string, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Test connection
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                logger.info("✅ Database connection successful")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {str(e)}")
            await self.cleanup()
            raise e
    
    async def cleanup(self):
        """Clean up database connections"""
        if self.tunnel:
            self.tunnel.stop()
            logger.info("🚇 SSH tunnel closed")
        self._initialized = False
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper cleanup"""
        if not self._initialized:
            await self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    async def save_routes_from_geojson(self, geojson_data: Dict, country: str, source_file: str) -> int:
        """Save routes from GeoJSON data to database"""
        try:
            async with self.get_session() as session:
                routes_saved = 0
                
                if 'features' not in geojson_data:
                    logger.warning(f"⚠️ No features found in GeoJSON data")
                    return 0
                
                for feature in geojson_data['features']:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry')
                    
                    if not geometry or geometry.get('type') != 'LineString':
                        logger.warning(f"⚠️ Skipping non-LineString feature")
                        continue
                    
                    # Extract route information
                    route_id = properties.get('route_id') or properties.get('id') or f"{country}_route_{routes_saved + 1}"
                    route_name = properties.get('route_short_name') or properties.get('name') or f"Route {route_id}"
                    
                    # Check if route already exists
                    existing_route = session.query(Route).filter_by(route_id=route_id).first()
                    if existing_route:
                        logger.info(f"📍 Route {route_id} already exists, updating...")
                        existing_route.name = route_name
                        # Update geometry as WKT
                        coordinates = geometry['coordinates']
                        linestring_wkt = f"LINESTRING({', '.join([f'{coord[0]} {coord[1]}' for coord in coordinates])})"
                        existing_route.shape = linestring_wkt
                    else:
                        # Create new route
                        coordinates = geometry['coordinates']
                        linestring_wkt = f"LINESTRING({', '.join([f'{coord[0]} {coord[1]}' for coord in coordinates])})"
                        
                        new_route = Route(
                            route_id=route_id,
                            name=route_name,
                            shape=linestring_wkt
                        )
                        session.add(new_route)
                        logger.info(f"📍 Added new route: {route_id}")
                    
                    routes_saved += 1
                
                session.commit()
                logger.info(f"✅ Saved {routes_saved} routes for {country} from {source_file}")
                return routes_saved
                
        except Exception as e:
            logger.error(f"❌ Error saving routes to database: {str(e)}")
            raise e
    
    async def save_vehicles_from_json(self, vehicle_data: List[Dict], country: str, source_file: str) -> int:
        """Save vehicles from JSON data to database"""
        try:
            async with self.get_session() as session:
                vehicles_saved = 0
                
                for vehicle_info in vehicle_data:
                    vehicle_id = vehicle_info.get('vehicle_id') or vehicle_info.get('id') or f"{country}_vehicle_{vehicles_saved + 1}"
                    status = vehicle_info.get('status', 'available')
                    route_id = vehicle_info.get('route_id')
                    
                    # Check if vehicle already exists
                    existing_vehicle = session.query(Vehicle).filter_by(vehicle_id=vehicle_id).first()
                    if existing_vehicle:
                        logger.info(f"🚌 Vehicle {vehicle_id} already exists, updating...")
                        existing_vehicle.status = status
                        existing_vehicle.route_id = route_id
                    else:
                        # Create new vehicle
                        new_vehicle = Vehicle(
                            vehicle_id=vehicle_id,
                            status=status,
                            route_id=route_id
                        )
                        session.add(new_vehicle)
                        logger.info(f"🚌 Added new vehicle: {vehicle_id}")
                    
                    vehicles_saved += 1
                
                session.commit()
                logger.info(f"✅ Saved {vehicles_saved} vehicles for {country} from {source_file}")
                return vehicles_saved
                
        except Exception as e:
            logger.error(f"❌ Error saving vehicles to database: {str(e)}")
            raise e
    
    async def get_countries_with_data(self) -> List[Dict[str, Any]]:
        """Get list of countries with fleet data"""
        try:
            async with self.get_session() as session:
                # Get countries with their route and vehicle counts using proper foreign key relationships
                query = text("""
                    SELECT 
                        c.country_id,
                        c.name as country_name,
                        c.iso_code,
                        COALESCE(r.route_count, 0) as route_count,
                        COALESCE(v.vehicle_count, 0) as vehicle_count
                    FROM countries c
                    LEFT JOIN (
                        SELECT country_id, COUNT(*) as route_count 
                        FROM routes 
                        WHERE is_active = true
                        GROUP BY country_id
                    ) r ON c.country_id = r.country_id
                    LEFT JOIN (
                        SELECT country_id, COUNT(*) as vehicle_count 
                        FROM vehicles 
                        WHERE status = 'available'
                        GROUP BY country_id
                    ) v ON c.country_id = v.country_id
                    ORDER BY c.name
                """)
                
                results = session.execute(query).fetchall()
                
                # Format results
                countries = []
                for row in results:
                    countries.append({
                        "country": row.iso_code.lower(),  # Use ISO code as identifier
                        "name": row.country_name,
                        "routes": row.route_count,
                        "vehicles": row.vehicle_count
                    })
                
                # Add default if no data - return empty list instead
                if not countries:
                    logger.warning("No countries found in database")
                
                return countries
                
        except Exception as e:
            logger.error(f"❌ Error getting countries: {str(e)}")
            # Return default data if database is not available
            return [{"country": "barbados", "name": "Barbados", "routes": 0, "vehicles": 0}]
    
    async def get_country_routes(self, country: str) -> List[Dict]:
        """Get all routes for a specific country"""
        try:
            async with self.get_session() as session:
                # Get country_id from ISO code
                country_query = text("SELECT country_id FROM countries WHERE LOWER(iso_code) = :iso_code")
                country_result = session.execute(country_query, {"iso_code": country.lower()}).fetchone()
                
                if not country_result:
                    logger.warning(f"Country not found for ISO code: {country}")
                    return []
                
                country_id = country_result.country_id
                
                # Get routes for this country using proper foreign key
                routes_query = text("""
                    SELECT 
                        r.route_id,
                        r.short_name,
                        r.long_name,
                        r.is_active,
                        COUNT(v.vehicle_id) as vehicle_count
                    FROM routes r
                    LEFT JOIN vehicles v ON r.route_id = v.preferred_route_id 
                    WHERE r.country_id = :country_id AND r.is_active = true
                    GROUP BY r.route_id, r.short_name, r.long_name, r.is_active
                    ORDER BY r.short_name
                """)
                
                routes = session.execute(routes_query, {"country_id": country_id}).fetchall()
                
                return [{
                    "route_id": str(route.route_id),
                    "name": route.long_name or route.short_name,
                    "short_name": route.short_name,
                    "has_geometry": False,  # TODO: Check if route has geometry
                    "vehicle_count": route.vehicle_count
                } for route in routes]
                
        except Exception as e:
            logger.error(f"❌ Error getting routes for {country}: {str(e)}")
            return []
    
    async def get_country_vehicles(self, country: str) -> List[Dict]:
        """Get all vehicles for a specific country"""
        try:
            async with self.get_session() as session:
                # Get country_id from ISO code
                country_query = text("SELECT country_id FROM countries WHERE LOWER(iso_code) = :iso_code")
                country_result = session.execute(country_query, {"iso_code": country.lower()}).fetchone()
                
                if not country_result:
                    logger.warning(f"Country not found for ISO code: {country}")
                    return []
                
                country_id = country_result.country_id
                
                # Get vehicles for this country using proper foreign key
                vehicles_query = text("""
                    SELECT 
                        v.vehicle_id,
                        v.reg_code,
                        v.status,
                        v.preferred_route_id,
                        r.short_name as route_name
                    FROM vehicles v
                    LEFT JOIN routes r ON v.preferred_route_id = r.route_id
                    WHERE v.country_id = :country_id
                    ORDER BY v.reg_code
                """)
                
                vehicles = session.execute(vehicles_query, {"country_id": country_id}).fetchall()
                
                return [{
                    "vehicle_id": str(vehicle.vehicle_id),
                    "reg_code": vehicle.reg_code,
                    "status": vehicle.status,
                    "route_id": str(vehicle.preferred_route_id) if vehicle.preferred_route_id else None,
                    "route_name": vehicle.route_name
                } for vehicle in vehicles]
                
        except Exception as e:
            logger.error(f"❌ Error getting vehicles for {country}: {str(e)}")
            return []
    
    async def delete_country_data(self, country: str) -> Dict[str, int]:
        """Delete all data for a specific country from database"""
        try:
            async with self.get_session() as session:
                # Get country_id from ISO code
                country_query = text("SELECT country_id FROM countries WHERE LOWER(iso_code) = :iso_code")
                country_result = session.execute(country_query, {"iso_code": country.lower()}).fetchone()
                
                if not country_result:
                    logger.warning(f"Country not found for ISO code: {country}")
                    return {"vehicles": 0, "routes": 0, "timetables": 0}
                
                country_id = country_result.country_id
                
                # Delete vehicles first (due to foreign key constraints)
                vehicles_delete_query = text("DELETE FROM vehicles WHERE country_id = :country_id")
                vehicles_result = session.execute(vehicles_delete_query, {"country_id": country_id})
                vehicles_deleted = vehicles_result.rowcount
                
                # Delete routes
                routes_delete_query = text("DELETE FROM routes WHERE country_id = :country_id")
                routes_result = session.execute(routes_delete_query, {"country_id": country_id})
                routes_deleted = routes_result.rowcount
                
                session.commit()
                
                result = {
                    "vehicles": vehicles_deleted,
                    "routes": routes_deleted,
                    "timetables": 0  # TODO: implement timetables
                }
                
                logger.info(f"🗑️ Deleted {vehicles_deleted} vehicles and {routes_deleted} routes for {country}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error deleting data for {country}: {str(e)}")
            raise e

# Global database service instance
db_service = FleetDatabaseService()
