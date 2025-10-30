"""
ArkNet Fleet Services - Service Manager
========================================

Utility to check status and stop the Fleet Services API.

Usage:
    python manage_fleet_services.py status    # Check if running
    python manage_fleet_services.py stop      # Stop the service
"""

import sys
import subprocess
import requests
from typing import Optional


def check_service_status() -> bool:
    """Check if ArkNet Fleet Services API is running."""
    try:
        response = requests.get("http://localhost:8000/gps/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def get_service_info() -> Optional[dict]:
    """Get service information if running."""
    try:
        response = requests.get("http://localhost:8000/gps/health", timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None


def stop_service():
    """Stop the service (cross-platform)."""
    if sys.platform == "win32":
        return stop_service_windows()
    else:
        return stop_service_unix()


def stop_service_windows():
    """Stop the service on Windows by killing the process."""
    # Find Python processes running arknet_fleet_services.py
    try:
        # Use tasklist to find processes
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print("⚠️  Could not query running processes")
            return False
        
        # Parse output and check command lines
        import csv
        import io
        
        stopped_any = False
        for row in csv.reader(io.StringIO(result.stdout)):
            if len(row) >= 2:
                pid = row[1].strip('"')
                try:
                    # Kill the process
                    kill_result = subprocess.run(
                        ["taskkill", "/F", "/PID", pid],
                        capture_output=True,
                        check=False
                    )
                    if kill_result.returncode == 0:
                        print(f"✅ Stopped process {pid}")
                        stopped_any = True
                except Exception:
                    pass
        
        if not stopped_any:
            print("⚠️  No running Fleet Services process found")
        
        return stopped_any
            
    except Exception as e:
        print(f"❌ Error stopping service: {e}")
        return False


def stop_service_unix():
    """Stop the service on Unix/Linux by killing the process."""
    try:
        result = subprocess.run(
            ["pkill", "-f", "arknet_fleet_services.py"],
            capture_output=True
        )
        if result.returncode == 0:
            print("✅ Fleet Services stopped")
            return True
        else:
            print("⚠️  No running Fleet Services process found")
            return False
    except Exception as e:
        print(f"❌ Error stopping service: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_fleet_services.py status")
        print("  python manage_fleet_services.py stop")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        print("🔍 Checking ArkNet Fleet Services API status...")
        print()
        
        if check_service_status():
            info = get_service_info()
            print("✅ Fleet Services API is RUNNING")
            print()
            print("📡 Service Information:")
            if info:
                print(f"   Status: {info.get('status', 'unknown')}")
                print(f"   Store Size: {info.get('store_size', 0)} devices")
                print(f"   Uptime: {info.get('uptime_seconds', 0):.1f} seconds")
            print()
            print("🌐 Endpoints:")
            print("   • GeospatialService:  http://localhost:8000/geo/*")
            print("   • GPSCentCom HTTP:    http://localhost:8000/gps/*")
            print("   • GPSCentCom WS:      ws://localhost:8000/gps/device")
            print("   • Manifest API:       http://localhost:8000/manifest/*")
        else:
            print("❌ Fleet Services API is NOT running")
            print()
            print("To start the service:")
            print("   python start_fleet_services.py")
    
    elif command == "stop":
        print("🛑 Stopping ArkNet Fleet Services API...")
        print()
        
        if not check_service_status():
            print("⚠️  Service is not running")
            sys.exit(0)
        
        success = stop_service()
        
        if success:
            print()
            print("✅ Fleet Services API stopped successfully")
    
    else:
        print(f"❌ Unknown command: {command}")
        print()
        print("Available commands:")
        print("  status - Check if service is running")
        print("  stop   - Stop the service")
        sys.exit(1)


if __name__ == "__main__":
    main()
