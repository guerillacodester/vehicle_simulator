#!/usr/bin/env python3
"""
Test the integrated RedisServiceManager + Health Checker
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from arknet_transit_launcher.health.redis_health import RedisHealthChecker

async def test_integration():
    """Test the service manager integration"""

    print("🧪 Testing RedisServiceManager + Health Checker Integration")
    print("=" * 60)

    # Create health checker (will automatically use service manager)
    checker = RedisHealthChecker(redis_url="redis://localhost:6379")

    print("✓ Health checker initialized with service manager")

    # Check if service manager is available
    if checker.service_manager:
        print("✓ RedisServiceManager available")

        # Check service detection
        service_info = checker.service_manager.detect_service()
        print(f"✓ Service detection: {service_info}")

        # Check service status
        status = checker.service_manager.get_status()
        print(f"✓ Service status: {status}")
    else:
        print("✗ RedisServiceManager not available")

    # Perform health check
    print("\n🔍 Performing health check...")
    health_result = await checker.check_health()

    print("Health check result:")
    print(f"  State: {health_result.get('state')}")
    print(f"  Message: {health_result.get('message')}")
    print(f"  Service Status: {health_result.get('service_status')}")

    print("\n✅ Integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_integration())