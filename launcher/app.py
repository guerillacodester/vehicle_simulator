"""
Main application entry point for the launcher.

Single Responsibility: Application initialization and execution flow.
"""

import time
from pathlib import Path

from .config import ConfigurationManager
from .factory import ServiceFactory
from .health import HealthChecker
from .console import ConsoleLauncher
from .orchestrator import StartupOrchestrator


class LauncherApplication:
    """
    Main launcher application.
    
    Coordinates all components to execute the staged startup.
    """
    
    def __init__(self, config_path: Path):
        """Initialize the launcher application."""
        # Load configuration
        self.config_manager = ConfigurationManager(config_path)
        self.launcher_config = self.config_manager.get_launcher_config()
        self.infra_config = self.config_manager.get_infrastructure_config()
        
        # Initialize dependencies
        self.health_checker = HealthChecker()
        self.console_launcher = ConsoleLauncher()
        self.orchestrator = StartupOrchestrator(self.health_checker, self.console_launcher)
        
        # Initialize service factory
        root_path = config_path.parent
        self.service_factory = ServiceFactory(root_path, self.launcher_config, self.infra_config)
    
    def run(self):
        """Execute the staged startup sequence."""
        print("=" * 70)
        print("🚀 ArkNet Fleet System - Staged Startup")
        print("=" * 70)
        print()
        
        # STAGE 1: Monitor Server
        self._stage_monitor()
        
        # STAGE 2: Strapi (Foundation)
        if not self._stage_strapi():
            self._abort("Strapi failed to start")
            return
        
        # STAGE 3: GPSCentCom
        if not self._stage_gpscentcom():
            self._abort("GPSCentCom failed to start")
            return
        
        # STAGE 4: Pre-simulator delay
        self._stage_delay()
        
        # STAGE 5: Simulators (parallel)
        self._stage_simulators()
        
        # STAGE 6: Fleet Services (parallel)
        self._stage_fleet_services()
        
        # Startup complete
        self._startup_complete()
        
        # Continuous monitoring
        self._monitor_services()
    
    def _stage_monitor(self):
        """Stage 1: Launch monitoring server."""
        print("=" * 70)
        print("STAGE 1: Monitor Server")
        print("=" * 70)
        print()
        
        monitor_service = self.service_factory.create_monitor_service()
        
        if monitor_service:
            if not self.orchestrator.launch_and_wait(monitor_service):
                print("   ⚠️  Monitor server failed (continuing anyway)")
        else:
            print(f"   ⏭️  Monitor server not implemented - skipping")
        
        print()
    
    def _stage_strapi(self) -> bool:
        """Stage 2: Launch Strapi."""
        print("=" * 70)
        print("STAGE 2: Strapi CMS (Foundation)")
        print("=" * 70)
        print()
        
        strapi_service = self.service_factory.create_strapi_service()
        
        if not strapi_service:
            print("   ❌ Strapi directory not found")
            return False
        
        success = self.orchestrator.launch_and_wait(strapi_service)
        print()
        return success
    
    def _stage_gpscentcom(self) -> bool:
        """Stage 3: Launch GPSCentCom."""
        gps_service = self.service_factory.create_gpscentcom_service()
        
        if not gps_service:
            print("   ⏭️  GPSCentCom disabled - skipping")
            print()
            return True  # Not required
        
        print("=" * 70)
        print("STAGE 3: GPSCentCom Server")
        print("=" * 70)
        print()
        
        success = self.orchestrator.launch_and_wait(gps_service)
        print()
        return success
    
    def _stage_delay(self):
        """Stage 4: Pre-simulator delay."""
        delay = self.launcher_config.simulator_delay
        
        print("=" * 70)
        print(f"STAGE 4: Pre-Simulator Delay ({delay}s)")
        print("=" * 70)
        print()
        print(f"⏳ Waiting {delay} seconds before launching simulators...")
        time.sleep(delay)
        print("   ✅ Delay complete")
        print()
    
    def _stage_simulators(self):
        """Stage 5: Launch simulators in parallel."""
        simulators = []
        
        vehicle_sim = self.service_factory.create_vehicle_simulator_service()
        if vehicle_sim:
            simulators.append(vehicle_sim)
        
        commuter_sim = self.service_factory.create_commuter_simulator_service()
        if commuter_sim:
            simulators.append(commuter_sim)
        
        if not simulators:
            return
        
        print("=" * 70)
        print("STAGE 5: Simulators (Parallel Launch)")
        print("=" * 70)
        print()
        
        self.orchestrator.launch_parallel(simulators)
        print()
    
    def _stage_fleet_services(self):
        """Stage 6: Launch fleet services."""
        services = []
        
        geospatial = self.service_factory.create_geospatial_service()
        if geospatial:
            services.append(geospatial)
        
        manifest = self.service_factory.create_manifest_service()
        if manifest:
            services.append(manifest)
        
        if not services:
            return
        
        print("=" * 70)
        print("STAGE 6: Fleet Services")
        print("=" * 70)
        print()
        
        for service in services:
            self.orchestrator.launch_and_wait(service)
            print()
    
    def _startup_complete(self):
        """Display startup complete message."""
        launched = self.orchestrator.get_launched_services()
        
        print("=" * 70)
        print(f"✅ Startup Complete - {len(launched)} services running")
        print("=" * 70)
        print()
        
        for service in launched:
            status = "🟢" if service.definition.health_url else "⚪"
            print(f"   {status} {service.definition.name}")
            if service.definition.port:
                print(f"      Port: {service.definition.port}")
        
        print()
    
    def _monitor_services(self):
        """Continuous health monitoring."""
        print("=" * 70)
        print("📊 Continuous Health Monitoring")
        print("=" * 70)
        print()
        print("   Press Ctrl+C to stop monitoring and exit")
        print()
        
        try:
            while True:
                print()
                print(f"🏥 Health Status - {time.strftime('%H:%M:%S')}")
                print("-" * 70)
                
                for service in self.orchestrator.get_launched_services():
                    service_name = service.definition.name.ljust(25)
                    
                    if service.definition.health_url:
                        is_healthy = self.health_checker.check_health(
                            service.definition.name,
                            service.definition.health_url,
                            timeout=2
                        )
                        
                        status = "🟢 HEALTHY" if is_healthy else "🔴 UNHEALTHY"
                        port_info = f"(port {service.definition.port})" if service.definition.port else ""
                        print(f"   {service_name} {status} {port_info}")
                    else:
                        print(f"   {service_name} ⚪ NO HEALTH CHECK")
                
                print("-" * 70)
                print("   Next check in 10s...")
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
    
    def _abort(self, reason: str):
        """Abort startup with error message."""
        print()
        print("=" * 70)
        print(f"🛑 STARTUP ABORTED: {reason}")
        print("=" * 70)
        print()
