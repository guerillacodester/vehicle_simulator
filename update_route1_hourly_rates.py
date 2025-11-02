#!/usr/bin/env python3
"""
Update Route 1 Spawn Config with Proper Hourly Rates

Sets realistic hourly multipliers for transit ridership.
"""

import requests

STRAPI_URL = "http://localhost:1337"

# Realistic hourly rates for a bus route (normalized 0.0-1.0)
# Peak hours: 6-9 AM (morning commute) and 4-7 PM (evening commute)
HOURLY_RATES = [
    0.05,  # 00:00 - Late night
    0.02,  # 01:00
    0.01,  # 02:00
    0.01,  # 03:00
    0.03,  # 04:00 - Early morning
    0.20,  # 05:00 - Pre-commute
    0.50,  # 06:00 - Morning commute starts
    0.80,  # 07:00 - Peak morning
    1.00,  # 08:00 - PEAK MORNING HOUR
    0.70,  # 09:00 - Post-peak
    0.40,  # 10:00
    0.35,  # 11:00
    0.40,  # 12:00 - Lunch
    0.35,  # 13:00
    0.30,  # 14:00
    0.35,  # 15:00
    0.60,  # 16:00 - Evening commute starts
    0.85,  # 17:00 - Peak evening
    0.70,  # 18:00
    0.45,  # 19:00
    0.25,  # 20:00
    0.15,  # 21:00
    0.10,  # 22:00
    0.07,  # 23:00
]

def update_spawn_config():
    """Update the spawn config for Route 1"""
    print("=" * 80)
    print("UPDATE ROUTE 1 SPAWN CONFIG - HOURLY RATES")
    print("=" * 80)
    print()
    
    # Get Route 1 spawn config
    print("Fetching Route 1 spawn config...")
    response = requests.get(
        f"{STRAPI_URL}/api/spawn-configs",
        params={
            "filters[route][documentId][$eq]": "gg3pv3z19hhm117v9xth5ezq"
        }
    )
    
    if response.status_code != 200:
        print(f"ERROR: Failed to fetch spawn config (status {response.status_code})")
        return
    
    configs = response.json().get("data", [])
    if not configs:
        print("ERROR: No spawn config found for Route 1")
        return
    
    config = configs[0]
    doc_id = config.get("documentId")
    print(f"✓ Found spawn config: {doc_id}")
    print()
    
    # Update with new hourly rates
    print("Updating hourly rates...")
    print("  Peak hours: 8 AM (1.0) and 5 PM (0.85)")
    print()
    
    update_data = {
        "data": {
            "hourly_rates": HOURLY_RATES
        }
    }
    
    response = requests.put(
        f"{STRAPI_URL}/api/spawn-configs/{doc_id}",
        json=update_data
    )
    
    if response.status_code == 200:
        print("=" * 80)
        print("✓ SUCCESS - Hourly rates updated!")
        print("=" * 80)
        print()
        print("Hourly Rate Distribution:")
        for hour, rate in enumerate(HOURLY_RATES):
            bar = "█" * int(rate * 50)
            print(f"  {hour:02d}:00  {rate:.2f}  {bar}")
        print()
    else:
        print(f"ERROR: Failed to update config (status {response.status_code})")
        print(response.text)


if __name__ == "__main__":
    update_spawn_config()
