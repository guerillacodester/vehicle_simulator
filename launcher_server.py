#!/usr/bin/env python3
"""
ArkNet Fleet System - Service Manager API Server
=================================================

Production-grade FastAPI service manager that provides API control for all services.
Does NOT auto-start any services - they must be started manually via API or dashboard.

This server:
- Registers all available services
- Exposes REST API on port 7000 for service control
- Provides WebSocket endpoint for real-time status events
- Waits for manual start/stop commands

Usage:
    python launcher_server.py

API Endpoints:
    GET  /services                    - List all registered services
    GET  /services/{name}/status      - Get service status
    POST /services/{name}/start       - Start a service
    POST /services/{name}/stop        - Stop a service
    GET  /services/{name}/logs        - Get service logs
    WS   /events                      - WebSocket for real-time events
"""

import sys
import uvicorn
import signal
from pathlib import Path
import io
import logging

# Force UTF-8 encoding for stdout (Windows console emoji support)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add launcher package to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging to file
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "launcher.log"),
        logging.StreamHandler()
    ]
)

from launcher.service_manager import app, manager, ManagedService, configure_cors
from launcher.config import ConfigurationManager
from launcher.socket_server import sio, socket_app
import socketio


def register_services():
    """
    Register all available services with the manager.
    Services are NOT started automatically - they wait for manual commands.
    """
    config_path = Path(__file__).parent / "config.ini"
    config_manager = ConfigurationManager(config_path)
    launcher_config = config_manager.get_launcher_config()
    service_configs = config_manager.get_service_configs()
    root_path = Path(__file__).parent
    
    print("📋 Registering available services...")
    print()
    
    # Register services from plugin configuration
    for service_name, service_config in service_configs.items():
        if not service_config.enabled:
            print(f"   ⏭️  Skipped: {service_name} (disabled)")
            continue
            
        # Determine script path and execution method based on service type
        if service_name == "strapi":
            script_path = root_path / "arknet_fleet_manager" / "arknet-fleet-api"
            is_npm = True
            npm_command = "develop"
            as_module = None
        elif service_name == "gpscentcom":
            script_path = root_path / "gpscentcom_server" / "server_main.py"
            is_npm = False
            npm_command = None
            as_module = None
        elif service_name == "geospatial":
            script_path = None
            is_npm = False
            npm_command = None
            as_module = "geospatial_service"
        elif service_name == "commuter_service":
            script_path = None
            is_npm = False
            npm_command = None
            as_module = "commuter_service"
        elif service_name == "redis":
            # Redis service - prefer a provided exe_path or fall back to redis-server on PATH
            exe_path = service_config.extra_config.get('exe_path')
            exe_cmd = service_config.extra_config.get('exe_cmd')
            if exe_path:
                script_path = Path(exe_path)
                is_npm = False
                npm_command = None
                as_module = None
            else:
                # Use raw command (no script_path) - will be translated by the manager
                script_path = None
                is_npm = False
                npm_command = None
                as_module = None
        elif service_name == "vehicle_simulator":
            script_path = None
            is_npm = False
            npm_command = None
            as_module = "arknet_transit_simulator"
        else:
            print(f"   ⚠️  Unknown service type: {service_name}")
            continue
        
        # Create the managed service
        service = ManagedService(
            name=service_name,
            port=service_config.port,
            health_url=service_config.health_url,
            script_path=script_path,
            is_npm=is_npm,
            npm_command=npm_command,
            as_module=as_module,
            dependencies=service_config.dependencies,
            spawn_console=service_config.spawn_console,
            extra_config=service_config.extra_config,
            display_name=service_config.display_name,
            description=service_config.description,
            category=service_config.category,
            icon=service_config.icon
        )
        
        # Add extra args for vehicle simulator mode
        if service_name == "vehicle_simulator":
            service.extra_args = ["--mode", service_config.extra_config.get('mode', 'depot')]
        # Redis: allow exe_path or exe_cmd via extra_config, else rely on redis-server on PATH
        if service_name == "redis":
            exe_path = service_config.extra_config.get('exe_path')
            exe_cmd = service_config.extra_config.get('exe_cmd')
            if exe_path:
                service.script_path = Path(exe_path)
            elif exe_cmd:
                service.raw_command = [exe_cmd]
            else:
                service.raw_command = ['redis-server']
            # If port configured, add as argument
            if service.port:
                # For redis-server, the port is passed as an argument
                service.extra_args = [str(service.port)]
        
        manager.register_service(service)
        print(f"   ✅ Registered: {service_name} (port {service_config.port})")
    
    print()
    print(f"✅ Total services registered: {len(manager.services)}")
    
    # Return config for use in main
    return config_manager


