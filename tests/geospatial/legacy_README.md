# Integration Tests

Automated tests for the ArkNet Vehicle Simulator system.

## Admin Import Tests

Tests the complete admin boundary import workflow.

### Prerequisites

1. **Strapi Running**:

   ```powershell
   cd arknet_fleet_manager/arknet-fleet-api
   npm run develop
   ```

2. **PostgreSQL Accessible**:
   - Database: `arknettransit`
   - User: `postgres` (update in test script if different)
   - admin_levels table seeded

3. **Python Dependencies**:

   ```powershell
   cd test
   pip install -r requirements.txt
   ```

### Running Tests

```powershell
# From test directory
python test_admin_import.py
```

### Test Coverage

The script validates:

1. ✅ Strapi server is running
2. ✅ Database connection works
3. ✅ Admin levels are seeded (4 levels: 6, 8, 9, 10)
4. ✅ PostGIS extension enabled
5. ✅ Regions table has correct PostGIS schema
6. ✅ GIST spatial index exists
7. ✅ All GeoJSON files exist
8. ✅ Import API endpoint accessible
9. ✅ Country record exists for testing
10. ✅ Clean existing test data
11. ✅ Parish import (level 6) completes
12. ✅ Parishes exist in database
13. ✅ All geometries are valid PostGIS MultiPolygons
14. ✅ Junction tables populated (country + admin_level links)
15. ✅ Spatial queries use GIST index (<10ms)

### Expected Output

```text
==================================================
ADMIN IMPORT INTEGRATION TESTS
==================================================

Started: 2025-10-26 12:34:56

[1/15] Running: Verify Strapi is running
    ✓ PASS Strapi Server Running (0.123s) - Status 200

[2/15] Running: Verify database connection
    ✓ PASS Database Connection (0.045s) - Connected successfully

... (more tests)

==================================================
TEST SUMMARY
==================================================

Total Tests: 15
Passed: 15
Failed: 0
Total Time: 5.234s
Completed: 2025-10-26 12:35:01

✓ ALL TESTS PASSED
```

### Troubleshooting

**Database Connection Failed**:

- Update `user` and `password` in `test_admin_import.py` (line 44-45)
- Verify PostgreSQL is running: `Get-Service postgresql*`

**Strapi Not Running**:

- Start Strapi: `cd arknet_fleet_manager/arknet-fleet-api && npm run develop`
- Check port 1337 is not in use: `netstat -an | findstr :1337`

**Admin Levels Not Seeded**:

- Run seed script: `psql -U postgres -d arknettransit -f seed_admin_levels.sql`

**Import Returns 401/403**:

- Test script doesn't handle authentication
- Run import manually through UI first to establish session
- Or add authentication headers to test script

### Configuration

Edit `test_admin_import.py` to customize:

```python
# Line 30-31: Database credentials
user="postgres",
password="your_password",

# Line 26: Strapi URL
self.strapi_url = "http://localhost:1337"
```

### Exit Codes

- `0`: All tests passed
- `1`: Some tests failed (80%+ success rate)
- `2`: Major failures (<80% success rate)
