"""
Unit Tests for SpawningCoordinator
===================================

Tests automatic passenger spawning coordination.

Test Coverage:
- Coordinator initialization
- Start/stop lifecycle
- Spawn generation and processing
- Callback invocation
- Configuration updates
- Statistics tracking
- Error handling
"""

import pytest
import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from commuter_service.spawning_coordinator import SpawningCoordinator


class MockSpawner:
    """Mock PoissonGeoJSONSpawner for testing"""
    
    def __init__(self, spawn_requests=None):
        self.spawn_requests = spawn_requests or []
        self.generate_calls = []
    
    async def generate_poisson_spawn_requests(
        self,
        current_time: datetime,
        time_window_minutes: float
    ):
        """Mock spawn request generation"""
        self.generate_calls.append({
            'time': current_time,
            'window': time_window_minutes
        })
        return self.spawn_requests


@pytest.fixture
def logger():
    """Create test logger"""
    return logging.getLogger("test_spawning")


@pytest.fixture
def mock_spawner():
    """Create mock spawner"""
    return MockSpawner()


@pytest.fixture
def spawn_callback():
    """Create mock spawn callback"""
    return AsyncMock()


@pytest.fixture
def coordinator(mock_spawner, spawn_callback, logger):
    """Create basic spawning coordinator"""
    return SpawningCoordinator(
        spawner=mock_spawner,
        spawn_interval=0.1,  # Fast for testing
        time_window_minutes=5.0,
        on_spawn_callback=spawn_callback,
        logger=logger
    )


class TestInitialization:
    """Test SpawningCoordinator initialization"""
    
    def test_initialization(self, mock_spawner, spawn_callback, logger):
        """Test coordinator initializes with correct defaults"""
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=30.0,
            time_window_minutes=10.0,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        assert coordinator.spawner == mock_spawner
        assert coordinator.spawn_interval == 30.0
        assert coordinator.time_window_minutes == 10.0
        assert coordinator.on_spawn_callback == spawn_callback
        assert coordinator.logger == logger
        assert coordinator.running is False
        assert coordinator.task is None
        assert coordinator.total_spawned == 0
        assert coordinator.total_failed == 0
    
    def test_default_logger(self, mock_spawner, spawn_callback):
        """Test coordinator creates default logger if none provided"""
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=30.0,
            on_spawn_callback=spawn_callback
        )
        
        assert coordinator.logger is not None
        assert isinstance(coordinator.logger, logging.Logger)


class TestStartStop:
    """Test start/stop lifecycle"""
    
    @pytest.mark.asyncio
    async def test_start(self, coordinator):
        """Test starting the coordinator"""
        await coordinator.start()
        
        assert coordinator.running is True
        assert coordinator.task is not None
        assert isinstance(coordinator.task, asyncio.Task)
        
        # Cleanup
        await coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_stop(self, coordinator):
        """Test stopping the coordinator"""
        await coordinator.start()
        await coordinator.stop()
        
        assert coordinator.running is False
        assert coordinator.task is None
    
    @pytest.mark.asyncio
    async def test_start_twice_raises_error(self, coordinator):
        """Test that starting twice raises RuntimeError"""
        await coordinator.start()
        
        with pytest.raises(RuntimeError, match="already running"):
            await coordinator.start()
        
        await coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, coordinator):
        """Test that stopping when not running is safe"""
        # Should not raise error
        await coordinator.stop()
        
        assert coordinator.running is False
    
    @pytest.mark.asyncio
    async def test_is_running(self, coordinator):
        """Test is_running method"""
        assert coordinator.is_running() is False
        
        await coordinator.start()
        assert coordinator.is_running() is True
        
        await coordinator.stop()
        assert coordinator.is_running() is False


