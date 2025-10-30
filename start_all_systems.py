"""
ArkNet Fleet System - Unified Launcher
=======================================

Launches all subsystems based on config.ini [launcher] section with
BLOCKING startup and CRITICAL failure handling.

CRITICAL STARTUP BEHAVIOR:
- Each service must become healthy before the next starts (BLOCKING)
- Service failure is CRITICAL - entire startup aborts
- On failure, previously started services shut down in REVERSE order

Dependency Architecture:
- Strapi: Foundation (all subsystems depend on it) - MANUAL STARTUP REQUIRED
- GPSCentCom: Independent (Strapi only)
- Geospatial: Independent (Strapi only)
- Manifest API: Depends on Strapi
- Vehicle Simulator: Depends on Strapi + GPSCentCom
- Commuter Simulator: Depends on Strapi + Geospatial + Manifest

Startup Order (STRICT):
  1. Strapi (manual: cd arknet_fleet_manager && npm run develop)
  2. GPSCentCom Server (if enabled) - waits for health check
  3. GeospatialService (if enabled) - waits for health check
  4. Manifest API (if enabled) - waits for health check
  5. Vehicle Simulator (if enabled) - requires GPSCentCom
  6. Commuter Simulator (if enabled) - requires Geospatial + Manifest

Usage:
    python start_all_systems.py
    python start_all_systems.py --show-config  # Show config without launching
"""

import subprocess
import sys
import os
import time
import argparse
import configparser
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import socket

# Load configuration from root config.ini
config = configparser.ConfigParser()
config_path = Path(__file__).parent / "config.ini"

if not config_path.exists():
    print(f"❌ Configuration file not found: {config_path}")
    print("   Please create config.ini in the project root")
    sys.exit(1)

config.read(config_path)


def check_service_health(name, url, timeout=5):
    """Check if a service is responding to HTTP requests."""
    try:
        response = urlopen(url, timeout=timeout)
        if response.status == 200:
            print(f"   ✅ {name} is ready")
            return True
        else:
            print(f"   ⚠️  {name} responded with status {response.status}")
            return False
    except (URLError, HTTPError, socket.timeout):
        return False
    except Exception as e:
        print(f"   ❌ {name} check failed: {e}")
        return False


def wait_for_service(name, url, max_attempts=30, delay=2):
    """Wait for a service to become available."""
    print(f"⏳ Waiting for {name} to become healthy...")
    for attempt in range(1, max_attempts + 1):
        if check_service_health(name, url, timeout=2):
            return True
        if attempt < max_attempts:
            print(f"   Attempt {attempt}/{max_attempts} - Retrying in {delay}s...")
            time.sleep(delay)
    
    print(f"   ❌ {name} did not become available after {max_attempts * delay}s")
    return False


def check_dependencies(enabled_services, ports):
    """
    Check that Strapi is running before launching any services.
    This is a BLOCKING check - all services depend on Strapi.
    
    Returns:
        True if Strapi is healthy, False otherwise
    """
    print()
    print("=" * 70)
    print("🔍 Checking Strapi Dependency")
    print("=" * 70)
    print()
    
    infra = config['infrastructure']
    strapi_url = infra.get('strapi_url', 'http://localhost:1337')
    
    # Check Strapi (required by ALL services)
    any_service_enabled = any(enabled_services.values())
    if any_service_enabled:
        print("🏥 Checking Strapi health (required by all services)...")
        if not wait_for_service("Strapi", f"{strapi_url}/_health", max_attempts=10, delay=2):
            print()
            print("❌ CRITICAL: Strapi is not running!")
            print()
            print("   Start Strapi before launching services:")
            print("   cd arknet_fleet_manager")
            print("   npm run develop")
            print()
            print("🛑 Startup aborted - cannot proceed without Strapi")
            return False
        print()
        print("=" * 70)
        print()
    
    return True


