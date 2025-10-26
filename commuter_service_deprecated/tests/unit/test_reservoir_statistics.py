"""
Unit Tests for ReservoirStatistics
===================================

Tests thread-safe statistics tracking for reservoirs.

Test Coverage:
- Statistics initialization
- Increment operations (spawned, picked_up, expired)
- Thread safety (async operations)
- Statistics retrieval
- Logging
- Reset functionality
- Synchronous operations
"""

import pytest
import asyncio
import logging
from datetime import datetime
from io import StringIO

from commuter_service.reservoir_statistics import ReservoirStatistics


@pytest.fixture
def stats():
    """Create basic statistics tracker"""
    return ReservoirStatistics(name="Test_Reservoir")


@pytest.fixture
def logger_with_capture():
    """Create logger that captures output"""
    logger = logging.getLogger("test_stats")
    logger.setLevel(logging.INFO)
    
    # String buffer to capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    return logger, log_capture


class TestInitialization:
    """Test ReservoirStatistics initialization"""
    
    def test_initialization(self):
        """Test stats initialize with correct defaults"""
        stats = ReservoirStatistics(name="Depot_Speightstown")
        
        assert stats.name == "Depot_Speightstown"
        assert stats.total_spawned == 0
        assert stats.total_picked_up == 0
        assert stats.total_expired == 0
        assert isinstance(stats.created_at, datetime)
        assert hasattr(stats, '_lock')
    
    def test_custom_initial_values(self):
        """Test initialization with custom values"""
        stats = ReservoirStatistics(
            name="Route_1A",
            total_spawned=10,
            total_picked_up=5,
            total_expired=2
        )
        
        assert stats.name == "Route_1A"
        assert stats.total_spawned == 10
        assert stats.total_picked_up == 5
        assert stats.total_expired == 2


class TestIncrementOperations:
    """Test increment operations"""
    
    @pytest.mark.asyncio
    async def test_increment_spawned(self, stats):
        """Test incrementing spawned count"""
        await stats.increment_spawned()
        
        assert stats.total_spawned == 1
        assert stats.total_picked_up == 0
        assert stats.total_expired == 0
    
    @pytest.mark.asyncio
    async def test_increment_spawned_by_amount(self, stats):
        """Test incrementing spawned by specific amount"""
        await stats.increment_spawned(5)
        
        assert stats.total_spawned == 5
    
    @pytest.mark.asyncio
    async def test_increment_picked_up(self, stats):
        """Test incrementing picked_up count"""
        await stats.increment_picked_up()
        
        assert stats.total_spawned == 0
        assert stats.total_picked_up == 1
        assert stats.total_expired == 0
    
    @pytest.mark.asyncio
    async def test_increment_picked_up_by_amount(self, stats):
        """Test incrementing picked_up by specific amount"""
        await stats.increment_picked_up(3)
        
        assert stats.total_picked_up == 3
    
    @pytest.mark.asyncio
    async def test_increment_expired(self, stats):
        """Test incrementing expired count"""
        await stats.increment_expired()
        
        assert stats.total_spawned == 0
        assert stats.total_picked_up == 0
        assert stats.total_expired == 1
    
    @pytest.mark.asyncio
    async def test_increment_expired_by_amount(self, stats):
        """Test incrementing expired by specific amount"""
        await stats.increment_expired(2)
        
        assert stats.total_expired == 2
    
    @pytest.mark.asyncio
    async def test_multiple_increments(self, stats):
        """Test multiple increment operations"""
        await stats.increment_spawned(10)
        await stats.increment_picked_up(7)
        await stats.increment_expired(2)
        
        assert stats.total_spawned == 10
        assert stats.total_picked_up == 7
        assert stats.total_expired == 2