class TestGenerateAndProcessSpawns:
    """Test spawn generation and processing"""
    
    @pytest.mark.asyncio
    async def test_generate_with_spawn_requests(
        self,
        mock_spawner,
        spawn_callback,
        logger
    ):
        """Test generating spawn requests"""
        # Set up spawner to return spawn requests
        mock_spawner.spawn_requests = [
            {'depot_id': 'D001', 'route_id': 'R1', 'destination': (13.0, -59.0)},
            {'depot_id': 'D002', 'route_id': 'R2', 'destination': (13.1, -59.1)},
        ]
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        count = await coordinator.generate_and_process_spawns()
        
        assert count == 2
        assert spawn_callback.call_count == 2
    
    @pytest.mark.asyncio
    async def test_callback_receives_spawn_requests(
        self,
        mock_spawner,
        logger
    ):
        """Test that callback receives spawn request data"""
        received_requests = []
        
        async def track_requests(request):
            received_requests.append(request)
        
        mock_spawner.spawn_requests = [
            {'depot_id': 'D001', 'route_id': 'R1'},
            {'depot_id': 'D002', 'route_id': 'R2'},
        ]
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=track_requests,
            logger=logger
        )
        
        await coordinator.generate_and_process_spawns()
        
        assert len(received_requests) == 2
        assert received_requests[0]['depot_id'] == 'D001'
        assert received_requests[1]['depot_id'] == 'D002'
    
    @pytest.mark.asyncio
    async def test_empty_spawn_requests(
        self,
        mock_spawner,
        spawn_callback,
        logger
    ):
        """Test with no spawn requests"""
        mock_spawner.spawn_requests = []
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        count = await coordinator.generate_and_process_spawns()
        
        assert count == 0
        assert spawn_callback.call_count == 0
    
    @pytest.mark.asyncio
    async def test_spawner_receives_parameters(
        self,
        mock_spawner,
        spawn_callback,
        logger
    ):
        """Test that spawner receives correct parameters"""
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            time_window_minutes=10.0,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        test_time = datetime(2025, 10, 14, 12, 0, 0)
        await coordinator.generate_and_process_spawns(current_time=test_time)
        
        assert len(mock_spawner.generate_calls) == 1
        call = mock_spawner.generate_calls[0]
        assert call['time'] == test_time
        assert call['window'] == 10.0
    
    @pytest.mark.asyncio
    async def test_callback_error_handling(self, mock_spawner, logger):
        """Test that callback errors are caught and logged"""
        # Callback that raises error
        async def failing_callback(request):
            raise ValueError("Callback error")
        
        mock_spawner.spawn_requests = [
            {'depot_id': 'D001'},
            {'depot_id': 'D002'},
        ]
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=failing_callback,
            logger=logger
        )
        
        # Should not raise, just log errors
        count = await coordinator.generate_and_process_spawns()
        
        assert count == 2  # Still generated 2 requests
        assert coordinator.total_failed == 2
        assert coordinator.total_spawned == 0
    
    @pytest.mark.asyncio
    async def test_spawner_error_handling(self, spawn_callback, logger):
        """Test handling errors from spawner"""
        class FailingSpawner:
            async def generate_poisson_spawn_requests(self, current_time, time_window_minutes):
                raise RuntimeError("Spawner error")
        
        coordinator = SpawningCoordinator(
            spawner=FailingSpawner(),
            spawn_interval=0.1,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        count = await coordinator.generate_and_process_spawns()
        
        assert count == 0


class TestStatisticsTracking:
    """Test statistics tracking"""
    
    @pytest.mark.asyncio
    async def test_stats_initial_state(self, coordinator):
        """Test initial statistics"""
        stats = coordinator.get_stats()
        
        assert stats['running'] is False
        assert stats['spawn_interval'] == 0.1
        assert stats['time_window_minutes'] == 5.0
        assert stats['total_spawned'] == 0
        assert stats['total_failed'] == 0
        assert stats['success_rate'] == 0.0
    
    @pytest.mark.asyncio
    async def test_stats_after_spawning(
        self,
        mock_spawner,
        spawn_callback,
        logger
    ):
        """Test statistics after successful spawning"""
        mock_spawner.spawn_requests = [
            {'depot_id': 'D001'},
            {'depot_id': 'D002'},
            {'depot_id': 'D003'},
        ]
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        await coordinator.generate_and_process_spawns()
        
        stats = coordinator.get_stats()
        
        assert stats['total_spawned'] == 3
        assert stats['total_failed'] == 0
        assert stats['success_rate'] == 1.0
    
    @pytest.mark.asyncio
    async def test_stats_with_failures(self, mock_spawner, logger):
        """Test statistics with some failures"""
        call_count = 0
        
        async def sometimes_fails(request):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Failed")
        
        mock_spawner.spawn_requests = [
            {'depot_id': 'D001'},
            {'depot_id': 'D002'},  # Will fail
            {'depot_id': 'D003'},
        ]
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=sometimes_fails,
            logger=logger
        )
        
        await coordinator.generate_and_process_spawns()
        
        stats = coordinator.get_stats()
        
        assert stats['total_spawned'] == 2
        assert stats['total_failed'] == 1
        assert stats['success_rate'] == 2.0 / 3.0
    
    @pytest.mark.asyncio
    async def test_reset_stats(self, coordinator):
        """Test resetting statistics"""
        coordinator.total_spawned = 10
        coordinator.total_failed = 2
        
        coordinator.reset_stats()
        
        assert coordinator.total_spawned == 0
        assert coordinator.total_failed == 0


