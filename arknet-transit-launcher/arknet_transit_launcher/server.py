"""
Simple FastAPI app factory for arknet-transit-launcher.
This is a starter stub; the real server will import service_manager and adapters.
"""
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
import os
import sys
import asyncio

# Add the current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from os_adapters import systemd, windows_service
from health import RedisHealthChecker

# Import RedisServiceManager for service management
try:
    from health.redis_service_manager import RedisServiceManager
    SERVICE_MANAGER_AVAILABLE = True
except ImportError:
    SERVICE_MANAGER_AVAILABLE = False


def create_app() -> FastAPI:
    app = FastAPI(title="ArkNet Transit Launcher")
    
    # Initialize Redis health checker
    redis_url = os.getenv("REDIS_URL", None)
    redis_health_checker = RedisHealthChecker(
        redis_url=redis_url,
        latency_threshold_ms=float(os.getenv("REDIS_LATENCY_THRESHOLD_MS", "100.0"))
    )

    # Initialize Redis service manager
    redis_service_manager = RedisServiceManager() if SERVICE_MANAGER_AVAILABLE else None

    # Store Redis status
    redis_status = {}
    
    async def update_redis_health():
        """Periodically update Redis health status"""
        nonlocal redis_status
        while True:
            try:
                redis_status = await redis_health_checker.check_health()
            except Exception as e:
                redis_status = {
                    "name": "redis",
                    "state": "unhealthy",
                    "message": f"Health check error: {str(e)}"
                }
            await asyncio.sleep(float(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30.0")))
    
    @app.on_event("startup")
    async def startup_event():
        """Start background tasks on startup"""
        asyncio.create_task(update_redis_health())

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "arknet-transit-launcher"}
    
    @app.get("/services")
    async def get_services_status() -> List[Dict[str, Any]]:
        """Get status of all services including Redis"""
        services: List[Dict[str, Any]] = []

        # Add Redis status if available
        if redis_status:
            services.append(redis_status)

        # Add Redis service management status if available
        if redis_service_manager and redis_service_manager.is_service_based_management_available():
            service_info = redis_service_manager.get_status()
            service_status = {
                "name": "redis-service",
                "type": "service",
                "state": "running" if service_info.is_running else "stopped",
                "message": f"Redis service is {'running' if service_info.is_running else 'stopped'}",
                "is_enabled": service_info.is_enabled,
                "status_message": service_info.status_message
            }
            services.append(service_status)

        return services

    @app.post("/autostart/enable")
    async def enable_autostart(service: str) -> Dict[str, Any]:
        """Enable autostart for a service."""
        if os.name == 'nt':  # Windows
            # Assume task name is service name
            result = windows_service.enable_user_autostart(service, f'"{service}"')  # Placeholder command
        else:  # Linux
            result = systemd.enable(service, user=True)
        
        if not result.get('ok'):
            raise HTTPException(status_code=500, detail=f"Failed to enable autostart: {result}")
        
        return {"message": f"Autostart enabled for {service}"}

    @app.post("/autostart/disable")
    async def disable_autostart(service: str) -> Dict[str, Any]:
        """Disable autostart for a service."""
        if os.name == 'nt':  # Windows
            result = windows_service.disable_user_autostart(service)
        else:  # Linux
            result = systemd.disable(service, user=True)
        
        if not result.get('ok'):
            raise HTTPException(status_code=500, detail=f"Failed to disable autostart: {result}")
        
        return {"message": f"Autostart disabled for {service}"}

    @app.get("/autostart/status")
    async def get_autostart_status(service: str) -> Dict[str, Any]:
        """Get autostart status for a service."""
        if os.name == 'nt':  # Windows
            enabled = windows_service.is_user_autostart_enabled(service)
        else:  # Linux
            enabled = systemd.is_active(service, user=True)
        
        return {"service": service, "autostart_enabled": enabled}

    @app.post("/services/redis/start")
    async def start_redis_service() -> Dict[str, Any]:
        """Start the Redis service using service manager."""
        if not redis_service_manager:
            raise HTTPException(status_code=500, detail="Redis service manager not available")

        success = redis_service_manager.ensure_running()
        if success:
            return {"message": "Redis service started successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start Redis service")

    @app.post("/services/redis/stop")
    async def stop_redis_service() -> Dict[str, Any]:
        """Stop the Redis service using service manager."""
        if not redis_service_manager:
            raise HTTPException(status_code=500, detail="Redis service manager not available")

        success = redis_service_manager.stop_service()
        if success:
            return {"message": "Redis service stopped successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop Redis service")

    @app.post("/services/redis/enable")
    async def enable_redis_service() -> Dict[str, Any]:
        """Enable Redis service auto-start."""
        if not redis_service_manager:
            raise HTTPException(status_code=500, detail="Redis service manager not available")

        success = redis_service_manager.ensure_auto_start()
        if success:
            return {"message": "Redis service auto-start enabled"}
        else:
            raise HTTPException(status_code=500, detail="Failed to enable Redis service auto-start")

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=7000)
