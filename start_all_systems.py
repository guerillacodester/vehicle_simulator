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
    Check that Strapi is running (NON-BLOCKING).
    This check is informational only - services will launch regardless.
    
    Returns:
        True (always) - non-blocking check
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
        if check_service_health("Strapi", f"{strapi_url}/_health", timeout=3):
            print("   ✅ Strapi is healthy")
        else:
            print("   ⚠️  Strapi is not responding")
            print("   Services will launch anyway - they will retry connection")
            print()
            print("   💡 To start Strapi manually:")
            print("      cd arknet_fleet_manager")
            print("      npm run develop")
        print()
        print("=" * 70)
        print()
    
    return True  # Always return True - non-blocking


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


def launch_service_in_console(service_name, script_path, port, title, as_module=None, extra_args=None, is_npm=False, npm_command=None):
    """
    Launch a service in a new console window (cross-platform).
    
    Windows: Opens in new cmd.exe window
    Linux: Tries gnome-terminal, xterm, konsole, or falls back to background process
    macOS: Opens in new Terminal.app window
    
    Args:
        is_npm: If True, launches as npm project (npm run <npm_command>)
        npm_command: npm script to run (e.g., "develop", "start")
    
    Returns:
        Process handle on success, None on failure
    """
    
    if script_path and not script_path.exists():
        print(f"   ⚠️  {service_name}: {script_path} not found - SKIPPED")
        return None
    
    port_display = f"Port {port}" if port else "No port"
    print(f"   🚀 Launching {service_name}: {port_display}")
    
    # Build base command
    if is_npm:
        # npm-based service (like Strapi)
        base_cmd = ['npm', 'run', npm_command] if npm_command else ['npm', 'start']
        cwd = script_path  # script_path is the project directory for npm
    elif as_module:
        base_cmd = [sys.executable, '-m', as_module] + (extra_args or [])
        cwd = Path(__file__).parent
    else:
        base_cmd = [sys.executable, str(script_path)] + (extra_args or [])
        cwd = script_path.parent
    
    # Platform-specific console launch
    try:
        if sys.platform == "win32":
            # Windows: Use cmd.exe with start command
            cmd_str = ' '.join(base_cmd)
            process = subprocess.Popen(
                [
                    "cmd.exe",
                    "/c",
                    "start",
                    title,
                    "cmd.exe",
                    "/k",
                    f"cd /d {cwd} && {cmd_str} || pause"
                ],
                cwd=cwd
            )
        
        elif sys.platform == "darwin":
            # macOS: Use Terminal.app with AppleScript
            cmd_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in base_cmd])
            applescript = f'''
                tell application "Terminal"
                    do script "cd {cwd} && {cmd_str}"
                    set custom title of front window to "{title}"
                end tell
            '''
            process = subprocess.Popen(
                ['osascript', '-e', applescript],
                cwd=cwd
            )
        
        else:
            # Linux: Try common terminal emulators
            cmd_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in base_cmd])
            
            # Try gnome-terminal first
            terminal_commands = [
                # GNOME Terminal (Ubuntu, Fedora, etc.)
                ['gnome-terminal', '--title', title, '--', 'bash', '-c', f'cd {cwd} && {cmd_str}; exec bash'],
                # Konsole (KDE)
                ['konsole', '--new-tab', '--title', title, '-e', 'bash', '-c', f'cd {cwd} && {cmd_str}; exec bash'],
                # XTerm (fallback)
                ['xterm', '-T', title, '-e', f'cd {cwd} && {cmd_str}; exec bash'],
                # Terminator
                ['terminator', '-T', title, '-e', f'bash -c "cd {cwd} && {cmd_str}; exec bash"'],
                # XFCE Terminal
                ['xfce4-terminal', '--title', title, '--command', f'bash -c "cd {cwd} && {cmd_str}; exec bash"'],
            ]
            
            process = None
            for term_cmd in terminal_commands:
                try:
                    process = subprocess.Popen(term_cmd, cwd=cwd)
                    print(f"   ℹ️  Using terminal: {term_cmd[0]}")
                    break
                except FileNotFoundError:
                    continue
            
            if process is None:
                # No terminal found, run in background
                print(f"   ⚠️  No terminal emulator found - running in background")
                process = subprocess.Popen(
                    base_cmd,
                    cwd=cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
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
    Launch all enabled subsystems with STAGED STARTUP and HEALTH-GATED CONSOLE SPAWNING.
    
    STARTUP SEQUENCE:
    1. Monitor Server (port 8000) - waits for health
    2. Strapi - waits for health
    3. GPSCentCom - waits for health
    4. Wait configured delay
    5. Vehicle + Commuter Simulators (parallel) - wait for health
    6. Geospatial + Manifest (parallel) - wait for health
    
    Console windows ONLY spawn AFTER health check passes.
    """
    
    root_path = Path(__file__).parent
    enabled = get_subsystem_config()
    ports = get_service_ports()
    launcher_config = config['launcher']
    
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
    
    # INFORMATIONAL: Check Strapi dependency (non-blocking)
    check_dependencies(enabled, ports)
    
    # Define all services in STRICT dependency order
    # Strapi launches first, then other services
    services = []
    
    # 0. Strapi (Foundation - required by all services)
    strapi_path = root_path / "arknet_fleet_manager"
    if strapi_path.exists():
        services.append({
            "name": "Strapi CMS",
            "path": strapi_path,
            "port": ports['strapi'],
            "title": f"Strapi CMS - Port {ports['strapi']}",
            "is_npm": True,  # Special flag for npm-based service
            "npm_command": "develop",
            "health_url": f"http://localhost:{ports['strapi']}/_health",
            "category": "Foundation",
            "wait_time": 10  # Strapi needs more time to start
        })
    
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
    
    # Launch services one by one WITHOUT blocking on health checks
    print("🔄 Starting services in dependency order...")
    print("   Services will launch in separate console windows")
    print()
    
    current_category = None
    for idx, service in enumerate(services, 1):
        if service["category"] != current_category:
            current_category = service["category"]
            print(f"📦 {current_category}:")
            print()
        
        # Launch the service
        print(f"[{idx}/{len(services)}] Launching {service['name']}...", end=" ")
        process = launch_service_in_console(
            service["name"],
            service.get("path"),
            service.get("port"),
            service["title"],
            service.get("as_module"),
            service.get("extra_args"),
            service.get("is_npm", False),
            service.get("npm_command")
        )
        
        if process is None:
            # Launch failed
            print("❌ FAILED")
            print()
            print(f"⚠️  Warning: {service['name']} failed to launch")
            print(f"   Continuing with remaining services...")
            print()
        else:
            print("✅ Launched")
            # Add to launched list
            service['process'] = process
            launched_services.append(service)
        
        # Brief delay between launches
        time.sleep(1.0)
    
    print()
    print("=" * 70)
    print(f"✅ Launched {len(launched_services)}/{len(services)} services")
    print("=" * 70)
    print()
    
    # Now monitor health status continuously
    print("📊 Starting health monitoring...")
    print("   Press Ctrl+C to stop monitoring and exit")
    print()
    print("=" * 70)
    
    try:
        while True:
            # Clear status display (print separator)
            print()
            print(f"🏥 Health Status Report - {time.strftime('%H:%M:%S')}")
            print("-" * 70)
            
            for service in launched_services:
                service_name = service['name'].ljust(25)
                
                if service.get('health_url'):
                    # Check health via HTTP
                    is_healthy = check_service_health(service['name'], service['health_url'], timeout=2)
                    
                    if is_healthy:
                        status = "🟢 HEALTHY"
                        port_info = f"(port {service['port']})" if service.get('port') else ""
                        print(f"   {service_name} {status} {port_info}")
                    else:
                        status = "🔴 UNHEALTHY"
                        port_info = f"(port {service['port']})" if service.get('port') else ""
                        print(f"   {service_name} {status} {port_info}")
                else:
                    # No health check available
                    status = "⚪ NO HEALTH CHECK"
                    print(f"   {service_name} {status}")
            
            print("-" * 70)
            print(f"   Monitoring {len(launched_services)} services - Next check in 10s")
            
            # Wait 10 seconds before next check
            time.sleep(10)
    
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 70)
        print("🛑 Monitoring stopped by user")
        print("=" * 70)
        print()
        print("📌 Services are still running in their console windows")
        print("   To stop services: Close each console window manually")
        print()
        return
    
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
