"""
AlembicVersion Model
====================
Represents Alembic migration version tracking
"""

from sqlalchemy import String
from .base import Base, Column

class AlembicVersion(Base):
    __tablename__ = 'alembic_version'
    
    version_num = Column(String(32), primary_key=True)
