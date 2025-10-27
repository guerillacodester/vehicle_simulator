#!/usr/bin/env python3
"""Update spawn config distribution_params in Strapi"""

import httpx
import json

# Get the current spawn config
url = 'http://localhost:1337/api/spawn-configs?populate=*&filters[route][documentId][$eq]=gg3pv3z19hhm117v9xth5ezq'
r = httpx.get(url)
config = r.json()['data'][0]
config_id = config['documentId']
print(f"Updating spawn config: {config_id}")

# Update distribution_params with actual values
update_data = {
    'data': {
        'distribution_params': [
            {
                'min_spawn_interval_seconds': 45,
                'passengers_per_building_per_hour': 0.3,
                'spawn_radius_meters': 800,
                'min_trip_distance_meters': 250,
                'trip_distance_mean_meters': 2000,
                'trip_distance_std_meters': 1000,
                'max_trip_distance_ratio': 0.95
            }
        ]
    }
}

# Send update
response = httpx.put(
    f'http://localhost:1337/api/spawn-configs/{config_id}?populate=distribution_params',
    json=update_data
)

print('Status:', response.status_code)
if response.status_code == 200:
    resp_data = response.json()['data']
    print('Response keys:', list(resp_data.keys()))
    if 'distribution_params' in resp_data:
        result = resp_data['distribution_params']
        print('✅ Updated distribution_params:')
        print(json.dumps(result, indent=2))
    else:
        print('distribution_params not in response, full data:')
        print(json.dumps(resp_data, indent=2)[:1000])
else:
    print('❌ Error:', response.text)
