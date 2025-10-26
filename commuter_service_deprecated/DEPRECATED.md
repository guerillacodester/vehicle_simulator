# ⚠️ DEPRECATED - DO NOT USE

This folder (`commuter_service_deprecated/`) contains the **old passenger spawning implementation** and is **no longer maintained**.

## Status: DEPRECATED (October 26, 2025)

### DO NOT USE THIS CODE FOR NEW DEVELOPMENT

## Migration Information

All functionality has been migrated to:

- **`commuter_simulator/`** - New architecture (Single Source of Truth pattern)

### Key Changes

1. **Geospatial Client**:
   - Old: `commuter_service/geospatial_client.py`
   - New: `commuter_simulator/infrastructure/geospatial/client.py`

2. **Tests**:
   - Old: `commuter_service/tests/`
   - New: `commuter_simulator/tests/`

3. **Architecture**:
   - Old: Mixed concerns, direct API access scattered
   - New: Clean separation (Infrastructure → Services → Core)

## Why Deprecated?

The old `commuter_service/` architecture had:

- ❌ No clear separation of concerns
- ❌ Direct API/database access scattered throughout
- ❌ Difficult to test and maintain
- ❌ Not following Single Source of Truth pattern

## What to Use Instead

See `commuter_simulator/README.md` for:

- ✅ Modern architecture with clean layers
- ✅ Single Source of Truth pattern
- ✅ Proper dependency injection
- ✅ Clear separation: Infrastructure → Services → Core
- ✅ Easier testing and maintenance

## Retention Policy

This folder is kept for **reference only** and will be:

- Removed in Phase 2 (Production Deployment)
- Not updated or maintained
- Not covered by tests

**Last Updated**: October 26, 2025  
**Deprecated By**: Phase 1.12 refactoring  
**Use Instead**: `commuter_simulator/`