class TestGetStats:
    """Test statistics retrieval"""
    
    @pytest.mark.asyncio
    async def test_get_stats_empty(self, stats):
        """Test getting stats with no activity"""
        result = await stats.get_stats()
        
        assert result["name"] == "Test_Reservoir"
        assert result["total_spawned"] == 0
        assert result["total_picked_up"] == 0
        assert result["total_expired"] == 0
        assert result["waiting_count"] == 0
        assert "uptime_seconds" in result
        assert result["uptime_seconds"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_stats_with_activity(self, stats):
        """Test getting stats after activity"""
        await stats.increment_spawned(10)
        await stats.increment_picked_up(6)
        await stats.increment_expired(2)
        
        result = await stats.get_stats()
        
        assert result["total_spawned"] == 10
        assert result["total_picked_up"] == 6
        assert result["total_expired"] == 2
        # Waiting = spawned - picked_up - expired = 10 - 6 - 2 = 2
        assert result["waiting_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_stats_with_provided_waiting_count(self, stats):
        """Test getting stats with explicit waiting count"""
        await stats.increment_spawned(10)
        
        result = await stats.get_stats(waiting_count=5)
        
        assert result["waiting_count"] == 5  # Uses provided value
    
    @pytest.mark.asyncio
    async def test_uptime_increases(self, stats):
        """Test that uptime increases over time"""
        result1 = await stats.get_stats()
        
        await asyncio.sleep(0.1)  # Wait 100ms
        
        result2 = await stats.get_stats()
        
        assert result2["uptime_seconds"] > result1["uptime_seconds"]


class TestLogStats:
    """Test statistics logging"""
    
    @pytest.mark.asyncio
    async def test_log_stats(self, stats, logger_with_capture):
        """Test logging statistics"""
        logger, log_capture = logger_with_capture
        
        await stats.increment_spawned(5)
        await stats.increment_picked_up(3)
        await stats.increment_expired(1)
        
        await stats.log_stats(logger)
        
        log_output = log_capture.getvalue()
        
        assert "Test_Reservoir Stats:" in log_output
        assert "5 spawned" in log_output
        assert "3 picked up" in log_output
        assert "1 expired" in log_output
        assert "1 waiting" in log_output  # 5 - 3 - 1 = 1
        assert "Uptime:" in log_output
    
    @pytest.mark.asyncio
    async def test_log_stats_with_waiting_count(self, stats, logger_with_capture):
        """Test logging with explicit waiting count"""
        logger, log_capture = logger_with_capture
        
        await stats.log_stats(logger, waiting_count=10)
        
        log_output = log_capture.getvalue()
        
        assert "10 waiting" in log_output
    
    @pytest.mark.asyncio
    async def test_log_stats_custom_level(self, stats):
        """Test logging with custom level"""
        logger = logging.getLogger("test_custom_level")
        logger.setLevel(logging.DEBUG)
        
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        await stats.log_stats(logger, level=logging.DEBUG)
        
        log_output = log_capture.getvalue()
        assert "Test_Reservoir Stats:" in log_output


class TestReset:
    """Test reset functionality"""
    
    @pytest.mark.asyncio
    async def test_reset(self, stats):
        """Test resetting statistics"""
        # Add some activity
        await stats.increment_spawned(10)
        await stats.increment_picked_up(5)
        await stats.increment_expired(2)
        
        # Reset
        await stats.reset()
        
        # Check all counters are zero
        assert stats.total_spawned == 0
        assert stats.total_picked_up == 0
        assert stats.total_expired == 0
    
    @pytest.mark.asyncio
    async def test_reset_updates_created_at(self, stats):
        """Test that reset updates created_at timestamp"""
        original_created = stats.created_at
        
        await asyncio.sleep(0.1)  # Wait a bit
        
        await stats.reset()
        
        assert stats.created_at > original_created


class TestSynchronousOperations:
    """Test synchronous (non-async) operations"""
    
    def test_get_stats_sync(self, stats):
        """Test synchronous stats retrieval"""
        stats.increment_spawned_sync(5)
        stats.increment_picked_up_sync(3)
        
        result = stats.get_stats_sync()
        
        assert result["total_spawned"] == 5
        assert result["total_picked_up"] == 3
        assert result["waiting_count"] == 2
    
    def test_increment_spawned_sync(self, stats):
        """Test synchronous increment_spawned"""
        stats.increment_spawned_sync(10)
        
        assert stats.total_spawned == 10
    
    def test_increment_picked_up_sync(self, stats):
        """Test synchronous increment_picked_up"""
        stats.increment_picked_up_sync(5)
        
        assert stats.total_picked_up == 5
    
    def test_increment_expired_sync(self, stats):
        """Test synchronous increment_expired"""
        stats.increment_expired_sync(3)
        
        assert stats.total_expired == 3
    
    def test_sync_with_custom_count(self, stats):
        """Test synchronous operations with custom counts"""
        stats.increment_spawned_sync(10)
        stats.increment_picked_up_sync(7)
        stats.increment_expired_sync(2)
        
        result = stats.get_stats_sync()
        
        assert result["total_spawned"] == 10
        assert result["total_picked_up"] == 7
        assert result["total_expired"] == 2
        assert result["waiting_count"] == 1


class TestThreadSafety:
    """Test thread safety of async operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_increments(self, stats):
        """Test concurrent increment operations"""
        # Run 100 concurrent increments
        tasks = [stats.increment_spawned() for _ in range(100)]
        await asyncio.gather(*tasks)
        
        # Should have exactly 100 spawns (no race conditions)
        assert stats.total_spawned == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, stats):
        """Test concurrent mixed increment operations"""
        tasks = []
        
        # 50 spawns
        tasks.extend([stats.increment_spawned() for _ in range(50)])
        
        # 30 pickups
        tasks.extend([stats.increment_picked_up() for _ in range(30)])
        
        # 10 expirations
        tasks.extend([stats.increment_expired() for _ in range(10)])
        
        # Run all concurrently
        await asyncio.gather(*tasks)
        
        # Check totals
        assert stats.total_spawned == 50
        assert stats.total_picked_up == 30
        assert stats.total_expired == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_reads_and_writes(self, stats):
        """Test concurrent reads and writes"""
        async def writer():
            for _ in range(10):
                await stats.increment_spawned()
                await asyncio.sleep(0.001)
        
        async def reader():
            for _ in range(5):
                result = await stats.get_stats()
                assert isinstance(result, dict)
                await asyncio.sleep(0.002)
        
        # Run writers and readers concurrently
        await asyncio.gather(
            writer(),
            writer(),
            reader(),
            reader()
        )
        
        # Should have 20 total spawns (2 writers × 10 each)
        assert stats.total_spawned == 20
