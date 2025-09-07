"""
SpatialRefSys model for fleet management (PostGIS)
"""
from sqlalchemy import Column, String, Integer
from .base import Base

class SpatialRefSys(Base):
    __tablename__ = 'spatial_ref_sys'
    
    srid = Column(Integer, primary_key=True)
    auth_name = Column(String(256))
    auth_srid = Column(Integer)
    srtext = Column(String(2048))
    proj4text = Column(String(2048))
    
    def __repr__(self):
        return f"<SpatialRefSys(srid={self.srid}, auth_name='{self.auth_name}')>"
