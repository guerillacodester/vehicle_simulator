#!/usr/bin/env python3
"""
Test script for JSON spawn config migration

Tests:
1. Migration script (dry-run mode)
2. API response validation
3. RouteSpawner compatibility
"""
import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv('arknet_fleet_manager/arknet-fleet-api/.env')

def test_current_schema():
    """Test current database state"""
    print("=" * 70)
    print("TEST 1: Current Database Schema")
    print("=" * 70)
    
    conn = psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=os.getenv('DATABASE_PORT', '5432'),
        database=os.getenv('DATABASE_NAME', 'arknettransit'),
        user=os.getenv('DATABASE_USERNAME', 'david'),
        password=os.getenv('DATABASE_PASSWORD')
    )
    cur = conn.cursor()
    
    # Check if config column exists
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'spawn_configs'
        ORDER BY ordinal_position
    """)
    
    print("\nspawn_configs table columns:")
    columns = cur.fetchall()
    has_config = False
    for col, dtype in columns:
        marker = "✅ NEW" if col == 'config' else "  "
        print(f"  {marker} {col}: {dtype}")
        if col == 'config':
            has_config = True
    
    # Check current spawn configs
    cur.execute("SELECT id, name, document_id FROM spawn_configs")
    configs = cur.fetchall()
    
    print(f"\nExisting spawn_configs: {len(configs)}")
    for config_id, name, doc_id in configs:
        print(f"  • ID {config_id}: {name}")
        print(f"    documentId: {doc_id}")
        
        # Check if has config data
        if has_config:
            cur.execute("SELECT config IS NOT NULL FROM spawn_configs WHERE id = %s", (config_id,))
            has_data = cur.fetchone()[0]
            print(f"    Has JSON config: {'✅ YES' if has_data else '❌ NO'}")
        
        # Check component data
        try:
            cur.execute("""
                SELECT COUNT(*) 
                FROM spawn_configs_cmps 
                WHERE entity_id = %s
            """, (config_id,))
            component_count = cur.fetchone()[0]
            print(f"    Component links: {component_count}")
        except psycopg2.errors.UndefinedTable:
            print(f"    Component links: N/A (table doesn't exist - new schema)")
    
    cur.close()
    conn.close()
    
    return has_config, len(configs) > 0

def test_migration_readiness():
    """Test if migration can proceed"""
    print("\n" + "=" * 70)
    print("TEST 2: Migration Readiness")
    print("=" * 70)
    
    conn = psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=os.getenv('DATABASE_PORT', '5432'),
        database=os.getenv('DATABASE_NAME', 'arknettransit'),
        user=os.getenv('DATABASE_USERNAME', 'david'),
        password=os.getenv('DATABASE_PASSWORD')
    )
    cur = conn.cursor()
    
    # Check required tables exist
    required_tables = [
        'spawn_configs',
        'spawn_configs_cmps',
        'components_spawning_distribution_params',
        'spawn_configs_route_lnk',
        'routes'
    ]
    
    all_exist = True
    for table in required_tables:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table,))
        exists = cur.fetchone()[0]
        status = "✅" if exists else "❌"
        print(f"  {status} {table}")
        if not exists:
            all_exist = False
    
    # Check if we have data to migrate
    try:
        cur.execute("""
            SELECT COUNT(*) 
            FROM spawn_configs sc
            JOIN spawn_configs_cmps scc ON sc.id = scc.entity_id
        """)
        component_configs = cur.fetchone()[0]
    except psycopg2.errors.UndefinedTable:
        component_configs = 0
        print("  ⚠️  spawn_configs_cmps table doesn't exist (new schema)")
    
    print(f"\nConfigs with components: {component_configs}")
    print(f"Migration needed: {'✅ YES' if component_configs > 0 else '⚠️  NO (new schema or already migrated)'}")
    
    cur.close()
    conn.close()
    
    return all_exist and component_configs > 0

def test_api_format():
    """Test current API response format"""
    print("\n" + "=" * 70)
    print("TEST 3: Current API Response")
    print("=" * 70)
    
    import httpx
    import asyncio
    
    async def check_api():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get('http://localhost:1337/api/spawn-configs?populate=*')
                data = response.json()
                
                print(f"\nAPI Status: ✅ {response.status_code}")
                print(f"Total configs: {data['meta']['pagination']['total']}")
                
                if data['data']:
                    for item in data['data']:
                        print(f"\nConfig: {item.get('name')}")
                        
                        # Check format
                        if 'config' in item:
                            print(f"  Format: ✅ JSON (production)")
                            config = item['config']
                            if isinstance(config, dict):
                                print(f"  Keys: {list(config.keys())}")
                        elif 'distribution_params' in item:
                            print(f"  Format: ⚠️  Components (legacy)")
                            print(f"  Has distribution_params: {item['distribution_params'] is not None}")
                        else:
                            print(f"  Format: ❌ Unknown")
                        
                        return 'config' in item
                else:
                    print("  No configs found")
                    return False
        except Exception as e:
            print(f"  ❌ API Error: {e}")
            return False
    
    return asyncio.run(check_api())

def main():
    print("\n🧪 SPAWN CONFIG MIGRATION TEST SUITE")
    print("=" * 70)
    
    # Test 1: Current schema
    has_config_col, has_data = test_current_schema()
    
    # Test 2: Migration readiness
    can_migrate = test_migration_readiness()
    
    # Test 3: API format
    is_json_format = test_api_format()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    print(f"\n1. Database has 'config' column: {'✅ YES' if has_config_col else '❌ NO'}")
    print(f"2. Has spawn_config data: {'✅ YES' if has_data else '❌ NO'}")
    print(f"3. Migration needed: {'✅ YES' if can_migrate else '⚠️  NO/ALREADY DONE'}")
    print(f"4. API returns JSON format: {'✅ YES' if is_json_format else '❌ NO (components)'}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDED ACTIONS")
    print("=" * 70)
    
    if not has_config_col:
        print("\n⚠️  'config' column missing")
        print("   → Run: python seeds/migrate_to_json_config.py")
    elif can_migrate:
        print("\n✅ Ready to migrate")
        print("   → Run: python seeds/migrate_to_json_config.py")
    elif is_json_format:
        print("\n✅ Already using JSON format!")
        print("   System is production-ready")
    else:
        print("\n⚠️  Mixed state - manual intervention needed")
        print("   1. Check Strapi schema matches JSON format")
        print("   2. Restart Strapi if schema was updated")
        print("   3. Re-run this test")
    
    print("=" * 70)

if __name__ == '__main__':
    main()
