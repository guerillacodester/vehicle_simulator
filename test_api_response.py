#!/usr/bin/env python3
"""Test what spawn-config API actually returns"""

import httpx
import json

async def test_api():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:1337/api/spawn-configs?"
            "populate=*&filters[route][documentId][$eq]=gg3pv3z19hhm117v9xth5ezq"
        )
        print("=== API RESPONSE ===")
        print(f"Status: {response.status_code}")
        data = response.json()
        
        if data.get('data') and len(data['data']) > 0:
            raw_config = data['data'][0]
            print(f"\nRaw config keys: {raw_config.keys()}")
            
            if 'config' in raw_config:
                config = raw_config['config']
                print(f"\n✅ Found 'config' field!")
                print(f"Config keys: {config.keys()}")
                
                if 'distribution_params' in config:
                    print(f"\nDistribution params: {config['distribution_params']}")
                
                if 'hourly_rates' in config:
                    print(f"\nHourly rates (sample): hour 16={config['hourly_rates'].get('16')}, hour 17={config['hourly_rates'].get('17')}")
                
                if 'day_multipliers' in config:
                    print(f"\nDay multipliers (sample): Monday={config['day_multipliers'].get('0')}, Thursday={config['day_multipliers'].get('3')}")
            else:
                print(f"\n❌ NO 'config' field found!")
                print(f"Full response: {json.dumps(raw_config, indent=2)[:500]}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api())
