"""
Clean up remaining ad-hoc scripts and log files from root directory.
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent

# Files to delete
DELETE_FILES = [
    # Ad-hoc check scripts
    'check_landuse_types.py',
    'check_pagination.py',
    'check_route_depots.py',
    'check_strapi_configs.py',
    'check_vehicles.py',
    'analyze_route_spawns.py',
    'analyze_spawn_distances.py',
    'calculate_route_distance.py',
    'debug_population_zones.py',
    'debug_spatial_cache.py',
    'diagnose_strapi.py',
    'inspect_route_tables.py',
    'inspect_zone_fields.py',
    'list_routes.py',
    'route_1a_summary.py',
    'verify_route_database.py',
    'verify_spawn_on_route.py',
    
    # Ad-hoc test/run scripts
    'add_numbers.py',
    'quick_test_socketio.py',
    'simple_socketio_test.py',
    'definitive_passenger_spawning_test.py',
    'run_commuter_production.py',
    'start_commuter_clean.py',
    'start_commuter_cli.py',
    'start_commuter_production.py',
    'start_commuter_raw.py',
    'start_commuter_service.py',
    'start_production_simple.py',
    'enable_boarding.py',
    
    # Log files
    'commuter_errors.log',
    'commuter_live.log',
    'commuter_output.log',
    'commuter_production.log',
    'commuter_startup.log',
    'commuter_stderr.log',
    'commuter_stdout.log',
    'production_spawns.log',
    
    # Cleanup script itself
    'cleanup_project.py',
]

def cleanup():
    deleted = []
    not_found = []
    
    print("Cleaning up root directory...")
    print()
    
    for filename in DELETE_FILES:
        filepath = ROOT / filename
        if filepath.exists():
            try:
                filepath.unlink()
                deleted.append(filename)
                print(f"  ✓ Deleted: {filename}")
            except Exception as e:
                print(f"  ✗ Error deleting {filename}: {e}")
        else:
            not_found.append(filename)
    
    print()
    print("="*60)
    print("CLEANUP SUMMARY")
    print("="*60)
    print(f"Files deleted: {len(deleted)}")
    if not_found:
        print(f"Files not found (already deleted): {len(not_found)}")
    print()
    print("Root directory cleaned!")

if __name__ == '__main__':
    cleanup()
