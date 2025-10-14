# Quick Start: Running Tests

## ⚡ Prerequisites
```bash
pip install pytest pytest-asyncio pytest-cov
```

## 🚀 Run Tests

### All tests:
```bash
pytest commuter_service/tests/ -v
```

### Only unit tests:
```bash
pytest commuter_service/tests/unit/ -v
```

### Specific file:
```bash
pytest commuter_service/tests/unit/test_geo_utils.py -v
```

### With coverage:
```bash
pytest commuter_service/tests/ --cov=commuter_service --cov-report=html
```

## 📊 Expected Output

```
commuter_service/tests/unit/test_constants.py::TestEarthConstants::test_earth_radius_positive PASSED
commuter_service/tests/unit/test_constants.py::TestEarthConstants::test_earth_radius_reasonable PASSED
...
commuter_service/tests/unit/test_geo_utils.py::TestHaversineDistance::test_zero_distance_same_point PASSED
...

======================== 43 passed in 0.15s ========================
```

## 📁 Structure Created

```
tests/
├── conftest.py          # Shared fixtures (200+ lines)
├── pytest.ini           # Pytest configuration
├── README.md            # Full documentation
│
├── unit/                # 43 unit tests ready
│   ├── test_constants.py     (21 tests)
│   └── test_geo_utils.py     (22 tests)
│
├── integration/         # Ready for integration tests
└── fixtures/            # Ready for test data
```

## ✅ What's Ready

- ✅ 43 unit tests for constants and geo_utils
- ✅ Comprehensive pytest configuration
- ✅ Shared fixtures for all tests
- ✅ Mock objects for Socket.IO, Strapi, Database
- ✅ Async test support enabled
- ✅ Coverage reporting configured

See `TEST_DIRECTORY_CREATION_SUMMARY.md` for full details!
