# Spawn Configuration Database Schema Analysis & Recommendations

**Date:** October 31, 2025  
**Issue:** RouteSpawner spawning 0 passengers due to schema/code mismatch  
**Root Cause:** Database schema over-engineered with normalized components, code expects denormalized JSON

---

## Current Schema Analysis

### ❌ PROBLEM: Over-Normalization

The Strapi schema uses **excessive normalization** with separate component tables:

```
spawn_configs (parent)
├── hourly_spawn_rates[] (components_spawning_hourly_patterns)
│   ├── hour: 0-23
│   └── spawn_rate: decimal
├── day_multipliers[] (components_spawning_day_multipliers)
│   ├── day_of_week: enum
│   └── multiplier: decimal
└── distribution_params[1] (components_spawning_distribution_params)
    ├── passengers_per_building_per_hour
    ├── spawn_radius_meters
    ├── min_trip_distance_meters
    ├── trip_distance_mean_meters
    ├── trip_distance_std_meters
    └── max_trip_distance_ratio
```

### 🔍 Code Expectations

RouteSpawner (`route_spawner.py:200-245`) expects:

```python
dist_params = {
    "spatial_base": 2.0,                    # ❌ MISSING
    "hourly_rates": {                       # ❌ WRONG STRUCTURE (array instead)
        "0": 0.1,
        "6": 0.8,
        "8": 2.0,
        # ... all 24 hours
    },
    "day_multipliers": {                    # ❌ WRONG STRUCTURE (array instead)
        "0": 1.3,  # Monday
        "1": 1.3,  # Tuesday
        # ... all 7 days
    }
}
```

### 📊 Database Reality

API returns:
```json
{
  "distribution_params": [{
    "id": 10,
    "min_spawn_interval_seconds": 45,
    "passengers_per_building_per_hour": 0.3,
    "spawn_radius_meters": 800
    // ❌ No spatial_base, hourly_rates, or day_multipliers
  }],
  "hourly_spawn_rates": [
    {"hour": 0, "spawn_rate": 0.05},
    {"hour": 1, "spawn_rate": 0.02}
    // ❌ Array, not dictionary
  ],
  "day_multipliers": [
    {"day_of_week": "monday", "multiplier": 1.0}
    // ❌ Array with string keys, not numeric
  ]
}
```

---

## Best Practice Recommendations

### ✅ OPTION 1: Simplify Database Schema (RECOMMENDED)

**Store all parameters as JSON in distribution_params**

#### Updated Schema:
```json
{
  "attributes": {
    "distribution_params": {
      "type": "json",
      "required": true,
      "description": "Complete Poisson distribution configuration"
    }
  }
}
```

#### Example Data:
```json
{
  "distribution_params": {
    "spatial_base": 2.0,
    "spawn_radius_meters": 800,
    "min_spawn_interval_seconds": 45,
    "passengers_per_building_per_hour": 0.3,
    "min_trip_distance_meters": 250,
    "trip_distance_mean_meters": 2000,
    "trip_distance_std_meters": 1000,
    "max_trip_distance_ratio": 1.0,
    "hourly_rates": {
      "0": 0.1, "1": 0.05, "2": 0.05, "3": 0.05,
      "4": 0.2, "5": 0.5, "6": 0.8, "7": 1.5,
      "8": 2.0, "9": 1.2, "10": 0.8, "11": 0.7,
      "12": 0.9, "13": 0.8, "14": 0.7, "15": 1.0,
      "16": 1.8, "17": 2.2, "18": 1.5, "19": 1.0,
      "20": 0.6, "21": 0.4, "22": 0.3, "23": 0.2
    },
    "day_multipliers": {
      "0": 1.3, "1": 1.3, "2": 1.3, "3": 1.3,
      "4": 1.3, "5": 0.6, "6": 0.3
    }
  }
}
```

**Pros:**
- ✅ Direct code compatibility (zero transformation needed)
- ✅ Single JSON field easier to edit in Strapi UI
- ✅ Simpler database queries (no joins)
- ✅ Faster API responses (no component population)
- ✅ Version control friendly (single JSON diff)

**Cons:**
- ⚠️ Loses Strapi's field validation UI
- ⚠️ Need custom JSON editor or validation

---

### ✅ OPTION 2: Fix Code to Transform Components

**Keep normalized schema, update RouteSpawner to transform data**

#### Add transformation layer in `route_spawner.py`:

```python
async def _load_spawn_config(self) -> Optional[Dict[str, Any]]:
    """Load spawn configuration from Strapi"""
    if self._spawn_config_cache:
        return self._spawn_config_cache
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.config_loader.api_base_url}/spawn-configs?"
                f"populate[hourly_spawn_rates]=*&"
                f"populate[day_multipliers]=*&"
                f"populate[distribution_params]=*&"
                f"filters[route][documentId][$eq]={self.route_id}"
            )
            data = response.json()
        
        if data.get('data') and len(data['data']) > 0:
            raw_config = data['data'][0]
            
            # Transform component arrays to dictionaries
            transformed = {
                'distribution_params': raw_config.get('distribution_params', [{}])[0]
            }
            
            # Convert hourly_spawn_rates array to dictionary
            hourly_rates = {}
            for item in raw_config.get('hourly_spawn_rates', []):
                hourly_rates[str(item['hour'])] = item['spawn_rate']
            transformed['distribution_params']['hourly_rates'] = hourly_rates
            
            # Convert day_multipliers array to dictionary
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2,
                'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
            }
            day_multipliers = {}
            for item in raw_config.get('day_multipliers', []):
                day_num = day_map.get(item['day_of_week'])
                if day_num is not None:
                    day_multipliers[str(day_num)] = item['multiplier']
            transformed['distribution_params']['day_multipliers'] = day_multipliers
            
            # Add spatial_base if missing
            if 'spatial_base' not in transformed['distribution_params']:
                transformed['distribution_params']['spatial_base'] = 2.0
            
            self._spawn_config_cache = transformed
            return self._spawn_config_cache
        
        return None
    except Exception as e:
        self.logger.error(f"Error loading spawn config: {e}")
        return None
```

