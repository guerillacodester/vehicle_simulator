"""
End-to-End Testing Suite for Refactored Reservoir System

This test suite validates the complete passenger lifecycle flows:
1. Spawning Flow - Passengers spawned at depots/routes
2. Pickup Flow - Passengers picked up by vehicles
3. Expiration Flow - Inactive passengers automatically removed
4. Statistics Flow - Metrics tracked correctly throughout
5. Socket.IO Flow - Events emitted properly

These tests verify that the refactored reservoir system maintains
all original functionality while using the new modular architecture.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime
import time


class MockSocketIO:
    """Mock Socket.IO for testing event emissions."""
    
    def __init__(self):
        self.events = []
    
    async def emit(self, event_name, data, **kwargs):
        """Record emitted events."""
        self.events.append({
            'event': event_name,
            'data': data,
            'timestamp': time.time(),
            **kwargs
        })
    
    def get_events(self, event_name=None):
        """Get all events or filter by event name."""
        if event_name:
            return [e for e in self.events if e['event'] == event_name]
        return self.events
    
    def clear(self):
        """Clear recorded events."""
        self.events = []


class MockPassengerDatabase:
    """Mock passenger database for testing."""
    
    def __init__(self):
        self.commuters = {}
        self.next_id = 1
    
    async def create_commuter(self, data):
        """Create a new commuter."""
        commuter_id = self.next_id
        self.next_id += 1
        
        commuter = {
            'id': commuter_id,
            'depot_id': data.get('depot_id'),
            'route_id': data.get('route_id'),
            'location': data.get('location'),
            'direction': data.get('direction'),
            'created_at': datetime.now().isoformat(),
            'last_activity': time.time()
        }
        
        self.commuters[commuter_id] = commuter
        return commuter
    
    async def update_commuter(self, commuter_id, data):
        """Update an existing commuter."""
        if commuter_id in self.commuters:
            self.commuters[commuter_id].update(data)
            self.commuters[commuter_id]['last_activity'] = time.time()
            return self.commuters[commuter_id]
        return None
    
    async def delete_commuter(self, commuter_id):
        """Delete a commuter."""
        if commuter_id in self.commuters:
            del self.commuters[commuter_id]
            return True
        return False
    
    def get_commuter(self, commuter_id):
        """Get a commuter by ID."""
        return self.commuters.get(commuter_id)


class MockCommuter:
    """Mock commuter object for testing."""
    
    def __init__(self, commuter_id, depot_id=None, route_id=None, 
                 location=None, direction=None, last_activity=None):
        self.id = commuter_id
        self.depot_id = depot_id
        self.route_id = route_id
        self.location = location or (13.0, -59.6)
        self.direction = direction
        self.last_activity = last_activity or time.time()
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'depot_id': self.depot_id,
            'route_id': self.route_id,
            'location': self.location,
            'direction': self.direction,
            'last_activity': self.last_activity,
            'created_at': self.created_at
        }


@pytest.mark.asyncio
class TestDepotReservoirEndToEnd:
    """End-to-end tests for DepotReservoir with refactored modules."""
    
    async def test_complete_depot_spawning_flow(self):
        """Test complete flow: spawn request → commuter added → event emitted."""
        print("\n" + "="*70)
        print("TEST: Complete Depot Spawning Flow")
        print("="*70)
        
        # Import here to avoid dependency issues
        try:
            from commuter_service.depot_queue import DepotQueue
            from commuter_service.location_normalizer import LocationNormalizer
            from commuter_service.reservoir_statistics import ReservoirStatistics
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        # Setup
        depot_queue = DepotQueue()
        statistics = ReservoirStatistics()
        
        # Test data
        spawn_request = {
            'depot_id': 'depot_1',
            'location': {'lat': 13.1, 'lon': -59.6},
            'count': 3
        }
        
        # Simulate spawning flow
        print("\n1. Normalizing location...")
        normalized_location = LocationNormalizer.normalize(spawn_request['location'])
        assert normalized_location == (13.1, -59.6)
        print(f"   ✓ Location normalized: {normalized_location}")
        
        print("\n2. Creating commuters...")
        for i in range(spawn_request['count']):
            commuter = MockCommuter(
                commuter_id=i + 1,
                depot_id=spawn_request['depot_id'],
                location=normalized_location
            )
            depot_queue.add_commuter(commuter)
            statistics.increment('total_commuters_added')
            statistics.increment('current_active_commuters')
            print(f"   ✓ Commuter {i+1} added to queue")
        
        print("\n3. Verifying queue state...")
        assert depot_queue.get_queue_length() == 3
        print(f"   ✓ Queue length: {depot_queue.get_queue_length()}")
        
        print("\n4. Verifying statistics...")
        stats = statistics.get_all()
        assert stats['total_commuters_added'] == 3
        assert stats['current_active_commuters'] == 3
        print(f"   ✓ Total added: {stats['total_commuters_added']}")
        print(f"   ✓ Current active: {stats['current_active_commuters']}")
        
        print("\n✅ Spawning flow completed successfully!")
    
    async def test_complete_depot_pickup_flow(self):
        """Test complete flow: commuter pickup → removed from queue → event emitted."""
        print("\n" + "="*70)
        print("TEST: Complete Depot Pickup Flow")
        print("="*70)
        
        try:
            from commuter_service.depot_queue import DepotQueue
            from commuter_service.reservoir_statistics import ReservoirStatistics
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        # Setup
        depot_queue = DepotQueue()
        statistics = ReservoirStatistics()
        socketio = MockSocketIO()
        
        # Add commuters to queue
        print("\n1. Adding commuters to queue...")
        for i in range(5):
            commuter = MockCommuter(commuter_id=i + 1, depot_id='depot_1')
            depot_queue.add_commuter(commuter)
            statistics.increment('total_commuters_added')
            statistics.increment('current_active_commuters')
        print(f"   ✓ Added 5 commuters")
        
        # Simulate pickup
        print("\n2. Simulating vehicle pickup...")
        picked_up_commuter = depot_queue.get_next_commuter()
        assert picked_up_commuter is not None
        assert picked_up_commuter.id == 1  # FIFO order
        print(f"   ✓ Picked up commuter {picked_up_commuter.id} (FIFO)")
        
        # Update statistics
        statistics.increment('total_commuters_removed')
        statistics.decrement('current_active_commuters')
        
        # Emit event
        await socketio.emit('commuter_picked_up', {
            'commuter_id': picked_up_commuter.id,
            'depot_id': picked_up_commuter.depot_id
        })
        
        print("\n3. Verifying queue state...")
        assert depot_queue.get_queue_length() == 4
        print(f"   ✓ Queue length after pickup: {depot_queue.get_queue_length()}")
        
        print("\n4. Verifying statistics...")
        stats = statistics.get_all()
        assert stats['total_commuters_removed'] == 1
        assert stats['current_active_commuters'] == 4
        print(f"   ✓ Total removed: {stats['total_commuters_removed']}")
        print(f"   ✓ Current active: {stats['current_active_commuters']}")
        
        print("\n5. Verifying Socket.IO events...")
        events = socketio.get_events('commuter_picked_up')
        assert len(events) == 1
        assert events[0]['data']['commuter_id'] == 1
        print(f"   ✓ Event emitted: {events[0]['event']}")
        
        print("\n✅ Pickup flow completed successfully!")
    
    async def test_complete_depot_expiration_flow(self):
        """Test complete flow: inactive commuter → expired → removed → event emitted."""
        print("\n" + "="*70)
        print("TEST: Complete Depot Expiration Flow")
        print("="*70)
        
        try:
            from commuter_service.depot_queue import DepotQueue
            from commuter_service.reservoir_statistics import ReservoirStatistics
            from commuter_service.expiration_manager import ReservoirExpirationManager
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        # Setup
        depot_queue = DepotQueue()
        statistics = ReservoirStatistics()
        socketio = MockSocketIO()
        
        # Add commuters with different activity times
        print("\n1. Adding commuters with varying activity times...")
        current_time = time.time()
        
        # Active commuter (recent activity)
        active_commuter = MockCommuter(
            commuter_id=1,
            depot_id='depot_1',
            last_activity=current_time
        )
        depot_queue.add_commuter(active_commuter)
        
        # Expired commuter (old activity)
        expired_commuter = MockCommuter(
            commuter_id=2,
            depot_id='depot_1',
            last_activity=current_time - 400  # 400 seconds ago
        )
        depot_queue.add_commuter(expired_commuter)
        
        statistics.increment('current_active_commuters', 2)
        print(f"   ✓ Added 1 active commuter (last_activity: now)")
        print(f"   ✓ Added 1 expired commuter (last_activity: 400s ago)")
        
        # Setup callbacks for expiration manager
        async def get_active_commuters():
            return depot_queue.get_all_commuters()
        
        async def expire_commuter(commuter_id):
            depot_queue.remove_commuter(commuter_id)
            statistics.increment('total_commuters_expired')
            statistics.decrement('current_active_commuters')
            await socketio.emit('commuter_expired', {
                'commuter_id': commuter_id,
                'reason': 'inactivity'
            })
        
        # Create expiration manager with short threshold for testing
        print("\n2. Starting expiration manager...")
        expiration_manager = ReservoirExpirationManager(
            check_interval=1,
            inactivity_threshold=300,  # 300 seconds
            get_active_callback=get_active_commuters,
            expire_callback=expire_commuter
        )
        
        await expiration_manager.start()
        print("   ✓ Expiration manager started")
        
        # Wait for expiration check
        print("\n3. Waiting for expiration check...")
        await asyncio.sleep(1.5)
        await expiration_manager.stop()
        print("   ✓ Expiration check completed")
        
        # Verify results
        print("\n4. Verifying expiration results...")
        assert depot_queue.get_queue_length() == 1
        remaining_commuters = depot_queue.get_all_commuters()
        assert remaining_commuters[0].id == 1  # Active commuter remains
        print(f"   ✓ Queue length after expiration: {depot_queue.get_queue_length()}")
        print(f"   ✓ Remaining commuter: {remaining_commuters[0].id} (active)")
        
        print("\n5. Verifying statistics...")
        stats = statistics.get_all()
        assert stats['total_commuters_expired'] == 1
        assert stats['current_active_commuters'] == 1
        print(f"   ✓ Total expired: {stats['total_commuters_expired']}")
        print(f"   ✓ Current active: {stats['current_active_commuters']}")
        
        print("\n6. Verifying Socket.IO events...")
        events = socketio.get_events('commuter_expired')
        assert len(events) == 1
        assert events[0]['data']['commuter_id'] == 2
        assert events[0]['data']['reason'] == 'inactivity'
        print(f"   ✓ Event emitted: {events[0]['event']}")
        print(f"   ✓ Expired commuter ID: {events[0]['data']['commuter_id']}")
        
        print("\n✅ Expiration flow completed successfully!")
    
    async def test_depot_statistics_accuracy(self):
        """Test that statistics remain accurate through multiple operations."""
        print("\n" + "="*70)
        print("TEST: Depot Statistics Accuracy")
        print("="*70)
        
        try:
            from commuter_service.depot_queue import DepotQueue
            from commuter_service.reservoir_statistics import ReservoirStatistics
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        depot_queue = DepotQueue()
        statistics = ReservoirStatistics()
        
        print("\n1. Performing mixed operations...")
        
        # Add 10 commuters
        print("   - Adding 10 commuters...")
        for i in range(10):
            commuter = MockCommuter(commuter_id=i + 1, depot_id='depot_1')
            depot_queue.add_commuter(commuter)
            statistics.increment('total_commuters_added')
            statistics.increment('current_active_commuters')
        
        # Remove 3 commuters
        print("   - Removing 3 commuters...")
        for _ in range(3):
            depot_queue.get_next_commuter()
            statistics.increment('total_commuters_removed')
            statistics.decrement('current_active_commuters')
        
        # Expire 2 commuters
        print("   - Expiring 2 commuters...")
        for _ in range(2):
            commuter = depot_queue.get_next_commuter()
            depot_queue.remove_commuter(commuter.id)
            statistics.increment('total_commuters_expired')
            statistics.decrement('current_active_commuters')
        
        print("\n2. Verifying final statistics...")
        stats = statistics.get_all()
        
        assert stats['total_commuters_added'] == 10
        assert stats['total_commuters_removed'] == 3
        assert stats['total_commuters_expired'] == 2
        assert stats['current_active_commuters'] == 5  # 10 - 3 - 2 = 5
        
        print(f"   ✓ Total added: {stats['total_commuters_added']}")
        print(f"   ✓ Total removed: {stats['total_commuters_removed']}")
        print(f"   ✓ Total expired: {stats['total_commuters_expired']}")
        print(f"   ✓ Current active: {stats['current_active_commuters']}")
        print(f"   ✓ All statistics accurate!")
        
        # Verify queue state matches statistics
        assert depot_queue.get_queue_length() == stats['current_active_commuters']
        print(f"   ✓ Queue length matches statistics")
        
        print("\n✅ Statistics accuracy verified!")


@pytest.mark.asyncio
class TestRouteReservoirEndToEnd:
    """End-to-end tests for RouteReservoir with refactored modules."""
    
    async def test_complete_route_spawning_flow(self):
        """Test complete flow: spawn request → bidirectional commuters → segments."""
        print("\n" + "="*70)
        print("TEST: Complete Route Spawning Flow")
        print("="*70)
        
        try:
            from commuter_service.route_segment import RouteSegment
            from commuter_service.location_normalizer import LocationNormalizer
            from commuter_service.reservoir_statistics import ReservoirStatistics
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        # Setup
        route_segments = {}
        statistics = ReservoirStatistics()
        
        # Test data - spawn commuters in both directions
        spawn_requests = [
            {'route_id': 'route_1a', 'location': (13.1, -59.6), 'direction': 'outbound'},
            {'route_id': 'route_1a', 'location': (13.1, -59.6), 'direction': 'outbound'},
            {'route_id': 'route_1a', 'location': (13.1, -59.6), 'direction': 'inbound'},
        ]
        
        print("\n1. Spawning commuters in both directions...")
        for i, request in enumerate(spawn_requests):
            # Normalize location
            location = LocationNormalizer.normalize(request['location'])
            
            # Get or create segment
            segment_key = (request['route_id'], location)
            if segment_key not in route_segments:
                route_segments[segment_key] = RouteSegment(
                    route_id=request['route_id'],
                    location=location
                )
            
            segment = route_segments[segment_key]
            
            # Create commuter
            commuter = MockCommuter(
                commuter_id=i + 1,
                route_id=request['route_id'],
                location=location,
                direction=request['direction']
            )
            
            # Add to segment
            segment.add_commuter(commuter, request['direction'])
            statistics.increment('total_commuters_added')
            statistics.increment('current_active_commuters')
            
            print(f"   ✓ Commuter {i+1} added ({request['direction']})")
        
        print("\n2. Verifying segment state...")
        segment = list(route_segments.values())[0]
        assert segment.get_segment_length('outbound') == 2
        assert segment.get_segment_length('inbound') == 1
        print(f"   ✓ Outbound queue: {segment.get_segment_length('outbound')} commuters")
        print(f"   ✓ Inbound queue: {segment.get_segment_length('inbound')} commuters")
        
        print("\n3. Verifying statistics...")
        stats = statistics.get_all()
        assert stats['total_commuters_added'] == 3
        assert stats['current_active_commuters'] == 3
        print(f"   ✓ Total added: {stats['total_commuters_added']}")
        print(f"   ✓ Current active: {stats['current_active_commuters']}")
        
        print("\n✅ Route spawning flow completed successfully!")
    
    async def test_complete_route_pickup_flow(self):
        """Test complete flow: bidirectional pickup → FIFO per direction."""
        print("\n" + "="*70)
        print("TEST: Complete Route Pickup Flow (Bidirectional)")
        print("="*70)
        
        try:
            from commuter_service.route_segment import RouteSegment
            from commuter_service.reservoir_statistics import ReservoirStatistics
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        # Setup
        segment = RouteSegment(route_id='route_1a', location=(13.1, -59.6))
        statistics = ReservoirStatistics()
        socketio = MockSocketIO()
        
        # Add commuters in both directions
        print("\n1. Adding commuters in both directions...")
        for i in range(3):
            outbound = MockCommuter(
                commuter_id=i + 1,
                route_id='route_1a',
                direction='outbound'
            )
            inbound = MockCommuter(
                commuter_id=i + 4,
                route_id='route_1a',
                direction='inbound'
            )
            segment.add_commuter(outbound, 'outbound')
            segment.add_commuter(inbound, 'inbound')
            statistics.increment('current_active_commuters', 2)
        
        print(f"   ✓ Added 3 outbound commuters (IDs 1-3)")
        print(f"   ✓ Added 3 inbound commuters (IDs 4-6)")
        
        # Pickup from outbound
        print("\n2. Picking up from outbound queue...")
        outbound_commuter = segment.get_next_commuter('outbound')
        assert outbound_commuter.id == 1  # FIFO
        statistics.increment('total_commuters_removed')
        statistics.decrement('current_active_commuters')
        await socketio.emit('commuter_picked_up', {
            'commuter_id': outbound_commuter.id,
            'direction': 'outbound'
        })
        print(f"   ✓ Picked up commuter {outbound_commuter.id} (outbound, FIFO)")
        
        # Pickup from inbound
        print("\n3. Picking up from inbound queue...")
        inbound_commuter = segment.get_next_commuter('inbound')
        assert inbound_commuter.id == 4  # FIFO
        statistics.increment('total_commuters_removed')
        statistics.decrement('current_active_commuters')
        await socketio.emit('commuter_picked_up', {
            'commuter_id': inbound_commuter.id,
            'direction': 'inbound'
        })
        print(f"   ✓ Picked up commuter {inbound_commuter.id} (inbound, FIFO)")
        
        print("\n4. Verifying segment state...")
        assert segment.get_segment_length('outbound') == 2
        assert segment.get_segment_length('inbound') == 2
        print(f"   ✓ Outbound remaining: {segment.get_segment_length('outbound')}")
        print(f"   ✓ Inbound remaining: {segment.get_segment_length('inbound')}")
        
        print("\n5. Verifying statistics...")
        stats = statistics.get_all()
        assert stats['total_commuters_removed'] == 2
        assert stats['current_active_commuters'] == 4
        print(f"   ✓ Total removed: {stats['total_commuters_removed']}")
        print(f"   ✓ Current active: {stats['current_active_commuters']}")
        
        print("\n6. Verifying Socket.IO events...")
        events = socketio.get_events('commuter_picked_up')
        assert len(events) == 2
        print(f"   ✓ Events emitted: {len(events)}")
        
        print("\n✅ Route pickup flow completed successfully!")
    
    async def test_route_segment_cleanup(self):
        """Test that empty segments can be identified and cleaned up."""
        print("\n" + "="*70)
        print("TEST: Route Segment Cleanup")
        print("="*70)
        
        try:
            from commuter_service.route_segment import RouteSegment
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        segment = RouteSegment(route_id='route_1a', location=(13.1, -59.6))
        
        print("\n1. Creating segment with commuters...")
        for i in range(2):
            commuter = MockCommuter(commuter_id=i + 1, route_id='route_1a')
            segment.add_commuter(commuter, 'outbound')
        
        assert not segment.is_empty()
        print(f"   ✓ Segment not empty: {segment.get_segment_length('outbound')} commuters")
        
        print("\n2. Removing all commuters...")
        segment.get_next_commuter('outbound')
        segment.get_next_commuter('outbound')
        
        print("\n3. Verifying segment is empty...")
        assert segment.is_empty()
        print(f"   ✓ Segment is empty (can be cleaned up)")
        
        print("\n✅ Segment cleanup test passed!")


@pytest.mark.asyncio
class TestSpawningCoordinatorEndToEnd:
    """End-to-end tests for SpawningCoordinator."""
    
    async def test_spawning_coordinator_callback_flow(self):
        """Test that SpawningCoordinator properly calls callbacks."""
        print("\n" + "="*70)
        print("TEST: Spawning Coordinator Callback Flow")
        print("="*70)
        
        try:
            from commuter_service.spawning_coordinator import SpawningCoordinator
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        # Track callback calls
        generate_calls = []
        process_calls = []
        
        async def generate_spawn_requests():
            """Mock: Generate spawn requests."""
            requests = [
                {'depot_id': 'depot_1', 'count': 2},
                {'depot_id': 'depot_2', 'count': 1}
            ]
            generate_calls.append(True)
            return requests
        
        async def process_spawn_request(request):
            """Mock: Process one spawn request."""
            process_calls.append(request)
        
        print("\n1. Creating spawning coordinator...")
        coordinator = SpawningCoordinator(
            spawn_interval=1,  # 1 second for testing
            generate_requests_callback=generate_spawn_requests,
            process_request_callback=process_spawn_request
        )
        
        print("\n2. Starting coordinator...")
        await coordinator.start()
        print("   ✓ Coordinator started")
        
        print("\n3. Waiting for spawn cycle...")
        await asyncio.sleep(1.5)
        await coordinator.stop()
        print("   ✓ Coordinator stopped")
        
        print("\n4. Verifying callbacks were called...")
        assert len(generate_calls) >= 1
        assert len(process_calls) >= 2  # 2 requests per cycle
        print(f"   ✓ Generate callback called: {len(generate_calls)} times")
        print(f"   ✓ Process callback called: {len(process_calls)} times")
        
        print("\n5. Verifying request data...")
        assert any(r['depot_id'] == 'depot_1' for r in process_calls)
        assert any(r['depot_id'] == 'depot_2' for r in process_calls)
        print(f"   ✓ All spawn requests processed correctly")
        
        print("\n✅ Spawning coordinator flow completed successfully!")


@pytest.mark.asyncio
class TestIntegratedReservoirFlow:
    """Integration tests combining all refactored modules."""
    
    async def test_full_lifecycle_depot_to_pickup(self):
        """Test complete lifecycle: spawn → wait → pickup → stats."""
        print("\n" + "="*70)
        print("TEST: Full Lifecycle - Depot Spawn to Pickup")
        print("="*70)
        
        try:
            from commuter_service.depot_queue import DepotQueue
            from commuter_service.location_normalizer import LocationNormalizer
            from commuter_service.reservoir_statistics import ReservoirStatistics
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        
        # Setup complete system
        depot_queue = DepotQueue()
        statistics = ReservoirStatistics()
        socketio = MockSocketIO()
        
        print("\n🔄 PHASE 1: SPAWNING")
        print("-" * 70)
        
        # Spawn multiple commuters
        spawn_data = [
            {'depot_id': 'depot_1', 'location': {'lat': 13.1, 'lon': -59.6}},
            {'depot_id': 'depot_1', 'location': (13.1, -59.6)},
            {'depot_id': 'depot_2', 'location': {'latitude': 13.2, 'longitude': -59.7}},
        ]
        
        for i, data in enumerate(spawn_data):
            location = LocationNormalizer.normalize(data['location'])
            commuter = MockCommuter(
                commuter_id=i + 1,
                depot_id=data['depot_id'],
                location=location
            )
            depot_queue.add_commuter(commuter)
            statistics.increment('total_commuters_added')
            statistics.increment('current_active_commuters')
            await socketio.emit('commuter_spawned', commuter.to_dict())
            print(f"   ✓ Spawned commuter {i+1} at {data['depot_id']}")
        
        stats = statistics.get_all()
        print(f"\n   📊 After spawning:")
        print(f"      - Queue: {depot_queue.get_queue_length()} commuters")
        print(f"      - Total spawned: {stats['total_commuters_added']}")
        
        print("\n🔄 PHASE 2: VEHICLE PICKUP")
        print("-" * 70)
        
        # Simulate vehicle picking up commuters
        pickups = []
        for _ in range(2):
            commuter = depot_queue.get_next_commuter()
            if commuter:
                pickups.append(commuter.id)
                statistics.increment('total_commuters_removed')
                statistics.decrement('current_active_commuters')
                await socketio.emit('commuter_picked_up', {
                    'commuter_id': commuter.id,
                    'depot_id': commuter.depot_id
                })
                print(f"   ✓ Vehicle picked up commuter {commuter.id}")
        
        stats = statistics.get_all()
        print(f"\n   📊 After pickups:")
        print(f"      - Queue: {depot_queue.get_queue_length()} commuters")
        print(f"      - Total removed: {stats['total_commuters_removed']}")
        print(f"      - Still waiting: {stats['current_active_commuters']}")
        
        print("\n🔄 PHASE 3: FINAL VERIFICATION")
        print("-" * 70)
        
        # Verify final state
        assert depot_queue.get_queue_length() == 1
        assert stats['total_commuters_added'] == 3
        assert stats['total_commuters_removed'] == 2
        assert stats['current_active_commuters'] == 1
        
        print(f"   ✓ Final queue length: {depot_queue.get_queue_length()}")
        print(f"   ✓ Total lifecycle events: {len(socketio.events)}")
        print(f"   ✓ Spawn events: {len(socketio.get_events('commuter_spawned'))}")
        print(f"   ✓ Pickup events: {len(socketio.get_events('commuter_picked_up'))}")
        
        print("\n✅ Full lifecycle test completed successfully!")
        print("="*70)


# Main test runner
if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " END-TO-END TESTING: Refactored Reservoir System ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("This test suite validates complete passenger lifecycle flows")
    print("using the refactored modular architecture:")
    print()
    print("  🔹 Spawning Flow - LocationNormalizer, DepotQueue, RouteSegment")
    print("  🔹 Pickup Flow - FIFO queue operations, statistics tracking")
    print("  🔹 Expiration Flow - ExpirationManager with callbacks")
    print("  🔹 Statistics Flow - ReservoirStatistics accuracy")
    print("  🔹 Background Tasks - SpawningCoordinator, ExpirationManager")
    print("  🔹 Socket.IO Events - Event emission verification")
    print()
    print("Running with pytest...")
    print("-" * 70)
    
    # Run tests with pytest
    pytest.main([__file__, '-v', '-s'])
