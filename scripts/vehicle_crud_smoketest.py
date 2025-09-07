import requests
import sys
import uuid
import time

API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10

# Adjust these fields as needed for your Vehicle schema
VEHICLE_CREATE_DATA = {
    "country_id": None,  # Will be set after creating a country
    "depot_id": None,   # Will be set after creating a depot
    "plate_number": f"TEST-{uuid.uuid4().hex[:6].upper()}",
    "reg_code": f"REG-{uuid.uuid4().hex[:6].upper()}",
    "model": "Test Model",
    "capacity": 40
}

VEHICLE_UPDATE_DATA = {
    "model": "Updated Model",
    "capacity": 50
}

def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)

def main():
    print("\n=== VEHICLE CRUD SMOKETEST ===\n")
    session = requests.Session()

    # 1. Create a country (dependency)
    country_data = {"iso_code": f"T{uuid.uuid4().hex[:2].upper()}", "name": "Test Country"}
    r = session.post(f"{API_BASE_URL}/countries", json=country_data, timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"Failed to create country: {r.text}")
    country_id = r.json()["country_id"]
    print(f"✅ Created country: {country_id}")

    # 2. Create a depot (dependency)
    depot_data = {"name": "Test Depot", "capacity": 100, "country_id": country_id}
    r = session.post(f"{API_BASE_URL}/depots", json=depot_data, timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"Failed to create depot: {r.text}")
    depot_id = r.json()["depot_id"]
    print(f"✅ Created depot: {depot_id}")

    # 3. Create a vehicle
    vehicle_data = VEHICLE_CREATE_DATA.copy()
    vehicle_data["country_id"] = country_id
    vehicle_data["depot_id"] = depot_id
    r = session.post(f"{API_BASE_URL}/vehicles", json=vehicle_data, timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"Failed to create vehicle: {r.text}")
    vehicle = r.json()
    vehicle_id = vehicle["vehicle_id"]
    print(f"✅ Created vehicle: {vehicle_id}")

    # 4. Read vehicle (single)
    r = session.get(f"{API_BASE_URL}/vehicles/{vehicle_id}", timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"Failed to read vehicle: {r.text}")
    print(f"✅ Read vehicle (single)")

    # 5. Read vehicles (list)
    r = session.get(f"{API_BASE_URL}/vehicles?limit=10", timeout=TIMEOUT)
    if r.status_code != 200 or not any(v["vehicle_id"] == vehicle_id for v in r.json()):
        fail(f"Failed to list vehicles or created vehicle not found")
    print(f"✅ Read vehicles (list)")

    # 6. Update vehicle
    r = session.put(f"{API_BASE_URL}/vehicles/{vehicle_id}", json=VEHICLE_UPDATE_DATA, timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"Failed to update vehicle: {r.text}")
    updated = r.json()
    if updated["model"] != VEHICLE_UPDATE_DATA["model"] or updated["capacity"] != VEHICLE_UPDATE_DATA["capacity"]:
        fail(f"Vehicle update did not persist changes")
    print(f"✅ Updated vehicle")

    # 7. Delete vehicle
    r = session.delete(f"{API_BASE_URL}/vehicles/{vehicle_id}", timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"Failed to delete vehicle: {r.text}")
    print(f"✅ Deleted vehicle")

    # 8. Verify deletion
    r = session.get(f"{API_BASE_URL}/vehicles/{vehicle_id}", timeout=TIMEOUT)
    if r.status_code != 404:
        fail(f"Vehicle still exists after deletion!")
    print(f"✅ Verified vehicle deletion")

    # Cleanup: delete created country and depot
    session.delete(f"{API_BASE_URL}/depots/{depot_id}", timeout=TIMEOUT)
    session.delete(f"{API_BASE_URL}/countries/{country_id}", timeout=TIMEOUT)
    print("\n=== VEHICLE CRUD SMOKETEST PASSED ===\n")

if __name__ == "__main__":
    main()
