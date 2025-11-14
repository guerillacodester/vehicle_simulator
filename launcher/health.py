"""
Health check service for monitoring service availability.

Single Responsibility: Check if a service is responding to health endpoints.
"""

import time
from typing import Optional
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


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
