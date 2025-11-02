"""
Orchestrator for managing the staged startup sequence.

Single Responsibility: Coordinate the startup stages.
Dependency Inversion: Depends on abstractions (HealthChecker, ConsoleLauncher).
"""

import time
from typing import List, Optional
from dataclasses import dataclass

from .models import ServiceDefinition
from .health import HealthChecker
from .console import ConsoleLauncher


@dataclass
class LaunchedService:
    """Represents a launched service with its process handle."""
    definition: ServiceDefinition
    process: Optional[object]


class StartupOrchestrator:
    """
    Orchestrates the staged startup sequence.
    
    STARTUP SEQUENCE:
    1. Monitor Server (port 8000)
    2. Strapi (Foundation)
    3. GPSCentCom (Core)
    4. Wait configured delay
    5. Vehicle Simulator + Commuter Service (parallel)
    6. Geospatial Service (Fleet Services)
    
    Note: Commuter Service is integrated (spawning + manifest API on port 4000)
    """
    
    def __init__(self, health_checker: HealthChecker, console_launcher: ConsoleLauncher):
        """Initialize orchestrator with dependencies."""
        self.health_checker = health_checker
        self.console_launcher = console_launcher
        self.launched_services: List[LaunchedService] = []
    
    def launch_and_wait(self, service: ServiceDefinition) -> bool:
        """
        Launch a service and wait for it to become healthy.
        
        Returns:
            True if service launched and became healthy, False otherwise
        """
        print(f"🚀 Launching {service.name}...")
        
        if service.port:
            print(f"   Port: {service.port}")
        
        # Launch the service in console
        process = self.console_launcher.launch(
            service_name=service.name,
            title=service.get_title(),
            script_path=service.script_path,
            as_module=service.as_module,
            is_npm=service.is_npm,
            npm_command=service.npm_command,
            extra_args=service.extra_args
        )
        
        if not process:
            print(f"   ❌ Failed to launch {service.name}")
            return False
        
        print(f"   ✅ Process started")
        
        # Wait for health check if applicable
        if service.health_url and service.startup_wait_seconds > 0:
            print(f"   ⏳ Waiting {service.startup_wait_seconds}s for health check...")
            
            if self.health_checker.wait_for_health(
                service.name,
                service.health_url,
                max_attempts=service.startup_wait_seconds,
                delay_seconds=1
            ):
                print(f"   ✅ {service.name} is HEALTHY")
            else:
                print(f"   ❌ {service.name} failed health check")
                return False
        
        # Add to launched services
        self.launched_services.append(LaunchedService(service, process))
        return True
    
    def launch_parallel(self, services: List[ServiceDefinition]) -> List[LaunchedService]:
        """
        Launch multiple services in parallel (no health check wait).
        
        Returns:
            List of successfully launched services
        """
        launched = []
        
        for service in services:
            print(f"🚀 Launching {service.name}...")
            
            process = self.console_launcher.launch(
                service_name=service.name,
                title=service.get_title(),
                script_path=service.script_path,
                as_module=service.as_module,
                is_npm=service.is_npm,
                npm_command=service.npm_command,
                extra_args=service.extra_args
            )
            
            if process:
                print(f"   ✅ {service.name} started")
                launched_service = LaunchedService(service, process)
                launched.append(launched_service)
                self.launched_services.append(launched_service)
            else:
                print(f"   ⚠️  {service.name} failed to start")
        
        return launched
    
    def get_launched_services(self) -> List[LaunchedService]:
        """Get list of all launched services."""
        return self.launched_services
