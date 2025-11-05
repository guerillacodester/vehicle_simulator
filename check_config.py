#!/usr/bin/env python3
"""Quick script to check Strapi operational configuration"""
import asyncio
import httpx
import json

async def check_config():
    async with httpx.AsyncClient(timeout=10) as client:
        # Check pickup_radius_km
        resp = await client.get(
            'http://localhost:1337/api/operational-configurations',
            params={'filters[parameter][$eq]': 'pickup_radius_km'}
        )
        data = resp.json()
        
        print(f"Status: {resp.status_code}")
        print(f"Found {len(data.get('data', []))} config(s)")
        
        if data.get('data'):
            for item in data['data']:
                attrs = item.get('attributes', {})
                print(f"\nConfig found:")
                print(f"  Section: {attrs.get('section')}")
                print(f"  Parameter: {attrs.get('parameter')}")
                print(f"  Value: {attrs.get('value')}")
                print(f"  Type: {attrs.get('value_type')}")
                print(f"  Default: {attrs.get('default_value')}")
        else:
            print("\n⚠️  NO CONFIG FOUND - pickup_radius_km not in Strapi!")
            print("This should cause simulator to fail with our Phase 2 changes.")
        
        print(json.dumps(data, indent=2))

if __name__ == '__main__':
    asyncio.run(check_config())
