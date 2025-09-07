"""
Fleet Management Configuration
=============================
Platform-agnostic configuration for distributed deployment
"""

import os
from typing import Optional

class FleetConfig:
    """Configuration for fleet management system"""
    
    # API Configuration
    GTFS_API_URL: str = os.getenv("GTFS_API_URL", "http://localhost:8000/api/v1")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    
    # File Upload Configuration  
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
    
    # Deployment Configuration
    DEPLOYMENT_ENV: str = os.getenv("DEPLOYMENT_ENV", "development")  # development, staging, production
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rock S0 specific settings
    IS_ROCK_S0: bool = os.getenv("IS_ROCK_S0", "false").lower() == "true"
    
    @classmethod
    def get_api_url(cls) -> str:
        """Get API URL based on deployment environment"""
        if cls.DEPLOYMENT_ENV == "production":
            # In production, API might be on a different server
            return cls.GTFS_API_URL
        elif cls.DEPLOYMENT_ENV == "staging":
            # Staging environment
            return cls.GTFS_API_URL
        else:
            # Development - local API
            return "http://localhost:8000/api/v1"
    
    @classmethod
    def is_remote_deployment(cls) -> bool:
        """Check if this is a remote deployment (like Rock S0)"""
        return cls.IS_ROCK_S0 or cls.DEPLOYMENT_ENV != "development"

# Environment-specific configurations
ROCK_S0_CONFIG = {
    "GTFS_API_URL": "http://backend-server:8000/api/v1",  # Backend on different server
    "UPLOAD_DIR": "/var/lib/fleet-management/uploads",
    "LOG_LEVEL": "WARNING",
    "IS_ROCK_S0": True
}

PRODUCTION_CONFIG = {
    "GTFS_API_URL": "https://api.arknettransit.com/api/v1",  # Production API server
    "UPLOAD_DIR": "/var/lib/fleet-management/uploads", 
    "LOG_LEVEL": "WARNING",
    "DEPLOYMENT_ENV": "production"
}
