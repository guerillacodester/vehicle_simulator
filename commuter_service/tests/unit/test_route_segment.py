"""
Unit Tests for RouteSegment
============================

Tests bidirectional commuter management for route segments.

Test Coverage:
- Segment initialization
- Adding commuters (inbound/outbound)
- Removing commuters
- Querying by direction
- Counting commuters
- Statistics tracking
"""

import pytest

from commuter_service.route_segment import RouteSegment
from commuter_service.location_aware_commuter import LocationAwareCommuter
from commuter_service.socketio_client import CommuterDirection


@pytest.fixture
def sample_grid_cell():
    """Sample grid cell coordinates"""
    return (1309, -5961)  # Represents Speightstown area


@pytest.fixture
def route_segment(sample_grid_cell):
    """Create a basic route segment"""
    return RouteSegment(
        route_id="ROUTE_1A",
        segment_id="1A_SPEIGHT_HOLE_OUT",
        grid_cell=sample_grid_cell
    )


@pytest.fixture
def mock_commuter():
    """Create mock commuters for testing"""
    def _create_commuter(
        person_id: str,
        location: tuple[float, float],
        direction: CommuterDirection
    ):
        commuter = LocationAwareCommuter(
            person_id=person_id,
            spawn_location=location,
            destination_location=(13.1139, -59.6128),  # Bridgetown
            trip_purpose="commute"
        )
        # Set direction attribute (not in constructor)
        commuter.direction = direction
        return commuter
    return _create_commuter


class TestRouteSegmentInitialization:
    """Test RouteSegment initialization"""
    
    def test_initialization(self, sample_grid_cell):
        """Test segment initializes with correct properties"""
        segment = RouteSegment(
            route_id="ROUTE_1A",
            segment_id="1A_TEST",
            grid_cell=sample_grid_cell
        )
        
        assert segment.route_id == "ROUTE_1A"
        assert segment.segment_id == "1A_TEST"
        assert segment.grid_cell == sample_grid_cell
        assert len(segment.commuters_inbound) == 0
        assert len(segment.commuters_outbound) == 0
        assert segment.total_spawned == 0
        assert segment.total_picked_up == 0
        assert segment.total_expired == 0
    
    def test_initial_count_is_zero(self, route_segment):
        """Test new segment has zero commuters"""
        assert route_segment.count() == 0
    
    def test_commuters_lists_are_separate(self, route_segment):
        """Test inbound and outbound lists are independent"""
        assert route_segment.commuters_inbound is not route_segment.commuters_outbound


class TestAddCommuter:
    """Test adding commuters to segments"""
    
    def test_add_outbound_commuter(self, route_segment, mock_commuter):
        """Test adding outbound commuter"""
        location = (13.0969, -59.6145)
        commuter = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        
        route_segment.add_commuter(commuter)
        
        assert route_segment.count() == 1
        assert len(route_segment.commuters_outbound) == 1
        assert len(route_segment.commuters_inbound) == 0
        assert route_segment.total_spawned == 1
        assert commuter in route_segment.commuters_outbound
    
    def test_add_inbound_commuter(self, route_segment, mock_commuter):
        """Test adding inbound commuter"""
        location = (13.0969, -59.6145)
        commuter = mock_commuter("C001", location, CommuterDirection.INBOUND)
        
        route_segment.add_commuter(commuter)
        
        assert route_segment.count() == 1
        assert len(route_segment.commuters_inbound) == 1
        assert len(route_segment.commuters_outbound) == 0
        assert route_segment.total_spawned == 1
        assert commuter in route_segment.commuters_inbound
    
    def test_add_multiple_commuters_same_direction(self, route_segment, mock_commuter):
        """Test adding multiple commuters in same direction"""
        location = (13.0969, -59.6145)
        
        commuter1 = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        commuter2 = mock_commuter("C002", location, CommuterDirection.OUTBOUND)
        commuter3 = mock_commuter("C003", location, CommuterDirection.OUTBOUND)
        
        route_segment.add_commuter(commuter1)
        route_segment.add_commuter(commuter2)
        route_segment.add_commuter(commuter3)
        
        assert route_segment.count() == 3
        assert len(route_segment.commuters_outbound) == 3
        assert route_segment.total_spawned == 3
    
    def test_add_bidirectional_commuters(self, route_segment, mock_commuter):
        """Test adding commuters in both directions"""
        location = (13.0969, -59.6145)
        
        outbound1 = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        outbound2 = mock_commuter("C002", location, CommuterDirection.OUTBOUND)
        inbound1 = mock_commuter("C003", location, CommuterDirection.INBOUND)
        inbound2 = mock_commuter("C004", location, CommuterDirection.INBOUND)
        inbound3 = mock_commuter("C005", location, CommuterDirection.INBOUND)
        
        route_segment.add_commuter(outbound1)
        route_segment.add_commuter(inbound1)
        route_segment.add_commuter(outbound2)
        route_segment.add_commuter(inbound2)
        route_segment.add_commuter(inbound3)
        
        assert route_segment.count() == 5
        assert len(route_segment.commuters_outbound) == 2
        assert len(route_segment.commuters_inbound) == 3
        assert route_segment.total_spawned == 5


