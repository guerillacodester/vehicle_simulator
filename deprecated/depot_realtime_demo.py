#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Depot Integration Example

Shows how the real-time passenger service integrates with your depot system
to continuously generate passengers for each route according to the models.
"""

import asyncio
import datetime
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DepotSystem:
    """Example depot system that integrates with real-time passenger generation."""
    
    def __init__(self):
        self.routes: Dict[str, Dict] = {}
        self.passengers_at_depot: Dict[str, List] = {}  # passengers waiting by route
        self.vehicles_in_service: Dict[str, Dict] = {}
        self.passenger_service = None
        
        # Initialize routes (would come from your route configuration)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup the routes that will have real-time passenger generation."""
        self.routes = {
            "1": {
                "name": "Bridgetown - University - South Coast",
                "stops": ["DEPOT_MAIN", "BRIDGETOWN_TERMINAL", "JUBILEE_MARKET", 
                         "UNIVERSITY_MAIN", "INDUSTRIAL_ESTATE", "SOUTH_COAST_TERMINAL"],
                "frequency_minutes": 15,
                "active": True
            },
            "1A": {
                "name": "Bridgetown - University Express", 
                "stops": ["DEPOT_MAIN", "BRIDGETOWN_TERMINAL", "UNIVERSITY_MAIN", 
                         "INDUSTRIAL_ESTATE", "SOUTH_COAST_TERMINAL"],
                "frequency_minutes": 20,
                "active": True
            },
            "1B": {
                "name": "Bridgetown - Mall Circuit",
                "stops": ["DEPOT_MAIN", "BRIDGETOWN_TERMINAL", "MALL_JUNCTION", "DEPOT_MAIN"],
                "frequency_minutes": 30,
                "active": True
            }
        }
        
        # Initialize passenger queues for each route
        for route_id in self.routes:
            self.passengers_at_depot[route_id] = []
    
    async def initialize_realtime_passengers(self):
        """Initialize the real-time passenger generation service."""
        try:
            from world.arknet_transit_simulator.services.realtime_passenger_service import (
                RealTimePassengerService, PassengerGenerationConfig
            )
            
            # Configure the service
            config = PassengerGenerationConfig(
                generation_interval_seconds=45,  # Generate every 45 seconds
                max_total_passengers=50,
                enable_real_time_factors=True,
                debug_logging=True
            )
            
            self.passenger_service = RealTimePassengerService(config)
            
            # Register all active routes
            for route_id, route_info in self.routes.items():
                if route_info["active"]:
                    success = self.passenger_service.register_route(
                        route_id=route_id,
                        route_name=route_info["name"],
                        stops=route_info["stops"],
                        frequency_minutes=route_info["frequency_minutes"]
                    )
                    
                    if success:
                        logger.info(f"✅ Registered Route {route_id} for real-time generation")
                    else:
                        logger.error(f"❌ Failed to register Route {route_id}")
            
            # Start the real-time generation
            if self.passenger_service.start_real_time_generation():
                logger.info("🚀 Real-time passenger generation started!")
                return True
            else:
                logger.error("❌ Failed to start real-time passenger generation")
                return False
                
        except ImportError as e:
            logger.warning(f"⚠️ Real-time passenger service not available: {e}")
            logger.info("📋 Using static passenger generation instead")
            return False
    
    def add_passengers_from_realtime(self, route_id: str, stop_id: str, passengers: List):
        """Called by the real-time service to add new passengers."""
        if route_id not in self.passengers_at_depot:
            self.passengers_at_depot[route_id] = []
        
        # Add passengers to the appropriate route queue
        depot_passengers = []
        route_passengers = []
        
        for passenger in passengers:
            passenger_data = {
                "id": passenger.passenger_id,
                "trip_purpose": passenger.trip_purpose,
                "wait_time": passenger.wait_time_seconds,
                "boarding_time": passenger.boarding_time_seconds,
                "location": stop_id,
                "timestamp": passenger.timestamp
            }
            
            if stop_id == "DEPOT_MAIN":
                depot_passengers.append(passenger_data)
            else:
                route_passengers.append(passenger_data)
        
        # Add to depot queue for this route
        self.passengers_at_depot[route_id].extend(depot_passengers)
        
        # Log the addition
        if depot_passengers:
            logger.info(f"👥 Added {len(depot_passengers)} passengers to Route {route_id} depot queue")
            
        if route_passengers:
            logger.info(f"🚌 Added {len(route_passengers)} passengers along Route {route_id}")
        
        return len(depot_passengers + route_passengers)
    
    def dispatch_vehicle(self, route_id: str, vehicle_id: str) -> Dict[str, Any]:
        """Dispatch a vehicle and load waiting passengers."""
        if route_id not in self.passengers_at_depot:
            return {"error": f"Route {route_id} not found"}
        
        waiting_passengers = self.passengers_at_depot[route_id]
        vehicle_capacity = 40  # Typical bus capacity
        
        # Load passengers up to vehicle capacity
        boarding_passengers = waiting_passengers[:vehicle_capacity]
        remaining_passengers = waiting_passengers[vehicle_capacity:]
        
        # Update passenger queue
        self.passengers_at_depot[route_id] = remaining_passengers
        
        # Create vehicle dispatch record
        dispatch_info = {
            "vehicle_id": vehicle_id,
            "route_id": route_id,
            "route_name": self.routes[route_id]["name"],
            "passengers_boarding": len(boarding_passengers),
            "passengers_remaining": len(remaining_passengers),
            "departure_time": datetime.datetime.now(),
            "passenger_details": boarding_passengers
        }
        
        # Track vehicle
        self.vehicles_in_service[vehicle_id] = dispatch_info
        
        # Notify passenger service about passengers who boarded
        if self.passenger_service:
            self.passenger_service.update_passenger_count(-len(boarding_passengers))
        
        logger.info(f"🚌 Dispatched Vehicle {vehicle_id} on Route {route_id}")
        logger.info(f"   👥 Boarding: {len(boarding_passengers)} passengers")
        logger.info(f"   ⏳ Remaining at depot: {len(remaining_passengers)} passengers")
        
        return dispatch_info
    
    def get_depot_status(self) -> Dict[str, Any]:
        """Get current depot status including passenger counts."""
        total_waiting = sum(len(passengers) for passengers in self.passengers_at_depot.values())
        
        route_status = {}
        for route_id, passengers in self.passengers_at_depot.items():
            route_info = self.routes[route_id]
            route_status[route_id] = {
                "name": route_info["name"],
                "passengers_waiting": len(passengers),
                "frequency_minutes": route_info["frequency_minutes"],
                "active": route_info["active"]
            }
        
        passenger_service_status = {}
        if self.passenger_service:
            passenger_service_status = self.passenger_service.get_service_status()
        
        return {
            "total_passengers_waiting": total_waiting,
            "vehicles_in_service": len(self.vehicles_in_service),
            "routes": route_status,
            "realtime_service": passenger_service_status,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    async def run_depot_operations(self, duration_minutes: int = 10):
        """Run depot operations with real-time passenger generation."""
        logger.info(f"🏢 Starting depot operations for {duration_minutes} minutes")
        logger.info("=" * 60)
        
        # Initialize real-time passengers
        realtime_available = await self.initialize_realtime_passengers()
        
        if not realtime_available:
            logger.info("📋 Running with static passenger generation")
        
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)
        
        vehicle_counter = 1
        
        try:
            while datetime.datetime.now() < end_time:
                # Show current status
                status = self.get_depot_status()
                current_time = datetime.datetime.now()
                
                logger.info(f"\n📊 DEPOT STATUS - {current_time.strftime('%H:%M:%S')}")
                logger.info(f"   Total passengers waiting: {status['total_passengers_waiting']}")
                logger.info(f"   Vehicles in service: {status['vehicles_in_service']}")
                
                for route_id, route_data in status['routes'].items():
                    if route_data['passengers_waiting'] > 0:
                        logger.info(f"   Route {route_id}: {route_data['passengers_waiting']} waiting")
                
                # Dispatch vehicles when enough passengers are waiting
                for route_id, route_data in status['routes'].items():
                    if route_data['passengers_waiting'] >= 5:  # Dispatch when 5+ passengers
                        vehicle_id = f"BUS_{vehicle_counter:03d}"
                        dispatch_info = self.dispatch_vehicle(route_id, vehicle_id)
                        vehicle_counter += 1
                        
                        if 'error' not in dispatch_info:
                            logger.info(f"🚀 Dispatched {vehicle_id} on Route {route_id}")
                
                # Wait before next status check
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("\n⏹️ Depot operations interrupted by user")
        
        # Stop real-time service
        if self.passenger_service:
            self.passenger_service.stop_real_time_generation()
            logger.info("✅ Real-time passenger service stopped")
        
        # Final status
        final_status = self.get_depot_status()
        logger.info(f"\n📋 FINAL DEPOT STATUS:")
        logger.info(f"   Total passengers still waiting: {final_status['total_passengers_waiting']}")
        logger.info(f"   Vehicles dispatched: {vehicle_counter - 1}")


async def main():
    """Run the depot system with real-time passenger generation."""
    print("🏢 DEPOT SYSTEM WITH REAL-TIME PASSENGER GENERATION")
    print("=" * 60)
    print("This demo shows how passengers are generated continuously")
    print("for each route according to the JSON models.")
    print("\nKey features:")
    print("• Passengers appear in real-time based on time of day")
    print("• Different rates for depot vs route stops")
    print("• Model-driven generation (peak/off-peak, trip purposes)")
    print("• Capacity management (max 50 total passengers)")
    print("• Vehicle dispatch when enough passengers waiting")
    print("=" * 60)
    
    depot = DepotSystem()
    
    # Run depot operations for 5 minutes (configurable)
    await depot.run_depot_operations(duration_minutes=5)
    
    print("\n✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())