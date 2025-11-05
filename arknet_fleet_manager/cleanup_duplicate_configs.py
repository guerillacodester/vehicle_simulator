#!/usr/bin/env python3
"""
Cleanup Duplicate Operational Configurations
=============================================
Removes duplicate entries from operational-configurations collection,
keeping only the oldest entry for each (section, parameter) combination.
"""

import asyncio
import aiohttp
import json
from collections import defaultdict

STRAPI_URL = "http://localhost:1337"


async def cleanup_duplicates():
    """Remove duplicate configuration entries, keep oldest."""
    
    async with aiohttp.ClientSession() as session:
        # Fetch ALL configurations
        async with session.get(
            f"{STRAPI_URL}/api/operational-configurations",
            params={"pagination[limit]": 1000}
        ) as response:
            data = await response.json()
            configs = data.get('data', [])
        
        print(f"\n📊 Found {len(configs)} total configuration entries")
        
        # Group by (section, parameter)
        groups = defaultdict(list)
        for config in configs:
            section = config.get('section')
            parameter = config.get('parameter')
            key = (section, parameter)
            groups[key].append(config)
        
        print(f"📋 Grouped into {len(groups)} unique (section, parameter) combinations")
        
        # Find duplicates
        duplicates_to_delete = []
        for key, entries in groups.items():
            if len(entries) > 1:
                section, parameter = key
                print(f"\n⚠️  Found {len(entries)} duplicates for {section}.{parameter}")
                
                # Sort by createdAt, keep oldest
                entries_sorted = sorted(entries, key=lambda x: x.get('createdAt', ''))
                oldest = entries_sorted[0]
                duplicates = entries_sorted[1:]
                
                print(f"   ✅ Keeping ID {oldest['id']} (created: {oldest.get('createdAt')})")
                for dup in duplicates:
                    print(f"   🗑️  Deleting ID {dup['id']} (created: {dup.get('createdAt')})")
                    duplicates_to_delete.append(dup)
        
        if not duplicates_to_delete:
            print(f"\n✨ No duplicates found - database is clean!")
            return True
        
        # Ask for confirmation
        print(f"\n" + "="*80)
        print(f"⚠️  ABOUT TO DELETE {len(duplicates_to_delete)} DUPLICATE ENTRIES")
        print("="*80)
        confirmation = input("\nProceed with deletion? (yes/no): ")
        
        if confirmation.lower() != 'yes':
            print("❌ Deletion cancelled")
            return False
        
        # Delete duplicates
        deleted_count = 0
        error_count = 0
        
        for dup in duplicates_to_delete:
            try:
                doc_id = dup.get('documentId')
                async with session.delete(
                    f"{STRAPI_URL}/api/operational-configurations/{doc_id}"
                ) as response:
                    if response.status in [200, 204]:
                        deleted_count += 1
                        section = dup.get('section', 'unknown')
                        parameter = dup.get('parameter', 'unknown')
                        print(f"✅ Deleted duplicate: {section}.{parameter} (ID {dup['id']})")
                    else:
                        error_count += 1
                        error_text = await response.text()
                        print(f"❌ Failed to delete ID {dup['id']}: {response.status} - {error_text[:100]}")
            except Exception as e:
                error_count += 1
                print(f"❌ Exception deleting ID {dup['id']}: {e}")
        
        print(f"\n" + "="*80)
        print(f"CLEANUP RESULTS:")
        print(f"  ✅ Deleted: {deleted_count}")
        print(f"  ❌ Errors: {error_count}")
        print("="*80)
        
        return error_count == 0


if __name__ == "__main__":
    print("="*80)
    print("CLEANUP DUPLICATE OPERATIONAL CONFIGURATIONS")
    print("="*80)
    
    success = asyncio.run(cleanup_duplicates())
    
    if success:
        print("\n🎉 Cleanup completed successfully!")
    else:
        print("\n⚠️  Cleanup completed with some errors")
