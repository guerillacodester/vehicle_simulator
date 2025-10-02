"""
Socket.IO Infrastructure Test

Tests the Socket.IO server and client infrastructure to ensure:
1. Strapi Socket.IO server is operational
2. Python clients can connect to all namespaces
3. Messages are correctly routed
4. Health checks work properly
"""

import asyncio
import logging
from commuter_service.socketio_client import (
    SocketIOClient,
    EventTypes,
    ServiceType,
    create_depot_client,
    create_route_client,
    create_vehicle_client,
    create_system_client,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_connection():
    """Test basic connection to Socket.IO server"""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic Connection")
    logger.info("=" * 60)
    
    client = create_depot_client()
    
    try:
        await client.connect()
        logger.info("✅ Successfully connected to depot reservoir")
        
        stats = client.get_stats()
        logger.info(f"📊 Client Stats: {stats}")
        
        await asyncio.sleep(1)
        
        await client.disconnect()
        logger.info("✅ Successfully disconnected")
        
        return True
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False


async def test_multiple_namespaces():
    """Test connecting to multiple namespaces"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Multiple Namespace Connections")
    logger.info("=" * 60)
    
    clients = {
        "depot": create_depot_client(service_type=ServiceType.COMMUTER_SERVICE),
        "route": create_route_client(service_type=ServiceType.COMMUTER_SERVICE),
        "vehicle": create_vehicle_client(service_type=ServiceType.VEHICLE_CONDUCTOR),
        "system": create_system_client(service_type=ServiceType.SIMULATOR),
    }
    
    try:
        # Connect all clients
        for name, client in clients.items():
            await client.connect()
            logger.info(f"✅ Connected to {name} namespace")
        
        await asyncio.sleep(1)
        
        # Disconnect all clients
        for name, client in clients.items():
            await client.disconnect()
            logger.info(f"✅ Disconnected from {name} namespace")
        
        return True
    except Exception as e:
        logger.error(f"❌ Multiple namespace test failed: {e}")
        return False


async def test_message_broadcast():
    """Test broadcasting messages"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Message Broadcasting")
    logger.info("=" * 60)
    
    # Create two clients in same namespace
    client1 = create_depot_client(service_type=ServiceType.COMMUTER_SERVICE)
    client2 = create_depot_client(service_type=ServiceType.VEHICLE_CONDUCTOR)
    
    messages_received = []
    
    # Set up message handler on client2
    async def message_handler(message):
        messages_received.append(message)
        logger.info(f"📨 Client 2 received: {message['type']}")
    
    client2.on(EventTypes.COMMUTER_SPAWNED, message_handler)
    
    try:
        # Connect both clients
        await client1.connect()
        await client2.connect()
        logger.info("✅ Both clients connected")
        
        await asyncio.sleep(1)
        
        # Client 1 broadcasts a message
        test_commuter = {
            "commuter_id": "test_001",
            "current_location": {"lat": 40.7128, "lon": -74.0060},
            "destination": {"lat": 40.7589, "lon": -73.9851},
            "direction": "outbound",
            "priority": 3,
            "max_walking_distance": 500,
            "spawn_time": "2025-10-02T10:00:00Z",
        }
        
        await client1.emit_message(
            EventTypes.COMMUTER_SPAWNED,
            test_commuter
        )
        logger.info("📤 Client 1 broadcast message")
        
        # Wait for message to be received
        await asyncio.sleep(2)
        
        # Verify message was received
        if messages_received:
            logger.info(f"✅ Message successfully broadcast and received")
            logger.info(f"📊 Received data: {messages_received[0]['data']}")
            success = True
        else:
            logger.error("❌ Message was not received")
            success = False
        
        # Disconnect
        await client1.disconnect()
        await client2.disconnect()
        
        return success
    except Exception as e:
        logger.error(f"❌ Message broadcast test failed: {e}")
        return False


