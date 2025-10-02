# Migration Archive

This folder contains files that were used during the development and migration phases of the Arknet Transit System but are no longer needed for day-to-day operations.

## Contents

### Migration Scripts & Analysis
- **Migration Scripts**: All `migrate_*.py` files used for data migration from PostgreSQL to Strapi
- **Analysis Scripts**: All `analyze_*.py` and `comprehensive_*.py` files used for data analysis
- **Setup Scripts**: Step-by-step migration setup files (`step*.py`)
- **Migration Runners**: `run_*.py` files that executed migrations in batch

### Documentation
- **MIGRATION_REPORT.md**: Final migration completion report
- **MIGRATION_TODO.md**: Migration task tracking (completed)
- **PASSENGER_MICROSERVICE_MIGRATION_PLAN.md**: Original migration planning document

### Test Files
- **test_comprehensive_spawning.py**: Tests for alternative spawning systems (replaced by commuter reservoir)
- **test_poisson_geojson_spawning.py**: Tests for GeoJSON-based spawning (replaced by commuter reservoir)  
- **ultimate_simulator_test.py**: Large integration test (replaced by targeted tests)
- **test_limited_migration.py**: Migration validation tests

### Migration Results
- **data_migration.log**: Migration execution logs
- **geometry_analysis_results.json**: Route geometry analysis results
- **route_shapes_content_type.json**: Strapi content type definitions

## Status

All files in this archive are **COMPLETED** and **NO LONGER NEEDED** for system operation. They are preserved for:
- Historical reference
- Debugging migration issues (if they arise)
- Understanding the migration process for future projects

## Current System

The current active system uses:
- **Commuter Reservoir System** (`commuter_service/commuter_reservoir.py`)
- **Strapi API Integration** (default strategy)
- **GTFS-Compliant Data Structure** (migrated successfully)

## Safe to Delete

These files can be safely deleted if disk space is needed, as the migration is complete and successful.