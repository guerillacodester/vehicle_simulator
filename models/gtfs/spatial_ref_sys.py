"""
SpatialRefSys Model
===================
Represents spatial reference system data (PostGIS)
"""

from sqlalchemy import String
from .base import Base, Column, Integer

class SpatialRefSys(Base):
    __tablename__ = 'spatial_ref_sys'
    
    srid = Column(Integer, primary_key=True)
    auth_name = Column(String(256))
    auth_srid = Column(Integer)
    srtext = Column(String(2048))
    proj4text = Column(String(2048))
