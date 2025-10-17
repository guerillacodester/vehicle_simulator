"""
Simple test to see where the reservoirs are hanging during startup
"""

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)

async def test_depot_reservoir():
    """Test depot reservoir initialization"""
    from commuter_service.depot_reservoir import DepotReservoir
    
    print("=" * 80)
    print("DEPOT RESERVOIR STARTUP TEST")
    print("=" * 80)
    
    depot = DepotReservoir(
        socketio_url="http://localhost:1337",
        strapi_url="http://localhost:1337"
    )
    
    print("\n▶️  Starting depot reservoir...")
    
    try:
        await depot.start()
        print("\n✅ Depot reservoir started successfully!")
        
        # Wait a bit
        print("\n⏳ Waiting 10 seconds...")
        await asyncio.sleep(10)
        
        print("\n🛑 Stopping...")
        await depot.stop()
        print("✅ Stopped")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_depot_reservoir())
