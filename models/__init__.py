from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import uuid

Base = declarative_base()

class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, unique=True, nullable=False)
    status = Column(String, default='available')
    route_id = Column(String, ForeignKey('routes.route_id'))

class Route(Base):
    __tablename__ = 'routes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    shape = Column(Geometry('LINESTRING'))
    vehicles = relationship("Vehicle", backref="route")

class Stop(Base):
    __tablename__ = 'stops'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stop_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    location = Column(Geometry('POINT'))

class Timetable(Base):
    __tablename__ = 'timetables'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, ForeignKey('routes.route_id'))
    departure_time = Column(DateTime, nullable=False)
    vehicle_id = Column(String, ForeignKey('vehicles.vehicle_id'))
    
class RouteStop(Base):
    __tablename__ = 'route_stops'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, ForeignKey('routes.route_id'))
    stop_id = Column(String, ForeignKey('stops.stop_id'))
    sequence = Column(Integer)  # Order of stops on route
    arrival_offset = Column(Integer)  # Minutes from route start