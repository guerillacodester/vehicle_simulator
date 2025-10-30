"""
ArkNet Fleet Services - Launcher
=================================

Launches all fleet services in separate console windows.
Configuration is loaded from .env file (single source of truth).

Usage:
    python start_fleet_services.py
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def get_service_config():
    """Get service configuration from environment variables with URL construction."""
    # Read ports from env (with defaults)
    gps_port = int(os.getenv('GPSCENTCOM_PORT', '5000'))
    geo_port = int(os.getenv('GEOSPATIAL_PORT', '6000'))
    manifest_port = int(os.getenv('MANIFEST_PORT', '4000'))
    
    # Construct URLs (use explicit env vars if set, otherwise build from localhost:port)
    gps_http_url = os.getenv('GPSCENTCOM_HTTP_URL', f'http://localhost:{gps_port}')
    gps_ws_url = os.getenv('GPSCENTCOM_WS_URL', f'ws://localhost:{gps_port}')
    geo_url = os.getenv('GEO_URL', f'http://localhost:{geo_port}')
    manifest_url = os.getenv('MANIFEST_URL', f'http://localhost:{manifest_port}')
    
    return {
        'gpscentcom': {
            'name': 'GPSCentCom Server',
            'port': gps_port,
            'http_url': gps_http_url,
            'ws_url': gps_ws_url
        },
        'geospatial': {
            'name': 'GeospatialService',
            'port': geo_port,
            'url': geo_url
        },
        'manifest': {
            'name': 'Manifest API',
            'port': manifest_port,
            'url': manifest_url
        }
    }


# Get service ports from environment variables (with defaults as fallback)
GPSCENTCOM_PORT = int(os.getenv('GPSCENTCOM_PORT', '5000'))
GEOSPATIAL_PORT = int(os.getenv('GEOSPATIAL_PORT', '6000'))
MANIFEST_PORT = int(os.getenv('MANIFEST_PORT', '4000'))


def launch_service_in_console(service_name, script_path, port, title, as_module=None):
    """Launch a service in a new console window."""
    
    if not script_path.exists():
        print(f"   ⚠️  {service_name}: {script_path} not found - SKIPPED")
        return False
    
    print(f"   🚀 {service_name}: Port {port}")
    
    # Platform-specific console launch
    if sys.platform == "win32":
        # Windows: Wrap Python command to keep console open on error
        if as_module:
            cmd = f'python -m {as_module} || pause'
            cwd = Path(__file__).parent
        else:
            # Don't quote the path - subprocess will handle it
            cmd = f'python {script_path.name} || pause'
            cwd = script_path.parent
            
        subprocess.Popen(
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
            subprocess.Popen(
                [sys.executable, "-m", as_module],
                cwd=Path(__file__).parent
            )
        else:
            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=script_path.parent
            )
    
    return True


def launch_all_services():
    """Launch all fleet services in separate console windows."""
    
    root_path = Path(__file__).parent
    config = get_service_config()
    
    print("=" * 70)
    print("🚀 Launching ArkNet Fleet Services")
    print("=" * 70)
    print()
    print("� Configuration loaded from .env")
    print()
    print("�📡 Starting services on separate ports...")
    print()
    
    services = [
        {
            "name": config['gpscentcom']['name'],
            "path": root_path / "gpscentcom_server" / "server_main.py",
            "port": config['gpscentcom']['port'],
            "title": f"GPSCentCom Server - Port {config['gpscentcom']['port']}",
            "as_module": None,
            "config": config['gpscentcom']
        },
        {
            "name": config['geospatial']['name'],
            "path": root_path / "geospatial_service" / "main.py",
            "port": config['geospatial']['port'],
            "title": f"GeospatialService - Port {config['geospatial']['port']}",
            "as_module": None,
            "config": config['geospatial']
        },
        {
            "name": config['manifest']['name'],
            "path": root_path / "commuter_simulator" / "interfaces" / "http" / "manifest_api.py",
            "port": config['manifest']['port'],
            "title": f"Manifest API - Port {config['manifest']['port']}",
            "as_module": "commuter_simulator.interfaces.http.manifest_api",
            "config": config['manifest']
        }
    ]
    
    launched = []
    for service in services:
        if launch_service_in_console(
            service["name"],
            service["path"],
            service["port"],
            service["title"],
            service.get("as_module")
        ):
            launched.append(service)
            time.sleep(0.5)  # Small delay between launches
    
    print()
    print("=" * 70)
    print(f"✅ Launched {len(launched)}/{len(services)} services successfully!")
    print("=" * 70)
    print()
    print("📡 Service Endpoints (from .env):")
    
    # Display GPSCentCom URLs
    gps = config['gpscentcom']
    print(f"   🔌 GPSCentCom Server")
    print(f"      HTTP: {gps['http_url']}")
    print(f"      WebSocket: {gps['ws_url']}/device")
    
    # Display Geospatial URL
    geo = config['geospatial']
    print(f"   🗺️  GeospatialService")
    print(f"      {geo['url']}")
    
    # Display Manifest URL
    manifest = config['manifest']
    print(f"   👥 Manifest API")
    print(f"      {manifest['url']}")
    
    print()
    print("� To stop services: Close each console window or press Ctrl+C in each")
    print("=" * 70)


if __name__ == "__main__":
    launch_all_services()

