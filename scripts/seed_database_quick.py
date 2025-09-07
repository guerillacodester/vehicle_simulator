#!/usr/bin/env python3
"""
Quick Database Seeder
Populates the database with sample fleet data for testing
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test if the API is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is accessible")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return False

def get_existing_country_id():
    """Get an existing country ID from the database"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/countries")
        if response.status_code == 200:
            countries = response.json()
            if countries:
                return countries[0]['country_id']
        return None
    except Exception as e:
        print(f"❌ Error getting countries: {e}")
        return None

def get_existing_depot_id():
    """Get an existing depot ID from the database"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/depots")
        if response.status_code == 200:
            depots = response.json()
            if depots:
                return depots[0]['depot_id']
        return None
    except Exception as e:
        print(f"❌ Error getting depots: {e}")
        return None

def seed_vehicles():
    """Seed vehicle data using existing country ID"""
    country_id = get_existing_country_id()
    if not country_id:
        print("❌ No existing country found. Please create a country first.")
        return
    
    vehicles = [
        {
            "country_id": country_id,
            "reg_code": "BBX-1234",
            "status": "available"
        },
        {
            "country_id": country_id,
            "reg_code": "BBX-5678", 
            "status": "available"
        },
        {
            "country_id": country_id,
            "reg_code": "BBX-9012",
            "status": "maintenance"
        },
        {
            "country_id": country_id,
            "reg_code": "BBX-3456",
            "status": "available"
        },
        {
            "country_id": country_id,
            "reg_code": "BBX-7890",
            "status": "retired"
        }
    ]
    
    print(f"\n🚐 Seeding Vehicles (using country_id: {country_id[:8]}...)...")
    for vehicle in vehicles:
        try:
            response = requests.post(f"{BASE_URL}/api/v1/vehicles", json=vehicle)
            if response.status_code in [200, 201]:
                print(f"  ✅ Added vehicle: {vehicle['reg_code']}")
            elif response.status_code == 409:
                print(f"  ⚠️ Vehicle already exists: {vehicle['reg_code']}")
            else:
                print(f"  ❌ Failed to add vehicle {vehicle['reg_code']}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error adding vehicle {vehicle['reg_code']}: {e}")

def seed_drivers():
    """Seed driver data using existing country ID"""
    country_id = get_existing_country_id()
    if not country_id:
        print("❌ No existing country found. Please create a country first.")
        return
    
    drivers = [
        {
            "country_id": country_id,
            "employee_id": "EMP001",
            "name": "John Smith",
            "license_no": "LIC001",
            "phone_number": "+1-246-555-0123",
            "email": "john.smith@arknet.bb"
        },
        {
            "country_id": country_id,
            "employee_id": "EMP002",
            "name": "Jane Doe",
            "license_no": "LIC002",
            "phone_number": "+1-246-555-0124",
            "email": "jane.doe@arknet.bb"
        },
        {
            "country_id": country_id,
            "employee_id": "EMP003",
            "name": "Michael Johnson",
            "license_no": "LIC003",
            "phone_number": "+1-246-555-0125",
            "email": "michael.johnson@arknet.bb"
        },
        {
            "country_id": country_id,
            "employee_id": "EMP004",
            "name": "Sarah Williams",
            "license_no": "LIC004",
            "phone_number": "+1-246-555-0126",
            "email": "sarah.williams@arknet.bb"
        }
    ]
    
    print(f"\n👨‍💼 Seeding Drivers (using country_id: {country_id[:8]}...)...")
    for driver in drivers:
        try:
            response = requests.post(f"{BASE_URL}/api/v1/drivers", json=driver)
            if response.status_code in [200, 201]:
                print(f"  ✅ Added driver: {driver['name']}")
            elif response.status_code == 409:
                print(f"  ⚠️ Driver already exists: {driver['name']}")
            else:
                print(f"  ❌ Failed to add driver {driver['name']}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error adding driver {driver['name']}: {e}")

def main():
    """Main seeding function"""
    print("🌱 Fleet Management Database Seeder")
    print("=" * 50)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Cannot proceed without API connection")
        return
    
    # Check if we have existing data
    country_id = get_existing_country_id()
    if country_id:
        print(f"✅ Using existing country: {country_id[:8]}...")
    else:
        print("⚠️ No countries found in database")
        return
    
    # Seed data
    seed_vehicles()
    seed_drivers()
    
    print("\n✅ Database seeding completed!")
    print("\n📊 Summary:")
    print("  - Vehicles: 5")
    print("  - Drivers: 4")
    print("\n🎉 Your fleet management system is ready to use!")

if __name__ == "__main__":
    main()
