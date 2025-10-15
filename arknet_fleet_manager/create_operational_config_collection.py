"""
Create Operational Configuration Collection in Strapi
=====================================================
This script creates the 'operational-configurations' collection type in Strapi
for storing runtime-configurable operational parameters.

Run this once to set up the database schema.
"""

import requests
import json

STRAPI_URL = "http://localhost:1337"
STRAPI_API_TOKEN = None  # Will use public API for collection creation

def create_collection_type():
    """Create the operational-configurations collection type."""
    
    # Collection type schema
    schema = {
        "contentType": {
            "kind": "collectionType",
            "collectionName": "operational_configurations",
            "info": {
                "singularName": "operational-configuration",
                "pluralName": "operational-configurations",
                "displayName": "Operational Configuration",
                "description": "Runtime-configurable operational parameters"
            },
            "options": {
                "draftAndPublish": False  # No draft mode needed
            },
            "pluginOptions": {},
            "attributes": {
                "section": {
                    "type": "string",
                    "required": True,
                    "unique": False
                },
                "parameter": {
                    "type": "string",
                    "required": True,
                    "unique": False
                },
                "value": {
                    "type": "json",
                    "required": True
                },
                "value_type": {
                    "type": "enumeration",
                    "enum": ["number", "string", "boolean", "object"],
                    "required": True
                },
                "default_value": {
                    "type": "json",
                    "required": True
                },
                "constraints": {
                    "type": "json",
                    "required": False
                },
                "description": {
                    "type": "text",
                    "required": False
                },
                "display_name": {
                    "type": "string",
                    "required": False
                },
                "ui_group": {
                    "type": "string",
                    "required": False
                },
                "requires_restart": {
                    "type": "boolean",
                    "default": False
                }
            }
        }
    }
    
    print("📋 Collection Schema:")
    print(json.dumps(schema, indent=2))
    print("\n⚠️  Note: Strapi v5 requires manual collection creation via Admin UI")
    print("\nSteps to create collection manually:")
    print("1. Go to http://localhost:1337/admin")
    print("2. Navigate to Content-Type Builder")
    print("3. Click 'Create new collection type'")
    print("4. Name it 'operational-configuration' (singular)")
    print("5. Add the following fields:")
    print("\n   Field: section")
    print("   - Type: Text (short)")
    print("   - Required: Yes")
    print("\n   Field: parameter")
    print("   - Type: Text (short)")
    print("   - Required: Yes")
    print("\n   Field: value")
    print("   - Type: JSON")
    print("   - Required: Yes")
    print("\n   Field: value_type")
    print("   - Type: Enumeration")
    print("   - Values: number, string, boolean, object")
    print("   - Required: Yes")
    print("\n   Field: default_value")
    print("   - Type: JSON")
    print("   - Required: Yes")
    print("\n   Field: constraints")
    print("   - Type: JSON")
    print("\n   Field: description")
    print("   - Type: Text (long)")
    print("\n   Field: display_name")
    print("   - Type: Text (short)")
    print("\n   Field: ui_group")
    print("   - Type: Text (short)")
    print("\n   Field: requires_restart")
    print("   - Type: Boolean")
    print("   - Default: false")
    print("\n6. Save and wait for Strapi to restart")
    
    return schema


