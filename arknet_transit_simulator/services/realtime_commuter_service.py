#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-Time Commuter Generation Service

Integrates with the depot system to continuously generate commuters
for each route according to the commuter models, with real-time factors
and capacity management.
"""

import asyncio
import datetime
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ActiveRoute:
    """Information about an active route in the system."""
    route_id: str
    route_name: str
    stops: List[str]
    frequency_minutes: int
    is_active: bool = True
    last_generation: Optional[datetime.datetime] = None

@dataclass 
class CommuterGenerationConfig:
    """Configuration for real-time commuter generation."""
    generation_interval_seconds: int = 30  # How often to generate
    max_total_commuters: int = 50
    enable_real_time_factors: bool = True
    enable_distance_modeling: bool = True  
    enable_group_patterns: bool = True
    debug_logging: bool = False

class RealTimeCommuterService:
    """Service for real-time commuter generation integrated with depot system."""
    
    def __init__(self, config: CommuterGenerationConfig = None):
        self.config = config or CommuterGenerationConfig()
        self.active_routes: Dict[str, ActiveRoute] = {}
        self.current_commuters = 0
        self.generation_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        
        # Try to import components
        try:
            from arknet_transit_simulator.services.commuter_model_loader import CommuterModelLoader
            from arknet_transit_simulator.services.commuter_generation_engine import CommuterGenerationEngine
            
            self.model_loader = CommuterModelLoader()
            self.generation_engine = CommuterGenerationEngine(self.model_loader)
            self.generation_engine.set_commuter_limit(self.config.max_total_commuters)
            
            # Load Route 1/1A/1B model
            model_loaded = self.model_loader.load_model("route_1_1a_1b_model.json")
            if model_loaded:
                logger.info("✅ Loaded Route 1/1A/1B commuter model for real-time generation")
            else:
                logger.warning("⚠️ Could not load commuter model - using fallback generation")
            
            self.components_available = True
            
        except ImportError as e:
            logger.warning(f"⚠️ Commuter generation components not available: {e}")
            self.model_loader = None
            self.generation_engine = None
            self.components_available = False
    
    def register_route(self, route_id: str, route_name: str, stops: List[str], frequency_minutes: int) -> bool:
        """Register a route for real-time commuter generation."""
        try:
            route = ActiveRoute(
                route_id=route_id,
                route_name=route_name,
                stops=stops,
                frequency_minutes=frequency_minutes,
                is_active=True
            )
            
            self.active_routes[route_id] = route
            logger.info(f"📝 Registered route {route_id} ({route_name}) with {len(stops)} stops")
            
            # Start generation task for this route if service is running
            if self.is_running:
                self._start_route_generation(route_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register route {route_id}: {e}")
            return False
    
    def start_real_time_generation(self) -> bool:
        """Start real-time commuter generation for all registered routes."""
        if not self.components_available:
            logger.error("❌ Cannot start real-time generation - components not available")
            return False
        
        if self.is_running:
            logger.warning("⚠️ Real-time generation already running")
            return True
        
        logger.info("🚀 Starting real-time commuter generation service")
        self.is_running = True
        
        # Start generation tasks for all registered routes
        for route_id in self.active_routes:
            self._start_route_generation(route_id)
        
        logger.info(f"✅ Started real-time generation for {len(self.active_routes)} routes")
        return True
    
    def stop_real_time_generation(self) -> None:
        """Stop real-time commuter generation."""
        logger.info("🛑 Stopping real-time commuter generation service")
        self.is_running = False
        
        # Cancel all generation tasks
        for route_id, task in self.generation_tasks.items():
            if not task.done():
                task.cancel()
                logger.debug(f"📝 Cancelled generation task for route {route_id}")
        
        self.generation_tasks.clear()
        logger.info("✅ Real-time commuter generation stopped")
    
    def _start_route_generation(self, route_id: str) -> None:
        """Start generation task for a specific route."""
        if route_id in self.generation_tasks:
            # Cancel existing task
            if not self.generation_tasks[route_id].done():
                self.generation_tasks[route_id].cancel()
        
        # Create new generation task
        task = asyncio.create_task(self._route_generation_loop(route_id))
        self.generation_tasks[route_id] = task
        logger.debug(f"🔄 Started generation task for route {route_id}")
    
    async def _route_generation_loop(self, route_id: str) -> None:
        """Main generation loop for a specific route."""
        route = self.active_routes.get(route_id)
        if not route:
            return
        
        logger.info(f"🔁 Starting generation loop for route {route_id}")
        
        try:
            while self.is_running and route.is_active:
                # Generate commuters for each stop on this route
                await self._generate_route_commuters(route)
                
                # Wait for next generation cycle
                await asyncio.sleep(self.config.generation_interval_seconds)
                
        except asyncio.CancelledError:
            logger.debug(f"📝 Generation loop cancelled for route {route_id}")
        except Exception as e:
            logger.error(f"❌ Error in generation loop for route {route_id}: {e}")
    
    async def _generate_route_commuters(self, route: ActiveRoute) -> None:
        """Generate commuters for all stops on a route."""
        current_time = datetime.datetime.now()
        
        # Skip if we generated recently (based on route frequency)
        if route.last_generation:
            minutes_since_last = (current_time - route.last_generation).total_seconds() / 60
            if minutes_since_last < (route.frequency_minutes / 2):  # Generate twice per frequency
                return
        
        route.last_generation = current_time
        
        if self.config.debug_logging:
            logger.debug(f"🎯 Generating commuters for route {route.route_id} at {current_time.strftime('%H:%M:%S')}")
        
        total_generated = 0
        
        # Generate for depot (first stop) and key route stops
        priority_stops = [route.stops[0]]  # Always include depot/first stop
        
        # Add a few key stops along the route (not all to avoid overwhelming)
        if len(route.stops) > 3:
            mid_stops = route.stops[1:-1]  # Exclude first and last
            step = max(1, len(mid_stops) // 2)  # Pick every 2nd stop approximately
            priority_stops.extend(mid_stops[::step])
        
        for stop_id in priority_stops:
            try:
                # Check capacity before generating
                if self.current_commuters >= self.config.max_total_commuters:
                    if self.config.debug_logging:
                        logger.debug(f"⚖️ Skipping generation - at capacity limit ({self.current_commuters}/{self.config.max_total_commuters})")
                    break
                
                # Generate commuter batch for this stop
                batch = self.generation_engine.generate_commuter_batch(
                    model_name="route_1_1a_1b_transit_model",
                    location_id=stop_id,
                    target_time=current_time,
                    duration_minutes=self.config.generation_interval_seconds // 60 or 1
                )
                
                if batch and batch.total_boarding > 0:
                    total_generated += batch.total_boarding
                    self.current_commuters += batch.total_boarding
                    
                    if self.config.debug_logging:
                        logger.debug(f"👥 Generated {batch.total_boarding} commuters at {stop_id}")
                    
                    # Notify depot system (this would be the integration point)
                    await self._notify_depot_system(route.route_id, stop_id, batch)
                
            except Exception as e:
                logger.error(f"❌ Error generating commuters for {stop_id}: {e}")
        
        if total_generated > 0:
            logger.info(f"🚌 Route {route.route_id}: Generated {total_generated} commuters across {len(priority_stops)} stops")
    
    async def _notify_depot_system(self, route_id: str, stop_id: str, batch) -> None:
        """Notify the depot system about newly generated commuters."""
        # This is where you would integrate with your actual depot system
        # For now, just log the notification
        
        commuter_details = []
        for commuter in batch.boarding_commuters[:3]:  # Show first 3
            commuter_details.append(f"{commuter.trip_purpose} (wait: {commuter.wait_time_seconds//60}min)")
        
        logger.info(f"📞 DEPOT NOTIFICATION: Route {route_id} @ {stop_id}")
        logger.info(f"   👥 {batch.total_boarding} new commuters: {', '.join(commuter_details)}")
        
        # Here you would call your depot system's commuter update method
        # Example: depot_system.add_commuters(route_id, stop_id, batch.boarding_commuters)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current status of the real-time generation service."""
        return {
            "is_running": self.is_running,
            "components_available": self.components_available,
            "registered_routes": len(self.active_routes),
            "active_generation_tasks": len([t for t in self.generation_tasks.values() if not t.done()]),
            "current_commuters": self.current_commuters,
            "max_commuters": self.config.max_total_commuters,
            "capacity_utilization": (self.current_commuters / self.config.max_total_commuters) * 100,
            "generation_interval": self.config.generation_interval_seconds,
            "routes": {
                route_id: {
                    "name": route.route_name,
                    "stops": len(route.stops),
                    "frequency": route.frequency_minutes,
                    "is_active": route.is_active,
                    "last_generation": route.last_generation.isoformat() if route.last_generation else None
                }
                for route_id, route in self.active_routes.items()
            }
        }
    
    def update_commuter_count(self, change: int) -> None:
        """Update current commuter count (when commuters board/alight)."""
        self.current_commuters = max(0, self.current_commuters + change)
        if self.config.debug_logging:
            logger.debug(f"📊 Commuter count updated: {self.current_commuters}")


