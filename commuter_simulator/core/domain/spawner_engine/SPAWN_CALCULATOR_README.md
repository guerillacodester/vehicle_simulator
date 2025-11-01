# Spawn Calculation Kernel

**Modular, testable implementation of the hybrid spawn model.**

## Overview

The `SpawnCalculator` class provides a **pure calculation kernel** for the hybrid spawn model, isolated from infrastructure concerns (API calls, logging, database, etc). This enables:

- ✅ **Easy testing** - Pure functions with no dependencies
- ✅ **Reusability** - Used by spawners, validation scripts, and tests
- ✅ **Maintainability** - Single source of truth for calculation logic
- ✅ **Debuggability** - Step-by-step breakdown of calculations

## Formula

The hybrid spawn model combines spatial and temporal factors:

```python
# Step 1: Temporal weighting
effective_rate = base_rate × hourly_multiplier × day_multiplier

# Step 2: Terminal population (total passengers/hour at depot)
terminal_population = buildings_near_depot × effective_rate

# Step 3: Route attractiveness (zero-sum distribution)
route_attractiveness = buildings_along_route / total_buildings_all_routes

# Step 4: Passengers for this route
passengers_per_hour = terminal_population × route_attractiveness

# Step 5: Poisson spawn count (for time window)
lambda = passengers_per_hour × (time_window_minutes / 60.0)
spawn_count = Poisson(lambda)
```

## Usage

### Production Spawners

```python
from commuter_simulator.core.domain.spawner_engine.spawn_calculator import SpawnCalculator
from datetime import datetime

# Get data from APIs
buildings_near_depot = 1556  # From geospatial API
buildings_along_route = 69    # From geospatial API
total_buildings_all_routes = 389  # Sum for all routes at depot
spawn_config = {...}  # From Strapi API
current_time = datetime.now()

# Calculate spawn count
result = SpawnCalculator.calculate_hybrid_spawn(
    buildings_near_depot=buildings_near_depot,
    buildings_along_route=buildings_along_route,
    total_buildings_all_routes=total_buildings_all_routes,
    spawn_config=spawn_config,
    current_time=current_time,
    time_window_minutes=15,
    seed=None  # Random
)

spawn_count = result['spawn_count']  # e.g., 48 passengers
```

### Validation Scripts

```python
# For deterministic validation (no Poisson sampling)
result = SpawnCalculator.calculate_validation_hybrid_spawn(
    buildings_near_depot=1556,
    buildings_along_route=69,
    total_buildings_all_routes=69,
    base_rate=0.05,
    hourly_mult=2.0,
    day_mult=1.3
)

print(f"Passengers/hour: {result['passengers_per_hour']:.2f}")
# Output: 202.28 (deterministic, no randomness)
```

### Step-by-Step Debugging

```python
# Extract temporal multipliers
base_rate, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
    spawn_config, current_time
)
print(f"Base: {base_rate}, Hourly: {hourly_mult}, Day: {day_mult}")

# Calculate effective rate
effective_rate = SpawnCalculator.calculate_effective_rate(
    base_rate, hourly_mult, day_mult
)
print(f"Effective rate: {effective_rate}")

# Calculate terminal population
terminal_pop = SpawnCalculator.calculate_terminal_population(
    buildings_near_depot, effective_rate
)
print(f"Terminal population: {terminal_pop:.2f} pass/hr")

# ... continue step-by-step
```

## API Reference

### `extract_temporal_multipliers(spawn_config, current_time)`
Extracts base_rate, hourly_multiplier, and day_multiplier from spawn config.

**Returns:** `(base_rate, hourly_mult, day_mult)`

### `calculate_effective_rate(base_rate, hourly_mult, day_mult)`
Combines temporal factors into single effective rate.

**Returns:** `float` - Effective passengers per building per hour

### `calculate_terminal_population(buildings_near_depot, effective_rate)`
Calculates total passengers/hour at depot.

**Returns:** `float` - Expected passengers per hour

### `calculate_route_attractiveness(buildings_along_route, total_buildings_all_routes)`
Calculates this route's share of passengers (zero-sum).

**Returns:** `float` - Attractiveness factor (0.0 to 1.0)

### `calculate_passengers_per_route(terminal_population, route_attractiveness)`
Distributes passengers to this route.

**Returns:** `float` - Expected passengers per hour for this route

### `calculate_lambda_for_time_window(passengers_per_hour, time_window_minutes)`
Converts hourly rate to Poisson lambda for time window.

**Returns:** `float` - Lambda parameter for Poisson distribution

### `generate_poisson_spawn_count(lambda_param, seed=None)`
Generates Poisson-distributed spawn count.

**Returns:** `int` - Spawn count drawn from Poisson(lambda)

### `calculate_hybrid_spawn(...)`
**Complete pipeline** - Runs all steps and returns full breakdown.

**Returns:** `dict` with keys:
- `base_rate`: Base spawn rate
- `hourly_mult`: Hourly multiplier
- `day_mult`: Day multiplier
- `effective_rate`: Combined temporal rate
- `terminal_population`: Total passengers/hour at depot
- `route_attractiveness`: This route's share
- `passengers_per_hour`: Passengers/hour for this route
- `lambda_param`: Poisson lambda
- `spawn_count`: Generated spawn count

### `calculate_validation_hybrid_spawn(...)`
**Validation pipeline** - Deterministic (no Poisson sampling).

**Returns:** `dict` with same keys except `spawn_count` and `lambda_param`

## Examples

