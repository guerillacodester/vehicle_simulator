# Integration Tests - Real Database Spawning

Integration tests that use the actual RouteSpawner and DepotSpawner to create real passengers in the database.

## Test Files

### `spawn_full_week_route1.py`
**Spawn Full Week of Passengers for Route 1**

Creates real passengers in the database for 7 days × 24 hours using the actual RouteSpawner.

**What it does:**
- Spawns passengers for Saturday through Friday (7 days)
- Runs hourly spawning (24 hours per day)
- Creates both depot and route passengers
- Inserts ~6,000-8,000 real passenger records into PostgreSQL via Strapi
- Validates insertion counts

**Usage:**
```bash
python tests/integration/spawn_full_week_route1.py
```

**Expected Output:**
- Hourly spawn counts for each day
- Daily totals (Saturday ~2,200, Sunday ~1,200, Monday ~900, etc.)
- Weekly total: ~6,000-8,000 passengers
- Database confirmation of inserted records

**Requirements:**
- Strapi API running (localhost:1337)
- Geospatial service running (localhost:8001)
- PostgreSQL database accessible
- Route 1 exists in database

---

### `test_route1_real_spawning.py`
**Single Hour Spawning Test**

Quick test that spawns passengers for just one hour (Monday 8 AM peak).

**Usage:**
```bash
python tests/integration/test_route1_real_spawning.py
```

**Expected Output:**
- ~90-100 passengers spawned
- Database confirmation
- Sample passenger records displayed

---

## Why These Tests?

These integration tests create **physical passengers over the entire time period**, allowing you to:

1. **Run statistical analysis on real data** (not simulations)
2. **Validate temporal patterns** from actual database records
3. **Test Poisson distribution** using real spawn counts
4. **Analyze depot vs route distribution** from passenger records
5. **Query passengers by hour/day** for detailed analysis
6. **Validate database integrity** and API performance

---

## Cleanup

After running tests, clean up passengers:

```bash
python reset_passengers.py
```

This removes all passenger records from the database.

---

## Database Queries

After spawning, you can query passengers:

**All passengers for Route 1:**
```
GET http://localhost:1337/api/passengers?filters[route_id][$eq]=14
```

**Passengers spawned on Monday:**
```
GET http://localhost:1337/api/passengers?filters[spawned_at][$gte]=2024-11-04T00:00:00Z&filters[spawned_at][$lt]=2024-11-05T00:00:00Z
```

**Passengers spawned at 8 AM:**
```
GET http://localhost:1337/api/passengers?filters[spawned_at][$gte]=2024-11-04T08:00:00Z&filters[spawned_at][$lt]=2024-11-04T09:00:00Z
```

**Count by depot vs route:**
```sql
SELECT 
  CASE WHEN depot_id IS NOT NULL THEN 'depot' ELSE 'route' END as spawn_type,
  COUNT(*) as count
FROM passengers
WHERE route_id = '14'
GROUP BY spawn_type;
```

---

## Expected Patterns

### Daily Totals (Full Week)
- Saturday: ~2,200 passengers
- Sunday: ~1,200 passengers
- Monday: ~900 passengers
- Tuesday: ~2,400 passengers
- Wednesday: ~2,300 passengers
- Thursday: ~2,500 passengers
- Friday: ~2,300 passengers

**Weekly Total: ~6,000-8,000 passengers**

### Peak Hours
- Morning: 7-9 AM (highest)
- Evening: 16-18:00 (second peak)
- Off-peak: 0-5 AM (minimal)

### Depot vs Route Distribution
- Depot: ~60% of total (450 buildings)
- Route: ~40% of total (320 buildings)

---

## Statistical Analysis Examples

Once you have real passengers in the database, you can:

1. **Validate Poisson distribution:**
   - Query hourly counts for 100 different hours
   - Calculate variance/mean ratio
   - Should be ≈ 1.0

2. **Validate temporal patterns:**
   - Extract all 8 AM spawns across the week
   - Compare to 2 AM spawns
   - Should show clear peak difference

3. **Validate day multipliers:**
   - Compare Monday total to Sunday total
   - Monday should have more (1.0 vs 0.4 multiplier)

4. **Validate independent spawning:**
   - Query depot passengers (where depot_id IS NOT NULL)
   - Query route passengers (where depot_id IS NULL)
   - Verify depot + route = total

All analysis can be done **at your own pace** since passengers persist in the database.
