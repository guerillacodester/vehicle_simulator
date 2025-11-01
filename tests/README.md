# Tests Directory

Organized test suite for the vehicle simulator project.

## Structure

```
tests/
├── geospatial/           # Database & PostGIS validation tests
│   ├── test_admin_import.py
│   ├── test_amenity_import.py
│   ├── test_geospatial_api.py
│   ├── test_highway_import.py
│   ├── test_landuse_import.py
│   ├── requirements.txt
│   └── legacy_README.md
│
├── integration/          # Integration tests for APIs and services
│   ├── test_geospatial_endpoints.py
│   ├── test_commuter_spawning.py
│   └── debug_route_spawner.py
│
└── validation/           # Validation scripts for spawn models
    ├── validate_hybrid_spawn_model.py     # Main hybrid model validation
    ├── test_spawn_calculator_kernel.py    # Kernel unit tests
    ├── validate_spawn_rates.py
    └── validate_weighted_spawn.py
```

## Integration Tests

Located in `integration/` - tests that interact with live services:

- **test_geospatial_endpoints.py** - Tests geospatial API endpoints
- **test_commuter_spawning.py** - Tests commuter spawning integration
- **debug_route_spawner.py** - Debug harness for route spawner

## Geospatial/Database Tests

Located in `geospatial/` - legacy tests for PostGIS database validation:

- **test_admin_import.py** - Administrative boundary import validation
- **test_amenity_import.py** - POI/amenity import validation
- **test_geospatial_api.py** - Geospatial service API integration tests
- **test_highway_import.py** - Highway/road network import validation
- **test_landuse_import.py** - Landuse zone import validation

These tests verify OSM data imports into PostgreSQL/PostGIS are working correctly.

## Validation Scripts

Located in `validation/` - scripts that validate spawn model calculations:

- **validate_hybrid_spawn_model.py** - Validates hybrid spawn model with real data
- **test_spawn_calculator_kernel.py** - Quick tests for spawn calculator kernel
- **validate_spawn_rates.py** - Rate validation tests
- **validate_weighted_spawn.py** - Weighted spawn validation

## Running Tests

### Running Geospatial/Database Tests

```bash
# Install dependencies first
pip install -r tests/geospatial/requirements.txt

# Test database imports
python tests/geospatial/test_landuse_import.py
python tests/geospatial/test_highway_import.py
python tests/geospatial/test_amenity_import.py
python tests/geospatial/test_admin_import.py

# Test geospatial API
python tests/geospatial/test_geospatial_api.py
```

### Running Integration Tests

```bash
# Test geospatial endpoints
python tests/integration/test_geospatial_endpoints.py

# Test commuter spawning
python tests/integration/test_commuter_spawning.py
```

### Running Validation Scripts

```bash
# Validate hybrid spawn model
python tests/validation/validate_hybrid_spawn_model.py

# Quick kernel test
python tests/validation/test_spawn_calculator_kernel.py
```

## Component Tests

Component-specific tests are located in their respective directories:

- `commuter_simulator/tests/` - Commuter simulator unit tests
- `geospatial_service/tests/` - Geospatial service tests
