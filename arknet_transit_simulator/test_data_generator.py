"""
Test data generator for simulator when no API is available.
Creates mock vehicles, drivers, and routes for autonomous testing.
"""
import logging
from typing import List, Dict, Any, Optional
from arknet_transit_simulator.core.interfaces import VehicleAssignment, DriverAssignment, RouteInfo

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Generate test data for simulator when API is unavailable."""
    
    @staticmethod
    def create_test_vehicles() -> List[VehicleAssignment]:
        """Create test vehicle assignments."""
        return [
            VehicleAssignment(
                vehicle_id="test-vehicle-1",
                vehicle_reg_code="ZR102",
                route_id="R1",
                vehicle_status="available"
            ),
            VehicleAssignment(
                vehicle_id="test-vehicle-2",
                vehicle_reg_code="ZR103",
                route_id="R1",
                vehicle_status="available"
            ),
        ]
    
    @staticmethod
    def create_test_drivers() -> List[DriverAssignment]:
        """Create test driver assignments."""
        return [
            DriverAssignment(
                driver_id="driver-1",
                driver_name="Alice Johnson",
                assigned_route_id="R1"
            ),
            DriverAssignment(
                driver_id="driver-2",
                driver_name="Bob Smith",
                assigned_route_id="R1"
            ),
        ]
    
    @staticmethod
    def create_test_route() -> Optional[RouteInfo]:
        """Create a test route with GPS coordinates."""
        # Simple rectangular loop: ~2km route
        coordinates = [
            [-74.0050, 40.7128],  # Start: Times Square area
            [-74.0040, 40.7140],
            [-74.0030, 40.7140],
            [-74.0030, 40.7120],
            [-74.0050, 40.7120],
            [-74.0050, 40.7128],  # Back to start
        ]
        
        route_info = RouteInfo(
            route_id="R1",
            route_code="R1",
            route_name="Test Route 1",
            geometry={
                "type": "LineString",
                "coordinates": coordinates
            },
            coordinate_count=len(coordinates)
        )
        return route_info
