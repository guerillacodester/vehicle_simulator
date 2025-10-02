# Strapi Content Types for Database-First Passenger Plugin System

This document outlines the Strapi content types needed to support the database-first passenger plugin system.

## Required Content Types

### 1. passenger-plugin-configs

**Purpose**: Store plugin configuration parameters for each country
**Collection Type**: Yes
**API ID**: passenger-plugin-configs

**Fields**:

```json
{
  "country_code": {
    "type": "string",
    "required": true,
    "unique": true,
    "maxLength": 2,
    "description": "ISO 2-letter country code (e.g., BB, JM, TT)"
  },
  "base_spawn_rate": {
    "type": "decimal",
    "required": true,
    "default": 0.15,
    "min": 0.01,
    "max": 2.0,
    "description": "Base passenger spawn rate per location per minute"
  },
  "rush_hour_multiplier": {
    "type": "decimal",
    "required": true,
    "default": 2.5,
    "min": 1.0,
    "max": 5.0,
    "description": "Multiplier for rush hour periods"
  },
  "off_peak_multiplier": {
    "type": "decimal",
    "required": true,
    "default": 0.8,
    "min": 0.1,
    "max": 2.0,
    "description": "Multiplier for off-peak periods"
  },
  "weekend_multiplier": {
    "type": "decimal",
    "required": true,
    "default": 0.4,
    "min": 0.1,
    "max": 2.0,
    "description": "Multiplier for weekend periods"
  },
  "walking_distance_meters": {
    "type": "integer",
    "required": true,
    "default": 80,
    "min": 50,
    "max": 500,
    "description": "Maximum walking distance for passenger spawning"
  },
  "generation_interval_seconds": {
    "type": "integer",
    "required": true,
    "default": 60,
    "min": 10,
    "max": 300,
    "description": "Interval between passenger generation cycles"
  },
  "passenger_demand_multiplier": {
    "type": "decimal",
    "required": true,
    "default": 1.0,
    "min": 0.1,
    "max": 5.0,
    "description": "Overall passenger demand adjustment"
  },
  "trip_purposes": {
    "type": "json",
    "required": true,
    "description": "Trip purpose distribution (JSON object with percentages)"
  },
  "time_patterns": {
    "type": "json",
    "required": true,
    "description": "Time-based patterns (JSON object with time ranges)"
  },
  "is_enabled": {
    "type": "boolean",
    "required": true,
    "default": true,
    "description": "Whether this plugin configuration is active"
  }
}
```

### 2. passenger-cultural-patterns

**Purpose**: Store cultural behavior patterns for each country
**Collection Type**: Yes
**API ID**: passenger-cultural-patterns

**Fields**:

```json
{
  "country_code": {
    "type": "string",
    "required": true,
    "unique": true,
    "maxLength": 2,
    "description": "ISO 2-letter country code"
  },
  "work_patterns": {
    "type": "json",
    "required": true,
    "description": "Work schedule patterns (start times, lunch breaks, etc.)"
  },
  "social_patterns": {
    "type": "json",
    "required": true,
    "description": "Social activity patterns (church, markets, recreation)"
  },
  "cultural_events": {
    "type": "json",
    "required": false,
    "description": "Cultural events and festivals with travel impact"
  },
  "location_modifiers": {
    "type": "json",
    "required": true,
    "description": "Location-specific spawn rate modifiers"
  },
  "time_modifiers": {
    "type": "json",
    "required": true,
    "description": "Time-based spawn rate modifiers"
  },
  "is_active": {
    "type": "boolean",
    "required": true,
    "default": true,
    "description": "Whether these cultural patterns are active"
  }
}
```

### 3. passenger-geojson-data

**Purpose**: Store GeoJSON data files for each country
**Collection Type**: Yes
**API ID**: passenger-geojson-data

**Fields**:

```json
{
  "country_code": {
    "type": "string",
    "required": true,
    "maxLength": 2,
    "description": "ISO 2-letter country code"
  },
  "data_type": {
    "type": "enumeration",
    "required": true,
    "enum": ["amenities", "busstops", "landuse", "highway", "names"],
    "description": "Type of GeoJSON data"
  },
  "geojson_file": {
    "type": "media",
    "required": true,
    "allowedTypes": ["files"],
    "description": "GeoJSON file upload"
  },
  "description": {
    "type": "text",
    "required": false,
    "description": "Description of this dataset"
  },
  "version": {
    "type": "string",
    "required": false,
    "description": "Dataset version"
  },
  "is_active": {
    "type": "boolean",
    "required": true,
    "default": true,
    "description": "Whether this dataset is active"
  }
}
```

### 4. passenger-generated-models

**Purpose**: Store pre-computed passenger models
**Collection Type**: Yes
**API ID**: passenger-generated-models

**Fields**:

```json
{
  "country_code": {
    "type": "string",
    "required": true,
    "maxLength": 2,
    "description": "ISO 2-letter country code"
  },
  "model_type": {
    "type": "enumeration",
    "required": true,
    "enum": ["passenger_model", "route_patterns", "temporal_distribution"],
    "description": "Type of generated model"
  },
  "model_data": {
    "type": "json",
    "required": true,
    "description": "Generated model data"
  },
  "generation_date": {
    "type": "datetime",
    "required": true,
    "description": "When this model was generated"
  },
  "parameters_used": {
    "type": "json",
    "required": false,
    "description": "Parameters used to generate this model"
  },
  "statistics": {
    "type": "json",
    "required": false,
    "description": "Model statistics and validation metrics"
  },
  "is_current": {
    "type": "boolean",
    "required": true,
    "default": true,
    "description": "Whether this is the current active model"
  }
}
```

## API Endpoints Created

After creating these content types, Strapi will automatically generate:

- `GET /api/passenger-plugin-configs` - List all plugin configurations
- `GET /api/passenger-plugin-configs?filters[country_code][$eq]=BB` - Get config for specific country
- `POST /api/passenger-plugin-configs` - Create new plugin configuration
- `PUT /api/passenger-plugin-configs/:id` - Update plugin configuration

- `GET /api/passenger-cultural-patterns` - List all cultural patterns
- `GET /api/passenger-cultural-patterns?filters[country_code][$eq]=BB` - Get patterns for specific country
- `POST /api/passenger-cultural-patterns` - Create new cultural patterns
- `PUT /api/passenger-cultural-patterns/:id` - Update cultural patterns

- `GET /api/passenger-geojson-data` - List all GeoJSON datasets
- `GET /api/passenger-geojson-data?filters[country_code][$eq]=BB&filters[data_type][$eq]=amenities` - Get specific dataset
- `POST /api/passenger-geojson-data` - Upload new GeoJSON data
- `PUT /api/passenger-geojson-data/:id` - Update GeoJSON data

- `GET /api/passenger-generated-models` - List all generated models
- `GET /api/passenger-generated-models?filters[country_code][$eq]=BB&filters[is_current][$eq]=true` - Get current models for country

## Admin Interface Benefits

With this database-first approach, users can:

1. **Configure Passenger Behavior** via admin interface:
    - Adjust spawn rates for different times of day
    - Modify cultural patterns and work schedules
    - Set trip purpose distributions
    - Configure location-specific modifiers

2. **Upload GeoJSON Data** via media library:
   - Drag-and-drop GeoJSON files
   - Version control of datasets
   - Easy replacement of outdated data

3. **Monitor Generated Models**:
   - View model statistics
   - Compare different model versions
   - Regenerate models with new parameters

4. **Real-time Configuration**:
   - Changes take effect immediately
   - No need to restart services
   - A/B testing of different configurations

5. **Multi-country Management**:
   - Easy duplication of configurations
   - Bulk updates across countries
   - Country-specific customization

## Implementation Steps

1. Create the content types in Strapi admin
2. Populate initial data for Barbados
3. Test the database plugin system
4. Migrate existing GeoJSON files to Strapi media library
5. Create admin-friendly forms for configuration
6. Add validation and constraints
7. Implement real-time updates via webhooks