def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print()
    print("🛑 Shutdown signal received - stopping all services...")
    print()
    
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def stop_all():
        for service_name, service in manager.services.items():
            if service.is_running():
                print(f"   Stopping {service_name}...")
                try:
                    await manager.stop_service(service_name)
                except Exception as e:
                    print(f"   ⚠️  Error stopping {service_name}: {e}")
    
    loop.run_until_complete(stop_all())
    print()
    print("👋 All services stopped. Goodbye!")
    sys.exit(0)


def main():
    """Main entry point - starts the API server without auto-starting services."""
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    config_path = Path(__file__).parent / "config.ini"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        print()
        print("   Please ensure config.ini exists in the root directory")
        sys.exit(1)
    
    try:
        print()
        print("=" * 70)
        print("🚀 ArkNet Fleet System - Service Manager API Server")
        print("=" * 70)
        print()
        
        # Register all available services (but don't start them)
        config_manager = register_services()
        launcher_config = config_manager.get_launcher_config()
        
        # Configure CORS from config
        print()
        print("🔒 Configuring CORS...")
        print(f"   Allowed origins: {', '.join(launcher_config.cors_origins)}")
        configure_cors(launcher_config.cors_origins)
        
        print()
        print("=" * 70)
        print("🌐 Starting API Server")
        print("=" * 70)
        print()
        print(f"   Server URL:     http://localhost:{launcher_config.api_port}")
        print(f"   WebSocket:      ws://localhost:{launcher_config.api_port}/events")
        print(f"   Socket.IO:      http://localhost:{launcher_config.api_port}/socket.io")
        print(f"   API Docs:       http://localhost:{launcher_config.api_port}/docs")
        print()
        print("📡 Available Endpoints:")
        print("   GET  /services                    - List all services")
        print("   GET  /services/{name}/status      - Get service status")
        print("   POST /services/{name}/start       - Start a service")
        print("   POST /services/{name}/stop        - Stop a service")
        print("   GET  /services/{name}/logs        - Get service logs")
        print("   WS   /events                      - Real-time events")
        print()
        print("⏳ All services are STOPPED. Use the dashboard or API to start them.")
        print("   Press Ctrl+C to stop the server")
        print("=" * 70)
        print()
        
        # Start monitoring task
        import asyncio
        
        @app.on_event("startup")
        async def startup_event():
            """Start the health monitoring task."""
            asyncio.create_task(manager._monitor_health())
        
        # Create combined ASGI app with Socket.IO
        print()
        print("🔌 Integrating Socket.IO server...")
        # Socket.IO must wrap the FastAPI app, not be mounted
        # NOTE: python-socketio expects socketio_path WITHOUT leading slash ('socket.io').
        # The JS client normally sends '/socket.io'. Engine.IO strips leading slash.
        combined_app = socketio.ASGIApp(
            sio,
            other_asgi_app=app,
            socketio_path='socket.io'
        )
        
        # Run combined app with uvicorn
        uvicorn.run(
            combined_app,
            host="0.0.0.0",
            port=launcher_config.api_port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print()
        print("⏹ Shutdown via Ctrl+C...")
        shutdown_handler(None, None)
    except Exception as e:
        print()
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
