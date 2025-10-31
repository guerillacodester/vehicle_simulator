"""
Startup script for all services in correct order with dependency checking.
"""
import requests
import time
import sys

BASE_URL = "http://localhost:7000"

def start_service(name):
    """Start a service and wait for it to become healthy."""
    print(f"\n{'='*70}")
    print(f"Starting {name}...")
    print('='*70)
    
    try:
        response = requests.post(f"{BASE_URL}/services/{name}/start")
        response.raise_for_status()
        result = response.json()
        print(f"✅ {result['message']}")
        
        # If service has health check, wait for it
        status_response = requests.get(f"{BASE_URL}/services/{name}/status")
        status = status_response.json()
        
        if status.get('health_url'):
            print(f"⏳ Waiting for {name} to become healthy...")
            max_attempts = 60  # 60 attempts = 60 seconds max
            for attempt in range(max_attempts):
                time.sleep(1)
                status_response = requests.get(f"{BASE_URL}/services/{name}/status")
                status = status_response.json()
                
                if status['state'] == 'healthy':
                    print(f"🎉 {name} is HEALTHY")
                    return True
                elif status['state'] == 'failed':
                    print(f"❌ {name} FAILED")
                    return False
                
                # Show progress
                if attempt % 5 == 0:
                    print(f"   Still waiting... ({attempt}s elapsed, state: {status['state']})")
            
            print(f"⚠️  {name} did not become healthy within {max_attempts} seconds")
            return False
        else:
            print(f"✅ {name} started (no health check)")
            return True
            
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to start {name}: {e.response.json()['detail']}")
        return False
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return False


def main():
    """Start all services in the correct order."""
    print("="*70)
    print("🚀 Starting ArkNet Fleet Services")
    print("="*70)
    
    # Define startup order with dependencies
    services = [
        ("strapi", "Strapi CMS (Foundation)"),
        ("gpscentcom", "GPSCentCom Server (depends on Strapi)"),
        ("geospatial", "Geospatial Service (depends on Strapi)"),
        ("manifest", "Manifest API (depends on Strapi)"),
    ]
    
    for service_name, description in services:
        if not start_service(service_name):
            print(f"\n❌ Startup aborted - {service_name} failed to start")
            sys.exit(1)
    
    print("\n" + "="*70)
    print("✅ ALL SERVICES STARTED SUCCESSFULLY")
    print("="*70)
    print("\n📊 Service Status:")
    
    # Show final status
    response = requests.get(f"{BASE_URL}/services")
    services_status = response.json()
    
    for svc in services_status:
        status_emoji = "🟢" if svc['state'] == 'healthy' else "🟡" if svc['state'] == 'running' else "🔴"
        print(f"   {status_emoji} {svc['name']:20s} - {svc['state']:10s} (port: {svc['port']})")
    
    print("\n💡 To view logs: http://localhost:7000/services/{name}/logs")
    print("💡 To stop a service: POST http://localhost:7000/services/{name}/stop")


if __name__ == "__main__":
    main()
