"""
API Proxy Routes
================

Proxy API calls to the simulator subprocess.
Allows fleet console to use single endpoint (host_server)
instead of connecting directly to simulator.
"""

import httpx
from fastapi import APIRouter, Request, Response, HTTPException
from typing import Any

from ..config import config
from ..simulator_manager import simulator_manager, ServiceStatus


router = APIRouter(prefix="/api", tags=["proxy"])


async def get_http_client():
    """Get HTTP client for proxying"""
    return httpx.AsyncClient(timeout=30.0)


@router.api_route(
    "/vehicles",
    methods=["GET"],
    summary="List all vehicles (proxied)"
)
@router.api_route(
    "/vehicles/{vehicle_id}",
    methods=["GET"],
    summary="Get vehicle details (proxied)"
)
@router.api_route(
    "/vehicles/{vehicle_id}/start-engine",
    methods=["POST"],
    summary="Start vehicle engine (proxied)"
)
@router.api_route(
    "/vehicles/{vehicle_id}/stop-engine",
    methods=["POST"],
    summary="Stop vehicle engine (proxied)"
)
@router.api_route(
    "/vehicles/{vehicle_id}/enable-boarding",
    methods=["POST"],
    summary="Enable boarding (proxied)"
)
@router.api_route(
    "/vehicles/{vehicle_id}/disable-boarding",
    methods=["POST"],
    summary="Disable boarding (proxied)"
)
@router.api_route(
    "/vehicles/{vehicle_id}/trigger-boarding",
    methods=["POST"],
    summary="Trigger boarding (proxied)"
)
@router.api_route(
    "/conductors",
    methods=["GET"],
    summary="List conductors (proxied)"
)
@router.api_route(
    "/conductors/{vehicle_id}",
    methods=["GET"],
    summary="Get conductor details (proxied)"
)
@router.api_route(
    "/sim/status",
    methods=["GET"],
    summary="Get simulator status (proxied)"
)
@router.api_route(
    "/sim/pause",
    methods=["POST"],
    summary="Pause simulator (proxied)"
)
@router.api_route(
    "/sim/resume",
    methods=["POST"],
    summary="Resume simulator (proxied)"
)
@router.api_route(
    "/sim/stop",
    methods=["POST"],
    summary="Stop simulator (proxied)"
)
@router.api_route(
    "/sim/set-time",
    methods=["POST"],
    summary="Set sim time (proxied)"
)
async def proxy_to_simulator(request: Request):
    """
    Proxy all requests to simulator API
    
    This allows fleet console to connect to host_server instead of
    directly to simulator subprocess.
    """
    # Check if simulator is running
    if simulator_manager.status != ServiceStatus.RUNNING:
        raise HTTPException(
            status_code=503,
            detail=f"Simulator is not running (status: {simulator_manager.status.value})"
        )
    
    # Build target URL
    path = request.url.path
    query = str(request.url.query) if request.url.query else ""
    target_url = f"http://localhost:{config.simulator_api_port}{path}"
    if query:
        target_url += f"?{query}"
    
    # Get request body if present
    body = await request.body()
    
    # Proxy the request
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body
            )
            
            # Return proxied response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to simulator API (service may be starting)"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Simulator API timeout"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Proxy error: {str(e)}"
            )
