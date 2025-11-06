"""
Service Registry
================

Central registry for managing all services.
Tracks service lifecycle, dependencies, and startup order.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from pathlib import Path
from .base_service_manager import BaseServiceManager, ServiceStatus
from .service_managers import (
    SimulatorServiceManager,
    GPSCentComServiceManager,
    CommuterServiceManager,
    GeospatialServiceManager
)
from .config import config

logger = logging.getLogger(__name__)


class ServiceDependency(str, Enum):
    """Service dependency ordering"""
    STRAPI = "strapi"  # External, not managed
    GPSCENTCOM = "gpscentcom"
    COMMUTER = "commuter_service"
    GEOSPATIAL = "geospatial"
    SIMULATOR = "simulator"


class ServiceRegistry:
    """
    Registry of all managed services.
    
    Manages:
    - Service lifecycle (start/stop/restart)
    - Service status and health
    - Dependency ordering
    - Startup/shutdown sequences
    """
    
    # Dependency order: Strapi is external, then dependent services, then simulators
    SERVICE_STARTUP_ORDER = [
        ServiceDependency.GPSCENTCOM,
        ServiceDependency.COMMUTER,
        ServiceDependency.GEOSPATIAL,
        ServiceDependency.SIMULATOR,
    ]
    
    def __init__(self, project_root: Path):
        """Initialize service registry"""
        self.project_root = project_root
        self.services: Dict[str, BaseServiceManager] = {}
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """Initialize all service managers"""
        self.services = {
            ServiceDependency.SIMULATOR.value: SimulatorServiceManager(
                "simulator",
                self.project_root,
                process_start_timeout=30.0
            ),
            ServiceDependency.GPSCENTCOM.value: GPSCentComServiceManager(
                "gpscentcom",
                self.project_root,
                process_start_timeout=15.0
            ),
            ServiceDependency.COMMUTER.value: CommuterServiceManager(
                "commuter_service",
                self.project_root,
                process_start_timeout=15.0
            ),
            ServiceDependency.GEOSPATIAL.value: GeospatialServiceManager(
                "geospatial",
                self.project_root,
                process_start_timeout=60.0
            ),
        }
    
    async def start_service(self, service_name: str, **kwargs) -> Dict[str, Any]:
        """Start a specific service"""
        if service_name not in self.services:
            return {
                "success": False,
                "message": f"Unknown service: {service_name}",
                "status": "error"
            }
        
        manager = self.services[service_name]
        return await manager.start(**kwargs)
    
    async def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop a specific service"""
        if service_name not in self.services:
            return {
                "success": False,
                "message": f"Unknown service: {service_name}",
                "status": "error"
            }
        
        manager = self.services[service_name]
        return await manager.stop()
    
    async def restart_service(self, service_name: str, **kwargs) -> Dict[str, Any]:
        """Restart a specific service"""
        if service_name not in self.services:
            return {
                "success": False,
                "message": f"Unknown service: {service_name}",
                "status": "error"
            }
        
        manager = self.services[service_name]
        return await manager.restart(**kwargs)
    
    async def start_all_services(self, **kwargs) -> Dict[str, Any]:
        """
        Start all services in dependency order.
        
        Order: GPSCentCom → Commuter → Geospatial → Simulator
        (Strapi is external and must be running already)
        """
        results = {}
        failed = False
        
        logger.info("Starting all services in order...")
        
        for service_name in self.SERVICE_STARTUP_ORDER:
            service_key = service_name.value
            logger.info(f"Starting {service_key}...")
            
            result = await self.start_service(service_key, **kwargs)
            results[service_key] = result
            
            if not result.get("success", False):
                logger.warning(f"Failed to start {service_key}: {result.get('message')}")
                failed = True
                # Continue trying to start other services even if one fails
        
        return {
            "success": not failed,
            "message": f"Started {sum(1 for r in results.values() if r.get('success'))} of {len(results)} services",
            "status": "partial" if failed else "started",
            "services": results
        }
    
    async def stop_all_services(self) -> Dict[str, Any]:
        """
        Stop all services in reverse dependency order.
        
        Order: Simulator → Geospatial → Commuter → GPSCentCom
        """
        results = {}
        
        logger.info("Stopping all services in reverse order...")
        
        # Reverse the startup order
        for service_name in reversed(self.SERVICE_STARTUP_ORDER):
            service_key = service_name.value
            logger.info(f"Stopping {service_key}...")
            
            result = await self.stop_service(service_key)
            results[service_key] = result
        
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "message": f"Stopped {sum(1 for r in results.values() if r.get('success'))} of {len(results)} services",
            "status": "stopped",
            "services": results
        }
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        services_status = {}
        
        for service_name, manager in self.services.items():
            services_status[service_name] = manager.get_status()
        
        return {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "services": services_status,
            "summary": {
                "total": len(self.services),
                "running": sum(1 for s in services_status.values() if s["status"] == ServiceStatus.RUNNING.value),
                "stopped": sum(1 for s in services_status.values() if s["status"] == ServiceStatus.STOPPED.value),
                "error": sum(1 for s in services_status.values() if s["status"] == ServiceStatus.ERROR.value),
            }
        }
    
    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific service"""
        if service_name not in self.services:
            return None
        
        return self.services[service_name].get_status()


# Global registry instance
service_registry = ServiceRegistry(config.project_root)
