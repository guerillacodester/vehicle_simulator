"""
Seed Operational Configuration Data
====================================
Populates the operational-configurations collection with initial parameters.
Run this after creating the collection in Strapi.
"""

import asyncio
import aiohttp
import json
from pathlib import Path

STRAPI_URL = "http://localhost:1337"


async def seed_configurations():
    """Seed initial configuration data into Strapi."""
    
    # Load seed data
    seed_file = Path(__file__).parent / "operational_config_seed_data.json"
    
    if not seed_file.exists():
        print("❌ Seed data file not found!")
        print("Run: python create_operational_config_collection.py first")
        return False
    
    with open(seed_file) as f:
        configs = json.load(f)
    
    print(f"\n📦 Loading {len(configs)} configuration parameters...")
    
    async with aiohttp.ClientSession() as session:
        created_count = 0
        error_count = 0
        
        for config in configs:
            try:
                # Create configuration entry
                async with session.post(
                    f"{STRAPI_URL}/api/operational-configurations",
                    json={"data": config},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status in [200, 201]:
                        created_count += 1
                        print(f"✅ Created: {config['section']}.{config['parameter']}")
                    else:
                        error_count += 1
                        error_text = await response.text()
                        print(f"❌ Failed: {config['section']}.{config['parameter']}")
                        print(f"   Status: {response.status}")
                        print(f"   Error: {error_text[:200]}")
            
            except Exception as e:
                error_count += 1
                print(f"❌ Exception for {config['section']}.{config['parameter']}: {e}")
        
        print(f"\n" + "="*80)
        print(f"RESULTS:")
        print(f"  ✅ Created: {created_count}")
        print(f"  ❌ Errors: {error_count}")
        print("="*80)
        
        return error_count == 0


if __name__ == "__main__":
    print("="*80)
    print("SEEDING OPERATIONAL CONFIGURATION DATA")
    print("="*80)
    
    success = asyncio.run(seed_configurations())
    
    if success:
        print("\n🎉 All configurations seeded successfully!")
        print("\nNext: Run test_step1_config_collection.py to verify")
    else:
        print("\n⚠️  Some configurations failed to seed")
        print("Check that:")
        print("  1. Strapi is running (http://localhost:1337)")
        print("  2. operational-configurations collection exists")
        print("  3. API permissions are enabled")
