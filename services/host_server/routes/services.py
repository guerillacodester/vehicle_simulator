"""
Service Management Routes
==========================

Routes for starting/stopping/managing all services.
Uses ServiceRegistry for centralized service orchestration.
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, AsyncGenerator
import asyncio
import json

from ..service_registry import service_registry


router = APIRouter(prefix="/api/services", tags=["services"])


class StartServiceRequest(BaseModel):
    """Request to start a service"""
    api_port: Optional[int] = None
    sim_time: Optional[str] = None
    enable_boarding_after: Optional[float] = None
    data_api_url: Optional[str] = None


class ServiceResponse(BaseModel):
    """Service operation response"""
    success: bool
    message: str
    status: str
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# Status Endpoints
# ============================================================================

@router.get("/status")
async def get_all_services_status():
    """Get status of all managed services"""
    return service_registry.get_all_status()


@router.get("/{service_name}/status")
async def get_service_status(service_name: str):
    """Get status of a specific service"""
    status = service_registry.get_service_status(service_name)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")
    return status


# ============================================================================
# Individual Service Control
# ============================================================================

@router.post("/{service_name}/start", response_model=ServiceResponse)
async def start_service(service_name: str, request: StartServiceRequest = StartServiceRequest()):
    """Start a specific service"""
    result = await service_registry.start_service(
        service_name,
        api_port=request.api_port,
        sim_time=request.sim_time,
        enable_boarding_after=request.enable_boarding_after,
        data_api_url=request.data_api_url
    )
    
    return ServiceResponse(
        success=result["success"],
        message=result["message"],
        status=result["status"],
        data={k: v for k, v in result.items() if k not in ["success", "message", "status"]}
    )


@router.post("/{service_name}/stop", response_model=ServiceResponse)
async def stop_service(service_name: str):
    """Stop a specific service"""
    result = await service_registry.stop_service(service_name)
    
    return ServiceResponse(
        success=result["success"],
        message=result["message"],
        status=result["status"],
        data={k: v for k, v in result.items() if k not in ["success", "message", "status"]}
    )


@router.post("/{service_name}/restart", response_model=ServiceResponse)
async def restart_service(service_name: str, request: StartServiceRequest = StartServiceRequest()):
    """Restart a specific service"""
    result = await service_registry.restart_service(
        service_name,
        api_port=request.api_port,
        sim_time=request.sim_time,
        enable_boarding_after=request.enable_boarding_after,
        data_api_url=request.data_api_url
    )
    
    return ServiceResponse(
        success=result["success"],
        message=result["message"],
        status=result["status"],
        data={k: v for k, v in result.items() if k not in ["success", "message", "status"]}
    )


# ============================================================================
# Bulk Service Control
# ============================================================================

@router.post("/start-all", response_model=ServiceResponse)
async def start_all_services(request: StartServiceRequest = StartServiceRequest()):
    """Start all services in dependency order"""
    result = await service_registry.start_all_services(
        api_port=request.api_port,
        sim_time=request.sim_time,
        enable_boarding_after=request.enable_boarding_after,
        data_api_url=request.data_api_url
    )
    
    return ServiceResponse(
        success=result["success"],
        message=result["message"],
        status=result["status"],
        data={k: v for k, v in result.items() if k not in ["success", "message", "status"]}
    )


@router.post("/stop-all", response_model=ServiceResponse)
async def stop_all_services():
    """Stop all services in reverse dependency order"""
    result = await service_registry.stop_all_services()
    
    return ServiceResponse(
        success=result["success"],
        message=result["message"],
        status=result["status"],
        data={k: v for k, v in result.items() if k not in ["success", "message", "status"]}
    )
