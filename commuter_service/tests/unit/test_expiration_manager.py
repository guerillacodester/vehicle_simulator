"""
Unit Tests for ExpirationManager
=================================

Tests background commuter expiration management.

Test Coverage:
- Manager initialization
- Start/stop lifecycle
- Expiration detection
- Callback invocation
- Timeout configuration
- ReservoirExpirationManager specialization
"""

import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from commuter_service.expiration_manager import (
    ExpirationManager,
    ReservoirExpirationManager
)


class MockCommuter:
    """Mock commuter for testing"""
    def __init__(self, person_id: str, spawn_time: datetime):
        self.person_id = person_id
        self.spawn_time = spawn_time


@pytest.fixture
def logger():
    """Create test logger"""
    return logging.getLogger("test_expiration")


@pytest.fixture
def expiration_callback():
    """Create mock expiration callback"""
    return AsyncMock()


@pytest.fixture
def manager(expiration_callback, logger):
    """Create basic expiration manager"""
    return ExpirationManager(
        check_interval=0.1,  # Fast for testing
        expiration_timeout=1.0,  # 1 second
        on_expire_callback=expiration_callback,
        logger=logger
    )


class TestInitialization:
    """Test ExpirationManager initialization"""
    
    def test_initialization(self, expiration_callback, logger):
        """Test manager initializes with correct defaults"""
        manager = ExpirationManager(
            check_interval=10.0,
            expiration_timeout=300.0,
            on_expire_callback=expiration_callback,
            logger=logger
        )
        
        assert manager.check_interval == 10.0
        assert manager.expiration_timeout == timedelta(seconds=300.0)
        assert manager.on_expire_callback == expiration_callback
        assert manager.logger == logger
        assert manager.running is False
        assert manager.task is None
    
    def test_default_logger(self, expiration_callback):
        """Test manager creates default logger if none provided"""
        manager = ExpirationManager(
            check_interval=10.0,
            expiration_timeout=300.0,
            on_expire_callback=expiration_callback
        )
        
        assert manager.logger is not None
        assert isinstance(manager.logger, logging.Logger)


class TestStartStop:
    """Test start/stop lifecycle"""
    
    @pytest.mark.asyncio
    async def test_start(self, manager):
        """Test starting the manager"""
        await manager.start()
        
        assert manager.running is True
        assert manager.task is not None
        assert isinstance(manager.task, asyncio.Task)
        
        # Cleanup
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_stop(self, manager):
        """Test stopping the manager"""
        await manager.start()
        await manager.stop()
        
        assert manager.running is False
        assert manager.task is None
    
    @pytest.mark.asyncio
    async def test_start_twice_raises_error(self, manager):
        """Test that starting twice raises RuntimeError"""
        await manager.start()
        
        with pytest.raises(RuntimeError, match="already running"):
            await manager.start()
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, manager):
        """Test that stopping when not running is safe"""
        # Should not raise error
        await manager.stop()
        
        assert manager.running is False
    
    @pytest.mark.asyncio
    async def test_is_running(self, manager):
        """Test is_running method"""
        assert manager.is_running() is False
        
        await manager.start()
        assert manager.is_running() is True
        
        await manager.stop()
        assert manager.is_running() is False


class TestCheckAndExpire:
    """Test check_and_expire functionality"""
    
    @pytest.mark.asyncio
    async def test_expire_old_commuters(self, manager, expiration_callback):
        """Test expiring old commuters"""
        # Create commuters - some old, some new
        now = datetime.now()
        commuters = {
            "C001": MockCommuter("C001", now - timedelta(seconds=5)),  # Old (> 1s)
            "C002": MockCommuter("C002", now - timedelta(seconds=0.5)),  # New
            "C003": MockCommuter("C003", now - timedelta(seconds=3)),  # Old
        }
        
        expired_ids = await manager.check_and_expire(commuters)
        
        # Should expire C001 and C003
        assert len(expired_ids) == 2
        assert "C001" in expired_ids
        assert "C003" in expired_ids
        assert "C002" not in expired_ids
    
    @pytest.mark.asyncio
    async def test_callback_called_for_expired(self, manager, expiration_callback):
        """Test that callback is called for each expired commuter"""
        now = datetime.now()
        commuters = {
            "C001": MockCommuter("C001", now - timedelta(seconds=2)),
            "C002": MockCommuter("C002", now - timedelta(seconds=3)),
        }
        
        await manager.check_and_expire(commuters)
        
        # Callback should be called twice
        assert expiration_callback.call_count == 2
    
    @pytest.mark.asyncio
    async def test_no_expirations(self, manager, expiration_callback):
        """Test when no commuters have expired"""
        now = datetime.now()
        commuters = {
            "C001": MockCommuter("C001", now),
            "C002": MockCommuter("C002", now),
        }
        
        expired_ids = await manager.check_and_expire(commuters)
        
        assert len(expired_ids) == 0
        assert expiration_callback.call_count == 0
    
    @pytest.mark.asyncio
    async def test_empty_commuters_dict(self, manager):
        """Test with empty commuters dictionary"""
        expired_ids = await manager.check_and_expire({})
        
        assert len(expired_ids) == 0
    
    @pytest.mark.asyncio
    async def test_custom_get_spawn_time(self, expiration_callback, logger):
        """Test using custom spawn time getter"""
        manager = ExpirationManager(
            check_interval=0.1,
            expiration_timeout=1.0,
            on_expire_callback=expiration_callback,
            logger=logger
        )
        
        # Commuter with different attribute name
        class CustomCommuter:
            def __init__(self, person_id, created_at):
                self.person_id = person_id
                self.created_at = created_at
        
        now = datetime.now()
        commuters = {
            "C001": CustomCommuter("C001", now - timedelta(seconds=2)),
        }
        
        # Use custom getter
        expired_ids = await manager.check_and_expire(
            commuters,
            get_spawn_time=lambda c: c.created_at
        )
        
        assert len(expired_ids) == 1
        assert "C001" in expired_ids
    
    @pytest.mark.asyncio
    async def test_missing_spawn_time(self, manager, logger):
        """Test handling commuter without spawn_time"""
        class NoSpawnTimeCommuter:
            def __init__(self, person_id):
                self.person_id = person_id
        
        commuters = {
            "C001": NoSpawnTimeCommuter("C001"),
        }
        
        expired_ids = await manager.check_and_expire(commuters)
        
        # Should not expire (and log warning)
        assert len(expired_ids) == 0
    
    @pytest.mark.asyncio
    async def test_callback_error_handling(self, logger):
        """Test that callback errors are caught and logged"""
        # Callback that raises error
        async def failing_callback(commuter):
            raise ValueError("Callback error")
        
        manager = ExpirationManager(
            check_interval=0.1,
            expiration_timeout=1.0,
            on_expire_callback=failing_callback,
            logger=logger
        )
        
        now = datetime.now()
        commuters = {
            "C001": MockCommuter("C001", now - timedelta(seconds=2)),
        }
        
        # Should not raise, just log error
        expired_ids = await manager.check_and_expire(commuters)
        
        assert len(expired_ids) == 1  # Still detected as expired


class TestConfigurationUpdates:
    """Test updating configuration"""
    
    def test_update_timeout(self, manager):
        """Test updating expiration timeout"""
        manager.update_timeout(600.0)
        
        assert manager.expiration_timeout == timedelta(seconds=600.0)
    
    def test_update_check_interval(self, manager):
        """Test updating check interval"""
        manager.update_check_interval(30.0)
        
        assert manager.check_interval == 30.0


class TestReservoirExpirationManager:
    """Test ReservoirExpirationManager specialization"""
    
    @pytest.fixture
    def commuters_dict(self):
        """Create mock commuters dictionary"""
        now = datetime.now()
        return {
            "C001": MockCommuter("C001", now - timedelta(seconds=5)),
            "C002": MockCommuter("C002", now - timedelta(seconds=0.5)),
            "C003": MockCommuter("C003", now - timedelta(seconds=3)),
        }
    
    @pytest.fixture
    def on_expire_callback(self):
        """Create mock on_expire callback"""
        return AsyncMock()
    
    @pytest.fixture
    def reservoir_manager(self, commuters_dict, on_expire_callback, logger):
        """Create reservoir expiration manager"""
        return ReservoirExpirationManager(
            get_commuters=lambda: commuters_dict,
            on_expire=on_expire_callback,
            check_interval=0.1,
            expiration_timeout=1.0,
            logger=logger
        )
    
    @pytest.mark.asyncio
    async def test_reservoir_manager_initialization(self, reservoir_manager):
        """Test reservoir manager initializes correctly"""
        assert reservoir_manager.check_interval == 0.1
        assert reservoir_manager.expiration_timeout == timedelta(seconds=1.0)
        assert reservoir_manager.running is False
    
    @pytest.mark.asyncio
    async def test_reservoir_manager_expires_commuters(
        self,
        reservoir_manager,
        on_expire_callback
    ):
        """Test reservoir manager detects and expires commuters"""
        await reservoir_manager.start()
        
        # Wait for expiration check to run
        await asyncio.sleep(0.3)
        
        await reservoir_manager.stop()
        
        # Should have called on_expire for expired commuters (C001, C003)
        assert on_expire_callback.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_reservoir_manager_on_expire_gets_id(
        self,
        commuters_dict,
        logger
    ):
        """Test that on_expire callback receives commuter_id and commuter"""
        received_calls = []
        
        async def track_calls(commuter_id, commuter):
            received_calls.append((commuter_id, commuter))
        
        manager = ReservoirExpirationManager(
            get_commuters=lambda: commuters_dict,
            on_expire=track_calls,
            check_interval=0.1,
            expiration_timeout=1.0,
            logger=logger
        )
        
        await manager.start()
        await asyncio.sleep(0.3)
        await manager.stop()
        
        # Should have received calls with IDs
        assert len(received_calls) >= 2
        
        # Check that IDs are correct
        ids = [call[0] for call in received_calls]
        assert "C001" in ids or "C003" in ids
    
    @pytest.mark.asyncio
    async def test_custom_spawn_time_getter(self, logger):
        """Test reservoir manager with custom spawn time getter"""
        class CustomCommuter:
            def __init__(self, person_id, created):
                self.person_id = person_id
                self.created = created
        
        now = datetime.now()
        commuters = {
            "C001": CustomCommuter("C001", now - timedelta(seconds=2)),
        }
        
        on_expire = AsyncMock()
        
        manager = ReservoirExpirationManager(
            get_commuters=lambda: commuters,
            on_expire=on_expire,
            check_interval=0.1,
            expiration_timeout=1.0,
            get_spawn_time=lambda c: c.created,
            logger=logger
        )
        
        await manager.start()
        await asyncio.sleep(0.3)
        await manager.stop()
        
        # Should have expired C001
        assert on_expire.call_count >= 1


class TestBackgroundTask:
    """Test background task behavior"""
    
    @pytest.mark.asyncio
    async def test_task_runs_periodically(self, logger):
        """Test that expiration task runs periodically"""
        check_count = 0
        
        async def count_checks(commuter):
            nonlocal check_count
            check_count += 1
        
        now = datetime.now()
        commuters = {
            "C001": MockCommuter("C001", now - timedelta(seconds=5)),
        }
        
        manager = ReservoirExpirationManager(
            get_commuters=lambda: commuters,
            on_expire=lambda cid, c: count_checks(c),
            check_interval=0.1,
            expiration_timeout=1.0,
            logger=logger
        )
        
        await manager.start()
        
        # Wait for multiple check cycles
        await asyncio.sleep(0.35)
        
        await manager.stop()
        
        # Should have run multiple times
        assert check_count >= 2
    
    @pytest.mark.asyncio
    async def test_task_cancellation_on_stop(self, manager):
        """Test that background task is cancelled on stop"""
        await manager.start()
        task = manager.task
        
        await manager.stop()
        
        assert task.cancelled() or task.done()
