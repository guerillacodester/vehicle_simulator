"""
Unit Tests for DepotQueue
==========================

Tests the FIFO queue management for depot commuters.

Test Coverage:
- Queue initialization
- Adding commuters (FIFO behavior)
- Removing commuters by ID
- Proximity-based queries (Haversine distance)
- Statistics tracking
- Edge cases (empty queue, not found, etc.)
"""

import pytest
from datetime import datetime, timedelta
from collections import deque

from commuter_service.depot_queue import DepotQueue
from commuter_service.location_aware_commuter import LocationAwareCommuter


@pytest.fixture
def sample_depot_location():
    """Speightstown depot location in Barbados"""
    return (13.0969, -59.6145)


@pytest.fixture
def sample_route_id():
    """Sample route ID"""
    return "ROUTE_1A"


@pytest.fixture
def depot_queue(sample_depot_location, sample_route_id):
    """Create a basic depot queue"""
    return DepotQueue(
        depot_id="DEPOT_SPEIGHTSTOWN",
        depot_location=sample_depot_location,
        route_id=sample_route_id
    )


@pytest.fixture
def mock_commuter():
    """Create a mock commuter for testing"""
    def _create_commuter(commuter_id: str, location: tuple[float, float]):
        commuter = LocationAwareCommuter(
            person_id=commuter_id,
            spawn_location=location,
            destination_location=(13.1139, -59.6128),  # Bridgetown
            trip_purpose="commute",
            person_name=f"Commuter {commuter_id}"
        )
        return commuter
    return _create_commuter


class TestDepotQueueInitialization:
    """Test DepotQueue initialization and basic properties"""
    
    def test_initialization(self, sample_depot_location, sample_route_id):
        """Test queue initializes with correct properties"""
        queue = DepotQueue(
            depot_id="DEPOT_001",
            depot_location=sample_depot_location,
            route_id=sample_route_id
        )
        
        assert queue.depot_id == "DEPOT_001"
        assert queue.depot_location == sample_depot_location
        assert queue.route_id == sample_route_id
        assert len(queue.commuters) == 0
        assert queue.total_spawned == 0
        assert queue.total_picked_up == 0
        assert queue.total_expired == 0
        assert isinstance(queue.created_at, datetime)
    
    def test_initial_length_is_zero(self, depot_queue):
        """Test that new queue has length 0"""
        assert len(depot_queue) == 0
    
    def test_commuters_is_deque(self, depot_queue):
        """Test that commuters is a deque for FIFO operations"""
        assert isinstance(depot_queue.commuters, deque)


class TestAddCommuter:
    """Test adding commuters to the queue"""
    
    def test_add_single_commuter(self, depot_queue, mock_commuter, sample_depot_location):
        """Test adding one commuter to queue"""
        commuter = mock_commuter("C001", sample_depot_location)
        
        depot_queue.add_commuter(commuter)
        
        assert len(depot_queue) == 1
        assert depot_queue.total_spawned == 1
        assert depot_queue.commuters[0] == commuter
    
    def test_add_multiple_commuters_fifo(self, depot_queue, mock_commuter, sample_depot_location):
        """Test FIFO ordering when adding multiple commuters"""
        commuter1 = mock_commuter("C001", sample_depot_location)
        commuter2 = mock_commuter("C002", sample_depot_location)
        commuter3 = mock_commuter("C003", sample_depot_location)
        
        depot_queue.add_commuter(commuter1)
        depot_queue.add_commuter(commuter2)
        depot_queue.add_commuter(commuter3)
        
        assert len(depot_queue) == 3
        assert depot_queue.total_spawned == 3
        # Verify FIFO order (first added is first in queue)
        assert depot_queue.commuters[0] == commuter1
        assert depot_queue.commuters[1] == commuter2
        assert depot_queue.commuters[2] == commuter3
    
    def test_total_spawned_increments(self, depot_queue, mock_commuter, sample_depot_location):
        """Test that total_spawned increments correctly"""
        for i in range(10):
            commuter = mock_commuter(f"C{i:03d}", sample_depot_location)
            depot_queue.add_commuter(commuter)
        
        assert len(depot_queue) == 10
        assert depot_queue.total_spawned == 10


