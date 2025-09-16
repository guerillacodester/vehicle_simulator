# Passenger Simulator Models

This directory contains all passenger simulation models, organized by type and purpose.

## 📁 Directory Structure

```text
passenger_simulator/models/
├── generated/                        # Auto-generated models from GeoJSON data
│   └── generated_barbados_model.json # Generated from amenities.geojson + busstops.geojson
├── enhanced/                         # Hand-crafted enhanced models
│   └── barbados_route_1_enhanced.json # Enhanced model with landuse integration
└── utilities/                        # Model utilities and loaders
    └── model_landuse_loader.py       # Model + landuse package loader
```

## 📊 Model Types

### Generated Models (`generated/`)

These models are automatically created using the `generate_passenger_model.py` tool from GeoJSON data sources.

#### `generated_barbados_model.json`

- **Source**: Auto-generated from `amenities.geojson` (1417 features) + `busstops.geojson` (204 stops)
- **Creation**: `python passenger_simulator/tools/generate_passenger_model.py`
- **Features**:
  - 209 transit stops with passenger generation rates
  - Realistic 24-hour time patterns
  - Catchment area analysis (600m walking distance)
  - Amenity-based passenger origin modeling
- **Usage**: Load directly with JSON or use with agnostic simulation system

### Enhanced Models (`enhanced/`)

These are hand-crafted models with additional features and integrations.

#### `barbados_route_1_enhanced.json`

- **Source**: Hand-crafted with field survey data and landuse integration
- **Features**:
  - Route 1, 1A, 1B passenger modeling
  - Integrated landuse data reference (`barbados_landuse.geojson`)
  - Peak time patterns with real-world calibration
  - Location-specific passenger rates
  - Enhanced demand profiles
- **Usage**: Load with `model_landuse_loader.py` for full landuse integration

### Utilities (`utilities/`)

#### `model_landuse_loader.py`

- **Purpose**: Unified loader for model + landuse packages
- **Features**:
  - Loads model JSON + referenced landuse GeoJSON together
  - Provides integrated `ModelLandusePackage` class
  - Handles relative path resolution
  - Error handling for missing files

## 🔧 Usage Examples

### Load Generated Model

```python
import json

# Simple JSON loading
with open('passenger_simulator/models/generated/generated_barbados_model.json', 'r') as f:
    model = json.load(f)

print(f"Model: {model['model_info']['name']}")
print(f"Stops: {model['model_info']['total_stops']}")
```

### Load Enhanced Model with Landuse

```python
from passenger_simulator.models.utilities.model_landuse_loader import ModelLanduseLoader

# Load complete package
loader = ModelLanduseLoader()
package = loader.load_package('passenger_simulator/models/enhanced/barbados_route_1_enhanced.json')

# Access model data
model_info = package.get_model_info()
locations = package.get_locations()

# Access landuse data
landuse_gdf = package.get_landuse_data()
landuse_config = package.get_landuse_config()
```

### Use with Agnostic Simulation System

```python
from passenger_simulator.agnostic_people_simulation import AgnosticPeopleSimulationSystem

# Initialize system
simulator = AgnosticPeopleSimulationSystem()

# Can work with both generated and enhanced models
# The system will automatically adapt to the available data
```

## 📈 Model Comparison

| Feature | Generated Models | Enhanced Models |
|---------|------------------|-----------------|
| **Creation** | Automatic from GeoJSON | Hand-crafted + surveys |
| **Data Sources** | OSM amenities + bus stops | Field surveys + landuse |
| **Landuse Integration** | Basic amenity analysis | Full landuse GeoJSON |
| **Customization** | Limited to generator params | Fully customizable |
| **Time Patterns** | Standard 8 patterns | Calibrated patterns |
| **Validation** | Algorithmic validation | Real-world validation |

## 🔄 Model Generation Workflow

1. **Collect GeoJSON Data**:
   - Extract amenities from OpenStreetMap via QGIS
   - Extract bus stops from OpenStreetMap via QGIS
   - Optional: Add shops, offices, leisure data

2. **Generate Base Model**:

   ```bash
   python passenger_simulator/tools/generate_passenger_model.py \
       --geojson passenger_simulator/data/geojson/amenities.geojson \
                passenger_simulator/data/geojson/busstops.geojson \
       --output passenger_simulator/models/generated/my_model.json
   ```

3. **Optional Enhancement**:
   - Add landuse data integration
   - Calibrate with field survey data
   - Customize time patterns
   - Save to `enhanced/` directory

4. **Integration**:
   - Use with agnostic simulation system
   - Load via appropriate loader utility
   - Generate realistic passenger patterns

## 🗂️ File Organization Rules

- **Generated Models**: Auto-created, reproducible, version-controlled
- **Enhanced Models**: Custom, validated, integrated with landuse
- **Utilities**: Shared loading and processing code
- **No Legacy Files**: Old plugin system files removed
- **Clear Naming**: Descriptive filenames indicating source and purpose

---

**Last Updated**: September 13, 2025  
**System**: Arknet Transit Vehicle Simulator v0.0.1.8