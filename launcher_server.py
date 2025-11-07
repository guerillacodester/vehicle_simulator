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

# Force UTF-8 encoding for stdout (Windows console emoji support)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add launcher package to path
sys.path.insert(0, str(Path(__file__).parent))

from launcher.service_manager import app, manager, ManagedService, configure_cors
from launcher.config import ConfigurationManager


def register_services():
    """
    Register all available services with the manager.
    Services are NOT started automatically - they wait for manual commands.
    """
    config_path = Path(__file__).parent / "config.ini"
    config_manager = ConfigurationManager(config_path)
    launcher_config = config_manager.get_launcher_config()
    infra_config = config_manager.get_infrastructure_config()
    root_path = Path(__file__).parent
    
    print("📋 Registering available services...")
    print()
    
    # Register Strapi
    manager.register_service(ManagedService(
        name="strapi",
        port=infra_config.strapi_port,
        health_url=f"http://localhost:{infra_config.strapi_port}/_health",
        script_path=root_path / "arknet_fleet_manager" / "arknet-fleet-api",
        is_npm=True,
        npm_command="develop",
        dependencies=[],
        spawn_console=launcher_config.spawn_console_strapi
    ))
    print(f"   ✅ Registered: strapi (port {infra_config.strapi_port})")
    
    # Register GPSCentCom
    manager.register_service(ManagedService(
        name="gpscentcom",
        port=infra_config.gpscentcom_port,
        health_url=f"http://localhost:{infra_config.gpscentcom_port}/health",
        script_path=root_path / "gpscentcom_server" / "server_main.py",
        dependencies=["strapi"],
        spawn_console=launcher_config.spawn_console_gpscentcom
    ))
    print(f"   ✅ Registered: gpscentcom (port {infra_config.gpscentcom_port})")
    
    # Register Geospatial Service
    if launcher_config.enable_geospatial:
        manager.register_service(ManagedService(
            name="geospatial",
            port=6001,
            health_url="http://localhost:6001/health",
            as_module="geospatial_service",
            dependencies=["strapi"],
            spawn_console=launcher_config.spawn_console_geospatial
        ))
        print(f"   ✅ Registered: geospatial (port 6001)")
    
    # Register Manifest API
    manager.register_service(ManagedService(
        name="manifest",
        port=4000,
        health_url="http://localhost:4000/health",
        as_module="commuter_service",
        dependencies=["strapi", "geospatial"],
        spawn_console=launcher_config.spawn_console_commuter_service
    ))
    print(f"   ✅ Registered: manifest (port 4000)")
    
    # Register Vehicle Simulator
    if launcher_config.enable_vehicle_simulator:
        manager.register_service(ManagedService(
            name="vehicle_simulator",
            port=None,
            health_url=None,
            as_module="arknet_transit_simulator",
            extra_args=["--mode", "depot"],  # Run in depot mode (continuous operation)
            dependencies=["strapi", "gpscentcom"],
            spawn_console=launcher_config.spawn_console_vehicle_simulator
        ))
        print(f"   ✅ Registered: vehicle_simulator (no fixed port)")
    
    # Register Commuter Service
    if launcher_config.enable_commuter_service:
        manager.register_service(ManagedService(
            name="commuter_service",
            port=4000,
            health_url="http://localhost:4000/health",
            as_module="commuter_service",
            dependencies=["strapi", "geospatial"],
            spawn_console=launcher_config.spawn_console_commuter_service
        ))
        print(f"   ✅ Registered: commuter_service (port 4000)")
    
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
        print(f"   Allowed origins: {', '.join(launcher_config.launcher_cors_origins)}")
        configure_cors(launcher_config.launcher_cors_origins)
        
        print()
        print("=" * 70)
        print("🌐 Starting API Server")
        print("=" * 70)
        print()
        print(f"   Server URL:     http://localhost:{launcher_config.launcher_api_port}")
        print(f"   WebSocket:      ws://localhost:{launcher_config.launcher_api_port}/events")
        print(f"   API Docs:       http://localhost:{launcher_config.launcher_api_port}/docs")
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
        
        # Run FastAPI with uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=launcher_config.launcher_api_port,
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
