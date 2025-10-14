# Test Directory README

This directory contains tests for the commuter service package.

## Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── pytest.ini                  # Pytest configuration
│
├── unit/                       # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_constants.py       # Tests for constants module
│   ├── test_geo_utils.py       # Tests for geographic utilities
│   └── ...                     # Additional unit tests
│
├── integration/                # Integration tests (may require services)
│   ├── __init__.py
│   └── ...                     # Integration test files
│
└── fixtures/                   # Shared test data and utilities
    ├── __init__.py
    └── ...                     # Fixture files
```

## Running Tests

### Run all tests:
```bash
pytest commuter_service/tests/ -v
```

### Run only unit tests:
```bash
pytest commuter_service/tests/unit/ -v
```

### Run only integration tests:
```bash
pytest commuter_service/tests/integration/ -v
```

### Run specific test file:
```bash
pytest commuter_service/tests/unit/test_geo_utils.py -v
```

### Run specific test class:
```bash
pytest commuter_service/tests/unit/test_geo_utils.py::TestHaversineDistance -v
```

### Run specific test method:
```bash
pytest commuter_service/tests/unit/test_geo_utils.py::TestHaversineDistance::test_zero_distance_same_point -v
```

### Run with coverage:
```bash
pytest commuter_service/tests/ --cov=commuter_service --cov-report=html
```

### Run tests matching a pattern:
```bash
pytest commuter_service/tests/ -k "distance" -v
```

## Test Markers

Tests can be marked with pytest markers for selective running:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.requires_socketio` - Needs Socket.IO server
- `@pytest.mark.requires_strapi` - Needs Strapi API

### Run only fast unit tests:
```bash
pytest -m "unit and not slow" -v
```

### Run tests that don't require external services:
```bash
pytest -m "not requires_socketio and not requires_strapi" -v
```

## Writing Tests

### Unit Test Example:
```python
import pytest
from commuter_service.geo_utils import haversine_distance

class TestHaversineDistance:
    def test_zero_distance(self):
        """Test distance from point to itself"""
        distance = haversine_distance(13.0, -59.0, 13.0, -59.0)
        assert distance == 0.0
```

### Async Test Example:
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async function"""
    result = await some_async_function()
    assert result is not None
```

### Using Fixtures:
```python
def test_with_fixture(test_coordinates):
    """Test using shared fixture"""
    lat = test_coordinates["lat"]
    lon = test_coordinates["lon"]
    assert lat is not None
```

## Test Coverage

Aim for:
- **80%+** overall code coverage
- **90%+** for critical modules (geo_utils, reservoirs)
- **100%** for constants and configuration

Check coverage report:
```bash
pytest --cov=commuter_service --cov-report=term-missing
```

## Continuous Integration

These tests should be run in CI/CD pipeline before merging:
1. All unit tests must pass
2. Coverage must meet minimum threshold
3. No linting errors

## Notes

- Keep unit tests fast (< 100ms each)
- Mock external dependencies in unit tests
- Use integration tests for end-to-end flows
- Add docstrings to all test methods
- Use descriptive test names
