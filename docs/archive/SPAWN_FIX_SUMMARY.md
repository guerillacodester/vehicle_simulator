# Spawn Configuration Database Fix - Summary

## Issue Diagnosed
RouteSpawner was spawning 0 passengers because:
- Database schema stored `hourly_spawn_rates` and `day_multipliers` as **separate component arrays**
- RouteSpawner code expected them as **dictionaries inside distribution_params**
- Missing `spatial_base` field entirely

## Root Cause: Schema Design Problem
The Strapi schema was **over-normalized** for configuration data that doesn't benefit from normalization.

### What Was Wrong:
```
spawn_configs
├── hourly_spawn_rates[] → Array of {hour, spawn_rate}  ❌
├── day_multipliers[] → Array of {day_of_week, multiplier}  ❌
└── distribution_params[1] → Missing spatial_base, hourly_rates, day_multipliers  ❌
```

### What Code Expected:
```json
{
  "distribution_params": [{
    "spatial_base": 2.0,
    "hourly_rates": {"0": 0.1, "8": 2.0, "17": 2.2, ...},
    "day_multipliers": {"0": 1.3, "1": 1.3, ..., "6": 0.3}
  }]
}
```

## Quick Fix Applied ✅

### 1. Database Schema Update
Added 3 new columns to `components_spawning_distribution_params`:
- `spatial_base` (NUMERIC) - Base spawn rate multiplier
- `hourly_rates` (JSONB) - Dictionary of hour→rate mappings
- `day_multipliers` (JSONB) - Dictionary of day→multiplier mappings

### 2. Strapi Schema Update
Updated `arknet-fleet-api/src/components/spawning/distribution-params.json`:
```json
{
  "spatial_base": {
    "type": "decimal",
    "default": 2.0,
    "description": "Base spatial spawn rate multiplier"
  },
  "hourly_rates": {
    "type": "json",
    "description": "Hourly spawn rate multipliers"
  },
  "day_multipliers": {
    "type": "json",
    "description": "Day-of-week multipliers"
  }
}
```

### 3. Data Population
Populated Route 1 spawn config with realistic values:
- **Hourly Rates**: Peak at 8am (2.0) and 5pm (2.2), lowest overnight (0.05-0.2)
- **Day Multipliers**: Weekdays 1.3x, Saturday 0.6x, Sunday 0.3x
- **Spatial Base**: 2.0

## Expected Results

### Spawn Calculation Formula:
```
lambda = spatial_base × hourly_rate × day_multiplier × (time_window / 60)
passengers = Poisson(lambda)
```

### Example Calculations:
| Time | Day | Calculation | Lambda | Expected Passengers |
|------|-----|-------------|---------|---------------------|
| 8am | Monday | 2.0 × 2.0 × 1.3 | 5.2 | ~4-6 |
| 5pm | Tuesday | 2.0 × 2.2 × 1.3 | 5.72 | ~5-7 |
| 12pm | Sunday | 2.0 × 0.9 × 0.3 | 0.54 | ~0-1 |
| 2am | Wednesday | 2.0 × 0.05 × 1.3 | 0.13 | ~0 |

## Testing Steps

1. **Restart Strapi** (for schema changes):
   ```bash
   # In Strapi terminal: Ctrl+C, then npm run develop
   ```

2. **Verify API Returns New Fields**:
   ```bash
   python check_spawn_configs.py
   ```
   Should now show `spatial_base`, `hourly_rates`, `day_multipliers`

3. **Restart Commuter Simulator**:
   ```bash
   python -m commuter_service.main
   ```

4. **Monitor Spawn Output**:
   ```
   16:XX:XX [INFO] RouteSpawner: Spawn calculation: 
     spatial=2.0 × hourly=2.0 × day=1.3 = lambda=5.20 → count=5
   16:XX:XX [INFO] RouteSpawner: Route gg3pv3z19hhm117v9xth5ezq: spawning 5 passengers
   ```

## Long-Term Recommendation

See `SPAWN_SCHEMA_ANALYSIS.md` for comprehensive analysis.

**TL;DR:** Consider refactoring to store entire config as single JSON field:
- ✅ Simpler (no joins, no transformations)
- ✅ Faster (single field fetch)
- ✅ More maintainable
- ✅ Direct code compatibility

Current fix works but maintains unnecessarily complex normalized structure.

## Files Modified

1. ✅ `seeds/quick_fix_spawn_config.py` - Database migration script
2. ✅ `arknet-fleet-api/src/components/spawning/distribution-params.json` - Strapi schema
3. ✅ `SPAWN_SCHEMA_ANALYSIS.md` - Comprehensive analysis document
4. ✅ Database table `components_spawning_distribution_params` - Added 3 columns

## Status
🟡 **Quick fix applied, awaiting Strapi restart and testing**

After Strapi restart, RouteSpawner should spawn realistic passenger counts matching Poisson distribution with configured hourly/daily patterns.
