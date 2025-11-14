"""
ArkNet Host Server
==================

Main orchestration server for ArkNet services.
Manages simulator, GPS server, commuter service, etc.

Usage:
    # Development:
    python -m services.host_server

    # Production (systemd):
    systemctl start arknet-host

    # With custom port:
    python -m services.host_server --port 8000
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .routes import services, health, proxy


# Configure logging with UTF-8 encoding for Unicode emoji support
console_handler = logging.StreamHandler(sys.stdout)
console_handler.stream.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

handlers = [console_handler]
if config.log_file:
    file_handler = logging.FileHandler(config.log_file, encoding='utf-8')
    handlers.append(file_handler)
else:
    handlers.append(logging.NullHandler())

logging.basicConfig(
    level=config.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create FastAPI application"""
    
    app = FastAPI(
        title="ArkNet Host Server",
        description="Service orchestration and management for ArkNet transit system",
        version="0.1.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(proxy.router)
    
    @app.on_event("startup")
    async def startup():
        """Startup event"""
        logger.info("=" * 60)
        logger.info("ArkNet Host Server Starting")
        logger.info("=" * 60)
        logger.info(f"Host: {config.host}:{config.port}")
        logger.info(f"Project Root: {config.project_root}")
        logger.info(f"Simulator API Port: {config.simulator_api_port}")
        logger.info("=" * 60)
    
    @app.on_event("shutdown")
    async def shutdown():
        """Shutdown event"""
        from .simulator_manager import simulator_manager
        
        logger.info("Shutting down host server...")
        
        # Stop simulator if running
        if simulator_manager.status.value in ["running", "starting"]:
            logger.info("Stopping simulator...")
            await simulator_manager.stop()
        
        logger.info("Host server shutdown complete")
    
    return app


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArkNet Host Server")
    parser.add_argument("--host", default=config.host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=config.port, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development)")
    args = parser.parse_args()
    
    # Update config
    config.host = args.host
    config.port = args.port
    
    # Run server
    uvicorn.run(
        "services.host_server.main:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True,
        log_level=config.log_level.lower()
    )


if __name__ == "__main__":
    main()
