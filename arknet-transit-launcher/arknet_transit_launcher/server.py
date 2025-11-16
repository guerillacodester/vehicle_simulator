"""
Simple FastAPI app factory for arknet-transit-launcher.
This is a starter stub; the real server will import service_manager and adapters.
"""
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import os
import sys

# Add the current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from os_adapters import systemd, windows_service


def create_app() -> FastAPI:
    app = FastAPI(title="ArkNet Transit Launcher")

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "arknet-transit-launcher"}

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

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=7000)