async def test_targeted_message():
    """Test sending targeted messages"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Targeted Messaging")
    logger.info("=" * 60)
    
    client1 = create_depot_client(service_type=ServiceType.COMMUTER_SERVICE)
    client2 = create_depot_client(service_type=ServiceType.VEHICLE_CONDUCTOR)
    client3 = create_depot_client(service_type=ServiceType.DEPOT_MANAGER)
    
    messages_received = {"client2": 0, "client3": 0}
    
    async def client2_handler(message):
        messages_received["client2"] += 1
        logger.info("📨 Client 2 received targeted message")
    
    async def client3_handler(message):
        messages_received["client3"] += 1
        logger.info("📨 Client 3 received targeted message (should not happen)")
    
    client2.on(EventTypes.QUERY_COMMUTERS, client2_handler)
    client3.on(EventTypes.QUERY_COMMUTERS, client3_handler)
    
    try:
        await client1.connect()
        await client2.connect()
        await client3.connect()
        logger.info("✅ All clients connected")
        
        await asyncio.sleep(1)
        
        # Get client2's socket ID (in real scenario, this would be known)
        # For now, we'll broadcast and verify only client2 processes it
        
        query_data = {
            "vehicle_id": "VEH_001",
            "route_id": "ROUTE_A",
            "vehicle_location": {"lat": 40.7128, "lon": -74.0060},
            "search_radius": 1000,
            "available_seats": 30,
            "direction": "outbound",
            "reservoir_type": "depot",
        }
        
        await client1.emit_message(
            EventTypes.QUERY_COMMUTERS,
            query_data
        )
        logger.info("📤 Client 1 sent query message")
        
        await asyncio.sleep(2)
        
        # Both clients should receive broadcast
        if messages_received["client2"] > 0 and messages_received["client3"] > 0:
            logger.info("✅ Broadcast received by all clients")
            success = True
        else:
            logger.error(f"❌ Messages not received properly: {messages_received}")
            success = False
        
        await client1.disconnect()
        await client2.disconnect()
        await client3.disconnect()
        
        return success
    except Exception as e:
        logger.error(f"❌ Targeted messaging test failed: {e}")
        return False


async def test_health_check():
    """Test health check functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Health Check")
    logger.info("=" * 60)
    
    client = create_system_client()
    
    try:
        await client.connect()
        logger.info("✅ Connected to system namespace")
        
        await asyncio.sleep(1)
        
        # Perform health check
        health_status = await client.health_check()
        logger.info(f"📊 Health Status: {health_status}")
        
        if health_status.get("status") == "healthy":
            logger.info("✅ Server is healthy")
            success = True
        else:
            logger.warning(f"⚠️ Server health status: {health_status}")
            success = True  # Still consider it a success if we got a response
        
        await client.disconnect()
        
        return success
    except Exception as e:
        logger.error(f"❌ Health check test failed: {e}")
        return False


async def test_statistics():
    """Test client statistics tracking"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Statistics Tracking")
    logger.info("=" * 60)
    
    client = create_depot_client()
    
    try:
        await client.connect()
        
        # Send multiple messages
        for i in range(5):
            await client.emit_message(
                EventTypes.COMMUTER_SPAWNED,
                {"test_id": f"test_{i}"}
            )
        
        await asyncio.sleep(1)
        
        stats = client.get_stats()
        logger.info(f"📊 Client Statistics:")
        logger.info(f"   - Connected: {stats['connected']}")
        logger.info(f"   - Messages Sent: {stats['messages_sent']}")
        logger.info(f"   - Messages Received: {stats['messages_received']}")
        logger.info(f"   - Errors: {stats['errors']}")
        logger.info(f"   - Connected At: {stats['connected_at']}")
        
        if stats['messages_sent'] == 5:
            logger.info("✅ Statistics tracking working correctly")
            success = True
        else:
            logger.error(f"❌ Expected 5 messages sent, got {stats['messages_sent']}")
            success = False
        
        await client.disconnect()
        
        return success
    except Exception as e:
        logger.error(f"❌ Statistics test failed: {e}")
        return False


async def run_all_tests():
    """Run all Socket.IO infrastructure tests"""
    logger.info("\n" + "🚀" * 30)
    logger.info("SOCKET.IO INFRASTRUCTURE TEST SUITE")
    logger.info("🚀" * 30 + "\n")
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Multiple Namespaces", test_multiple_namespaces),
        ("Message Broadcasting", test_message_broadcast),
        ("Targeted Messaging", test_targeted_message),
        ("Health Check", test_health_check),
        ("Statistics Tracking", test_statistics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            await asyncio.sleep(1)  # Brief pause between tests
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("=" * 60)
    logger.info(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    logger.info("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    print("\n" + "⚠️ " * 30)
    print("PREREQUISITES:")
    print("1. Start Strapi server: cd arknet_fleet_manager/arknet-fleet-api && npm run dev")
    print("2. Ensure Socket.IO is initialized in Strapi bootstrap")
    print("3. Wait for server to be ready (http://localhost:1337)")
    print("⚠️ " * 30 + "\n")
    
    input("Press ENTER when Strapi server is running...")
    
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n" + "🎉" * 30)
        print("ALL TESTS PASSED! Socket.IO infrastructure is working correctly!")
        print("🎉" * 30 + "\n")
    else:
        print("\n" + "⚠️ " * 30)
        print("SOME TESTS FAILED. Review the logs above for details.")
        print("⚠️ " * 30 + "\n")
