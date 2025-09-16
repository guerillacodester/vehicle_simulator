#!/usr/bin/env python3
"""
Assign drivers to ALL vehicles in the database
"""
import database
from sqlalchemy import text

print('Assigning drivers to ALL vehicles...')
engine = database.get_engine()

with engine.connect() as conn:
    # Get all vehicles and drivers
    print('Getting all vehicles and drivers...')
    
    vehicles_result = conn.execute(text("SELECT vehicle_id, reg_code FROM vehicles ORDER BY reg_code"))
    vehicles = vehicles_result.fetchall()
    
    drivers_result = conn.execute(text("SELECT driver_id, name FROM drivers ORDER BY name"))
    drivers = drivers_result.fetchall()
    
    print(f'Found {len(vehicles)} vehicles and {len(drivers)} drivers')
    
    if not drivers:
        print('❌ No drivers found! Cannot assign.')
        exit(1)
    
    # Assign drivers to vehicles in round-robin fashion
    assignments = []
    for i, (vehicle_id, reg_code) in enumerate(vehicles):
        # Use modulo to cycle through drivers
        driver_idx = i % len(drivers)
        driver_id, driver_name = drivers[driver_idx]
        
        print(f'Assigning {driver_name} to {reg_code}')
        conn.execute(text("UPDATE vehicles SET assigned_driver_id = :driver_id WHERE vehicle_id = :vehicle_id"), 
                     {"driver_id": driver_id, "vehicle_id": vehicle_id})
        
        assignments.append((reg_code, driver_name))
    
    conn.commit()
    print('✅ ALL vehicles now have assigned drivers!')
    
    # Verify all assignments
    print('\nVerifying ALL assignments...')
    result = conn.execute(text("""
        SELECT v.reg_code, d.name 
        FROM vehicles v 
        LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id 
        ORDER BY v.reg_code
    """))
    
    all_assignments = result.fetchall()
    unassigned_count = 0
    
    for vehicle, driver in all_assignments:
        if driver:
            print(f'✅ {vehicle} -> {driver}')
        else:
            print(f'❌ {vehicle} -> UNASSIGNED')
            unassigned_count += 1
    
    print(f'\n📊 Assignment Summary:')
    print(f'   Total vehicles: {len(all_assignments)}')
    print(f'   Assigned: {len(all_assignments) - unassigned_count}')
    print(f'   Unassigned: {unassigned_count}')

print('\nAll vehicle-driver assignments complete!')