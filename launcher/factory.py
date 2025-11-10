"""
Service factory for creating service definitions.

Single Responsibility: Service instantiation and configuration.
"""

from pathlib import Path
from typing import Optional
from .models import ServiceDefinition, ServiceType
from .config import ServiceConfig


class ServiceFactory:
    """
    Creates service definitions based on service configurations.
    
    Single Responsibility: Service creation and configuration.
    """
    
    def __init__(self, root_path: Path):
        """Initialize service factory."""
        self.root_path = root_path
    
    def create_service_definition(self, service_config: ServiceConfig) -> Optional[ServiceDefinition]:
        """Create a service definition from a service configuration."""
        if not service_config.enabled:
            return None
        
        # Determine service type from category
        service_type_map = {
            'foundation': ServiceType.FOUNDATION,
            'core': ServiceType.CORE,
            'simulator': ServiceType.SIMULATOR,
            'fleet': ServiceType.FLEET
        }
        service_type = service_type_map.get(service_config.category, ServiceType.CORE)
        
        # Create service definition
        definition = ServiceDefinition(
            name=service_config.display_name,
            service_type=service_type,
            port=service_config.port,
            health_url=service_config.health_url,
            startup_wait_seconds=service_config.startup_wait
        )
        
        # Set launch configuration based on service name
        if service_config.name == 'strapi':
            definition.script_path = self.root_path / "arknet_fleet_manager" / "arknet-fleet-api"
            definition.is_npm = True
            definition.npm_command = "develop"
        elif service_config.name == 'gpscentcom':
            definition.script_path = self.root_path / "gpscentcom_server" / "server_main.py"
        elif service_config.name == 'geospatial':
            definition.as_module = "geospatial_service"
        elif service_config.name == 'vehicle_simulator':
            definition.as_module = "arknet_transit_simulator"
            definition.extra_args = ["--mode", service_config.extra_config.get('mode', 'depot')]
        elif service_config.name == 'commuter_service':
            definition.as_module = "commuter_service"
        
        return definition
