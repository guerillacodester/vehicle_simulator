"""
Service models representing different types of services in the fleet system.

Each service type has specific launch requirements and behaviors.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from enum import Enum


class ServiceType(Enum):
    """Types of services in the system."""
    MONITOR = "monitor"
    FOUNDATION = "foundation"  # Strapi
    CORE = "core"  # GPSCentCom, Geospatial
    FLEET = "fleet"  # Manifest API
    SIMULATOR = "simulator"  # Vehicle, Commuter


@dataclass
class ServiceDefinition:
    """
    Definition of a service to be launched.
    
    Represents the 'what' and 'how' of a service.
    """
    name: str
    service_type: ServiceType
    port: Optional[int] = None
    health_url: Optional[str] = None
    
    # Launch configuration
    script_path: Optional[Path] = None
    as_module: Optional[str] = None
    is_npm: bool = False
    npm_command: Optional[str] = None
    extra_args: Optional[List[str]] = None
    
    # Timing
    startup_wait_seconds: int = 10
    
    def get_title(self) -> str:
        """Get console window title."""
        if self.port:
            return f"{self.name} - Port {self.port}"
        return self.name
