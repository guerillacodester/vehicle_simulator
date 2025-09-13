# Passenger Simulator Data Organization

This directory contains all the data files used by the passenger simulation system, organized by type and purpose.

## 📁 Directory Structure

```
passenger_simulator/data/
├── geojson/                          # Primary GeoJSON data files
│   ├── amenities.geojson            # OSM amenities data (1417 features)
│   └── busstops.geojson             # Bus stops data (204 stops)
└── landuse/                         # Landuse analysis files
    ├── barbados_landuse.geojson     # Barbados-specific landuse data
    └── landuse.geojson              # General landuse data
```

## 📊 Data Files Description

### GeoJSON Files (`geojson/`)

#### `amenities.geojson`
- **Source**: QGIS extraction from OpenStreetMap
- **Features**: 1,417 amenity locations
- **Types**: restaurants, schools, banks, hospitals, shops, etc.
- **Usage**: Primary passenger origin points for simulation
- **Coverage**: Complete Barbados amenity data

#### `busstops.geojson`
- **Source**: QGIS extraction from OpenStreetMap
- **Features**: 204 bus stop locations
- **Usage**: Transit stops for passenger boarding/alighting
- **Coverage**: Comprehensive bus stop network

### Landuse Files (`landuse/`)

#### `barbados_landuse.geojson`
- **Source**: Enhanced landuse data for Barbados
- **Usage**: Referenced by `barbados_route_1_enhanced.json` model
- **Purpose**: Landuse-based passenger generation analysis

#### `landuse.geojson`
- **Source**: General landuse classification data
- **Usage**: Available for general landuse analysis
- **Purpose**: Backup/alternative landuse data

## 🔗 File Relationships

The data files are used by various components of the passenger simulation system:

1. **Model Generation**:
   - `amenities.geojson` + `busstops.geojson` → `generate_passenger_model.py` → Generated models

2. **Enhanced Models**:
   - `barbados_route_1_enhanced.json` references `barbados_landuse.geojson`
   - Loaded together by `model_landuse_loader.py`

3. **Demonstrations**:
   - `real_world_passenger_demo.py` uses `amenities.geojson` + `busstops.geojson`
   - `demo_model_generator.py` can use any GeoJSON files

## 📈 Data Statistics

| File | Size | Features | Last Updated |
|------|------|----------|--------------|
| amenities.geojson | ~2.1MB | 1,417 | 2025-09-13 |
| busstops.geojson | ~0.5MB | 204 | 2025-09-13 |
| barbados_landuse.geojson | Variable | Variable | 2025-09-13 |
| landuse.geojson | Variable | Variable | 2025-09-13 |

## 🛠️ Usage Examples

### Loading GeoJSON Data
```python
import geopandas as gpd

# Load amenities
amenities = gpd.read_file('passenger_simulator/data/geojson/amenities.geojson')

# Load bus stops
busstops = gpd.read_file('passenger_simulator/data/geojson/busstops.geojson')
```

### Generate New Model
```bash
python passenger_simulator/tools/generate_passenger_model.py \
    --geojson "passenger_simulator/data/geojson/amenities.geojson" \
             "passenger_simulator/data/geojson/busstops.geojson" \
    --output "my_model.json"
```

### Load Enhanced Model with Landuse
```python
from passenger_simulator.models.people_models.model_landuse_loader import load_model_package

package = load_model_package('passenger_simulator/models/people_models/barbados_route_1_enhanced.json')
landuse_data = package.get_landuse_data()
```

---

**Note**: All paths are relative to the `vehicle_simulator` root directory.