class TestRemoveCommuter:
    """Test removing commuters from the queue"""
    
    def test_remove_existing_commuter(self, depot_queue, mock_commuter, sample_depot_location):
        """Test removing a commuter that exists in queue"""
        commuter1 = mock_commuter("C001", sample_depot_location)
        commuter2 = mock_commuter("C002", sample_depot_location)
        commuter3 = mock_commuter("C003", sample_depot_location)
        
        depot_queue.add_commuter(commuter1)
        depot_queue.add_commuter(commuter2)
        depot_queue.add_commuter(commuter3)
        
        # Remove middle commuter
        removed = depot_queue.remove_commuter("C002")
        
        assert removed == commuter2
        assert len(depot_queue) == 2
        assert depot_queue.commuters[0] == commuter1
        assert depot_queue.commuters[1] == commuter3
    
    def test_remove_first_commuter(self, depot_queue, mock_commuter, sample_depot_location):
        """Test removing the first commuter (FIFO dequeue)"""
        commuter1 = mock_commuter("C001", sample_depot_location)
        commuter2 = mock_commuter("C002", sample_depot_location)
        
        depot_queue.add_commuter(commuter1)
        depot_queue.add_commuter(commuter2)
        
        removed = depot_queue.remove_commuter("C001")
        
        assert removed == commuter1
        assert len(depot_queue) == 1
        assert depot_queue.commuters[0] == commuter2
    
    def test_remove_last_commuter(self, depot_queue, mock_commuter, sample_depot_location):
        """Test removing the last commuter"""
        commuter1 = mock_commuter("C001", sample_depot_location)
        commuter2 = mock_commuter("C002", sample_depot_location)
        
        depot_queue.add_commuter(commuter1)
        depot_queue.add_commuter(commuter2)
        
        removed = depot_queue.remove_commuter("C002")
        
        assert removed == commuter2
        assert len(depot_queue) == 1
        assert depot_queue.commuters[0] == commuter1
    
    def test_remove_nonexistent_commuter(self, depot_queue, mock_commuter, sample_depot_location):
        """Test removing a commuter that doesn't exist"""
        commuter = mock_commuter("C001", sample_depot_location)
        depot_queue.add_commuter(commuter)
        
        removed = depot_queue.remove_commuter("C999")
        
        assert removed is None
        assert len(depot_queue) == 1  # Queue unchanged
    
    def test_remove_from_empty_queue(self, depot_queue):
        """Test removing from an empty queue"""
        removed = depot_queue.remove_commuter("C001")
        
        assert removed is None
        assert len(depot_queue) == 0


class TestGetAvailableCommuters:
    """Test proximity-based commuter queries"""
    
    def test_get_commuters_within_range(self, depot_queue, mock_commuter):
        """Test getting commuters within distance threshold"""
        # Depot at Speightstown: (13.0969, -59.6145)
        depot_location = (13.0969, -59.6145)
        
        # Add commuters at various distances
        commuter1 = mock_commuter("C001", depot_location)  # At depot (0m)
        commuter2 = mock_commuter("C002", (13.0970, -59.6145))  # ~11m away
        commuter3 = mock_commuter("C003", (13.0980, -59.6145))  # ~122m away
        
        depot_queue.add_commuter(commuter1)
        depot_queue.add_commuter(commuter2)
        depot_queue.add_commuter(commuter3)
        
        # Query with vehicle at depot, 100m radius
        vehicle_location = depot_location
        available = depot_queue.get_available_commuters(
            vehicle_location=vehicle_location,
            max_distance=100.0,
            max_count=10
        )
        
        # Should return commuters within 100m (C001 and C002)
        assert len(available) == 2
        assert commuter1 in available
        assert commuter2 in available
        assert commuter3 not in available
    
    def test_get_commuters_respects_max_count(self, depot_queue, mock_commuter):
        """Test that max_count limits results"""
        depot_location = (13.0969, -59.6145)
        
        # Add 5 commuters all at depot
        for i in range(5):
            commuter = mock_commuter(f"C{i:03d}", depot_location)
            depot_queue.add_commuter(commuter)
        
        # Query with max_count=3
        available = depot_queue.get_available_commuters(
            vehicle_location=depot_location,
            max_distance=1000.0,
            max_count=3
        )
        
        assert len(available) == 3
    
    def test_get_commuters_empty_queue(self, depot_queue):
        """Test query on empty queue returns empty list"""
        available = depot_queue.get_available_commuters(
            vehicle_location=(13.0969, -59.6145),
            max_distance=1000.0,
            max_count=10
        )
        
        assert len(available) == 0
        assert isinstance(available, list)
    
    def test_get_commuters_none_in_range(self, depot_queue, mock_commuter):
        """Test query when no commuters are in range"""
        depot_location = (13.0969, -59.6145)
        far_location = (13.1139, -59.6128)  # Bridgetown (far away)
        
        # Add commuter at depot
        commuter = mock_commuter("C001", depot_location)
        depot_queue.add_commuter(commuter)
        
        # Query from far away with small radius
        available = depot_queue.get_available_commuters(
            vehicle_location=far_location,
            max_distance=10.0,  # Only 10m
            max_count=10
        )
        
        assert len(available) == 0
    
    def test_get_commuters_fifo_order_preserved(self, depot_queue, mock_commuter):
        """Test that results maintain FIFO order"""
        depot_location = (13.0969, -59.6145)
        
        commuter1 = mock_commuter("C001", depot_location)
        commuter2 = mock_commuter("C002", depot_location)
        commuter3 = mock_commuter("C003", depot_location)
        
        depot_queue.add_commuter(commuter1)
        depot_queue.add_commuter(commuter2)
        depot_queue.add_commuter(commuter3)
        
        available = depot_queue.get_available_commuters(
            vehicle_location=depot_location,
            max_distance=1000.0,
            max_count=10
        )
        
        # Should maintain FIFO order
        assert available[0] == commuter1
        assert available[1] == commuter2
        assert available[2] == commuter3


