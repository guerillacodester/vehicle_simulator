from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import uuid
import enum
from datetime import datetime

Base = declarative_base()

# Enums
class VehicleStatus(enum.Enum):
    available = "available"
    retired = "retired"

# Core Models
class Country(Base):
    __tablename__ = 'countries'
    
    country_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iso_code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    routes = relationship("Route", back_populates="country", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="country", cascade="all, delete-orphan")
    depots = relationship("Depot", back_populates="country", cascade="all, delete-orphan")
    drivers = relationship("Driver", back_populates="country", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="country", cascade="all, delete-orphan")
    blocks = relationship("Block", back_populates="country", cascade="all, delete-orphan")

class Route(Base):
    __tablename__ = 'routes'
    
    route_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    short_name = Column(Text, nullable=False)
    long_name = Column(Text)
    parishes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    valid_from = Column(Date, default=datetime.utcnow().date())
    valid_to = Column(Date)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="routes")
    vehicles = relationship("Vehicle", back_populates="preferred_route")
    trips = relationship("Trip", back_populates="route")
    route_shapes = relationship("RouteShape", back_populates="route")

class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    vehicle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    reg_code = Column(Text, nullable=False)
    home_depot_id = Column(UUID(as_uuid=True), ForeignKey('depots.depot_id'))
    preferred_route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'))
    status = Column(Enum(VehicleStatus), nullable=False, default=VehicleStatus.available)
    profile_id = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="vehicles")
    home_depot = relationship("Depot", back_populates="vehicles")
    preferred_route = relationship("Route", back_populates="vehicles")
    assignments = relationship("VehicleAssignment", back_populates="vehicle")
    status_events = relationship("VehicleStatusEvent", back_populates="vehicle")

class Stop(Base):
    __tablename__ = 'stops'
    
    stop_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    stop_times = relationship("StopTime", back_populates="stop")

class Depot(Base):
    __tablename__ = 'depots'
    
    depot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    location = Column(Geometry('POINT'))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="depots")
    vehicles = relationship("Vehicle", back_populates="home_depot")

class Driver(Base):
    __tablename__ = 'drivers'
    
    driver_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    license_number = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="drivers")
    assignments = relationship("DriverAssignment", back_populates="driver")

class Service(Base):
    __tablename__ = 'services'
    
    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    monday = Column(Boolean, default=True)
    tuesday = Column(Boolean, default=True)
    wednesday = Column(Boolean, default=True)
    thursday = Column(Boolean, default=True)
    friday = Column(Boolean, default=True)
    saturday = Column(Boolean, default=True)
    sunday = Column(Boolean, default=False)
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="services")
    trips = relationship("Trip", back_populates="service")

class Trip(Base):
    __tablename__ = 'trips'
    
    trip_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    trip_headsign = Column(Text)
    direction_id = Column(Integer)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    route = relationship("Route", back_populates="trips")
    service = relationship("Service", back_populates="trips")
    block = relationship("Block", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip", order_by="StopTime.stop_sequence")

class StopTime(Base):
    __tablename__ = 'stop_times'
    
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), primary_key=True)
    stop_id = Column(UUID(as_uuid=True), ForeignKey('stops.stop_id'), primary_key=True)
    stop_sequence = Column(Integer, primary_key=True)
    arrival_time = Column(Text)  # HH:MM:SS format
    departure_time = Column(Text)  # HH:MM:SS format
    pickup_type = Column(Integer, default=0)
    drop_off_type = Column(Integer, default=0)
    
    # Relationships
    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")

class Block(Base):
    __tablename__ = 'blocks'
    
    block_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey('countries.country_id'), nullable=False)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="blocks")
    trips = relationship("Trip", back_populates="block")

class Shape(Base):
    __tablename__ = 'shapes'
    
    shape_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    geom = Column(Geometry('LINESTRING', srid=4326), nullable=False)
    
    # Relationships
    route_shapes = relationship("RouteShape", back_populates="shape")

class RouteShape(Base):
    __tablename__ = 'route_shapes'
    
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), primary_key=True)
    shape_id = Column(UUID(as_uuid=True), ForeignKey('shapes.shape_id'), primary_key=True)
    is_default = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    route = relationship("Route", back_populates="route_shapes")
    shape = relationship("Shape", back_populates="route_shapes")

class Frequency(Base):
    __tablename__ = 'frequencies'
    
    frequency_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), nullable=False)
    start_time = Column(Text, nullable=False)  # HH:MM:SS
    end_time = Column(Text, nullable=False)    # HH:MM:SS
    headway_s = Column(Integer, nullable=False)  # Seconds between trips
    
    # Relationships
    trip = relationship("Trip")

class Timetable(Base):
    __tablename__ = 'timetables'
    
    timetable_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.route_id'), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.service_id'), nullable=False)
    name = Column(Text, nullable=False)
    effective_date = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    route = relationship("Route")
    service = relationship("Service")

class VehicleAssignment(Base):
    __tablename__ = 'vehicle_assignments'
    
    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.driver_id'))
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="assignments")
    trip = relationship("Trip")
    driver = relationship("Driver")

class DriverAssignment(Base):
    __tablename__ = 'driver_assignments'
    
    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.driver_id'), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    shift_start = Column(DateTime, nullable=False)
    shift_end = Column(DateTime, nullable=False)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    driver = relationship("Driver", back_populates="assignments")
    vehicle = relationship("Vehicle")

class VehicleStatusEvent(Base):
    __tablename__ = 'vehicle_status_events'
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.vehicle_id'), nullable=False)
    status = Column(Enum(VehicleStatus), nullable=False)
    event_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="status_events")

class BlockTrip(Base):
    __tablename__ = 'block_trips'
    
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), primary_key=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.trip_id'), primary_key=True)
    layover_minutes = Column(Integer, default=0)
    
    # Relationships
    block = relationship("Block")
    trip = relationship("Trip")

class BlockBreak(Base):
    __tablename__ = 'block_breaks'
    
    break_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.block_id'), nullable=False)
    start_time = Column(Text, nullable=False)  # HH:MM:SS
    break_duration = Column(Integer, nullable=False)  # Minutes
    
    # Relationships
    block = relationship("Block")

# Legacy compatibility - keep old names for existing code
RouteStop = StopTime  # For backward compatibility