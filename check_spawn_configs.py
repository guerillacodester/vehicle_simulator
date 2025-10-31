"""Check spawn-configs in Strapi database"""
import httpx
import asyncio
import json

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Get spawn-configs
        response = await client.get('http://localhost:1337/api/spawn-configs?populate=*')
        data = response.json()
        
        print(f"\n=== SPAWN-CONFIGS ===")
        print(f"Total: {data['meta']['pagination']['total']}")
        
        if data['data']:
            for item in data['data']:
                route_name = item.get('route', {}).get('short_name', 'N/A') if item.get('route') else 'NO ROUTE'
                route_id = item.get('route', {}).get('documentId', 'N/A') if item.get('route') else 'N/A'
                print(f"\nConfig: {item.get('name')}")
                print(f"  ID: {item.get('id')}")
                print(f"  Route: {route_name} (documentId: {route_id})")
                
                # Check if using new JSON format or old components
                if 'config' in item:
                    config = item['config']
                    print(f"  Format: ✅ JSON (production)")
                    print(f"  Config structure:")
                    if isinstance(config, dict):
                        for key in config.keys():
                            if isinstance(config[key], dict):
                                print(f"    • {key}: {len(config[key])} entries")
                            else:
                                print(f"    • {key}: {type(config[key]).__name__}")
                        
                        # Show distribution params details
                        if 'distribution_params' in config:
                            dp = config['distribution_params']
                            print(f"  Distribution params:")
                            print(f"    • spatial_base: {dp.get('spatial_base', 'N/A')}")
                            print(f"    • spawn_radius: {dp.get('spawn_radius_meters', 'N/A')}m")
                        
                        if 'hourly_rates' in config:
                            hr = config['hourly_rates']
                            print(f"  Hourly rates: {len(hr)} hours configured")
                            peak_hour = max(hr.items(), key=lambda x: float(x[1]))
                            print(f"    • Peak hour: {peak_hour[0]} ({peak_hour[1]}x)")
                        
                        if 'day_multipliers' in config:
                            dm = config['day_multipliers']
                            print(f"  Day multipliers: {len(dm)} days configured")
                            print(f"    • Weekday (0): {dm.get('0', 'N/A')}x")
                            print(f"    • Sunday (6): {dm.get('6', 'N/A')}x")
                    else:
                        print(f"  Config: {json.dumps(config, indent=2)}")
                        
                elif 'distribution_params' in item:
                    print(f"  Format: ⚠️  Components (legacy)")
                    print(f"  Distribution Params: {json.dumps(item['distribution_params'], indent=2)}")
                else:
                    print(f"  Format: ❌ Invalid (no config data)")
        else:
            print("\n⚠️  NO SPAWN-CONFIGS FOUND IN DATABASE")

if __name__ == '__main__':
    asyncio.run(main())