class TestRemoveCommuter:
    """Test removing commuters from segments"""
    
    def test_remove_outbound_commuter(self, route_segment, mock_commuter):
        """Test removing outbound commuter"""
        location = (13.0969, -59.6145)
        commuter = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        
        route_segment.add_commuter(commuter)
        removed = route_segment.remove_commuter("C001")
        
        assert removed == commuter
        assert route_segment.count() == 0
        assert len(route_segment.commuters_outbound) == 0
    
    def test_remove_inbound_commuter(self, route_segment, mock_commuter):
        """Test removing inbound commuter"""
        location = (13.0969, -59.6145)
        commuter = mock_commuter("C001", location, CommuterDirection.INBOUND)
        
        route_segment.add_commuter(commuter)
        removed = route_segment.remove_commuter("C001")
        
        assert removed == commuter
        assert route_segment.count() == 0
        assert len(route_segment.commuters_inbound) == 0
    
    def test_remove_from_mixed_directions(self, route_segment, mock_commuter):
        """Test removing commuters from segment with both directions"""
        location = (13.0969, -59.6145)
        
        outbound = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        inbound = mock_commuter("C002", location, CommuterDirection.INBOUND)
        
        route_segment.add_commuter(outbound)
        route_segment.add_commuter(inbound)
        
        # Remove outbound
        removed = route_segment.remove_commuter("C001")
        assert removed == outbound
        assert route_segment.count() == 1
        assert len(route_segment.commuters_inbound) == 1
        
        # Remove inbound
        removed = route_segment.remove_commuter("C002")
        assert removed == inbound
        assert route_segment.count() == 0
    
    def test_remove_nonexistent_commuter(self, route_segment, mock_commuter):
        """Test removing commuter that doesn't exist"""
        location = (13.0969, -59.6145)
        commuter = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        
        route_segment.add_commuter(commuter)
        removed = route_segment.remove_commuter("C999")
        
        assert removed is None
        assert route_segment.count() == 1  # Unchanged
    
    def test_remove_from_empty_segment(self, route_segment):
        """Test removing from empty segment"""
        removed = route_segment.remove_commuter("C001")
        
        assert removed is None
        assert route_segment.count() == 0


class TestGetCommutersByDirection:
    """Test querying commuters by direction"""
    
    def test_get_outbound_commuters(self, route_segment, mock_commuter):
        """Test getting outbound commuters"""
        location = (13.0969, -59.6145)
        
        outbound1 = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        outbound2 = mock_commuter("C002", location, CommuterDirection.OUTBOUND)
        inbound1 = mock_commuter("C003", location, CommuterDirection.INBOUND)
        
        route_segment.add_commuter(outbound1)
        route_segment.add_commuter(outbound2)
        route_segment.add_commuter(inbound1)
        
        outbound = route_segment.get_commuters_by_direction(CommuterDirection.OUTBOUND)
        
        assert len(outbound) == 2
        assert outbound1 in outbound
        assert outbound2 in outbound
        assert inbound1 not in outbound
    
    def test_get_inbound_commuters(self, route_segment, mock_commuter):
        """Test getting inbound commuters"""
        location = (13.0969, -59.6145)
        
        inbound1 = mock_commuter("C001", location, CommuterDirection.INBOUND)
        inbound2 = mock_commuter("C002", location, CommuterDirection.INBOUND)
        outbound1 = mock_commuter("C003", location, CommuterDirection.OUTBOUND)
        
        route_segment.add_commuter(inbound1)
        route_segment.add_commuter(inbound2)
        route_segment.add_commuter(outbound1)
        
        inbound = route_segment.get_commuters_by_direction(CommuterDirection.INBOUND)
        
        assert len(inbound) == 2
        assert inbound1 in inbound
        assert inbound2 in inbound
        assert outbound1 not in inbound
    
    def test_get_empty_direction(self, route_segment, mock_commuter):
        """Test getting commuters when direction is empty"""
        location = (13.0969, -59.6145)
        
        # Add only outbound
        outbound = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        route_segment.add_commuter(outbound)
        
        # Query inbound (should be empty)
        inbound = route_segment.get_commuters_by_direction(CommuterDirection.INBOUND)
        
        assert len(inbound) == 0
        assert isinstance(inbound, list)


