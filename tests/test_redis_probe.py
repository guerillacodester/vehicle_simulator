import pytest

from launcher.health import redis_probe


def test_redis_probe_returns_keys():
    """Smoke test: redis_probe returns the expected dictionary keys."""
    result = redis_probe(host='127.0.0.1', port=6379, timeout=0.2)
    assert isinstance(result, dict)
    # Ensure expected keys exist
    for k in ('listening', 'on_path', 'system_service', 'details'):
        assert k in result
    assert isinstance(result['details'], list)