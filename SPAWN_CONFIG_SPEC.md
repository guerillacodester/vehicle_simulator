# Spawn Configuration Parameters

## Overview
The spawn configuration controls passenger generation rates using a normalized temporal-spatial model.

## Formula
```
effective_rate = (spatial_base_rate × hourly_rate × day_multiplier) / 60
spawn_count = Poisson(effective_rate × building_count)
```

Where:
- `effective_rate` = passengers per minute
- Division by 60 converts hourly rate to per-minute rate
- `building_count` = number of buildings in catchment area

---

## Parameter Summary

| Parameter | Type | Normalized | Range | Current | Purpose |
|-----------|------|------------|-------|---------|---------|
| `spatial_base_rate` | Float | ❌ No | 1.0 - 20.0 | **5.0** | Base passengers per building per hour at peak time. Scales overall spawn intensity. |
| `hourly_rates` | Array[24] | ✅ Yes | 0.0 - 1.0 | See below | Temporal multiplier for each hour (00:00-23:00). Models daily commute patterns. |
| `day_multipliers` | Array[7] | ✅ Yes | 0.0 - 1.0 | See below | Multiplier for each day (Mon-Sun). Models weekly patterns (weekday vs weekend). |

### Current `hourly_rates` (24 values)
| Hour | Value | Description |
|------|-------|-------------|
| 00:00-04:00 | 0.0 | No spawning (overnight) |
| 05:00 | 0.15 | Early morning start |
| 06:00 | 0.35 | Morning ramp up |
| 07:00 | 0.75 | Pre-peak |
| 08:00 | **1.0** | **PEAK MORNING** |
| 09:00 | 0.45 | Post-peak |
| 10:00-11:00 | 0.20-0.25 | Mid-morning |
| 12:00 | 0.30 | Lunch hour |
| 13:00-14:00 | 0.25-0.30 | Early afternoon |
| 15:00 | 0.40 | Afternoon pickup |
| 16:00 | 0.55 | Pre-evening peak |
| 17:00 | **0.85** | **PEAK EVENING** |
| 18:00 | 0.40 | Post-evening peak |
| 19:00-20:00 | 0.10-0.20 | Evening wind down |
| 21:00 | 0.05 | Late evening |
| 22:00-23:00 | 0.0 | No spawning |

### Current `day_multipliers` (7 values)
| Day | Value | Description |
|-----|-------|-------------|
| Monday | 1.0 | Full weekday traffic |
| Tuesday | 1.0 | Full weekday traffic |
| Wednesday | 1.0 | Full weekday traffic |
| Thursday | 1.0 | Full weekday traffic |
| Friday | 1.0 | Full weekday traffic |
| Saturday | 1.0 | Full weekend traffic |
| Sunday | **0.6** | Reduced weekend traffic |

---

## Parameters

### 1. `spatial_base_rate` (float)
**Description**: Base passenger generation rate per building per hour at peak time.

**Type**: Positive float

**Normalization**: NOT normalized (absolute value)

**Typical Range**: 1.0 - 10.0

**Example Values**:
- `5.0` = Low density residential area (suburban)
- `10.0` = Medium density mixed use
- `20.0` = High density urban core

**Current Value**: `5.0`

**Purpose**: Scales the overall spawn intensity. Higher values = more passengers.

---

### 2. `hourly_rates` (array of 24 floats)
**Description**: Temporal multiplier for each hour of the day (00:00-23:00).

**Type**: Array of 24 floats

**Normalization**: **YES - Values must be between 0.0 and 1.0**

**Indexing**: `hourly_rates[0]` = midnight (00:00), `hourly_rates[23]` = 11 PM (23:00)

**Typical Pattern**:
- `0.0` = No spawning (midnight to 4 AM)
- `0.15` = Early morning start (5 AM)
- `1.0` = **Peak hour** (typically 8 AM for morning commute)
- `0.85` = Secondary peak (typically 5 PM for evening commute)
- `0.05` = Late evening wind down (9 PM)

**Current Values**:
```python
[
    0.0,   # 00:00 - midnight (no spawns)
    0.0,   # 01:00
    0.0,   # 02:00
    0.0,   # 03:00
    0.0,   # 04:00
    0.15,  # 05:00 - early morning start
    0.35,  # 06:00 - morning ramp up
    0.75,  # 07:00 - pre-peak
    1.0,   # 08:00 - PEAK MORNING
    0.45,  # 09:00 - post-peak
    0.25,  # 10:00 - mid-morning
    0.20,  # 11:00
    0.30,  # 12:00 - lunch
    0.25,  # 13:00
    0.30,  # 14:00
    0.40,  # 15:00 - afternoon pickup
    0.55,  # 16:00 - pre-evening peak
    0.85,  # 17:00 - PEAK EVENING
    0.40,  # 18:00 - post-evening peak
    0.20,  # 19:00
    0.10,  # 20:00 - evening wind down
    0.05,  # 21:00
    0.0,   # 22:00
    0.0,   # 23:00
]
```

