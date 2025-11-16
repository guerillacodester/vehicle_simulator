#!/usr/bin/env python3
"""
Test health checker directly
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from arknet_transit_launcher.health.redis_health import RedisHealthChecker

async def test_health():
    checker = RedisHealthChecker()
    result = await checker.check_health()
    print('🔍 Health Check Result')
    print('======================')
    print(f'State: {result["state"]}')
    print(f'Message: {result["message"]}')
    print(f'Latency: {result.get("latency_ms", "N/A")}')
    print(f'Service Status: {result.get("service_status", "None")}')

if __name__ == '__main__':
    asyncio.run(test_health())