#!/usr/bin/env python3
"""
DEBUG: Test what RouteSpawner actually receives from the API
"""
import asyncio
import httpx
import json

async def test_route_spawner_load():
    route_id = "gg3pv3z19hhm117v9xth5ezq"
    api_base = "http://localhost:1337/api"
    
    print("=" * 70)
    print("DEBUGGING RouteSpawner Config Loading")
    print("=" * 70)
    
    # Simulate what RouteSpawner does
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"{api_base}/spawn-configs?populate=*&filters[route][documentId][$eq]={route_id}"
        print(f"\n1. API Query URL:")
        print(f"   {url}")
        
        response = await client.get(url)
        data = response.json()
        
        print(f"\n2. API Response Status: {response.status_code}")
        print(f"   Total results: {len(data.get('data', []))}")
        
        if data.get('data') and len(data['data']) > 0:
            raw_config = data['data'][0]
            print(f"\n3. Raw Config Keys: {list(raw_config.keys())}")
            
            # Check if 'config' field exists (new JSON format)
            if 'config' in raw_config:
                print(f"\n4. ✅ 'config' field EXISTS (new JSON format)")
                config = raw_config['config']
                print(f"   Type: {type(config)}")
                print(f"   Keys: {list(config.keys()) if isinstance(config, dict) else 'NOT A DICT'}")
                
                if isinstance(config, dict):
                    print(f"\n5. Config Structure:")
                    for key, value in config.items():
                        if isinstance(value, dict):
                            print(f"   • {key}: dict with {len(value)} entries")
                            if key == 'distribution_params':
                                print(f"     - spatial_base: {value.get('spatial_base', 'MISSING')}")
                                print(f"     - spawn_radius_meters: {value.get('spawn_radius_meters', 'MISSING')}")
                        else:
                            print(f"   • {key}: {type(value).__name__}")
                    
                    # Test the actual code path
                    print(f"\n6. Simulating RouteSpawner Code:")
                    
                    # This is what the OLD code does (before our fix)
                    dist_params_old = raw_config.get('distribution_params', {})
                    print(f"   OLD: raw_config.get('distribution_params') = {dist_params_old}")
                    
                    # This is what the NEW code should do
                    spawn_config = config  # Extract config field
                    dist_params_new = spawn_config.get('distribution_params', {})
                    hourly_rates = spawn_config.get('hourly_rates', {})
                    day_multipliers = spawn_config.get('day_multipliers', {})
                    
                    print(f"\n   NEW (after fix):")
                    print(f"   • spawn_config = raw_config['config']")
                    print(f"   • dist_params = spawn_config.get('distribution_params')")
                    print(f"     → spatial_base: {dist_params_new.get('spatial_base', 'MISSING')}")
                    print(f"   • hourly_rates = spawn_config.get('hourly_rates')")
                    print(f"     → type: {type(hourly_rates)}, length: {len(hourly_rates) if isinstance(hourly_rates, dict) else 'N/A'}")
                    print(f"     → hour '17': {hourly_rates.get('17', 'MISSING')}")
                    print(f"   • day_multipliers = spawn_config.get('day_multipliers')")
                    print(f"     → type: {type(day_multipliers)}, length: {len(day_multipliers) if isinstance(day_multipliers, dict) else 'N/A'}")
                    print(f"     → day '3': {day_multipliers.get('3', 'MISSING')}")
                    
                    # Calculate what SHOULD happen
                    spatial_base = dist_params_new.get('spatial_base', 1.0)
                    hour_17_rate = float(hourly_rates.get('17', 0.5))
                    day_3_mult = float(day_multipliers.get('3', 1.0))
                    expected_lambda = spatial_base * hour_17_rate * day_3_mult
                    
                    print(f"\n7. Expected Spawn Calculation (5:24 PM Thursday):")
                    print(f"   lambda = {spatial_base} × {hour_17_rate} × {day_3_mult} = {expected_lambda:.2f}")
                    print(f"   Expected: ~{int(expected_lambda)}-{int(expected_lambda)+2} passengers")
                    
            else:
                print(f"\n4. ❌ 'config' field MISSING (old component format)")
                print(f"   Keys present: {list(raw_config.keys())}")
        else:
            print(f"\n❌ NO SPAWN CONFIG FOUND!")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    asyncio.run(test_route_spawner_load())
