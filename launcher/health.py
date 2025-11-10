"""
Health check service for monitoring service availability.

Single Responsibility: Check if a service is responding to health endpoints.
"""

import time
from typing import Optional
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import socket
import shutil
import subprocess
import sys
from typing import Dict, Any


class HealthChecker:
    """
    Checks health status of services.
    
    Single Responsibility: Health verification.
    """
    
    def check_health(self, service_name: str, health_url: str, timeout: int = 5) -> bool:
        """
        Check if a service is healthy.
        
        Args:
            service_name: Name of the service (for logging)
            health_url: URL of the health endpoint
            timeout: Request timeout in seconds
            
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = urlopen(health_url, timeout=timeout)
            status_code = response.getcode()
            
            # Accept both 200 and 204 as healthy
            if status_code in [200, 204]:
                return True
            else:
                return False
                
        except (URLError, HTTPError, TimeoutError):
            return False
        except Exception:
            return False
    
    def wait_for_health(
        self,
        service_name: str,
        health_url: str,
        max_attempts: int = 10,
        delay_seconds: int = 1
    ) -> bool:
        """
        Wait for a service to become healthy.
        
        Args:
            service_name: Name of the service
            health_url: URL of the health endpoint
            max_attempts: Maximum number of check attempts
            delay_seconds: Delay between attempts
            
        Returns:
            True if service became healthy, False if timeout
        """
        for attempt in range(1, max_attempts + 1):
            if self.check_health(service_name, health_url, timeout=2):
                return True
            
            if attempt < max_attempts:
                time.sleep(delay_seconds)
        
        return False


def redis_probe(host: str = '127.0.0.1', port: int = 6379, timeout: float = 0.5) -> Dict[str, Any]:
    """
    Best-effort probe for Redis presence and availability.

    Checks performed (in order):
      1. TCP connect to host:port (listening)
      2. `shutil.which('redis-server')` (on PATH)
      3. Best-effort system service check (systemd on Linux, Get-Service on Windows)

    Returns a dict with keys: listening, on_path, system_service (or None), details (list of messages)
    """
    result: Dict[str, Any] = {
        "listening": False,
        "on_path": False,
        "system_service": None,
        "details": []
    }

    # 1) TCP probe
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            result["listening"] = True
            result["details"].append(f"TCP connect OK to {host}:{port}")
    except Exception as e:
        result["details"].append(f"TCP connect failed: {e}")

    # 2) which check
    try:
        if shutil.which("redis-server"):
            result["on_path"] = True
            result["details"].append("redis-server found on PATH")
        else:
            result["details"].append("redis-server not found on PATH")
    except Exception as e:
        result["details"].append(f"which probe error: {e}")

    # 3) system service check (best-effort)
    try:
        if sys.platform.startswith("linux"):
            # Try common service names
            for unit in ("redis-server", "redis"):
                try:
                    rc = subprocess.call(["systemctl", "is-active", "--quiet", unit])
                    if rc == 0:
                        result["system_service"] = unit
                        result["details"].append(f"systemctl reports {unit} active")
                        break
                except FileNotFoundError:
                    # systemctl not available
                    result["details"].append("systemctl not available on this host")
                    break
        elif sys.platform.startswith("win"):
            try:
                # Use PowerShell to find Redis services that are running
                ps = subprocess.run([
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-Service -Name Redis* | Where-Object {$_.Status -eq 'Running'} | Select-Object -ExpandProperty Name"
                ], capture_output=True, text=True)
                if ps.returncode == 0 and ps.stdout.strip():
                    svc = ps.stdout.strip().splitlines()[0]
                    result["system_service"] = svc
                    result["details"].append(f"Windows service running: {svc}")
                else:
                    result["details"].append("No running Windows Redis service found")
            except FileNotFoundError:
                result["details"].append("PowerShell not available to query services")
    except Exception as e:
        result["details"].append(f"system service probe error: {e}")

    return result