**Pros:**
- ✅ Keeps existing database schema
- ✅ Strapi UI validation remains
- ✅ No database migration needed

**Cons:**
- ⚠️ Complex transformation logic
- ⚠️ Slower (multiple populate queries)
- ⚠️ Harder to maintain
- ⚠️ Still missing `spatial_base` field in schema

---

### ✅ OPTION 3: Hybrid Approach (COMPROMISE)

**Keep components for UI, add JSON cache field**

```json
{
  "attributes": {
    "hourly_spawn_rates": {
      "type": "component",
      "repeatable": true,
      "component": "spawning.hourly-pattern"
    },
    "day_multipliers": {
      "type": "component",
      "repeatable": true,
      "component": "spawning.day-multiplier"
    },
    "distribution_params_cache": {
      "type": "json",
      "description": "Auto-generated cache from components (lifecycle hook)"
    }
  }
}
```

**Add Strapi lifecycle hook:**
```javascript
// src/api/spawn-config/content-types/spawn-config/lifecycles.js
module.exports = {
  async beforeCreate(event) {
    buildDistributionCache(event);
  },
  async beforeUpdate(event) {
    buildDistributionCache(event);
  }
};

function buildDistributionCache(event) {
  const { data } = event.params;
  
  // Build hourly_rates dictionary
  const hourlyRates = {};
  if (data.hourly_spawn_rates) {
    data.hourly_spawn_rates.forEach(item => {
      hourlyRates[String(item.hour)] = item.spawn_rate;
    });
  }
  
  // Build day_multipliers dictionary
  const dayMap = {
    monday: 0, tuesday: 1, wednesday: 2,
    thursday: 3, friday: 4, saturday: 5, sunday: 6
  };
  const dayMults = {};
  if (data.day_multipliers) {
    data.day_multipliers.forEach(item => {
      const dayNum = dayMap[item.day_of_week];
      if (dayNum !== undefined) {
        dayMults[String(dayNum)] = item.multiplier;
      }
    });
  }
  
  // Merge into cache
  data.distribution_params_cache = {
    ...data.distribution_params[0],
    hourly_rates: hourlyRates,
    day_multipliers: dayMults,
    spatial_base: data.distribution_params[0]?.spatial_base || 2.0
  };
}
```

**Pros:**
- ✅ User-friendly Strapi UI
- ✅ Fast API queries (use cache)
- ✅ Direct code compatibility
- ✅ Automatic cache updates

**Cons:**
- ⚠️ Data duplication
- ⚠️ Requires lifecycle hook maintenance

---

## Final Recommendation

**🏆 OPTION 1: Simplify Schema (Store as JSON)**

**Rationale:**
1. **KISS Principle** - Configuration data doesn't need normalization
2. **Performance** - Single field fetch vs multiple joins
3. **Maintainability** - Less code, fewer moving parts
4. **Flexibility** - Easy to add new parameters without migrations
5. **Version Control** - Clean diffs for config changes

**Implementation Steps:**

1. **Update Schema** (`src/api/spawn-config/content-types/spawn-config/schema.json`):
```json
{
  "attributes": {
    "name": { "type": "string", "required": true },
    "description": { "type": "text" },
    "distribution_params": {
      "type": "json",
      "required": true,
      "description": "Complete Poisson spawn configuration with hourly_rates and day_multipliers"
    },
    "is_active": { "type": "boolean", "default": true },
    "route": {
      "type": "relation",
      "relation": "oneToOne",
      "target": "api::route.route"
    }
  }
}
```

2. **Remove unused component tables** (drop in production carefully)

3. **Create seed data** with proper JSON structure

4. **Code works immediately** - no transformation needed

**When to Use Components Instead:**
- If you need Strapi's drag-and-drop UI
- If non-technical users manage configs
- If you want per-field validation in admin panel

For simulation configs managed by developers, **JSON is superior**.

---

## Quick Fix for Current System

**Immediate workaround (no schema changes):**

Add `spatial_base`, `hourly_rates`, and `day_multipliers` fields to `components_spawning_distribution_params`:

```sql
ALTER TABLE components_spawning_distribution_params 
ADD COLUMN spatial_base NUMERIC(5,2) DEFAULT 2.0,
ADD COLUMN hourly_rates JSONB,
ADD COLUMN day_multipliers JSONB;
```

Update seed script to populate JSON fields:
```python
hourly_rates_json = json.dumps({
    "0": 0.1, "1": 0.05, ... "23": 0.2
})
day_mults_json = json.dumps({
    "0": 1.3, "1": 1.3, ... "6": 0.3
})

cur.execute("""
    UPDATE components_spawning_distribution_params
    SET spatial_base = 2.0,
        hourly_rates = %s,
        day_multipliers = %s
    WHERE id = 10
""", (hourly_rates_json, day_mults_json))
```

This gets you working **today** while you plan the proper schema refactor.
