#!/usr/bin/env python3
"""
Test Fleet Management CLI
===========================

Quick syntax and import validation test.
"""

import sys
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    try:
        from clients.fleet.models import VehicleState, CommandResult, HealthResponse
        print("  ✅ Models imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import models: {e}")
        return False
    
    try:
        from clients.fleet.connector import FleetConnector
        print("  ✅ Connector imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import connector: {e}")
        return False
    
    try:
        from clients.fleet.fleet_console import FleetConsole, main
        print("  ✅ Fleet console imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import fleet console: {e}")
        return False
    
    return True

async def test_connector_instantiation():
    """Test that connector can be instantiated"""
    print("\nTesting connector instantiation...")
    try:
        from clients.fleet.connector import FleetConnector
        connector = FleetConnector(base_url="http://localhost:5001")
        print(f"  ✅ Connector created: {connector.base_url}")
        await connector.close()
        return True
    except Exception as e:
        print(f"  ❌ Failed to create connector: {e}")
        return False

async def test_console_instantiation():
    """Test that console can be instantiated"""
    print("\nTesting console instantiation...")
    try:
        from clients.fleet.fleet_console import FleetConsole
        console = FleetConsole(api_url="http://localhost:5001")
        print(f"  ✅ Console created: {console.api_url}")
        await console.connector.close()
        return True
    except Exception as e:
        print(f"  ❌ Failed to create console: {e}")
        return False

async def test_all_commands_exist():
    """Test that all command methods exist"""
    print("\nTesting command methods...")
    try:
        from clients.fleet.fleet_console import FleetConsole
        console = FleetConsole()
        
        required_commands = [
            'cmd_status', 'cmd_vehicles', 'cmd_vehicle', 'cmd_conductors',
            'cmd_start', 'cmd_stop', 'cmd_enable', 'cmd_disable', 'cmd_trigger',
            'cmd_stream', 'cmd_sim_status', 'cmd_pause', 'cmd_resume', 'cmd_stop_sim',
            'cmd_set_time', 'cmd_services', 'cmd_start_service', 'cmd_stop_service',
            'cmd_restart_service', 'cmd_dashboard', 'cmd_help'
        ]
        
        missing = []
        for cmd in required_commands:
            if not hasattr(console, cmd):
                missing.append(cmd)
        
        if missing:
            print(f"  ❌ Missing commands: {', '.join(missing)}")
            return False
        
        print(f"  ✅ All {len(required_commands)} command methods exist")
        await console.connector.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to verify commands: {e}")
        return False

async def main_test():
    """Run all tests"""
    print("="*70)
    print("FLEET MANAGEMENT CLI - SYNTAX & IMPORT VALIDATION")
    print("="*70)
    
    tests = [
        test_imports,
        test_connector_instantiation,
        test_console_instantiation,
        test_all_commands_exist,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test error: {e}")
            results.append(False)
    
    print("\n" + "="*70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*70)
    
    if all(results):
        print("\n✅ All validation tests passed!")
        print("\nTo start the CLI, run:")
        print("  python -m clients.fleet")
        print("\nMake sure the simulator is running with:")
        print("  python -m arknet_transit_simulator --mode depot")
        return 0
    else:
        print("\n❌ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main_test())
    sys.exit(exit_code)
