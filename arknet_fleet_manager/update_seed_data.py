"""
Update seed data to use JSON-stringified values for text fields
"""
import json
from pathlib import Path

# Load existing seed data
seed_file = Path(__file__).parent / "operational_config_seed_data.json"
with open(seed_file) as f:
    configs = json.load(f)

# Convert value and default_value to JSON strings
for config in configs:
    # Convert value to JSON string
    config["value"] = json.dumps(config["value"])
    
    # Convert default_value to JSON string
    config["default_value"] = json.dumps(config["default_value"])
    
    # constraints is already an object, keep as is (will be stored as JSON)

# Save updated seed data
with open(seed_file, 'w') as f:
    json.dump(configs, f, indent=2)

print(f"✅ Updated {len(configs)} configurations")
print("Values and default_values are now JSON strings")
print("\nExample:")
print(json.dumps(configs[0], indent=2))
