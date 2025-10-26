"""
Unit Tests for Constants Module
================================

Tests for constants.py configuration values.
"""

import pytest
from commuter_service.constants import (
    # Earth/Geographic
    EARTH_RADIUS_METERS,
    GRID_CELL_SIZE_DEGREES,
    
    # Distance Thresholds
    MAX_BOARDING_DISTANCE_METERS,
    ROUTE_PROXIMITY_THRESHOLD_METERS,
    NEARBY_QUERY_RADIUS_METERS,
    
    # Time Intervals
    EXPIRATION_CHECK_INTERVAL_SECONDS,
    POSITION_UPDATE_INTERVAL_SECONDS,
    STATISTICS_LOG_INTERVAL_SECONDS,
    
    # Vehicle Configuration
    DEFAULT_VEHICLE_CAPACITY,
    AVERAGE_VEHICLE_SPEED_KMH,
)


class TestEarthConstants:
    """Test geographic constants"""
    
    def test_earth_radius_positive(self):
        """Earth radius should be positive"""
        assert EARTH_RADIUS_METERS > 0
    
    def test_earth_radius_reasonable(self):
        """Earth radius should be approximately 6371km"""
        expected = 6_371_000  # meters
        tolerance = 10_000     # ±10km tolerance
        
        assert abs(EARTH_RADIUS_METERS - expected) < tolerance
    
    def test_grid_cell_size_positive(self):
        """Grid cell size should be positive"""
        assert GRID_CELL_SIZE_DEGREES > 0
    
    def test_grid_cell_size_reasonable(self):
        """Grid cell size should be reasonable (0.001 to 0.1 degrees)"""
        assert 0.001 <= GRID_CELL_SIZE_DEGREES <= 0.1


class TestDistanceThresholds:
    """Test distance threshold constants"""
    
    def test_boarding_distance_positive(self):
        """Max boarding distance should be positive"""
        assert MAX_BOARDING_DISTANCE_METERS > 0
    
    def test_boarding_distance_reasonable(self):
        """Max boarding distance should be reasonable (10-200m)"""
        assert 10 <= MAX_BOARDING_DISTANCE_METERS <= 200
    
    def test_route_proximity_positive(self):
        """Route proximity threshold should be positive"""
        assert ROUTE_PROXIMITY_THRESHOLD_METERS > 0
    
    def test_route_proximity_reasonable(self):
        """Route proximity should be reasonable (50-500m)"""
        assert 50 <= ROUTE_PROXIMITY_THRESHOLD_METERS <= 500
    
    def test_nearby_query_radius_positive(self):
        """Nearby query radius should be positive"""
        assert NEARBY_QUERY_RADIUS_METERS > 0
    
    def test_nearby_query_larger_than_boarding(self):
        """Nearby query radius should be larger than boarding distance"""
        assert NEARBY_QUERY_RADIUS_METERS >= MAX_BOARDING_DISTANCE_METERS


class TestTimeIntervals:
    """Test time interval constants"""
    
    def test_expiration_check_positive(self):
        """Expiration check interval should be positive"""
        assert EXPIRATION_CHECK_INTERVAL_SECONDS > 0
    
    def test_expiration_check_reasonable(self):
        """Expiration check interval should be reasonable (5-60s)"""
        assert 5 <= EXPIRATION_CHECK_INTERVAL_SECONDS <= 60
    
    def test_position_update_positive(self):
        """Position update interval should be positive"""
        assert POSITION_UPDATE_INTERVAL_SECONDS > 0
    
    def test_position_update_reasonable(self):
        """Position update interval should be reasonable (1-30s)"""
        assert 1 <= POSITION_UPDATE_INTERVAL_SECONDS <= 30
    
    def test_statistics_log_positive(self):
        """Statistics log interval should be positive"""
        assert STATISTICS_LOG_INTERVAL_SECONDS > 0


class TestVehicleConfiguration:
    """Test vehicle configuration constants"""
    
    def test_vehicle_capacity_positive(self):
        """Vehicle capacity should be positive"""
        assert DEFAULT_VEHICLE_CAPACITY > 0
    
    def test_vehicle_capacity_reasonable(self):
        """Vehicle capacity should be reasonable (10-100 passengers)"""
        assert 10 <= DEFAULT_VEHICLE_CAPACITY <= 100
    
    def test_vehicle_speed_positive(self):
        """Average vehicle speed should be positive"""
        assert AVERAGE_VEHICLE_SPEED_KMH > 0
    
    def test_vehicle_speed_reasonable(self):
        """Average vehicle speed should be reasonable (20-80 km/h)"""
        assert 20 <= AVERAGE_VEHICLE_SPEED_KMH <= 80


class TestConstantRelationships:
    """Test relationships between constants"""
    
    def test_boarding_smaller_than_route_proximity(self):
        """Boarding distance should be smaller than route proximity"""
        assert MAX_BOARDING_DISTANCE_METERS <= ROUTE_PROXIMITY_THRESHOLD_METERS
    
    def test_position_update_faster_than_expiration_check(self):
        """Position updates should happen at least as often as expiration checks"""
        assert POSITION_UPDATE_INTERVAL_SECONDS <= EXPIRATION_CHECK_INTERVAL_SECONDS


# Run with: pytest commuter_service/tests/unit/test_constants.py -v
