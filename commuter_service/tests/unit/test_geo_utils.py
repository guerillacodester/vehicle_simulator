"""
Unit Tests for Geographic Utilities
====================================

Tests for geo_utils.py module functions.
"""

import pytest
from math import isclose

from commuter_service.geo_utils import (
    haversine_distance,
    get_grid_cell,
    get_nearby_cells,
    is_within_distance,
    bearing_between_points,
)
from commuter_service.constants import (
    EARTH_RADIUS_METERS,
    GRID_CELL_SIZE_DEGREES,
)


class TestHaversineDistance:
    """Test haversine distance calculations"""
    
    def test_zero_distance_same_point(self):
        """Distance from point to itself should be 0"""
        lat, lon = 13.0969, -59.6145
        distance = haversine_distance(lat, lon, lat, lon)
        assert distance == 0.0
    
    def test_known_distance_bridgetown_speightstown(self):
        """Test known distance between Bridgetown and Speightstown"""
        # Bridgetown
        lat1, lon1 = 13.0969, -59.6145
        # Speightstown (approximately 22km north)
        lat2, lon2 = 13.2510, -59.6410
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 19-20km (accounting for route curvature)
        assert 18000 < distance < 21000, f"Expected ~19-20km, got {distance/1000:.2f}km"
    
    def test_short_distance_accuracy(self):
        """Test accuracy for short distances (< 1km)"""
        # Two points approximately 500m apart
        lat1, lon1 = 13.0965, -59.6086
        lat2, lon2 = 13.1010, -59.6120
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 500-600m
        assert 400 < distance < 700, f"Expected ~500m, got {distance:.2f}m"
    
    def test_symmetry(self):
        """Distance A->B should equal distance B->A"""
        lat1, lon1 = 13.0969, -59.6145
        lat2, lon2 = 13.2510, -59.6410
        
        distance_ab = haversine_distance(lat1, lon1, lat2, lon2)
        distance_ba = haversine_distance(lat2, lon2, lat1, lon1)
        
        assert isclose(distance_ab, distance_ba, rel_tol=1e-9)
    
    def test_negative_coordinates(self):
        """Test with negative coordinates (Western hemisphere)"""
        # Both points in Western hemisphere (negative longitude)
        lat1, lon1 = 13.0, -59.0
        lat2, lon2 = 14.0, -60.0
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be positive distance
        assert distance > 0


class TestGridCell:
    """Test grid cell calculations"""
    
    def test_same_point_same_cell(self):
        """Same coordinates should produce same grid cell"""
        lat, lon = 13.0969, -59.6145
        
        cell1 = get_grid_cell(lat, lon)
        cell2 = get_grid_cell(lat, lon)
        
        assert cell1 == cell2
    
    def test_nearby_points_nearby_cells(self):
        """Points 100m apart should be in same or adjacent cells"""
        # Two points very close together
        lat1, lon1 = 13.0969, -59.6145
        lat2, lon2 = 13.0970, -59.6146  # ~100m apart
        
        cell1 = get_grid_cell(lat1, lon1)
        cell2 = get_grid_cell(lat2, lon2)
        
        # Should be same cell or adjacent
        x_diff = abs(cell1[0] - cell2[0])
        y_diff = abs(cell1[1] - cell2[1])
        
        assert x_diff <= 1 and y_diff <= 1
    
    def test_grid_cell_format(self):
        """Grid cell should be tuple of two integers"""
        cell = get_grid_cell(13.0969, -59.6145)
        
        assert isinstance(cell, tuple)
        assert len(cell) == 2
        assert isinstance(cell[0], int)
        assert isinstance(cell[1], int)
    
    def test_consistent_grid_size(self):
        """Grid cells should be consistent size"""
        # Points exactly GRID_CELL_SIZE_DEGREES apart should be in different cells
        lat1, lon1 = 0.0, 0.0
        lat2, lon2 = 0.0, GRID_CELL_SIZE_DEGREES
        
        cell1 = get_grid_cell(lat1, lon1)
        cell2 = get_grid_cell(lat2, lon2)
        
        # Should be in adjacent cells (1 unit apart in x direction)
        assert cell2[0] - cell1[0] == 1
        assert cell2[1] - cell1[1] == 0