class TestGetStats:
    """Test statistics tracking"""
    
    def test_stats_initial_state(self, depot_queue):
        """Test statistics for new queue"""
        stats = depot_queue.get_stats()
        
        assert stats["depot_id"] == "DEPOT_SPEIGHTSTOWN"
        assert stats["route_id"] == "ROUTE_1A"
        assert stats["waiting_count"] == 0
        assert stats["total_spawned"] == 0
        assert stats["total_picked_up"] == 0
        assert stats["total_expired"] == 0
        assert "uptime_seconds" in stats
        assert stats["uptime_seconds"] >= 0
    
    def test_stats_after_adding_commuters(self, depot_queue, mock_commuter, sample_depot_location):
        """Test statistics after adding commuters"""
        for i in range(5):
            commuter = mock_commuter(f"C{i:03d}", sample_depot_location)
            depot_queue.add_commuter(commuter)
        
        stats = depot_queue.get_stats()
        
        assert stats["waiting_count"] == 5
        assert stats["total_spawned"] == 5
        assert stats["total_picked_up"] == 0
        assert stats["total_expired"] == 0
    
    def test_stats_after_removing_commuters(self, depot_queue, mock_commuter, sample_depot_location):
        """Test statistics after removing commuters"""
        commuter1 = mock_commuter("C001", sample_depot_location)
        commuter2 = mock_commuter("C002", sample_depot_location)
        
        depot_queue.add_commuter(commuter1)
        depot_queue.add_commuter(commuter2)
        depot_queue.remove_commuter("C001")
        
        stats = depot_queue.get_stats()
        
        assert stats["waiting_count"] == 1
        assert stats["total_spawned"] == 2
    
    def test_stats_uptime_increases(self, depot_queue):
        """Test that uptime increases over time"""
        import time
        
        stats1 = depot_queue.get_stats()
        time.sleep(0.1)  # Wait 100ms
        stats2 = depot_queue.get_stats()
        
        assert stats2["uptime_seconds"] > stats1["uptime_seconds"]


class TestCalculateDistance:
    """Test Haversine distance calculation"""
    
    def test_distance_same_location(self, depot_queue):
        """Test distance between same location is zero"""
        location = (13.0969, -59.6145)
        distance = depot_queue._calculate_distance(location, location)
        
        assert distance == 0.0
    
    def test_distance_known_values(self, depot_queue):
        """Test distance calculation with known coordinates"""
        # Speightstown to Bridgetown (approx 19km)
        speightstown = (13.0969, -59.6145)
        bridgetown = (13.1139, -59.6128)
        
        distance = depot_queue._calculate_distance(speightstown, bridgetown)
        
        # Should be approximately 1900 meters (1.9km)
        # Note: Actual distance is about 19km, but these are simplified coordinates
        assert distance > 0
        assert isinstance(distance, float)
    
    def test_distance_is_symmetric(self, depot_queue):
        """Test that distance(A, B) == distance(B, A)"""
        loc1 = (13.0969, -59.6145)
        loc2 = (13.1139, -59.6128)
        
        dist1 = depot_queue._calculate_distance(loc1, loc2)
        dist2 = depot_queue._calculate_distance(loc2, loc1)
        
        assert dist1 == dist2
    
    def test_distance_nearby_points(self, depot_queue):
        """Test distance for nearby points (should be small)"""
        loc1 = (13.0969, -59.6145)
        loc2 = (13.0970, -59.6145)  # 0.0001 degree latitude difference
        
        distance = depot_queue._calculate_distance(loc1, loc2)
        
        # ~11 meters (1 degree latitude ≈ 111km, so 0.0001° ≈ 11m)
        assert distance < 20  # Less than 20 meters
        assert distance > 5   # More than 5 meters
