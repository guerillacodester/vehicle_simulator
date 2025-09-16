"""
Base models and database setup for fleet management
"""
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text, Time, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import uuid
from datetime import datetime

Base = declarative_base()

# Enum for vehicle status
from sqlalchemy import Enum as SQLEnum
import enum

class VehicleStatus(enum.Enum):
    available = "available"
    in_service = "in_service"
    maintenance = "maintenance"
    retired = "retired"
