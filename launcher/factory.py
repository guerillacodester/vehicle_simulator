"""
Service factory for creating service definitions.

Single Responsibility: Service instantiation and configuration.
"""

from pathlib import Path
from typing import Optional
from .models import ServiceDefinition, ServiceType
from .config import LauncherConfig, InfrastructureConfig


class ServiceFactory:
    """
    Creates service definitions based on configuration.
    
    Single Responsibility: Service creation and configuration.
    """
    
    def __init__(self, root_path: Path, launcher_config: LauncherConfig, infra_config: InfrastructureConfig):
        """Initialize service factory."""
        self.root_path = root_path
        self.launcher_config = launcher_config
        self.infra_config = infra_config
    
    def create_monitor_service(self) -> Optional[ServiceDefinition]:
        """Create monitoring service definition."""
        # TODO: Implement monitoring service
        return None
    
    def create_strapi_service(self) -> Optional[ServiceDefinition]:
        """Create Strapi service definition."""
        strapi_path = self.root_path / "arknet_fleet_manager" / "arknet-fleet-api"
        
        if not strapi_path.exists():
            return None
        
        return ServiceDefinition(
            name="Strapi CMS",
            service_type=ServiceType.FOUNDATION,
            port=self.infra_config.strapi_port,
            health_url=f"{self.infra_config.strapi_url}/_health",
            script_path=strapi_path,
            is_npm=True,
            npm_command="develop",
            startup_wait_seconds=self.launcher_config.strapi_startup_wait
        )
    
    def create_gpscentcom_service(self) -> Optional[ServiceDefinition]:
        """Create GPSCentCom service definition."""
        if not self.launcher_config.enable_gpscentcom:
            return None
        
        return ServiceDefinition(
            name="GPSCentCom Server",
            service_type=ServiceType.CORE,
            port=self.infra_config.gpscentcom_port,
            health_url=f"http://localhost:{self.infra_config.gpscentcom_port}/health",
            script_path=self.root_path / "gpscentcom_server" / "server_main.py",
            startup_wait_seconds=self.launcher_config.gpscentcom_startup_wait
        )
    
    def create_geospatial_service(self) -> Optional[ServiceDefinition]:
        """Create Geospatial service definition."""
        if not self.launcher_config.enable_geospatial:
            return None
        
        return ServiceDefinition(
            name="GeospatialService",
            service_type=ServiceType.CORE,
            port=self.infra_config.geospatial_port,
            health_url=f"http://localhost:{self.infra_config.geospatial_port}/health",
            script_path=self.root_path / "geospatial_service" / "main.py",
            startup_wait_seconds=self.launcher_config.service_startup_wait
        )
    
    def create_manifest_service(self) -> Optional[ServiceDefinition]:
        """Create Manifest API service definition."""
        if not self.launcher_config.enable_manifest:
            return None
        
        return ServiceDefinition(
            name="Manifest API",
            service_type=ServiceType.FLEET,
            port=self.infra_config.manifest_port,
            health_url=f"http://localhost:{self.infra_config.manifest_port}/health",
            as_module="commuter_simulator.interfaces.http.manifest_api",
            startup_wait_seconds=self.launcher_config.service_startup_wait
        )
    
    def create_vehicle_simulator_service(self) -> Optional[ServiceDefinition]:
        """Create Vehicle Simulator service definition."""
        if not self.launcher_config.enable_vehicle_simulator:
            return None
        
        return ServiceDefinition(
            name="Vehicle Simulator",
            service_type=ServiceType.SIMULATOR,
            as_module="arknet_transit_simulator",
            startup_wait_seconds=0  # No health check for simulators
        )
    
    def create_commuter_simulator_service(self) -> Optional[ServiceDefinition]:
        """Create Commuter Simulator service definition."""
        if not self.launcher_config.enable_commuter_simulator:
            return None
        
        return ServiceDefinition(
            name="Commuter Simulator",
            service_type=ServiceType.SIMULATOR,
            as_module="commuter_simulator.main",
            startup_wait_seconds=0  # No health check for simulators
        )