**Purpose**: Models daily commute patterns. Peak value (1.0) defines maximum hourly spawn rate.

---

### 3. `day_multipliers` (array of 7 floats)
**Description**: Multiplier for each day of the week.

**Type**: Array of 7 floats

**Normalization**: **YES - Values must be between 0.0 and 1.0**

**Indexing**: 
- `day_multipliers[0]` = Monday
- `day_multipliers[1]` = Tuesday
- `day_multipliers[2]` = Wednesday
- `day_multipliers[3]` = Thursday
- `day_multipliers[4]` = Friday
- `day_multipliers[5]` = Saturday
- `day_multipliers[6]` = Sunday

**Typical Pattern**:
- `1.0` = Full weekday traffic (Mon-Fri)
- `0.8-1.0` = Reduced Saturday traffic
- `0.4-0.6` = Significantly reduced Sunday traffic

**Current Values**:
```python
[
    1.0,  # Monday    - full weekday traffic
    1.0,  # Tuesday   - full weekday traffic
    1.0,  # Wednesday - full weekday traffic
    1.0,  # Thursday  - full weekday traffic
    1.0,  # Friday    - full weekday traffic
    1.0,  # Saturday  - full weekend traffic
    0.6,  # Sunday    - reduced weekend traffic
]
```

**Purpose**: Models weekly patterns (weekday commuting vs weekend leisure travel).

---

## Calculation Example

### Scenario: Monday at 8:00 AM, Depot with 450 buildings

**Given**:
- `spatial_base_rate` = 5.0
- `hourly_rates[8]` = 1.0 (8 AM peak)
- `day_multipliers[0]` = 1.0 (Monday)
- `depot_buildings` = 450

**Calculation**:
```python
effective_rate = (5.0 × 1.0 × 1.0) / 60 = 0.0833 passengers/minute

expected_depot_passengers = Poisson(0.0833 × 450)
                          = Poisson(37.5)
                          ≈ 37-38 passengers/hour
```

### Scenario: Sunday at 8:00 AM, Same Depot

**Given**:
- `spatial_base_rate` = 5.0
- `hourly_rates[8]` = 1.0 (8 AM peak)
- `day_multipliers[6]` = 0.6 (Sunday)
- `depot_buildings` = 450

**Calculation**:
```python
effective_rate = (5.0 × 1.0 × 0.6) / 60 = 0.05 passengers/minute

expected_depot_passengers = Poisson(0.05 × 450)
                          = Poisson(22.5)
                          ≈ 22-23 passengers/hour
```

---

## Validation Ranges

### Expected Daily Totals (Route 1, 450 depot + 320 route buildings):
- **Weekday (Mon-Fri)**: ~400-450 passengers/day
- **Saturday**: ~400-450 passengers/day  
- **Sunday**: ~250-300 passengers/day (60% reduction)

### Expected Peak Hour (8 AM, Weekday):
- **Depot**: ~30-40 passengers
- **Route**: ~25-30 passengers
- **Total**: ~55-70 passengers

### Expected Off-Peak Hour (12 PM Noon):
- **Depot**: ~10-15 passengers
- **Route**: ~8-12 passengers
- **Total**: ~20-25 passengers

---

## Strapi Database Schema

### API Endpoint
```
PUT http://localhost:1337/api/spawn-configs/{documentId}
```

### JSON Body Format
```json
{
  "data": {
    "spatial_base_rate": 5.0,
    "hourly_rates": [0.0, 0.0, ..., 0.0],
    "day_multipliers": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6]
  }
}
```

### Field Types
- `spatial_base_rate`: Decimal (or Float)
- `hourly_rates`: JSON (array of 24 floats)
- `day_multipliers`: JSON (array of 7 floats)

---

## Design Principles

1. **Normalization**: `hourly_rates` and `day_multipliers` are normalized (0-1) to allow independent scaling
2. **Peak Definition**: The value `1.0` in `hourly_rates` defines the peak hour (typically 8 AM)
3. **Absolute Scaling**: `spatial_base_rate` provides the absolute magnitude
4. **Independent Additive**: Depot and route passengers are calculated separately and summed
5. **Poisson Distribution**: Spawn counts follow Poisson distribution for realistic variance

---

## Common Patterns

### Morning Commute Pattern
- Ramp up: 5 AM (0.15) → 8 AM (1.0)
- Ramp down: 8 AM (1.0) → 10 AM (0.25)

### Evening Commute Pattern
- Ramp up: 3 PM (0.40) → 5 PM (0.85)
- Ramp down: 5 PM (0.85) → 8 PM (0.20)

### Weekend Pattern
- Later start (6-7 AM vs 5 AM weekday)
- Flatter distribution (less pronounced peaks)
- Lower overall volume (day_multiplier < 1.0)

### Night Pattern
- Zero spawning: 12 AM - 4 AM (all 0.0)
- Ensures no unrealistic midnight passengers
