import requests
import json

# Fetch all spawn configs
response = requests.get('http://localhost:1337/api/spawn-configs?populate=*')
configs = response.json()['data']

print("=" * 80)
print("SPAWN-CONFIG SCOPE ANALYSIS")
print("=" * 80)
print()
print(f"Total spawn-configs in database: {len(configs)}")
print()

for config in configs:
    print(f"Config ID: {config['id']}")
    print(f"  Name: {config.get('name', 'N/A')}")
    country = config.get('country')
    country_name = country.get('name') if country else 'N/A'
    print(f"  Country: {country_name}")
    print(f"  Building weights: {len(config.get('building_weights', []))}")
    print(f"  POI weights: {len(config.get('poi_weights', []))}")
    print(f"  Hourly rates: {len(config.get('hourly_spawn_rates', []))}")
    print(f"  Day multipliers: {len(config.get('day_multipliers', []))}")
    print()

print("=" * 80)
print("ARCHITECTURE ANALYSIS")
print("=" * 80)
print()

# Check if configs are country-based
countries = set()
for config in configs:
    country = config.get('country')
    if country:
        countries.add(country.get('name'))

if len(configs) == 1:
    print("✓ Single universal spawn-config (applies to all routes)")
elif len(countries) == len(configs):
    print("✓ Country-based spawn-configs (one per country)")
    print(f"  Countries: {', '.join(countries)}")
else:
    print("⚠ Mixed architecture (some with countries, some without)")

print()
print("SCOPE:")
print("  These hourly rates apply to: ", end="")

if len(configs) == 1 and not configs[0].get('country'):
    print("ALL ROUTES GLOBALLY")
    print("  ⚠ This means rural and urban routes use SAME temporal patterns!")
elif len(configs) >= 1:
    has_country = any(c.get('country') for c in configs)
    if has_country:
        country_name = next((c.get('country', {}).get('name') for c in configs if c.get('country')), 'Unknown')
        print(f"COUNTRY-LEVEL ({country_name.upper() if country_name else 'N/A'})")
        print(f"  ⚠ This means rural St Lucy and urban Bridgetown use SAME rates!")
    else:
        print("ALL ROUTES GLOBALLY")
else:
    print("DIFFERENT PATTERNS PER COUNTRY")

print()
print("RECOMMENDATION:")
print("  For realistic simulations, you may need:")
print("  1. Regional spawn-configs (urban vs rural)")
print("  2. Route-specific overrides for special cases")
print("  3. Or: Accept that temporal patterns are country-wide averages")
