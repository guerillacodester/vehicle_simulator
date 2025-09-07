"""
Fleet Management CRUD Operations
==============================
Comprehensive CRUD operations for all fleet entities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, select, insert, update, delete
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, date
import uuid

from config.database import get_ssh_tunnel, get_db_config
from models import (
    Base, Country, Route, Vehicle, Stop, Depot, Driver, Service, 
    Trip, StopTime, Block, Shape, RouteShape, Frequency, Timetable,
    VehicleAssignment, DriverAssignment, VehicleStatusEvent, 
    BlockTrip, BlockBreak, VehicleStatus
)

logger = logging.getLogger(__name__)

class FleetCRUDService:
    """Comprehensive CRUD service for fleet management"""
    
    def __init__(self):
        self.tunnel = None
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
            
        try:
            logger.info("🔌 Initializing CRUD service...")
            
            self.tunnel = get_ssh_tunnel()
            self.tunnel.start()
            
            db_config = get_db_config(self.tunnel)
            connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
            
            self.engine = create_engine(connection_string, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine)
            self._initialized = True
            
            logger.info("✅ CRUD service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CRUD service: {str(e)}")
            raise e
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper cleanup"""
        if not self._initialized:
            await self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.tunnel:
            self.tunnel.stop()
        self._initialized = False

    # =============================================================================
    # COUNTRY OPERATIONS
    # =============================================================================
    
    async def create_country(self, iso_code: str, name: str) -> Dict[str, Any]:
        """Create a new country"""
        async with self.get_session() as session:
            country = Country(iso_code=iso_code, name=name)
            session.add(country)
            session.commit()
            session.refresh(country)
            
            return {
                "country_id": str(country.country_id),
                "iso_code": country.iso_code,
                "name": country.name,
                "created_at": country.created_at.isoformat()
            }
    
    async def get_countries(self) -> List[Dict[str, Any]]:
        """Get all countries"""
        async with self.get_session() as session:
            countries = session.query(Country).all()
            return [{
                "country_id": str(country.country_id),
                "iso_code": country.iso_code,
                "name": country.name,
                "created_at": country.created_at.isoformat()
            } for country in countries]
    
    async def get_country(self, country_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific country"""
        async with self.get_session() as session:
            country = session.query(Country).filter(Country.country_id == country_id).first()
            if not country:
                return None
            
            return {
                "country_id": str(country.country_id),
                "iso_code": country.iso_code,
                "name": country.name,
                "created_at": country.created_at.isoformat()
            }
    
    async def update_country(self, country_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a country"""
        async with self.get_session() as session:
            country = session.query(Country).filter(Country.country_id == country_id).first()
            if not country:
                return None
            
            for key, value in kwargs.items():
                if hasattr(country, key):
                    setattr(country, key, value)
            
            session.commit()
            session.refresh(country)
            
            return {
                "country_id": str(country.country_id),
                "iso_code": country.iso_code,
                "name": country.name,
                "created_at": country.created_at.isoformat()
            }
    
    async def delete_country(self, country_id: str) -> bool:
        """Delete a country (and all related data)"""
        async with self.get_session() as session:
            country = session.query(Country).filter(Country.country_id == country_id).first()
            if not country:
                return False
            
            session.delete(country)
            session.commit()
            return True

    # =============================================================================
    # ROUTE OPERATIONS
    # =============================================================================
    
    async def create_route(self, country_id: str, short_name: str, long_name: str = None, **kwargs) -> Dict[str, Any]:
        """Create a new route"""
        async with self.get_session() as session:
            route = Route(
                country_id=country_id,
                short_name=short_name,
                long_name=long_name,
                **kwargs
            )
            session.add(route)
            session.commit()
            session.refresh(route)
            
            return {
                "route_id": str(route.route_id),
                "country_id": str(route.country_id),
                "short_name": route.short_name,
                "long_name": route.long_name,
                "parishes": route.parishes,
                "is_active": route.is_active,
                "valid_from": route.valid_from.isoformat() if route.valid_from else None,
                "valid_to": route.valid_to.isoformat() if route.valid_to else None,
                "created_at": route.created_at.isoformat(),
                "updated_at": route.updated_at.isoformat()
            }
    
    async def get_routes(self, country_id: str = None) -> List[Dict[str, Any]]:
        """Get routes, optionally filtered by country"""
        async with self.get_session() as session:
            query = session.query(Route)
            if country_id:
                query = query.filter(Route.country_id == country_id)
            
            routes = query.all()
            return [{
                "route_id": str(route.route_id),
                "country_id": str(route.country_id),
                "short_name": route.short_name,
                "long_name": route.long_name,
                "parishes": route.parishes,
                "is_active": route.is_active,
                "valid_from": route.valid_from.isoformat() if route.valid_from else None,
                "valid_to": route.valid_to.isoformat() if route.valid_to else None,
                "created_at": route.created_at.isoformat(),
                "updated_at": route.updated_at.isoformat()
            } for route in routes]

    # =============================================================================
    # VEHICLE OPERATIONS
    # =============================================================================
    
    async def create_vehicle(self, country_id: str, reg_code: str, **kwargs) -> Dict[str, Any]:
        """Create a new vehicle"""
        async with self.get_session() as session:
            vehicle = Vehicle(
                country_id=country_id,
                reg_code=reg_code,
                **kwargs
            )
            session.add(vehicle)
            session.commit()
            session.refresh(vehicle)
            
            return {
                "vehicle_id": str(vehicle.vehicle_id),
                "country_id": str(vehicle.country_id),
                "reg_code": vehicle.reg_code,
                "home_depot_id": str(vehicle.home_depot_id) if vehicle.home_depot_id else None,
                "preferred_route_id": str(vehicle.preferred_route_id) if vehicle.preferred_route_id else None,
                "status": vehicle.status.value,
                "profile_id": vehicle.profile_id,
                "notes": vehicle.notes,
                "created_at": vehicle.created_at.isoformat(),
                "updated_at": vehicle.updated_at.isoformat()
            }
    
    async def get_vehicles(self, country_id: str = None) -> List[Dict[str, Any]]:
        """Get vehicles, optionally filtered by country"""
        async with self.get_session() as session:
            query = session.query(Vehicle)
            if country_id:
                query = query.filter(Vehicle.country_id == country_id)
            
            vehicles = query.all()
            return [{
                "vehicle_id": str(vehicle.vehicle_id),
                "country_id": str(vehicle.country_id),
                "reg_code": vehicle.reg_code,
                "home_depot_id": str(vehicle.home_depot_id) if vehicle.home_depot_id else None,
                "preferred_route_id": str(vehicle.preferred_route_id) if vehicle.preferred_route_id else None,
                "status": vehicle.status.value,
                "profile_id": vehicle.profile_id,
                "notes": vehicle.notes,
                "created_at": vehicle.created_at.isoformat(),
                "updated_at": vehicle.updated_at.isoformat()
            } for vehicle in vehicles]

    # =============================================================================
    # STOP OPERATIONS  
    # =============================================================================
    
    async def create_stop(self, name: str, latitude: float, longitude: float, **kwargs) -> Dict[str, Any]:
        """Create a new stop"""
        async with self.get_session() as session:
            # Create PostGIS POINT geometry
            location_wkt = f"POINT({longitude} {latitude})"
            
            stop = Stop(
                name=name,
                location=location_wkt,
                **kwargs
            )
            session.add(stop)
            session.commit()
            session.refresh(stop)
            
            return {
                "stop_id": str(stop.stop_id),
                "name": stop.name,
                "latitude": latitude,
                "longitude": longitude,
                "is_active": stop.is_active,
                "created_at": stop.created_at.isoformat()
            }

    # =============================================================================
    # TIMETABLE OPERATIONS
    # =============================================================================
    
    async def create_timetable(self, route_id: str, service_id: str, name: str, effective_date: date, **kwargs) -> Dict[str, Any]:
        """Create a new timetable"""
        async with self.get_session() as session:
            timetable = Timetable(
                route_id=route_id,
                service_id=service_id,
                name=name,
                effective_date=effective_date,
                **kwargs
            )
            session.add(timetable)
            session.commit()
            session.refresh(timetable)
            
            return {
                "timetable_id": str(timetable.timetable_id),
                "route_id": str(timetable.route_id),
                "service_id": str(timetable.service_id),
                "name": timetable.name,
                "effective_date": timetable.effective_date.isoformat(),
                "is_active": timetable.is_active,
                "created_at": timetable.created_at.isoformat(),
                "updated_at": timetable.updated_at.isoformat()
            }
    
    async def get_timetables(self, route_id: str = None) -> List[Dict[str, Any]]:
        """Get timetables, optionally filtered by route"""
        async with self.get_session() as session:
            query = session.query(Timetable)
            if route_id:
                query = query.filter(Timetable.route_id == route_id)
            
            timetables = query.all()
            return [{
                "timetable_id": str(timetable.timetable_id),
                "route_id": str(timetable.route_id),
                "service_id": str(timetable.service_id),
                "name": timetable.name,
                "effective_date": timetable.effective_date.isoformat(),
                "is_active": timetable.is_active,
                "created_at": timetable.created_at.isoformat(),
                "updated_at": timetable.updated_at.isoformat()
            } for timetable in timetables]

# Global CRUD service instance
crud_service = FleetCRUDService()