### Route 1 Solo (Current State)
```python
result = SpawnCalculator.calculate_hybrid_spawn(
    buildings_near_depot=1556,
    buildings_along_route=69,
    total_buildings_all_routes=69,  # Only 1 route
    spawn_config=route_1_config,
    current_time=datetime(2024, 10, 28, 8, 0),  # Monday 8 AM
    time_window_minutes=15
)

# Output:
# terminal_population: 202.28 pass/hr
# route_attractiveness: 1.00 (100%)
# passengers_per_hour: 202.28
# lambda_param: 50.57 (for 15 min)
# spawn_count: ~48 (Poisson sample)
```

### Route 1 with 5 Routes
```python
result = SpawnCalculator.calculate_hybrid_spawn(
    buildings_near_depot=1556,
    buildings_along_route=69,
    total_buildings_all_routes=389,  # 5 routes total
    spawn_config=route_1_config,
    current_time=datetime(2024, 10, 28, 8, 0),  # Monday 8 AM
    time_window_minutes=15
)

# Output:
# terminal_population: 202.28 pass/hr (SAME - depot-based)
# route_attractiveness: 0.177 (17.7% - reduced)
# passengers_per_hour: 35.88 (reduced proportionally)
# lambda_param: 8.97
# spawn_count: ~8 (lower due to distribution)
```

### Peak vs Night Comparison
```python
# Monday 8 AM peak
peak_result = SpawnCalculator.calculate_validation_hybrid_spawn(
    buildings_near_depot=1556,
    buildings_along_route=69,
    total_buildings_all_routes=69,
    base_rate=0.05, hourly_mult=2.0, day_mult=1.3
)
# passengers_per_hour: 202.28

# Monday 2 AM night
night_result = SpawnCalculator.calculate_validation_hybrid_spawn(
    buildings_near_depot=1556,
    buildings_along_route=69,
    total_buildings_all_routes=69,
    base_rate=0.05, hourly_mult=0.05, day_mult=1.3
)
# passengers_per_hour: 5.06

# Difference: 202.28 / 5.06 = 40x reduction
```

## Testing

Comprehensive unit tests in `commuter_simulator/tests/test_spawn_calculator.py`:

```bash
pytest commuter_simulator/tests/test_spawn_calculator.py -v
```

Quick integration test:

```bash
python test_spawn_calculator_kernel.py
```

## Design Principles

### 1. Pure Functions
All calculations are **pure functions** - no side effects, no global state. Same inputs always produce same outputs (when using `seed` parameter).

### 2. Single Responsibility
Each method does **one thing**:
- Extract multipliers
- Calculate rate
- Calculate population
- etc.

### 3. Composability
Methods can be used **independently** or **combined**:
```python
# Use full pipeline
result = SpawnCalculator.calculate_hybrid_spawn(...)

# Or compose manually
base, hourly, day = SpawnCalculator.extract_temporal_multipliers(...)
effective = SpawnCalculator.calculate_effective_rate(base, hourly, day)
terminal = SpawnCalculator.calculate_terminal_population(buildings, effective)
# ... etc
```

### 4. Testability
Pure functions with no dependencies = **easy to test**:
```python
def test_effective_rate():
    rate = SpawnCalculator.calculate_effective_rate(0.05, 2.0, 1.3)
    assert rate == 0.13  # Simple, deterministic
```

### 5. Zero Dependencies
The kernel has **zero external dependencies** except:
- `datetime` (stdlib)
- `numpy` (for Poisson sampling only)

No API clients, no loggers, no database - pure calculation logic.

## Migration Guide

### Before (Duplicated Logic)
```python
# In route_spawner.py
spatial_factor = building_count * passengers_per_building
hourly_rate = float(hourly_rates.get(hour_str, 0.5))
day_mult = float(day_multipliers.get(day_str, 1.0))
lambda_param = spatial_factor * hourly_rate * day_mult * (time_window_minutes / 60.0)
spawn_count = np.random.poisson(lambda_param)

# Same logic duplicated in depot_spawner.py, validation scripts, etc.
```

### After (Using Kernel)
```python
# In route_spawner.py
from commuter_simulator.core.domain.spawner_engine.spawn_calculator import SpawnCalculator

result = SpawnCalculator.calculate_hybrid_spawn(
    buildings_near_depot=self.catchment_size,
    buildings_along_route=building_count,
    total_buildings_all_routes=total_buildings,
    spawn_config=spawn_config,
    current_time=current_time,
    time_window_minutes=time_window_minutes
)

spawn_count = result['spawn_count']
```

## Conservation Property

The kernel guarantees **zero-sum conservation**:

```python
# Terminal population is FIXED (depot-based)
terminal_pop = buildings_near_depot × effective_rate  # 202.28

# Routes get proportional shares
route_1_share = 69 / 389 = 17.7% → 35.88 pass/hr
route_2_share = 80 / 389 = 20.6% → 41.67 pass/hr
route_3_share = 100 / 389 = 25.7% → 51.99 pass/hr
route_4_share = 50 / 389 = 12.9% → 26.09 pass/hr
route_5_share = 90 / 389 = 23.1% → 46.73 pass/hr

# Sum = 202.28 (conserved!) ✅
```

As routes are added, terminal population **stays constant**, shares **redistribute automatically**.

## Files

- **Kernel**: `commuter_simulator/core/domain/spawner_engine/spawn_calculator.py`
- **Tests**: `commuter_simulator/tests/test_spawn_calculator.py`
- **Quick Test**: `test_spawn_calculator_kernel.py`
- **Documentation**: This file