class TestConfigurationUpdates:
    """Test updating configuration"""
    
    def test_update_spawn_interval(self, coordinator):
        """Test updating spawn interval"""
        coordinator.update_spawn_interval(60.0)
        
        assert coordinator.spawn_interval == 60.0
    
    def test_update_time_window(self, coordinator):
        """Test updating time window"""
        coordinator.update_time_window(15.0)
        
        assert coordinator.time_window_minutes == 15.0


class TestBackgroundTask:
    """Test background task behavior"""
    
    @pytest.mark.asyncio
    async def test_task_runs_periodically(
        self,
        mock_spawner,
        spawn_callback,
        logger
    ):
        """Test that spawning task runs periodically"""
        mock_spawner.spawn_requests = [
            {'depot_id': 'D001'},
        ]
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        await coordinator.start()
        
        # Wait for multiple spawn cycles
        await asyncio.sleep(0.35)
        
        await coordinator.stop()
        
        # Should have run multiple times
        assert spawn_callback.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_task_cancellation_on_stop(self, coordinator):
        """Test that background task is cancelled on stop"""
        await coordinator.start()
        task = coordinator.task
        
        await coordinator.stop()
        
        assert task.cancelled() or task.done()
    
    @pytest.mark.asyncio
    async def test_running_state_during_execution(
        self,
        mock_spawner,
        spawn_callback,
        logger
    ):
        """Test running state is correct during execution"""
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=spawn_callback,
            logger=logger
        )
        
        await coordinator.start()
        
        stats = coordinator.get_stats()
        assert stats['running'] is True
        
        await coordinator.stop()
        
        stats = coordinator.get_stats()
        assert stats['running'] is False


class TestWithoutCallback:
    """Test coordinator behavior without callback"""
    
    @pytest.mark.asyncio
    async def test_no_callback_provided(self, mock_spawner, logger):
        """Test coordinator works without callback (just generates)"""
        mock_spawner.spawn_requests = [
            {'depot_id': 'D001'},
            {'depot_id': 'D002'},
        ]
        
        coordinator = SpawningCoordinator(
            spawner=mock_spawner,
            spawn_interval=0.1,
            on_spawn_callback=None,  # No callback
            logger=logger
        )
        
        count = await coordinator.generate_and_process_spawns()
        
        # Should generate but not process
        assert count == 2
        assert coordinator.total_spawned == 0  # Nothing spawned (no callback)
