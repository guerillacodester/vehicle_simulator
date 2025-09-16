"""
Shared dependencies for Fleet Management API
"""
from sqlalchemy.orm import Session
from ..database import get_session

def get_db():
    """Dependency to get database session"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