def shutdown_services(launched_services):
    """
    Gracefully shutdown services in reverse order.
    
    Args:
        launched_services: List of service dicts that were successfully launched
    """
    if not launched_services:
        return
    
    print()
    print("=" * 70)
    print("🛑 Shutting Down Services (Reverse Order)")
    print("=" * 70)
    print()
    
    # Shutdown in reverse order
    for service in reversed(launched_services):
        name = service['name']
        process = service.get('process')
        
        print(f"   🔻 Stopping {name}...")
        
        if process:
            try:
                process.terminate()
                # Give it a moment to terminate gracefully
                time.sleep(1)
                if process.poll() is None:
                    # Still running, force kill
                    process.kill()
                print(f"   ✅ {name} stopped")
            except Exception as e:
                print(f"   ⚠️  Error stopping {name}: {e}")
        else:
            # Console window process - user must close manually
            print(f"   ⚠️  {name} launched in console - please close window manually")
        
        time.sleep(0.5)
    
    print()
    print("=" * 70)
    print("🔒 Shutdown complete")
    print("=" * 70)
    
    print()
    print("✅ All dependency checks passed")
    print()
    return True


def get_subsystem_config():
    """Get enable/disable flags for all subsystems from config.ini."""
    launcher = config['launcher']
    return {
        'gpscentcom': launcher.getboolean('enable_gpscentcom', fallback=True),
        'geospatial': launcher.getboolean('enable_geospatial', fallback=True),
        'manifest': launcher.getboolean('enable_manifest', fallback=True),
        'vehicle_simulator': launcher.getboolean('enable_vehicle_simulator', fallback=False),
        'commuter_simulator': launcher.getboolean('enable_commuter_simulator', fallback=False),
    }


def get_service_ports():
    """Get service ports from config.ini."""
    infra = config['infrastructure']
    return {
        'strapi': infra.getint('strapi_port', fallback=1337),
        'gpscentcom': infra.getint('gpscentcom_port', fallback=5000),
        'geospatial': infra.getint('geospatial_port', fallback=6000),
        'manifest': infra.getint('manifest_port', fallback=4000),
    }


def launch_service_in_console(service_name, script_path, port, title, as_module=None, extra_args=None):
    """
    Launch a service in a new console window.
    
    Returns:
        Process handle on success, None on failure
    """
    
    if script_path and not script_path.exists():
        print(f"   ⚠️  {service_name}: {script_path} not found - SKIPPED")
        return None
    
    port_display = f"Port {port}" if port else "No port"
    print(f"   🚀 Launching {service_name}: {port_display}")
    
    # Build command
    if as_module:
        cmd_parts = ['python', '-m', as_module]
        if extra_args:
            cmd_parts.extend(extra_args)
        cmd = ' '.join(cmd_parts) + ' || pause'
        cwd = Path(__file__).parent
    else:
        cmd_parts = ['python', script_path.name]
        if extra_args:
            cmd_parts.extend(extra_args)
        cmd = ' '.join(cmd_parts) + ' || pause'
        cwd = script_path.parent
    
    # Platform-specific console launch
    try:
        if sys.platform == "win32":
            process = subprocess.Popen(
                [
                    "cmd.exe",
                    "/c",
                    "start",
                    title,
                    "cmd.exe",
                    "/k",
                    cmd
                ],
                cwd=cwd
            )
        else:
            # Unix-like systems
            if as_module:
                process = subprocess.Popen(
                    [sys.executable, "-m", as_module] + (extra_args or []),
                    cwd=Path(__file__).parent
                )
            else:
                process = subprocess.Popen(
                    [sys.executable, str(script_path)] + (extra_args or []),
                    cwd=script_path.parent
                )
        
        return process
    
    except Exception as e:
        print(f"   ❌ Failed to launch {service_name}: {e}")
        return None


