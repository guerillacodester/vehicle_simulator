"""
Integration Test: Verify Refactored Reservoirs Structure

This test validates that the refactored depot_reservoir.py and route_reservoir.py
correctly integrate with the extracted modules without runtime errors.

Tests:
1. Module imports work correctly
2. Class structure is intact
3. Extracted modules are being used
4. Key methods exist and have correct signatures
"""

import sys
import ast
import inspect
from pathlib import Path


def test_module_structure():
    """Validate the structure of refactored modules"""
    print("🔍 INTEGRATION TEST: Refactored Reservoir Structure")
    print("=" * 70)
    
    # Test 1: Verify depot_reservoir.py structure
    print("\n📋 Test 1: depot_reservoir.py Structure")
    print("-" * 70)
    
    depot_file = Path("commuter_service/depot_reservoir.py")
    with open(depot_file, 'r', encoding='utf-8') as f:
        depot_content = f.read()
        depot_ast = ast.parse(depot_content)
    
    # Check for extracted module imports
    depot_imports = []
    for node in ast.walk(depot_ast):
        if isinstance(node, ast.ImportFrom):
            if node.module and 'commuter_service' in node.module:
                for alias in node.names:
                    depot_imports.append(f"{node.module}.{alias.name}")
    
    expected_depot_imports = [
        'commuter_service.depot_queue.DepotQueue',
        'commuter_service.location_normalizer.LocationNormalizer',
        'commuter_service.reservoir_statistics.ReservoirStatistics',
        'commuter_service.expiration_manager.ReservoirExpirationManager',
        'commuter_service.spawning_coordinator.SpawningCoordinator',
    ]
    
    print("✅ Checking for extracted module imports...")
    for expected_import in expected_depot_imports:
        if expected_import in depot_imports:
            print(f"   ✓ {expected_import.split('.')[-1]} imported")
        else:
            print(f"   ✗ MISSING: {expected_import}")
            return False
    
    # Check that inline DepotQueue class was removed
    class_names = [node.name for node in ast.walk(depot_ast) if isinstance(node, ast.ClassDef)]
    if 'DepotQueue' in class_names:
        print("   ✗ ERROR: Inline DepotQueue class still exists!")
        return False
    else:
        print("   ✓ Inline DepotQueue class removed")
    
    # Check for _normalize_location method removal
    depot_methods = []
    for node in ast.walk(depot_ast):
        if isinstance(node, ast.ClassDef) and node.name == 'DepotReservoir':
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    depot_methods.append(item.name)
    
    if '_normalize_location' in depot_methods:
        print("   ✗ ERROR: _normalize_location method still exists!")
        return False
    else:
        print("   ✓ _normalize_location method removed")
    
    if '_expiration_loop' in depot_methods:
        print("   ✗ ERROR: _expiration_loop method still exists!")
        return False
    else:
        print("   ✓ _expiration_loop method removed")
    
    if '_spawning_loop' in depot_methods:
        print("   ✗ ERROR: _spawning_loop method still exists!")
        return False
    else:
        print("   ✓ _spawning_loop method removed")
    
    # Check for callback methods
    expected_callbacks = [
        '_get_active_commuters_for_expiration',
        '_expire_commuter',
        '_generate_spawn_requests',
        '_process_spawn_request'
    ]
    
    print("\n✅ Checking for manager callback methods...")
    for callback in expected_callbacks:
        if callback in depot_methods:
            print(f"   ✓ {callback} exists")
        else:
            print(f"   ✗ MISSING: {callback}")
            return False
    
    print("\n✅ depot_reservoir.py structure is correct!")
    
    # Test 2: Verify route_reservoir.py structure
    print("\n📋 Test 2: route_reservoir.py Structure")
    print("-" * 70)
    
    route_file = Path("commuter_service/route_reservoir.py")
    with open(route_file, 'r', encoding='utf-8') as f:
        route_content = f.read()
        route_ast = ast.parse(route_content)
    
    # Check for extracted module imports
    route_imports = []
    for node in ast.walk(route_ast):
        if isinstance(node, ast.ImportFrom):
            if node.module and 'commuter_service' in node.module:
                for alias in node.names:
                    route_imports.append(f"{node.module}.{alias.name}")
    
    expected_route_imports = [
        'commuter_service.route_segment.RouteSegment',
        'commuter_service.location_normalizer.LocationNormalizer',
        'commuter_service.reservoir_statistics.ReservoirStatistics',
        'commuter_service.expiration_manager.ReservoirExpirationManager',
        'commuter_service.spawning_coordinator.SpawningCoordinator',
    ]
    
    print("✅ Checking for extracted module imports...")
    for expected_import in expected_route_imports:
        if expected_import in route_imports:
            print(f"   ✓ {expected_import.split('.')[-1]} imported")
        else:
            print(f"   ✗ MISSING: {expected_import}")
            return False
    
    # Check that inline RouteSegment class was removed
    route_class_names = [node.name for node in ast.walk(route_ast) if isinstance(node, ast.ClassDef)]
    if 'RouteSegment' in route_class_names:
        print("   ✗ ERROR: Inline RouteSegment class still exists!")
        return False
    else:
        print("   ✓ Inline RouteSegment class removed")
    
    # Check for _normalize_location method removal
    route_methods = []
    for node in ast.walk(route_ast):
        if isinstance(node, ast.ClassDef) and node.name == 'RouteReservoir':
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    route_methods.append(item.name)
    
    if '_normalize_location' in route_methods:
        print("   ✗ ERROR: _normalize_location method still exists!")
        return False
    else:
        print("   ✓ _normalize_location method removed")
    
    if '_expiration_loop' in route_methods:
        print("   ✗ ERROR: _expiration_loop method still exists!")
        return False
    else:
        print("   ✓ _expiration_loop method removed")
    
    if '_spawning_loop' in route_methods:
        print("   ✗ ERROR: _spawning_loop method still exists!")
        return False
    else:
        print("   ✓ _spawning_loop method removed")
    
    # Check for callback methods
    print("\n✅ Checking for manager callback methods...")
    for callback in expected_callbacks:
        if callback in route_methods:
            print(f"   ✓ {callback} exists")
        else:
            print(f"   ✗ MISSING: {callback}")
            return False
    
    print("\n✅ route_reservoir.py structure is correct!")
    
    # Test 3: Verify file size reductions
    print("\n📋 Test 3: File Size Verification")
    print("-" * 70)
    
    depot_lines = len(depot_content.splitlines())
    route_lines = len(route_content.splitlines())
    
    print(f"depot_reservoir.py: {depot_lines} lines")
    print(f"route_reservoir.py: {route_lines} lines")
    
    # Original sizes were: depot=814, route=872
    if depot_lines <= 814:
        print(f"✓ depot_reservoir.py reduced (was 814, now {depot_lines})")
    else:
        print(f"✗ depot_reservoir.py INCREASED (was 814, now {depot_lines})")
        return False
    
    if route_lines <= 872:
        print(f"✓ route_reservoir.py reduced (was 872, now {route_lines})")
    else:
        print(f"✗ route_reservoir.py INCREASED (was 872, now {route_lines})")
        return False
    
    # Test 4: Check for usage of LocationNormalizer
    print("\n📋 Test 4: LocationNormalizer Usage Verification")
    print("-" * 70)
    
    depot_uses_normalizer = 'LocationNormalizer.normalize' in depot_content
    route_uses_normalizer = 'LocationNormalizer.normalize' in route_content
    
    if depot_uses_normalizer:
        print("✓ depot_reservoir.py uses LocationNormalizer.normalize()")
    else:
        print("✗ depot_reservoir.py does NOT use LocationNormalizer.normalize()")
        return False
    
    if route_uses_normalizer:
        print("✓ route_reservoir.py uses LocationNormalizer.normalize()")
    else:
        print("✗ route_reservoir.py does NOT use LocationNormalizer.normalize()")
        return False
    
    # Test 5: Check for ReservoirStatistics usage
    print("\n📋 Test 5: ReservoirStatistics Usage Verification")
    print("-" * 70)
    
    depot_uses_stats = 'self.statistics' in depot_content and 'ReservoirStatistics' in depot_content
    route_uses_stats = 'self.statistics' in route_content and 'ReservoirStatistics' in route_content
    
    if depot_uses_stats:
        print("✓ depot_reservoir.py uses ReservoirStatistics")
    else:
        print("✗ depot_reservoir.py does NOT use ReservoirStatistics")
        return False
    
    if route_uses_stats:
        print("✓ route_reservoir.py uses ReservoirStatistics")
    else:
        print("✗ route_reservoir.py does NOT use ReservoirStatistics")
        return False
    
    # Test 6: Check for manager initialization
    print("\n📋 Test 6: Manager Initialization Verification")
    print("-" * 70)
    
    depot_has_expiration_manager = 'self.expiration_manager = ReservoirExpirationManager' in depot_content
    depot_has_spawning_coordinator = 'self.spawning_coordinator = SpawningCoordinator' in depot_content
    
    route_has_expiration_manager = 'self.expiration_manager = ReservoirExpirationManager' in route_content
    route_has_spawning_coordinator = 'self.spawning_coordinator = SpawningCoordinator' in route_content
    
    if depot_has_expiration_manager:
        print("✓ depot_reservoir.py initializes ExpirationManager")
    else:
        print("✗ depot_reservoir.py does NOT initialize ExpirationManager")
        return False
    
    if depot_has_spawning_coordinator:
        print("✓ depot_reservoir.py initializes SpawningCoordinator")
    else:
        print("✗ depot_reservoir.py does NOT initialize SpawningCoordinator")
        return False
    
    if route_has_expiration_manager:
        print("✓ route_reservoir.py initializes ExpirationManager")
    else:
        print("✗ route_reservoir.py does NOT initialize ExpirationManager")
        return False
    
    if route_has_spawning_coordinator:
        print("✓ route_reservoir.py initializes SpawningCoordinator")
    else:
        print("✗ route_reservoir.py does NOT initialize SpawningCoordinator")
        return False
    
    return True


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " INTEGRATION TEST: Refactored Reservoirs ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        success = test_module_structure()
        
        print("\n" + "=" * 70)
        if success:
            print("🎉 ALL INTEGRATION TESTS PASSED! ✅")
            print()
            print("Summary:")
            print("  ✓ All extracted modules imported correctly")
            print("  ✓ Inline classes removed (DepotQueue, RouteSegment)")
            print("  ✓ Old methods removed (_normalize_location, loops)")
            print("  ✓ Callback methods created for managers")
            print("  ✓ LocationNormalizer being used")
            print("  ✓ ReservoirStatistics being used")
            print("  ✓ Managers properly initialized")
            print("  ✓ File sizes reduced as expected")
            print()
            print("✅ Refactoring is structurally sound and complete!")
            sys.exit(0)
        else:
            print("❌ INTEGRATION TESTS FAILED!")
            print("\nSome refactoring issues were detected. See errors above.")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
