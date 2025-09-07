from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import uuid

Base = declarative_base()

class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String, unique=True, nullable=False)
    status = Column(String, default='available')
    route_id = Column(String, ForeignKey('routes.route_id'))

class Route(Base):
    __tablename__ = 'routes'
    
    id = Column(Integer, primary_key=True)
    route_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    shape = Column(Geometry('LINESTRING'))
    vehicles = relationship("Vehicle", backref="route")