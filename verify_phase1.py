#!/usr/bin/env python3
"""
Phase 1 Verification Checklist

Verifies that all Phase 1 components are in place before moving to Phase 2.
"""

import os
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and print result"""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}")
    print(f"   {filepath}")
    return exists

def main():
    print("\n" + "=" * 80)
    print("🔍 PHASE 1 VERIFICATION CHECKLIST")
    print("=" * 80 + "\n")
    
    base_path = Path(__file__).parent
    strapi_path = base_path / "arknet_fleet_manager" / "arknet-fleet-api"
    
    all_files_exist = True
    
    # Check Strapi TypeScript files
    print("📂 Strapi TypeScript Files:")
    print("-" * 80)
    
    files_to_check = [
        (strapi_path / "config" / "socket.ts", "Socket.IO Configuration"),
        (strapi_path / "src" / "socketio" / "types.ts", "Type Definitions"),
        (strapi_path / "src" / "socketio" / "message-format.ts", "Message Format Standards"),
        (strapi_path / "src" / "socketio" / "server.ts", "Socket.IO Server"),
        (strapi_path / "src" / "index.ts", "Strapi Bootstrap (updated)"),
    ]
    
    for filepath, description in files_to_check:
        all_files_exist &= check_file_exists(filepath, description)
    
    # Check Python files
    print("\n📂 Python Client Files:")
    print("-" * 80)
    
    files_to_check = [
        (base_path / "commuter_service" / "socketio_client.py", "Socket.IO Client Library"),
        (base_path / "test_socketio_infrastructure.py", "Comprehensive Test Suite"),
        (base_path / "quick_test_socketio.py", "Quick Start Test"),
    ]
    
    for filepath, description in files_to_check:
        all_files_exist &= check_file_exists(filepath, description)
    
    # Check documentation
    print("\n📂 Documentation:")
    print("-" * 80)
    
    files_to_check = [
        (base_path / "PHASE_1_SOCKETIO_FOUNDATION_COMPLETE.md", "Phase 1 Documentation"),
        (base_path / "TODO.md", "Updated TODO with Phase 1 status"),
    ]
    
    for filepath, description in files_to_check:
        all_files_exist &= check_file_exists(filepath, description)
    
    # Check npm packages
    print("\n📦 npm Packages:")
    print("-" * 80)
    
    package_json = strapi_path / "package.json"
    if package_json.exists():
        with open(package_json, 'r') as f:
            content = f.read()
            if 'socket.io' in content:
                print("✅ Socket.IO installed in package.json")
            else:
                print("❌ Socket.IO NOT found in package.json")
                all_files_exist = False
    else:
        print("❌ package.json not found")
        all_files_exist = False
    
    # Summary
    print("\n" + "=" * 80)
    if all_files_exist:
        print("✅ ALL PHASE 1 COMPONENTS VERIFIED!")
        print("=" * 80 + "\n")
        print("🚀 Ready for Testing:")
        print("   1. Start Strapi: cd arknet_fleet_manager/arknet-fleet-api && npm run dev")
        print("   2. Quick test: python quick_test_socketio.py")
        print("   3. Full suite: python test_socketio_infrastructure.py")
        print("\n🎯 After successful testing, proceed to Phase 2: Commuter Service")
    else:
        print("❌ SOME COMPONENTS MISSING!")
        print("=" * 80 + "\n")
        print("⚠️  Please review the checklist above and ensure all files are created.")
    
    print("=" * 80 + "\n")
    
    return all_files_exist

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
