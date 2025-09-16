"""
AlembicVersion model for fleet management
"""
from sqlalchemy import Column, String
from .base import Base

class AlembicVersion(Base):
    __tablename__ = 'alembic_version'
    
    version_num = Column(String(32), primary_key=True)
    
    def __repr__(self):
        return f"<AlembicVersion(version_num='{self.version_num}')>"
