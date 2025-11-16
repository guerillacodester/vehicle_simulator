#!/usr/bin/env python3
"""
Demonstration: How the Unified RedisServiceManager Works
========================================================

This script shows the unified cross-platform Redis service management in action.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from arknet_transit_launcher.health.redis_service_manager import RedisServiceManager

def demonstrate_unified_approach():
    """Demonstrate the unified Redis service management approach."""

    print("🔧 Unified Redis Service Manager Demonstration")
    print("=" * 50)

    # Create manager (same API on all platforms)
    manager = RedisServiceManager()

    print(f"📍 Platform: {manager._adapter_available}")
    print(f"🔌 Adapter Type: {manager.__class__.__module__.split('.')[-1]}")

    # Step 1: Detect Redis service
    print("\n1️⃣ Detecting Redis Service...")
    service_info = manager.detect_service()

    if service_info.exists:
        print(f"✅ Found Redis service: {service_info.name}")
        print(f"   Scope: {service_info.scope}")
    else:
        print(f"❌ No Redis service found: {service_info.reason}")
        print("   (This is normal if Redis isn't installed as a service)")

    # Step 2: Check status
    print("\n2️⃣ Checking Service Status...")
    status = manager.get_status()

    print(f"🏃 Running: {status.is_running}")
    print(f"🔄 Enabled: {status.is_enabled}")
    print(f"📝 Message: {status.status_message}")

    # Step 3: Service management (would work if service exists)
    print("\n3️⃣ Service Management Operations...")

    if service_info.exists:
        print("🔄 Ensuring service is running...")
        running_result = manager.ensure_running()
        print(f"   Result: {'✅ Success' if running_result else '❌ Failed'}")

        print("🔧 Ensuring auto-start...")
        autostart_result = manager.ensure_auto_start()
        print(f"   Result: {'✅ Success' if autostart_result else '❌ Failed'}")
    else:
        print("⏭️  Skipping service operations (no service detected)")

    # Step 4: Show unified API
    print("\n4️⃣ Unified API Demonstration...")
    print("   Same methods work on Linux & Windows:")
    print("   • detect_service() → ServiceInfo")
    print("   • get_status() → ServiceStatus")
    print("   • ensure_running() → bool")
    print("   • ensure_auto_start() → bool")
    print("   • stop_service() → bool")
    print("   • restart_service() → bool")

    # Step 5: Platform abstraction
    print("\n5️⃣ Platform Abstraction...")
    print("   Linux: Uses systemd adapter")
    print("   Windows: Uses windows_service adapter")
    print("   Both provide identical API to RedisServiceManager")

    print("\n🎯 Key Benefits:")
    print("   ✅ No polling - direct OS service status")
    print("   ✅ Cross-platform - same code on Linux/Windows")
    print("   ✅ Automatic startup - integrates with OS boot")
    print("   ✅ Immediate status - no 30-second delays")
    print("   ✅ Resource efficient - OS handles monitoring")

    print("\n✨ This eliminates Redis connection spam and provides true resilience!")

if __name__ == "__main__":
    demonstrate_unified_approach()