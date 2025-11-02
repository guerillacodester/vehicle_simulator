#!/usr/bin/env python3
"""
ArkNet Fleet System Launcher - FastAPI Service Manager
=======================================================

Production-grade service manager with API control and automatic staged startup.

STARTUP SEQUENCE:
1. Strapi (mandatory) → wait for healthy
2. GPSCentCom → wait for healthy
3. Geospatial, Manifest (parallel) → wait for healthy
4. Vehicle Simulator, Commuter Simulator (if enabled)

Each service automatically waits for dependencies before starting.

Usage:
    python launch.py
"""

import sys
import uvicorn
import asyncio
import httpx
from pathlib import Path
from threading import Thread
from time import sleep

# Add launcher package to path
sys.path.insert(0, str(Path(__file__).parent))

from launcher.service_manager import app, manager, ManagedService
from launcher.config import ConfigurationManager


async def auto_start_services():
    """Automatically start all enabled services in the correct order."""
    await asyncio.sleep(2)  # Wait for FastAPI to be ready
    
    client = httpx.AsyncClient(timeout=30.0)
    
    print()
    print("=" * 70)
    print("🚀 AUTOMATIC STAGED STARTUP")
    print("=" * 70)
    print()
    
    # Service startup order
    startup_sequence = [
        ("strapi", "Strapi CMS (Foundation)", True),
        ("gpscentcom", "GPSCentCom Server", True),
        ("geospatial", "Geospatial Service", True),
        ("manifest", "Manifest API", True),
        ("vehicle_simulator", "Vehicle Simulator", False),  # No health check
        ("commuter_service", "Commuter Simulator", False),  # No health check
    ]
    
    for service_name, display_name, wait_healthy in startup_sequence:
        if service_name not in manager.services:
            continue
        
        print(f"📦 Starting {display_name}...")
        
        try:
            # Start the service
            response = await client.post(f"http://localhost:7000/services/{service_name}/start")
            result = response.json()
            
            print(f"   ✅ {display_name} process started (PID: {result.get('port', 'N/A')})")
            
            if wait_healthy:
                # Wait for healthy status
                max_attempts = 30
                for attempt in range(max_attempts):
                    await asyncio.sleep(1)
                    status_response = await client.get(f"http://localhost:7000/services/{service_name}/status")
                    status = status_response.json()
                    
                    if status['state'] == 'healthy':
                        print(f"   🟢 {display_name} is HEALTHY (port {status['port']})")
                        break
                    elif attempt == max_attempts - 1:
                        print(f"   ⚠️  {display_name} did not become healthy (state: {status['state']})")
                else:
                    print(f"   ⏳ Waiting for {display_name} to become healthy...")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Failed to start {display_name}: {e}")
            print()
            continue
    
    await client.aclose()
    
    print("=" * 70)
    print("✅ STARTUP COMPLETE")
    print("=" * 70)
    print()
    print("All services are running. Access the API at:")
    print("   http://localhost:7000/services (list all services)")
    print("   http://localhost:7000/services/{name}/status")
    print("   http://localhost:7000/services/{name}/logs")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 70)
    print()


def register_services():
    """Register all services with the manager."""
    config_path = Path(__file__).parent / "config.ini"
    config_manager = ConfigurationManager(config_path)
    launcher_config = config_manager.get_launcher_config()
    infra_config = config_manager.get_infrastructure_config()
    root_path = Path(__file__).parent
    
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
    
    # Register GPSCentCom
    manager.register_service(ManagedService(
        name="gpscentcom",
        port=infra_config.gpscentcom_port,
        health_url=f"http://localhost:{infra_config.gpscentcom_port}/health",
        script_path=root_path / "gpscentcom_server" / "server_main.py",
        dependencies=["strapi"],
        spawn_console=launcher_config.spawn_console_gpscentcom
    ))
    
    # Register Geospatial Service
    if launcher_config.enable_geospatial:
        manager.register_service(ManagedService(
            name="geospatial",
            port=6000,
            health_url="http://localhost:6000/health",
            script_path=root_path / "geospatial_service" / "main.py",
            dependencies=["strapi"],
            spawn_console=launcher_config.spawn_console_geospatial
        ))
    
    # Register Manifest API
    if launcher_config.enable_manifest:
        manager.register_service(ManagedService(
            name="manifest",
            port=4000,
            health_url="http://localhost:4000/health",
            as_module="commuter_service.interfaces.http.manifest_api",
            dependencies=["strapi"],
            spawn_console=launcher_config.spawn_console_manifest
        ))
    
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
    
    # Register Commuter Simulator
    if launcher_config.enable_commuter_service:
        manager.register_service(ManagedService(
            name="commuter_service",
            port=None,
            health_url=None,
            script_path=root_path / "commuter_service" / "main.py",
            dependencies=["strapi", "manifest"],
            spawn_console=launcher_config.spawn_console_commuter_service
        ))


def run_auto_startup():
    """Run the auto-startup sequence in a background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(auto_start_services())


def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print()
    print("🛑 Shutdown signal received...")
    
    # Trigger graceful shutdown via HTTP
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def trigger_shutdown():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post("http://localhost:7000/shutdown")
        except Exception as e:
            print(f"⚠️  Error during shutdown: {e}")
    
    loop.run_until_complete(trigger_shutdown())
    sys.exit(0)


def main():
    """Main entry point."""
    import signal
    
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
        print("=" * 70)
        print("🚀 ArkNet Fleet System - FastAPI Service Manager")
        print("=" * 70)
        print()
        print("📋 Registering services...")
        
        register_services()
        
        print(f"   ✅ Registered {len(manager.services)} services")
        print()
        print("🌐 Starting FastAPI service manager on http://localhost:7000")
        print()
        
        # Start auto-startup in a background thread
        startup_thread = Thread(target=run_auto_startup, daemon=True)
        startup_thread.start()
        
        # Run FastAPI with uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=7000,
            log_level="warning"  # Reduce noise
        )
    except KeyboardInterrupt:
        print()
        print("� Shutdown via Ctrl+C...")
        shutdown_handler(None, None)
    except Exception as e:
        print()
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