class TestCount:
    """Test counting commuters"""
    
    def test_count_empty_segment(self, route_segment):
        """Test count on empty segment"""
        assert route_segment.count() == 0
    
    def test_count_single_direction(self, route_segment, mock_commuter):
        """Test count with only one direction"""
        location = (13.0969, -59.6145)
        
        for i in range(5):
            commuter = mock_commuter(f"C{i:03d}", location, CommuterDirection.OUTBOUND)
            route_segment.add_commuter(commuter)
        
        assert route_segment.count() == 5
    
    def test_count_bidirectional(self, route_segment, mock_commuter):
        """Test count with both directions"""
        location = (13.0969, -59.6145)
        
        # Add 3 outbound
        for i in range(3):
            commuter = mock_commuter(f"OUT{i}", location, CommuterDirection.OUTBOUND)
            route_segment.add_commuter(commuter)
        
        # Add 4 inbound
        for i in range(4):
            commuter = mock_commuter(f"IN{i}", location, CommuterDirection.INBOUND)
            route_segment.add_commuter(commuter)
        
        assert route_segment.count() == 7
    
    def test_count_by_direction_outbound(self, route_segment, mock_commuter):
        """Test count_by_direction for outbound"""
        location = (13.0969, -59.6145)
        
        for i in range(3):
            outbound = mock_commuter(f"OUT{i}", location, CommuterDirection.OUTBOUND)
            route_segment.add_commuter(outbound)
        
        for i in range(2):
            inbound = mock_commuter(f"IN{i}", location, CommuterDirection.INBOUND)
            route_segment.add_commuter(inbound)
        
        assert route_segment.count_by_direction(CommuterDirection.OUTBOUND) == 3
    
    def test_count_by_direction_inbound(self, route_segment, mock_commuter):
        """Test count_by_direction for inbound"""
        location = (13.0969, -59.6145)
        
        for i in range(3):
            outbound = mock_commuter(f"OUT{i}", location, CommuterDirection.OUTBOUND)
            route_segment.add_commuter(outbound)
        
        for i in range(2):
            inbound = mock_commuter(f"IN{i}", location, CommuterDirection.INBOUND)
            route_segment.add_commuter(inbound)
        
        assert route_segment.count_by_direction(CommuterDirection.INBOUND) == 2


class TestGetStats:
    """Test statistics tracking"""
    
    def test_stats_empty_segment(self, route_segment, sample_grid_cell):
        """Test stats for empty segment"""
        stats = route_segment.get_stats()
        
        assert stats["route_id"] == "ROUTE_1A"
        assert stats["segment_id"] == "1A_SPEIGHT_HOLE_OUT"
        assert stats["grid_cell"] == sample_grid_cell
        assert stats["inbound_count"] == 0
        assert stats["outbound_count"] == 0
        assert stats["total_waiting"] == 0
        assert stats["total_spawned"] == 0
        assert stats["total_picked_up"] == 0
        assert stats["total_expired"] == 0
    
    def test_stats_with_commuters(self, route_segment, mock_commuter):
        """Test stats with commuters added"""
        location = (13.0969, -59.6145)
        
        # Add 3 outbound, 2 inbound
        for i in range(3):
            outbound = mock_commuter(f"OUT{i}", location, CommuterDirection.OUTBOUND)
            route_segment.add_commuter(outbound)
        
        for i in range(2):
            inbound = mock_commuter(f"IN{i}", location, CommuterDirection.INBOUND)
            route_segment.add_commuter(inbound)
        
        stats = route_segment.get_stats()
        
        assert stats["inbound_count"] == 2
        assert stats["outbound_count"] == 3
        assert stats["total_waiting"] == 5
        assert stats["total_spawned"] == 5
    
    def test_stats_after_removal(self, route_segment, mock_commuter):
        """Test stats after removing commuters"""
        location = (13.0969, -59.6145)
        
        commuter1 = mock_commuter("C001", location, CommuterDirection.OUTBOUND)
        commuter2 = mock_commuter("C002", location, CommuterDirection.INBOUND)
        
        route_segment.add_commuter(commuter1)
        route_segment.add_commuter(commuter2)
        route_segment.remove_commuter("C001")
        
        stats = route_segment.get_stats()
        
        assert stats["outbound_count"] == 0
        assert stats["inbound_count"] == 1
        assert stats["total_waiting"] == 1
        assert stats["total_spawned"] == 2  # Still counts removed
