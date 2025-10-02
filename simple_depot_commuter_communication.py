"""
Simple Direct Communication Pattern
==================================

For immediate implementation: Direct in-process communication between
depot and commuter service components.

This approach allows us to implement basic proximity boarding without
complex networking, then migrate to microservice architecture later.
"""

from typing import List, Tuple, Optional
import logging

class SimpleDepotCommuterCommunication:
    """
    Direct in-process communication between depot and commuter service.
    
    This is the simplest approach that works immediately while we can
    later migrate to Socket.IO microservice architecture.
    """
    
    def __init__(self):
        self.commuter_reservoir = None
        self.logger = logging.getLogger(__name__)
    
    def connect_reservoir(self, reservoir):
        """
        Direct connection to commuter reservoir.
        
        Args:
            reservoir: CommuterReservoir instance
        """
        self.commuter_reservoir = reservoir
        self.logger.info("✅ Direct connection established to commuter reservoir")
    
    def query_nearby_commuters(
        self, 
        vehicle_position: Tuple[float, float],
        route_id: str,
        proximity_radius_m: float = 200
    ) -> List:
        """
        Query commuters near vehicle position.
        
        Args:
            vehicle_position: (lat, lon) of vehicle
            route_id: Route identifier (e.g., "1A")
            proximity_radius_m: Search radius in meters
            
        Returns:
            List of nearby commuters
        """
        if not self.commuter_reservoir:
            self.logger.warning("❌ No commuter reservoir connected")
            return []
        
        try:
            # Direct method call - no networking required
            nearby_commuters = self.commuter_reservoir.find_commuters_near_position(
                position=vehicle_position,
                radius_m=proximity_radius_m,
                route_filter=route_id
            )
            
            self.logger.debug(f"📍 Found {len(nearby_commuters)} commuters near {vehicle_position}")
            return nearby_commuters
            
        except Exception as e:
            self.logger.error(f"❌ Error querying commuters: {e}")
            return []
    
    def notify_commuter_boarding(self, commuter_id: str, vehicle_id: str) -> bool:
        """
        Notify reservoir that commuter has boarded.
        
        Args:
            commuter_id: ID of commuter boarding
            vehicle_id: ID of vehicle
            
        Returns:
            True if notification successful
        """
        if not self.commuter_reservoir:
            return False
        
        try:
            # Direct method call to update commuter status
            success = self.commuter_reservoir.mark_commuter_boarded(commuter_id, vehicle_id)
            if success:
                self.logger.info(f"✅ Commuter {commuter_id} boarded vehicle {vehicle_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error notifying boarding: {e}")
            return False
    
    def get_communication_status(self) -> dict:
        """Get current communication status."""
        return {
            'type': 'direct_in_process',
            'reservoir_connected': self.commuter_reservoir is not None,
            'status': 'operational' if self.commuter_reservoir else 'no_reservoir'
        }


# Usage pattern for conductor:
"""
# In conductor initialization
from simple_depot_commuter_communication import SimpleDepotCommuterCommunication

class EnhancedConductor:
    def __init__(self):
        self.communication = SimpleDepotCommuterCommunication()
        
    def connect_to_commuter_service(self, reservoir):
        # Direct connection - no networking
        self.communication.connect_reservoir(reservoir)
    
    def scan_for_passengers(self, vehicle_position, route_id):
        # Direct query - immediate response
        nearby_commuters = self.communication.query_nearby_commuters(
            vehicle_position, route_id
        )
        return nearby_commuters
"""