"""
Health Check Routes
===================

Host server health and status endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

from ..config import config
from ..simulator_manager import simulator_manager


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Host server health check"""
    from .. import __version__
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=__version__,
        services={
            "simulator": simulator_manager.get_status()
        }
    )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ArkNet Host Server",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }
