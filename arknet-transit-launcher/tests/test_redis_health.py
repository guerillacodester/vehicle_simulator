"""
Tests for Redis Health Checker
================================
"""

import asyncio
from unittest.mock import AsyncMock, patch

try:
    import pytest
except ImportError:
    pytest = None

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from arknet_transit_launcher.health.redis_health import (
    RedisHealthChecker,
    RedisHealthStatus
)


@pytest.mark.asyncio
async def test_redis_not_configured():
    """Test Redis not configured"""
    checker = RedisHealthChecker(None)
    
    result = await checker.check_health()
    
    assert result["name"] == "redis"
    assert result["state"] == RedisHealthStatus.NOT_CONFIGURED.value
    assert result["latency_ms"] is None
    assert "not configured" in result["message"].lower()


@pytest.mark.asyncio
async def test_redis_healthy():
    """Test Redis healthy state"""
    checker = RedisHealthChecker("redis://localhost:6379", latency_threshold_ms=100.0)
    
    with patch('arknet_transit_launcher.health.redis_health.aioredis.from_url') as mock_redis:
        # Create mock client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        # Make from_url awaitable and return the mock client
        async def create_client(*args, **kwargs):
            return mock_client
        mock_redis.side_effect = create_client
        
        result = await checker.check_health()
        
        assert result["name"] == "redis"
        assert result["state"] == RedisHealthStatus.HEALTHY.value
        assert "connected" in result["message"].lower()
        assert result["latency_ms"] < 100.0
        assert result["host"] == "localhost"
        assert result["port"] == 6379
        assert "Connected" in result["message"]


@pytest.mark.asyncio
async def test_redis_high_latency():
    """Test Redis unhealthy due to high latency"""
    checker = RedisHealthChecker("redis://localhost:6379", latency_threshold_ms=1.0)
    
    with patch('arknet_transit_launcher.health.redis_health.aioredis.from_url') as mock_redis:
        mock_client = AsyncMock()
        
        async def slow_ping():
            await asyncio.sleep(0.002)  # 2ms delay
            return True
        
        mock_client.ping = slow_ping
        # Make from_url awaitable and return the mock client
        async def create_client(*args, **kwargs):
            return mock_client
        mock_redis.side_effect = create_client
        
        result = await checker.check_health()
        
        assert result["name"] == "redis"
        assert result["state"] == RedisHealthStatus.UNHEALTHY.value
        assert "latency" in result["message"].lower()


@pytest.mark.asyncio
async def test_redis_connection_timeout():
    """Test Redis unreachable (timeout)"""
    checker = RedisHealthChecker("redis://invalid:6379")
    
    with patch('arknet_transit_launcher.health.redis_health.aioredis.from_url') as mock_redis:
        mock_redis.side_effect = asyncio.TimeoutError()
        
        result = await checker.check_health()
        
        assert result["name"] == "redis"
        assert result["state"] == RedisHealthStatus.UNREACHABLE.value
        assert "timeout" in result["message"].lower()


@pytest.mark.asyncio
async def test_redis_connection_error():
    """Test Redis connection error"""
    checker = RedisHealthChecker("redis://localhost:6379")
    
    with patch('arknet_transit_launcher.health.redis_health.aioredis.from_url') as mock_redis:
        mock_redis.side_effect = ConnectionError("Connection refused")
        
        result = await checker.check_health()
        
        assert result["name"] == "redis"
        assert result["state"] == RedisHealthStatus.UNHEALTHY.value
        assert "failed" in result["message"].lower()


@pytest.mark.asyncio
async def test_redis_url_parsing():
    """Test Redis URL parsing"""
    checker = RedisHealthChecker("redis://example.com:6380")
    
    host, port = checker._parse_redis_url("redis://example.com:6380")
    
    assert host == "example.com"
    assert port == 6380


@pytest.mark.asyncio
async def test_redis_url_parsing_default_port():
    """Test Redis URL parsing with default port"""
    checker = RedisHealthChecker("redis://example.com")
    
    host, port = checker._parse_redis_url("redis://example.com")
    
    assert host == "example.com"
    assert port == 6379


@pytest.mark.asyncio
async def test_redis_close():
    """Test closing Redis connection"""
    checker = RedisHealthChecker("redis://localhost:6379")
    
    with patch('arknet_transit_launcher.health.redis_health.aioredis.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.close = AsyncMock()
        # Make from_url awaitable and return the mock client
        async def create_client(*args, **kwargs):
            return mock_client
        mock_redis.side_effect = create_client
        
        # First call creates the client
        await checker.check_health()
        
        # Close should call client.close()
        await checker.close()
        mock_client.close.assert_called_once()
