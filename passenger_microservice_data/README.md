# Passenger Microservice Data - Plugin System

This directory contains the **plugin-based country system** for passenger behavior modeling in the ArkNet Transit System.

## 🏗️ Architecture Overview

```text
passenger_microservice_data/
├── base/                           # Base plugin system
│   ├── country_plugin.py         # Abstract base class for plugins
│   ├── plugin_loader.py          # Plugin discovery and loading
│   └── __init__.py               # Base package exports
│
├── countries/                     # Country-specific plugins
│   ├── barbados/                 # Barbados plugin
│   │   ├── __init__.py          # Plugin registration
│   │   ├── config.ini           # Country configuration
│   │   ├── cultural_model.py    # Cultural behavior patterns
│   │   ├── geographic_data/     # GeoJSON files
│   │   │   ├── barbados_amenities.geojson
│   │   │   ├── barbados_busstops.geojson
│   │   │   ├── barbados_highway.geojson
│   │   │   ├── barbados_landuse.geojson
│   │   │   └── barbados_names.geojson
│   │   └── generated_models/    # Pre-computed models
│   │
│   ├── jamaica/                 # Future: Jamaica plugin
│   └── trinidad/                # Future: Trinidad plugin
│
└── README.md                    # This file
```

## 🔌 Plugin System Features

### **Country-Agnostic Design**

- Each country is a self-contained plugin
- Plugins can be added/removed without affecting core system
- Standardized interface for all countries

### **Cultural Behavior Modeling**

- Time-based spawn rate modifiers
- Location-specific passenger patterns
- Cultural events and holidays
- Work patterns and social behaviors

### **Configuration-Driven**

- Each plugin has its own `config.ini`
- GeoJSON data paths configurable
- Processing parameters customizable
- Trip purpose distributions adjustable

### **Extensible Architecture**

- Easy to add new countries
- Plugin validation system
- Feature detection and support
- Hot-swappable during runtime

## 🚀 Usage Examples

### **Basic Plugin Loading**

```python
from passenger_microservice_data import get_plugin_manager

# Get plugin manager
manager = get_plugin_manager()

# Discover available countries
countries = manager.get_available_countries()
print(countries)  # {'bb': 'Barbados'}

# Set active country
manager.set_country('bb')

# Get spawn rate modifier
from datetime import datetime
current_time = datetime.now()
modifier = manager.get_spawn_rate_modifier(current_time, 'residential')
```

### **Cultural Pattern Access**

```python
# Get current plugin
plugin = manager.get_current_plugin()

# Get cultural metadata
metadata = plugin.get_cultural_metadata()
print(metadata['work_patterns'])
print(metadata['cultural_events'])

# Get trip purpose distribution
trip_purposes = plugin.get_trip_purpose_distribution(current_time, 'commercial')
```

### **Configuration Access**

```python
# Get country configuration
config = manager.get_country_config('bb')
spawn_rate = config.getfloat('passenger_model', 'base_spawn_rate')
rush_multiplier = config.getfloat('passenger_model', 'rush_hour_multiplier')
```

## 🔧 Creating New Country Plugins

### **1. Create Directory Structure**

```bash
countries/jamaica/
├── __init__.py
├── config.ini
├── cultural_model.py
├── geographic_data/
└── generated_models/
```

### **2. Implement Plugin Registration (`__init__.py`)**

```python
from .cultural_model import JamaicaCulturalModel
from ..base.country_plugin import CountryPlugin

class JamaicaPlugin(CountryPlugin):
    def __init__(self):
        super().__init__()
        self.country_code = "jm"
        self.country_name = "Jamaica"
        # ... implement required methods

def get_plugin():
    return JamaicaPlugin()

PLUGIN_INFO = {
    "name": "Jamaica",
    "code": "jm",
    "version": "1.0.0",
    # ... plugin metadata
}
```

### **3. Create Cultural Model (`cultural_model.py`)**

```python
class JamaicaCulturalModel:
    def get_spawn_rate_modifier(self, current_time, location_type):
        # Implement Jamaica-specific patterns
        pass
    
    def get_trip_purpose_distribution(self, current_time, origin_type):
        # Implement Jamaica-specific trip purposes
        pass
```

### **4. Configure Settings (`config.ini`)**

```ini
[country]
country_code = jm
country_name = Jamaica
timezone = America/Jamaica

[cultural_patterns]
work_start_time = 08:00
# ... Jamaica-specific settings

[geographic_data]
amenities = geographic_data/jamaica_amenities.geojson
# ... other GeoJSON files
```

## 📊 Data Requirements

### **Required GeoJSON Files**

- `amenities.geojson` - Points of interest, shops, services
- `busstops.geojson` - Public transport stops
- `landuse.geojson` - Land use patterns (residential, commercial, etc.)
- `highway.geojson` - Road network and transportation corridors
- `names.geojson` - Place names and geographic features

### **Configuration Sections**

- `[country]` - Basic country information
- `[cultural_patterns]` - Time patterns and cultural events
- `[passenger_model]` - Statistical model parameters
- `[geographic_data]` - File paths to GeoJSON data
- `[processing]` - Processing and generation parameters
- `[trip_purposes]` - Trip purpose probability distributions

## 🧪 Testing and Validation

### **Plugin Validation**

```python
# Validate specific plugin
plugin = manager.loader.get_plugin('bb')
is_valid, errors = plugin.validate_plugin()

# Validate all plugins
results = manager.loader.validate_all_plugins()
for country, (valid, errors) in results.items():
    print(f"{country}: {'✅' if valid else '❌'} {errors}")
```

### **Feature Testing**

```python
# Test spawn rate patterns
test_times = [
    datetime(2025, 10, 1, 7, 30),  # Rush hour
    datetime(2025, 10, 1, 14, 0),  # Mid-day
    datetime(2025, 10, 5, 10, 0),  # Weekend
]

for test_time in test_times:
    modifier = manager.get_spawn_rate_modifier(test_time, 'residential')
    print(f"{test_time}: {modifier}x spawn rate")
```

## 🎯 Integration with Passenger Microservice

The plugin system is designed to integrate seamlessly with the passenger microservice:

1. **Startup**: Microservice discovers and loads country plugin
2. **Configuration**: Plugin provides all country-specific settings
3. **Runtime**: Plugin calculates spawn rates and trip patterns
4. **Data Access**: Plugin provides paths to GeoJSON data
5. **Cultural Events**: Plugin handles special event modifiers

This architecture ensures that adding support for new countries requires only creating a new plugin directory with the appropriate files - no changes to the core microservice code.