def seed_initial_data():
    """Seed initial configuration parameters."""
    
    initial_configs = [
        # Conductor - Proximity Settings
        {
            "section": "conductor.proximity",
            "parameter": "pickup_radius_km",
            "value": 0.2,
            "value_type": "number",
            "default_value": 0.2,
            "constraints": {
                "min": 0.05,
                "max": 5.0,
                "step": 0.05,
                "unit": "kilometers"
            },
            "description": "Maximum distance from passenger for conductor to offer pickup",
            "display_name": "Pickup Radius",
            "ui_group": "Proximity Settings",
            "requires_restart": False
        },
        {
            "section": "conductor.proximity",
            "parameter": "boarding_time_window_minutes",
            "value": 5.0,
            "value_type": "number",
            "default_value": 5.0,
            "constraints": {
                "min": 1.0,
                "max": 30.0,
                "step": 0.5,
                "unit": "minutes"
            },
            "description": "Time window for passenger boarding eligibility",
            "display_name": "Boarding Time Window",
            "ui_group": "Proximity Settings",
            "requires_restart": False
        },
        
        # Conductor - Stop Duration Settings
        {
            "section": "conductor.stop_duration",
            "parameter": "min_seconds",
            "value": 15.0,
            "value_type": "number",
            "default_value": 15.0,
            "constraints": {
                "min": 5.0,
                "max": 60.0,
                "step": 1.0,
                "unit": "seconds"
            },
            "description": "Minimum stop duration",
            "display_name": "Minimum Stop Duration",
            "ui_group": "Stop Duration",
            "requires_restart": False
        },
        {
            "section": "conductor.stop_duration",
            "parameter": "max_seconds",
            "value": 180.0,
            "value_type": "number",
            "default_value": 180.0,
            "constraints": {
                "min": 30.0,
                "max": 600.0,
                "step": 10.0,
                "unit": "seconds"
            },
            "description": "Maximum stop duration",
            "display_name": "Maximum Stop Duration",
            "ui_group": "Stop Duration",
            "requires_restart": False
        },
        {
            "section": "conductor.stop_duration",
            "parameter": "per_passenger_boarding_time",
            "value": 8.0,
            "value_type": "number",
            "default_value": 8.0,
            "constraints": {
                "min": 1.0,
                "max": 30.0,
                "step": 0.5,
                "unit": "seconds"
            },
            "description": "Time allocated per passenger for boarding",
            "display_name": "Boarding Time per Passenger",
            "ui_group": "Stop Duration",
            "requires_restart": False
        },
        {
            "section": "conductor.stop_duration",
            "parameter": "per_passenger_disembarking_time",
            "value": 5.0,
            "value_type": "number",
            "default_value": 5.0,
            "constraints": {
                "min": 1.0,
                "max": 20.0,
                "step": 0.5,
                "unit": "seconds"
            },
            "description": "Time allocated per passenger for disembarking",
            "display_name": "Disembarking Time per Passenger",
            "ui_group": "Stop Duration",
            "requires_restart": False
        },
        
        # Conductor - Operational Settings
        {
            "section": "conductor.operational",
            "parameter": "monitoring_interval_seconds",
            "value": 2.0,
            "value_type": "number",
            "default_value": 2.0,
            "constraints": {
                "min": 0.5,
                "max": 10.0,
                "step": 0.5,
                "unit": "seconds"
            },
            "description": "Interval for monitoring passenger status",
            "display_name": "Monitoring Interval",
            "ui_group": "Operational",
            "requires_restart": False
        },
        {
            "section": "conductor.operational",
            "parameter": "gps_precision_meters",
            "value": 10.0,
            "value_type": "number",
            "default_value": 10.0,
            "constraints": {
                "min": 1.0,
                "max": 100.0,
                "step": 1.0,
                "unit": "meters"
            },
            "description": "GPS precision for location tracking",
            "display_name": "GPS Precision",
            "ui_group": "Operational",
            "requires_restart": False
        },
        
        # Driver - Waypoint Settings
        {
            "section": "driver.waypoints",
            "parameter": "proximity_threshold_km",
            "value": 0.05,
            "value_type": "number",
            "default_value": 0.05,
            "constraints": {
                "min": 0.01,
                "max": 0.5,
                "step": 0.01,
                "unit": "kilometers"
            },
            "description": "Distance threshold for waypoint arrival detection (50 meters default)",
            "display_name": "Waypoint Proximity Threshold",
            "ui_group": "Waypoints",
            "requires_restart": False
        },
        {
            "section": "driver.waypoints",
            "parameter": "broadcast_interval_seconds",
            "value": 5.0,
            "value_type": "number",
            "default_value": 5.0,
            "constraints": {
                "min": 1.0,
                "max": 30.0,
                "step": 1.0,
                "unit": "seconds"
            },
            "description": "Interval for broadcasting location updates",
            "display_name": "Location Broadcast Interval",
            "ui_group": "Waypoints",
            "requires_restart": False
        },
        
        # Passenger Spawning Settings
        {
            "section": "passenger_spawning.rates",
            "parameter": "average_passengers_per_hour",
            "value": 30,
            "value_type": "number",
            "default_value": 30,
            "constraints": {
                "min": 1,
                "max": 500,
                "step": 1,
                "unit": "passengers/hour"
            },
            "description": "Average number of passengers spawned per hour",
            "display_name": "Passengers per Hour",
            "ui_group": "Spawn Rates",
            "requires_restart": False
        },
        {
            "section": "passenger_spawning.geographic",
            "parameter": "spawn_radius_meters",
            "value": 500.0,
            "value_type": "number",
            "default_value": 500.0,
            "constraints": {
                "min": 50.0,
                "max": 5000.0,
                "step": 50.0,
                "unit": "meters"
            },
            "description": "Radius around spawn points for passenger placement",
            "display_name": "Spawn Radius",
            "ui_group": "Geographic",
            "requires_restart": False
        }
    ]
    
    print("\n\n📦 Seed Data Ready")
    print(f"Will create {len(initial_configs)} initial configuration parameters")
    print("\nTo seed data after creating collection:")
    print("  python seed_operational_config.py")
    
    # Save to file for later seeding
    with open('operational_config_seed_data.json', 'w') as f:
        json.dump(initial_configs, f, indent=2)
    
    print(f"\n✅ Seed data saved to: operational_config_seed_data.json")
    
    return initial_configs


if __name__ == "__main__":
    print("="*80)
    print("PHASE 4 - STEP 1: CREATE OPERATIONAL CONFIGURATION COLLECTION")
    print("="*80)
    
    schema = create_collection_type()
    seed_data = seed_initial_data()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Create the collection in Strapi Admin UI (see instructions above)")
    print("2. Run: python seed_operational_config.py (to populate initial data)")
    print("3. Test: python test_step1_config_collection.py")
    print("="*80)
