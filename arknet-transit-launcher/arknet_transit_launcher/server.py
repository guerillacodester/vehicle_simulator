"""
Simple FastAPI app factory for arknet-transit-launcher.
This is a starter stub; the real server will import service_manager and adapters.
"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import os
import sys
import asyncio

import configparser
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config.ini'))

def get_enabled_services():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')
    services = []
    for section in config.sections():
        if section == 'launcher':
            continue
        enabled = config.getboolean(section, 'enabled', fallback=False)
        if enabled:
            services.append({
                'name': section,
                'display_name': config.get(section, 'display_name', fallback=section),
                'description': config.get(section, 'description', fallback=''),
                'category': config.get(section, 'category', fallback=''),
                'icon': config.get(section, 'icon', fallback=''),
                'port': config.get(section, 'port', fallback=''),
                'health_url': config.get(section, 'health_url', fallback=''),
                'spawn_console': config.getboolean(section, 'spawn_console', fallback=False),
                'startup_wait': config.get(section, 'startup_wait', fallback='0'),
                'dependencies': config.get(section, 'dependencies', fallback=''),
            })
    return services

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
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan event handler for startup/shutdown"""
        # Startup
        asyncio.create_task(update_redis_health())
        yield
        # Shutdown (if needed)
    
    app = FastAPI(title="ArkNet Transit Launcher", lifespan=lifespan)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "arknet-transit-launcher"}
    

    @app.get("/services")
    async def get_services_status() -> List[Dict[str, Any]]:
        """Get all enabled services from config.ini"""
        return get_enabled_services()

    @app.post("/services/{service_name}/start")
    async def start_service(service_name: str) -> Dict[str, Any]:
        services = get_enabled_services()
        service = next((s for s in services if s['name'] == service_name), None)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found or not enabled")
        # Example: spawn a process or call a script here
        # For now, just simulate success
        # TODO: Implement actual start logic
        return {"message": f"Service '{service_name}' started (simulated)"}

    @app.post("/services/{service_name}/stop")
    async def stop_service(service_name: str) -> Dict[str, Any]:
        services = get_enabled_services()
        service = next((s for s in services if s['name'] == service_name), None)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found or not enabled")
        # Example: stop a process or call a script here
        # For now, just simulate success
        # TODO: Implement actual stop logic
        return {"message": f"Service '{service_name}' stopped (simulated)"}

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

# Expose FastAPI app for Uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
