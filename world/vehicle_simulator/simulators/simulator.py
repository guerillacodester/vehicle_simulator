"""
Vehicle Simulator Implementation

Core simulator class that manages fleet vehicles and their simulation lifecycle.
"""

import threading
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from world.vehicle_simulator.utils.logging_system import get_logger, LogComponent
from world.vehicle_simulator.vehicle.vahicle_object import Vehicle, VehicleState


@dataclass
class SimulationConfig:
    """Configuration for vehicle simulation."""
    tick_time: float = 2.0
    enable_gps: bool = True
    max_vehicles: int = 10
    server_url: str = "ws://localhost:8001"
    token: str = "simulator_token"


class VehicleSimulator:
    """
    Main vehicle simulator that manages multiple vehicles and their simulation.
    
    This class orchestrates the simulation of multiple vehicles, managing their
    lifecycle, GPS transmission, and coordination with the telemetry system.
    """
    
    def __init__(self, tick_time: float = 2.0, enable_gps: bool = True, 
                 vehicle_data: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the vehicle simulator.
        
        Args:
            tick_time: Time interval between simulation ticks (seconds)
            enable_gps: Whether to enable GPS transmission
            vehicle_data: List of vehicle data dictionaries from API
        """
        self.logger = get_logger(LogComponent.SIMULATOR)
        
        # Configuration
        self.config = SimulationConfig(
            tick_time=tick_time,
            enable_gps=enable_gps
        )
        
        # Vehicle management
        self.vehicles: Dict[str, Vehicle] = {}
        self.vehicle_data = vehicle_data or []
        
        # Simulation state
        self._running = False
        self._simulation_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self.logger.info(f"VehicleSimulator initialized with {len(self.vehicle_data)} vehicles")
        self.logger.debug(f"Configuration: tick_time={tick_time}s, gps_enabled={enable_gps}")
    
    def start(self) -> None:
        """Start the vehicle simulation."""
        if self._running:
            self.logger.warning("Simulator is already running")
            return
        
        self.logger.info("🚀 Starting Vehicle Simulator...")
        
        try:
            # Initialize vehicles from data
            self._initialize_vehicles()
            
            # Start simulation thread
            self._running = True
            self._stop_event.clear()
            self._simulation_thread = threading.Thread(
                target=self._simulation_loop,
                name="VehicleSimulator"
            )
            self._simulation_thread.start()
            
            self.logger.info(f"✅ Vehicle Simulator started with {len(self.vehicles)} vehicles")
            self.logger.info(f"📡 GPS transmission: {'enabled' if self.config.enable_gps else 'disabled'}")
            self.logger.info(f"⏱️ Simulation tick time: {self.config.tick_time}s")
            
        except Exception as e:
            self.logger.error(f"Failed to start simulator: {e}")
            self._running = False
            raise
    
    def stop(self) -> None:
        """Stop the vehicle simulation."""
        if not self._running:
            self.logger.info("Simulator is not running")
            return
        
        self.logger.info("🛑 Stopping Vehicle Simulator...")
        
        # Signal stop
        self._running = False
        self._stop_event.set()
        
        # Stop all vehicles
        for vehicle in self.vehicles.values():
            try:
                vehicle.turn_off()
                self.logger.debug(f"Stopped vehicle {vehicle.id}")
            except Exception as e:
                self.logger.warning(f"Error stopping vehicle {vehicle.id}: {e}")
        
        # Wait for simulation thread
        if self._simulation_thread and self._simulation_thread.is_alive():
            self._simulation_thread.join(timeout=5.0)
            if self._simulation_thread.is_alive():
                self.logger.warning("Simulation thread did not stop gracefully")
        
        self.vehicles.clear()
        self.logger.info("✅ Vehicle Simulator stopped")
    
    def _initialize_vehicles(self) -> None:
        """Initialize vehicles from the provided vehicle data."""
        if not self.vehicle_data:
            self.logger.error("No vehicle data provided - cannot initialize vehicles")
            raise ValueError("No vehicle data available for simulation")
        
        self.logger.info(f"Initializing {len(self.vehicle_data)} vehicles...")
        
        for vehicle_info in self.vehicle_data:
            try:
                vehicle_id = self._extract_vehicle_id(vehicle_info)
                
                # Create vehicle configuration
                vehicle_config = {
                    "interval": self.config.tick_time,
                    "method": "ws",  # WebSocket method
                }
                
                # Create vehicle instance
                vehicle = Vehicle(
                    vehicle_id=vehicle_id,
                    server_url=self.config.server_url,
                    token=self.config.token,
                    config=vehicle_config,
                    default_interval=self.config.tick_time
                )
                
                self.vehicles[vehicle_id] = vehicle
                self.logger.debug(f"Initialized vehicle {vehicle_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize vehicle from data {vehicle_info}: {e}")
    
    def _extract_vehicle_id(self, vehicle_info: Dict[str, Any]) -> str:
        """Extract vehicle ID from vehicle data dictionary."""
        # Try common field names for vehicle ID
        for field in ['id', 'vehicle_id', 'reg_code', 'registration_number']:
            if field in vehicle_info:
                return str(vehicle_info[field])
        
        # If no standard field found, use a fallback
        if 'name' in vehicle_info:
            return str(vehicle_info['name'])
        
        # Last resort - use string representation
        return f"vehicle_{hash(str(vehicle_info)) % 10000}"
    
    def _simulation_loop(self) -> None:
        """Main simulation loop that runs in a separate thread."""
        self.logger.debug("Simulation loop started")
        
        try:
            # Start all vehicles
            for vehicle_id, vehicle in self.vehicles.items():
                try:
                    if self.config.enable_gps:
                        vehicle.turn_on()
                        self.logger.debug(f"Started GPS transmission for vehicle {vehicle_id}")
                    else:
                        self.logger.debug(f"GPS disabled for vehicle {vehicle_id}")
                except Exception as e:
                    self.logger.error(f"Failed to start vehicle {vehicle_id}: {e}")
            
            # Main simulation loop
            tick_count = 0
            while self._running and not self._stop_event.is_set():
                tick_count += 1
                
                # Log periodic status
                if tick_count % 30 == 0:  # Every 30 ticks
                    active_vehicles = sum(1 for v in self.vehicles.values() if v.is_on())
                    self.logger.info(f"🚌 Simulation tick {tick_count}: {active_vehicles}/{len(self.vehicles)} vehicles active")
                
                # Wait for next tick
                if self._stop_event.wait(self.config.tick_time):
                    break  # Stop event was set
            
        except Exception as e:
            self.logger.error(f"Error in simulation loop: {e}")
        finally:
            self.logger.debug("Simulation loop ended")
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        active_vehicles = sum(1 for v in self.vehicles.values() if v.is_on())
        
        return {
            'running': self._running,
            'total_vehicles': len(self.vehicles),
            'active_vehicles': active_vehicles,
            'tick_time': self.config.tick_time,
            'gps_enabled': self.config.enable_gps,
            'vehicle_ids': list(self.vehicles.keys())
        }
    
    def get_vehicle_status(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific vehicle."""
        if vehicle_id not in self.vehicles:
            return None
        
        vehicle = self.vehicles[vehicle_id]
        return {
            'vehicle_id': vehicle_id,
            'active': vehicle.is_on(),
            'state': str(vehicle.state),
            'gps_enabled': self.config.enable_gps
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()