# Example usage and integration
async def example_depot_integration():
    """Example of how to integrate with depot system."""
    # Create service with configuration
    config = CommuterGenerationConfig(
        generation_interval_seconds=45,  # Generate every 45 seconds
        max_total_commuters=50,
        enable_real_time_factors=True,
        debug_logging=True
    )
    
    service = RealTimeCommuterService(config)
    
    # Register routes (this would come from your depot system)
    routes_to_register = [
        ("1", "Bridgetown - University - South Coast", 
         ["DEPOT_MAIN", "BRIDGETOWN_TERMINAL", "JUBILEE_MARKET", "UNIVERSITY_MAIN", "INDUSTRIAL_ESTATE", "SOUTH_COAST_TERMINAL"], 
         15),
        ("1A", "Bridgetown - University Express", 
         ["DEPOT_MAIN", "BRIDGETOWN_TERMINAL", "UNIVERSITY_MAIN", "INDUSTRIAL_ESTATE", "SOUTH_COAST_TERMINAL"], 
         20),
        ("1B", "Bridgetown - Mall Circuit", 
         ["DEPOT_MAIN", "BRIDGETOWN_TERMINAL", "MALL_JUNCTION", "DEPOT_MAIN"], 
         30)
    ]
    
    # Register all routes
    for route_id, name, stops, frequency in routes_to_register:
        success = service.register_route(route_id, name, stops, frequency)
        if success:
            print(f"✅ Registered {route_id}: {name}")
        else:
            print(f"❌ Failed to register {route_id}")
    
    # Start real-time generation
    if service.start_real_time_generation():
        print("🚀 Real-time commuter generation started!")
        
        # Let it run for a demo period
        try:
            for i in range(10):  # Run for 10 cycles
                await asyncio.sleep(30)  # Wait 30 seconds
                status = service.get_service_status()
                print(f"\n📊 Status Update #{i+1}:")
                print(f"   Active commuters: {status['current_commuters']}/{status['max_commuters']}")
                print(f"   Capacity: {status['capacity_utilization']:.1f}%")
                print(f"   Active tasks: {status['active_generation_tasks']}")
                
                # Simulate commuters boarding/alighting
                if i % 3 == 0:  # Every 3rd cycle, some commuters leave
                    commuters_leaving = min(5, status['current_commuters'])
                    service.update_commuter_count(-commuters_leaving)
                    print(f"   🚪 {commuters_leaving} commuters alighted")
        
        except KeyboardInterrupt:
            print("\n⏹️ Demo interrupted by user")
        
        # Stop the service
        service.stop_real_time_generation()
        print("✅ Real-time commuter generation stopped")
    
    else:
        print("❌ Failed to start real-time commuter generation")


if __name__ == "__main__":
    asyncio.run(example_depot_integration())