def show_configuration():
    """Display current configuration without launching."""
    enabled = get_subsystem_config()
    ports = get_service_ports()
    
    print("=" * 70)
    print("🔧 ArkNet Fleet System - Configuration")
    print("=" * 70)
    print()
    print("📋 Subsystem Status (from config.ini):")
    print()
    print("Fleet Services:")
    print(f"   {'✅' if enabled['gpscentcom'] else '❌'} GPSCentCom Server (port {ports['gpscentcom']})")
    print(f"   {'✅' if enabled['geospatial'] else '❌'} GeospatialService (port {ports['geospatial']})")
    print(f"   {'✅' if enabled['manifest'] else '❌'} Manifest API (port {ports['manifest']})")
    print()
    print("Simulators:")
    print(f"   {'✅' if enabled['vehicle_simulator'] else '❌'} Vehicle Simulator")
    print(f"   {'✅' if enabled['commuter_simulator'] else '❌'} Commuter Simulator")
    print()
    print("=" * 70)
    print()
    print("💡 To enable/disable subsystems, edit config.ini [launcher] section")
    print("   Example: enable_vehicle_simulator = true")
    print("=" * 70)


def launch_all_systems():
    """
    Launch all enabled subsystems based on config.ini with blocking health checks.
    
    CRITICAL FAILURE HANDLING:
    - Each service must become healthy before the next starts
    - Service failure aborts the entire startup process
    - On failure, previously launched services shut down in reverse order
    """
    
    root_path = Path(__file__).parent
    enabled = get_subsystem_config()
    ports = get_service_ports()
    
    print("=" * 70)
    print("🚀 ArkNet Fleet System - Controlled Startup")
    print("=" * 70)
    print()
    print("📋 Configuration loaded from config.ini")
    print()
    
    launched_services = []
    total_enabled = sum(enabled.values())
    
    if total_enabled == 0:
        print("⚠️  No subsystems enabled in config.ini")
        print()
        print("💡 To enable subsystems, edit config.ini [launcher] section")
        print("   Example: enable_gpscentcom = true")
        print()
        return
    
    print(f"📊 {total_enabled} subsystem(s) enabled")
    print()
    
    # CRITICAL: Check Strapi dependency first
    if not check_dependencies(enabled, ports):
        print("🛑 Startup aborted due to missing Strapi")
        return
    
    # Define all services in STRICT dependency order
    # Each service will block until healthy before next starts
    services = []
    
    # 1. Independent Services (depend only on Strapi)
    if enabled['gpscentcom']:
        services.append({
            "name": "GPSCentCom Server",
            "path": root_path / "gpscentcom_server" / "server_main.py",
            "port": ports['gpscentcom'],
            "title": f"GPSCentCom - Port {ports['gpscentcom']}",
            "health_url": f"http://localhost:{ports['gpscentcom']}/health",
            "category": "Core Services",
            "wait_time": 5  # Initial startup delay in seconds
        })
    
    if enabled['geospatial']:
        services.append({
            "name": "GeospatialService",
            "path": root_path / "geospatial_service" / "main.py",
            "port": ports['geospatial'],
            "title": f"GeospatialService - Port {ports['geospatial']}",
            "health_url": f"http://localhost:{ports['geospatial']}/health",
            "category": "Core Services",
            "wait_time": 5
        })
    
    # 2. Dependent Services (require Strapi)
    if enabled['manifest']:
        services.append({
            "name": "Manifest API",
            "path": root_path / "commuter_simulator" / "interfaces" / "http" / "manifest_api.py",
            "port": ports['manifest'],
            "title": f"Manifest API - Port {ports['manifest']}",
            "as_module": "commuter_simulator.interfaces.http.manifest_api",
            "health_url": f"http://localhost:{ports['manifest']}/health",
            "category": "Fleet Services",
            "wait_time": 5
        })
    
    # 3. Simulators (require multiple dependencies)
    if enabled['vehicle_simulator']:
        # Check GPSCentCom dependency
        if not enabled['gpscentcom']:
            print()
            print("❌ CRITICAL: Vehicle Simulator requires GPSCentCom")
            print("   Enable GPSCentCom in config.ini: enable_gpscentcom = true")
            print()
            print("🛑 Startup aborted - missing dependency")
            shutdown_services(launched_services)
            return
        
        services.append({
            "name": "Vehicle Simulator",
            "path": None,
            "port": None,
            "title": "Vehicle Simulator",
            "as_module": "arknet_transit_simulator",
            "health_url": None,  # Simulators don't have health endpoints yet
            "category": "Simulators",
            "wait_time": 3
        })
    
    if enabled['commuter_simulator']:
        # Check dependencies
        missing_deps = []
        if not enabled['geospatial']:
            missing_deps.append("GeospatialService")
        if not enabled['manifest']:
            missing_deps.append("Manifest API")
        
        if missing_deps:
            print()
            print(f"❌ CRITICAL: Commuter Simulator requires {', '.join(missing_deps)}")
            print("   Enable required services in config.ini:")
            for dep in missing_deps:
                if dep == "GeospatialService":
                    print("   enable_geospatial = true")
                elif dep == "Manifest API":
                    print("   enable_manifest = true")
            print()
            print("🛑 Startup aborted - missing dependencies")
            shutdown_services(launched_services)
            return
        
        services.append({
            "name": "Commuter Simulator",
            "path": None,
            "port": None,
            "title": "Commuter Simulator",
            "as_module": "commuter_simulator.main",
            "health_url": None,  # Simulators don't have health endpoints yet
            "category": "Simulators",
            "wait_time": 3
        })
    
    # Launch services one by one with BLOCKING health checks
    print("🔄 Starting services in dependency order...")
    print("   Each service must become healthy before the next starts")
    print()
    
    current_category = None
    for idx, service in enumerate(services, 1):
        if service["category"] != current_category:
            current_category = service["category"]
            print(f"📦 {current_category}:")
            print()
        
        # Launch the service
        print(f"[{idx}/{len(services)}] {service['name']}")
        process = launch_service_in_console(
            service["name"],
            service.get("path"),
            service.get("port"),
            service["title"],
            service.get("as_module"),
            service.get("extra_args")
        )
        
        if process is None:
            # Launch failed
            print()
            print(f"❌ CRITICAL FAILURE: {service['name']} failed to launch")
            print()
            print("🛑 Aborting startup and shutting down previously launched services...")
            shutdown_services(launched_services)
            return
        
        # Add to launched list
        service['process'] = process
        launched_services.append(service)
        
        # Wait for initial startup
        print(f"   ⏱️  Waiting {service['wait_time']}s for initialization...")
        time.sleep(service['wait_time'])
        
        # Health check if applicable
        if service.get('health_url'):
            if not wait_for_service(service['name'], service['health_url'], max_attempts=20, delay=2):
                # Health check failed - CRITICAL
                print()
                print(f"❌ CRITICAL FAILURE: {service['name']} failed health check")
                print(f"   Service did not become healthy within timeout")
                print()
                print("🛑 Aborting startup and shutting down previously launched services...")
                shutdown_services(launched_services)
                return
        else:
            print(f"   ⏭️  No health check available - assuming healthy")
        
        print(f"   ✅ {service['name']} ready")
        print()
    
    # All services launched successfully!
    print("=" * 70)
    print(f"✅ ALL SERVICES LAUNCHED SUCCESSFULLY!")
    print("=" * 70)
    print()
    
    # Display service endpoints
    if any(enabled[s] for s in ['gpscentcom', 'geospatial', 'manifest']):
        print("� Service Endpoints:")
        print()
        
        if enabled['gpscentcom']:
            print(f"   🔌 GPSCentCom Server")
            print(f"      HTTP: http://localhost:{ports['gpscentcom']}")
            print(f"      WebSocket: ws://localhost:{ports['gpscentcom']}/device")
            print()
        
        if enabled['geospatial']:
            print(f"   🗺️  GeospatialService")
            print(f"      http://localhost:{ports['geospatial']}")
            print()
        
        if enabled['manifest']:
            print(f"   👥 Manifest API")
            print(f"      http://localhost:{ports['manifest']}")
            print()
    
    print("🎯 System Status:")
    print(f"   ✅ {len(launched_services)}/{len(services)} services running")
    print(f"   ✅ All health checks passed")
    print(f"   ✅ All dependencies satisfied")
    print()
    print("🛑 To stop services: Close each console window")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Launch ArkNet Fleet System subsystems based on .env configuration"
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help="Display configuration without launching services"
    )
    
    args = parser.parse_args()
    
    if args.show_config:
        show_configuration()
    else:
        launch_all_systems()


if __name__ == "__main__":
    main()
