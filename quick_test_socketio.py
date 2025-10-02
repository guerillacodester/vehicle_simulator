"""
Quick Start: Testing Socket.IO Foundation

This script provides a quick verification that Phase 1 is working correctly.
"""

import asyncio
import logging
from commuter_service.socketio_client import create_depot_client, EventTypes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def quick_test():
    """Quick Socket.IO connection and message test"""
    
    print("\n" + "=" * 60)
    print("QUICK START: Socket.IO Foundation Test")
    print("=" * 60 + "\n")
    
    # Step 1: Create client
    logger.info("Step 1: Creating Socket.IO client...")
    client = create_depot_client()
    
    # Step 2: Connect
    logger.info("Step 2: Connecting to Strapi Socket.IO server...")
    try:
        await client.connect()
        logger.info("✅ Connected successfully!")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("Make sure Strapi is running: cd arknet_fleet_manager/arknet-fleet-api && npm run dev")
        return False
    
    # Step 3: Send a test message
    logger.info("Step 3: Sending test message...")
    test_data = {
        "commuter_id": "TEST_001",
        "current_location": {"lat": 40.7128, "lon": -74.0060},
        "destination": {"lat": 40.7589, "lon": -73.9851},
        "direction": "outbound",
        "priority": 3,
        "max_walking_distance": 500,
        "spawn_time": "2025-10-02T10:00:00Z"
    }
    
    try:
        await client.emit_message(EventTypes.COMMUTER_SPAWNED, test_data)
        logger.info("✅ Message sent successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to send message: {e}")
        await client.disconnect()
        return False
    
    # Step 4: Check statistics
    logger.info("Step 4: Checking client statistics...")
    await asyncio.sleep(1)
    stats = client.get_stats()
    logger.info(f"📊 Messages Sent: {stats['messages_sent']}")
    logger.info(f"📊 Connected: {stats['connected']}")
    logger.info(f"📊 Namespace: {stats['namespace']}")
    
    # Step 5: Disconnect
    logger.info("Step 5: Disconnecting...")
    await client.disconnect()
    logger.info("✅ Disconnected successfully!")
    
    print("\n" + "=" * 60)
    print("✅ QUICK TEST PASSED! Socket.IO Foundation is working!")
    print("=" * 60 + "\n")
    print("Next Steps:")
    print("1. Run full test suite: python test_socketio_infrastructure.py")
    print("2. Proceed to Phase 2: Commuter Service with Reservoirs")
    print("=" * 60 + "\n")
    
    return True


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITE: Start Strapi server first!")
    print("   cd arknet_fleet_manager/arknet-fleet-api && npm run dev\n")
    
    input("Press ENTER when Strapi is running...")
    
    success = asyncio.run(quick_test())
    
    if not success:
        print("\n❌ Quick test failed. See errors above.")
        exit(1)