class TestNearbyCells:
    """Test nearby cells calculation"""
    
    def test_nearby_cells_count(self):
        """Should return correct number of nearby cells"""
        center_cell = (10, 20)
        
        nearby = get_nearby_cells(center_cell, radius=1)
        
        # 3x3 grid = 9 cells
        assert len(nearby) == 9
    
    def test_nearby_cells_include_center(self):
        """Nearby cells should include the center cell"""
        center_cell = (10, 20)
        
        nearby = get_nearby_cells(center_cell, radius=1)
        
        assert center_cell in nearby
    
    def test_nearby_cells_radius_0(self):
        """Radius 0 should return only center cell"""
        center_cell = (10, 20)
        
        nearby = get_nearby_cells(center_cell, radius=0)
        
        assert len(nearby) == 1
        assert nearby[0] == center_cell
    
    def test_nearby_cells_radius_2(self):
        """Radius 2 should return 5x5 grid"""
        center_cell = (10, 20)
        
        nearby = get_nearby_cells(center_cell, radius=2)
        
        # 5x5 grid = 25 cells
        assert len(nearby) == 25


class TestIsWithinDistance:
    """Test distance threshold checks"""
    
    def test_within_distance_true(self):
        """Points within threshold should return True"""
        lat1, lon1 = 13.0969, -59.6145
        lat2, lon2 = 13.0970, -59.6146  # ~100m apart
        
        result = is_within_distance(lat1, lon1, lat2, lon2, threshold_meters=200)
        
        assert result is True
    
    def test_within_distance_false(self):
        """Points outside threshold should return False"""
        lat1, lon1 = 13.0969, -59.6145
        lat2, lon2 = 13.2510, -59.6410  # ~20km apart
        
        result = is_within_distance(lat1, lon1, lat2, lon2, threshold_meters=1000)
        
        assert result is False
    
    def test_within_distance_exact_threshold(self):
        """Point exactly at threshold should return True"""
        lat1, lon1 = 13.0969, -59.6145
        lat2, lon2 = 13.0970, -59.6146
        
        # Calculate actual distance first
        actual_distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Test with exact distance as threshold
        result = is_within_distance(lat1, lon1, lat2, lon2, threshold_meters=actual_distance)
        
        assert result is True


class TestBearing:
    """Test bearing calculations"""
    
    def test_bearing_north(self):
        """Bearing to point directly north should be ~0°"""
        lat1, lon1 = 13.0, -59.0
        lat2, lon2 = 14.0, -59.0  # 1° north
        
        bearing = bearing_between_points(lat1, lon1, lat2, lon2)
        
        # Should be close to 0° (allowing for earth curvature)
        assert -10 < bearing < 10 or 350 < bearing < 360
    
    def test_bearing_east(self):
        """Bearing to point directly east should be ~90°"""
        lat1, lon1 = 13.0, -59.0
        lat2, lon2 = 13.0, -58.0  # 1° east
        
        bearing = bearing_between_points(lat1, lon1, lat2, lon2)
        
        # Should be close to 90°
        assert 80 < bearing < 100
    
    def test_bearing_south(self):
        """Bearing to point directly south should be ~180°"""
        lat1, lon1 = 14.0, -59.0
        lat2, lon2 = 13.0, -59.0  # 1° south
        
        bearing = bearing_between_points(lat1, lon1, lat2, lon2)
        
        # Should be close to 180°
        assert 170 < bearing < 190
    
    def test_bearing_west(self):
        """Bearing to point directly west should be ~270°"""
        lat1, lon1 = 13.0, -58.0
        lat2, lon2 = 13.0, -59.0  # 1° west
        
        bearing = bearing_between_points(lat1, lon1, lat2, lon2)
        
        # Should be close to 270°
        assert 260 < bearing < 280
    
    def test_bearing_range(self):
        """Bearing should always be in range [0, 360)"""
        test_points = [
            (13.0, -59.0, 14.0, -60.0),
            (13.0, -59.0, 12.0, -58.0),
            (-13.0, 59.0, 14.0, -60.0),
        ]
        
        for lat1, lon1, lat2, lon2 in test_points:
            bearing = bearing_between_points(lat1, lon1, lat2, lon2)
            assert 0 <= bearing < 360, f"Bearing {bearing} out of range [0, 360)"


# Run with: pytest commuter_service/tests/unit/test_geo_utils.py -v
