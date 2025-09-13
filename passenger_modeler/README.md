# Passenger Model Generator

This directory contains the data and configuration files needed to generate passenger models for the Arknet Transit Simulator. The generated JSON models are consumed by the main simulator to create realistic passenger flows.

## 🎯 Purpose

Generate JSON passenger models from GeoJSON data that can be consumed by `world/arknet_transit_simulator` for real-time passenger generation during vehicle simulation.

## 📁 Structure

```text
passenger_modeler/
├── config.json              # Configuration for model generation
├── passenger_modeler.py     # Main model generator script
├── data/
│   └── barbados/            # All GeoJSON data files
│       ├── amenities.geojson       # POIs and amenities (1417 features)
│       ├── busstops.geojson        # Transit stops (204 features)
│       ├── barbados_landuse.geojson # Land use data (optional)
│       └── landuse.geojson         # Additional land use data
└── models/
    └── generated/           # Output directory for generated models
        └── generated_barbados_model.json
```

## ⚙️ Configuration

The `config.json` file specifies:

- **Data Sources**: Which GeoJSON files to process
- **Generation Parameters**: Catchment radius, time patterns, amenity weights
- **Output Settings**: Where to save generated models

### Example Usage

```bash
# Run the passenger model generator (from project root)
python passenger_modeler/passenger_modeler.py --config passenger_modeler/config.json
```

The generator will:

1. Load GeoJSON files specified in config
2. Calculate catchment areas around bus stops
3. Generate realistic time-based passenger patterns
4. Export complete model to `models/generated/`

## 🔄 Integration with Arknet Transit Simulator

The generated JSON models are consumed by:

- `world/arknet_transit_simulator/services/passenger_model_loader.py`
- `world/arknet_transit_simulator/services/passenger_generation_engine.py`
- `world/arknet_transit_simulator/services/realtime_passenger_service.py`

These services use the model data to generate realistic passenger flows during vehicle simulation.

## 📊 Data Sources

### Barbados Transit Data

- **Amenities**: 1417 features extracted from OpenStreetMap via QGIS
  - Shops, restaurants, schools, hospitals, offices, leisure facilities
- **Bus Stops**: 204 transit stops from OpenStreetMap
  - Public bus stops and platforms across Barbados
- **Land Use**: Optional land use classifications for enhanced modeling

### Adding New Data

1. Extract GeoJSON from OpenStreetMap using QGIS
2. Place files in `data/barbados/` directory
3. Update `config.json` to reference new files
4. Run `passenger_modeler.py` to create updated passenger model

---

**System**: Arknet Transit Vehicle Simulator v0.0.1.8  
**Purpose**: Data preprocessing for real-time passenger simulation

---

## 🧪 Statistical Model Plugins

Passenger demand is modeled using pluggable statistical distributions (currently Poisson and Gaussian). Each plugin has its own config file in:

```text
passenger_modeler/plugins/configs/
```

You can select which model to generate interactively. Generated model JSON includes a `statistics` block.

### Poisson Model (Discrete Arrivals)

Key parameters:

| Parameter | Meaning | Effect |
|-----------|---------|--------|
| `base_lambda` | Average passengers per hour baseline | Higher = more overall riders |
| `time_patterns.*.multiplier` | Hour group multipliers | Increase rush hour demand |
| `amenity_weights.*` | Influence of nearby locations | Boost demand near certain amenities |

### Gaussian Model (Continuous Flow)

| Parameter | Meaning | Effect |
|-----------|---------|--------|
| `base_mean` / `mean_passengers` | Average hourly passengers | Higher = more overall riders |
| `base_std` / `std_passengers` | Variability around mean | Larger = more fluctuation |
| `time_patterns.*.multiplier` | Same role as Poisson | Shape daily peaks |
| `amenity_weights.*` | Same role as Poisson | Localized influence |

---

## 📈 Viewing Passenger Statistics

After generating a model JSON (in `models/generated/`), you can view an easy-to-read passenger demand summary:

```bash
python passenger_modeler/passenger_modeler.py --model-file passenger_modeler/models/generated/<your_model>.json
```

Default output is plain English only. To include technical details:

```bash
python passenger_modeler/passenger_modeler.py --model-file passenger_modeler/models/generated/<your_model>.json --raw
```

### Export to Markdown

```bash
python passenger_modeler/passenger_modeler.py \
  --model-file passenger_modeler/models/generated/<your_model>.json \
  --export-md reports/<your_model>_stats.md

# Include technical breakdown too
python passenger_modeler/passenger_modeler.py \
  --model-file passenger_modeler/models/generated/<your_model>.json \
  --raw --export-md reports/<your_model>_stats_full.md
```

The Markdown file contains:

1. File metadata
2. Plain-language narrative
3. (Optional) technical structure summary

---

## 🔧 How To Tune Passenger Demand

| Goal | What To Change | Typical Adjustment |
|------|----------------|--------------------|
| Increase overall demand | `base_lambda` (Poisson) / `base_mean` (Gaussian) | +10–30% |
| Reduce overall demand | Lower same parameters | −10–30% |
| Stronger rush hours | Raise `time_patterns` multipliers for commute windows | 1.8 → 2.3 |
| Flatten peaks | Lower peak multipliers, raise off-peak | 2.5 → 1.9 + 0.6 → 0.9 |
| Make one area busier | Increase specific `amenity_weights` | 8 → 12 |
| Reduce variability | Poisson: lower base & multipliers; Gaussian: lower `base_std` | σ 5 → 3 |
| Increase variability | Opposite adjustments | σ 3 → 5 |
| More evening activity | Increase evening pattern multiplier | 1.2 → 1.6 |

After edits, regenerate a model and re-run the stats viewer to confirm changes.

---

## 🧪 Interpreting Key Plain-English Outputs

| Output Phrase | Meaning |
|---------------|---------|
| "Typical hour" | Approximate average demand |
| "Variation" | How much actual values bounce around |
| "Rarely above X" | Rough peak threshold (≈95th percentile) |
| "Planning Hint" | Suggested capacity target |
| "Increase overall passengers" | Guidance to scale baseline inputs |

Percentiles are translated into everyday language instead of raw numbers.

---

## 📝 Roadmap Ideas

Potential future enhancements:

- Model comparison: diff two JSON models (`--compare A.json B.json`)
- Seasonality / special event overlays
- Scenario batch generation & summary index
- Visual plots (ASCII or HTML export)

---

## ▶ Quick Commands Reference

```bash
# Generate a model (interactive)
python passenger_modeler/passenger_modeler.py

# View plain-English stats
python passenger_modeler/passenger_modeler.py --model-file models/generated/example.json

# Plain + technical
python passenger_modeler/passenger_modeler.py --model-file models/generated/example.json --raw

# Export to Markdown
python passenger_modeler/passenger_modeler.py --model-file models/generated/example.json --export-md reports/example_stats.md

# Export with technical detail
python passenger_modeler/passenger_modeler.py --model-file models/generated/example.json --raw --export-md reports/example_stats_full.md
```

---

## ✅ Summary

You can now:

- Generate statistical passenger models with multiple distributions
- Read easy passenger demand summaries in plain English
- Export summaries to Markdown for sharing
- Tune demand intuitively via plugin configuration

Need more examples or want automated tuning helpers? Open an issue or extend a plugin.
