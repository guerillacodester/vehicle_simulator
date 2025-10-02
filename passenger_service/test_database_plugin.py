"""
Test Database-First Passenger Plugin System
==========================================

This script demonstrates the database-first approach where passenger behavior
configurations are loaded from Strapi database instead of file-based plugins.
"""

import asyncio
import sys
from pathlib import Path

# Add the passenger_service to path
sys.path.append(str(Path(__file__).parent))

from database_plugin_system import get_database_plugin_manager
from datetime import datetime

async def test_database_plugin_system():
    """Test the database-first plugin system"""
    
    print("🔄 Testing Database-First Passenger Plugin System")
    print("-" * 50)
    
    try:
        # Get the database plugin manager
        manager = await get_database_plugin_manager()
        
        # Get available countries from database
        print("📋 Loading countries from Strapi database...")
        countries = await manager.get_available_countries()
        print(f"✅ Found {len(countries)} countries: {list(countries.keys())}")
        
        if 'bb' in countries:
            print(f"\n🏝️ Testing Barbados plugin...")
            
            # Set Barbados as active country
            success = await manager.set_country('bb')
            if success:
                print(f"✅ Successfully loaded Barbados plugin from database")
                
                # Get current plugin
                plugin = manager.get_current_plugin()
                if plugin:
                    # Test spawn rate modifiers
                    rush_hour = datetime(2025, 10, 1, 7, 30)  # 7:30 AM weekday
                    modifier = manager.get_spawn_rate_modifier(rush_hour, 'residential')
                    print(f"🚌 Rush hour spawn modifier: {modifier:.2f}x")
                    
                    # Test trip purposes
                    purposes = manager.get_trip_purpose_distribution(rush_hour, 'residential')
                    print("🎯 Trip purposes during rush hour:")
                    for purpose, percentage in purposes.items():
                        print(f"   {purpose}: {percentage:.1%}")
                    
                    # Get cultural metadata
                    metadata = plugin.get_cultural_metadata()
                    print(f"\n📊 Cultural metadata:")
                    print(f"   Country: {metadata['country_name']} ({metadata['country_code']})")
                    print(f"   Timezone: {metadata.get('timezone', 'Not set')}")
                    print(f"   Currency: {metadata.get('currency', 'Not set')}")
                    print(f"   API-driven: {metadata.get('api_driven', False)}")
                    
                    # Show configuration source
                    print(f"\n⚙️ Configuration loaded from database:")
                    config = metadata.get('plugin_config', {})
                    print(f"   Base spawn rate: {config.get('base_spawn_rate', 'Not set')}")
                    print(f"   Rush hour multiplier: {config.get('rush_hour_multiplier', 'Not set')}")
                    print(f"   Weekend multiplier: {config.get('weekend_multiplier', 'Not set')}")
                    print(f"   Walking distance: {config.get('walking_distance_meters', 'Not set')}m")
                else:
                    print("❌ No plugin instance available")
            else:
                print("❌ Failed to load Barbados plugin")
                print("   This is expected if the database content types don't exist yet")
                print("   Create the content types as described in STRAPI_CONTENT_TYPES.md")
        else:
            print("❌ Barbados (BB) not found in database countries")
            print("   Available countries:", list(countries.keys()))
    
    except Exception as e:
        print(f"❌ Error testing database plugin system: {e}")
        print("\n💡 This is expected if:")
        print("   1. Strapi is not running on http://localhost:1337")
        print("   2. The required content types haven't been created yet")
        print("   3. No passenger plugin configurations exist in the database")
        print("\n🔧 To fix:")
        print("   1. Start Strapi server")
        print("   2. Create content types from STRAPI_CONTENT_TYPES.md") 
        print("   3. Add sample configuration data")

if __name__ == "__main__":
    asyncio.run(test_database_plugin_system())