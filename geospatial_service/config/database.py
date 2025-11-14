"""
Database Configuration for Geospatial Service
Direct PostgreSQL + PostGIS connection (read-only)
"""

import os
from dotenv import load_dotenv
import asyncpg
from typing import Optional

load_dotenv()

class DatabaseConfig:
    """PostgreSQL connection configuration"""
    
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "arknettransit")
        self.user = os.getenv("DB_USER", "david")
        self.password = os.getenv("DB_PASSWORD", "")
        
    def get_dsn(self) -> str:
        """Get connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get async database connection"""
        return await asyncpg.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
    
    async def get_pool(self, min_size: int = 5, max_size: int = 20) -> asyncpg.Pool:
        """Get connection pool for production use"""
        return await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            min_size=min_size,
            max_size=max_size
        )


# Global instance
db_config = DatabaseConfig()
