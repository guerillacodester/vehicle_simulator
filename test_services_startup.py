#!/usr/bin/env python3
"""
Test script to start all services and show status
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:6000"


async def show_services():
    """Show current services status"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/services/status")
            data = response.json()
            
            print("\n" + "="*80)
            print("📊 SERVICES STATUS")
            print("="*80)
            
            services = data.get('services', {})
            for name, svc in services.items():
                status = svc.get('status', 'unknown')
                pid = svc.get('pid', 'N/A')
                uptime = svc.get('uptime')
                uptime_str = f"{int(uptime)}s" if uptime and uptime != 'N/A' else "N/A"
                
                status_emoji = {
                    'running': '🟢',
                    'stopped': '🔴',
                    'starting': '🟡',
                    'error': '❌'
                }.get(status, '⚪')
                
                print(f"{status_emoji} {name:20} | Status: {status:10} | PID: {str(pid):6} | Uptime: {uptime_str}")
            
            print("="*80 + "\n")
        except Exception as e:
            print(f"❌ Error: {e}")


async def start_service(service_name: str):
    """Start a specific service"""
    print(f"\n🚀 Starting {service_name}...")
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            payload = {
                "api_port": None,
                "sim_time": None,
                "enable_boarding_after": None,
                "data_api_url": None
            }
            response = await client.post(
                f"{BASE_URL}/api/services/{service_name}/start",
                json=payload
            )
            data = response.json()
            
            if data.get('success'):
                print(f"✅ {data.get('message', 'Started')}")
                if data.get('data'):
                    if data['data'].get('pid'):
                        print(f"   PID: {data['data']['pid']}")
                    if data['data'].get('api_url'):
                        print(f"   API: {data['data']['api_url']}")
            else:
                print(f"❌ Failed: {data.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main test function"""
    print("\n" + "="*80)
    print("🚀 ArkNet Multi-Service Startup Test")
    print("="*80)
    
    # Show initial status
    await show_services()
    
    # Start services one by one with status checks
    services_to_start = ["gpscentcom", "commuter_service", "geospatial", "simulator"]
    
    for service in services_to_start:
        await start_service(service)
        await asyncio.sleep(2)  # Wait 2 seconds between starts
        await show_services()
    
    print("\n" + "="*80)
    print("✅ All services started!")
    print("="*80)
    print("\nNext: Connect console with: python -m clients.fleet")
    print("Then run: vehicles")
    print("         start <vehicle_id>")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
