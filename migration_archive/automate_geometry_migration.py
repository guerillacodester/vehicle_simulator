#!/usr/bin/env python3
"""
AUTOMATED GEOMETRY MIGRATION - MASTER CONTROLLER
===============================================
Orchestrates the complete automated migration process step by step.
"""
import subprocess
import sys
import time
import os

def run_step(step_number, script_name, description):
    """Run a migration step and handle results"""
    print(f"\n🚀 STEP {step_number}: {description}")
    print("=" * 80)
    
    try:
        # Check if script exists
        if not os.path.exists(script_name):
            print(f"❌ Script not found: {script_name}")
            return False
        
        # Run the step
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.getcwd())
        
        # Display output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check result
        if result.returncode == 0:
            print(f"✅ STEP {step_number} COMPLETED SUCCESSFULLY")
            return True
        else:
            print(f"❌ STEP {step_number} FAILED (Exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error running Step {step_number}: {e}")
        return False

def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 CHECKING PREREQUISITES")
    print("=" * 80)
    
    # Check if Strapi is running
    import requests
    try:
        response = requests.get('http://localhost:1337/api/routes', timeout=5)
        if response.status_code == 200:
            print("✅ Strapi API is running")
        else:
            print(f"⚠️  Strapi API returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Strapi API not accessible: {e}")
        print("💡 Make sure Strapi is running: npm run develop")
        return False
    
    # Check required scripts
    scripts = [
        'step1_alternative_create_schema_files.py',
        'step2_setup_permissions.py', 
        'step3_migrate_geometry.py'
    ]
    
    for script in scripts:
        if os.path.exists(script):
            print(f"✅ {script}")
        else:
            print(f"❌ {script} not found")
            return False
    
    return True

def main():
    print("🤖 AUTOMATED GEOMETRY MIGRATION SYSTEM")
    print("=" * 80)
    print("This will automate the complete geometry migration process:")
    print("  Step 1: Create route-shapes content type")
    print("  Step 2: Setup permissions")  
    print("  Step 3: Migrate PostGIS geometry data")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return
    
    print("✅ All prerequisites met!")
    
    # Ask for confirmation
    print("\n⚠️  IMPORTANT NOTES:")
    print("• This will create 1,000+ records in your Strapi database")
    print("• Make sure you have a backup if needed")
    print("• The process may take several minutes")
    print("• You will be prompted for confirmations during the process")
    
    confirm = input(f"\nProceed with automated migration? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Automation cancelled")
        return
    
    # Execute steps
    steps = [
        (1, 'step1_alternative_create_schema_files.py', 'CREATE ROUTE-SHAPES CONTENT TYPE'),
        (2, 'step2_setup_permissions.py', 'SETUP PERMISSIONS'),
        (3, 'step3_migrate_geometry.py', 'MIGRATE GEOMETRY DATA')
    ]
    
    successful_steps = 0
    
    for step_num, script, desc in steps:
        success = run_step(step_num, script, desc)
        
        if success:
            successful_steps += 1
            
            # Special handling for Step 1
            if step_num == 1:
                print(f"\n⏳ STEP 1 COMPLETE - RESTART REQUIRED")
                print("Strapi needs to be restarted to load the new content type.")
                print("Please restart Strapi server now:")
                print("  1. Stop current Strapi (Ctrl+C)")
                print("  2. Run: npm run develop")
                print("  3. Wait for Strapi to fully load")
                
                input("\nPress Enter when Strapi has been restarted and is running...")
            
            # Brief pause between steps
            if step_num < len(steps):
                time.sleep(2)
        else:
            print(f"\n❌ AUTOMATION STOPPED - Step {step_num} failed")
            break
    
    # Final summary
    print(f"\n🏁 AUTOMATION COMPLETE")
    print("=" * 80)
    print(f"Successfully completed: {successful_steps}/{len(steps)} steps")
    
    if successful_steps == len(steps):
        print("🎉 FULL SUCCESS - All geometry data has been migrated!")
        print("\nNext steps:")
        print("• Verify data in Strapi admin panel")
        print("• Test route visualization in your application")
        print("• Consider creating a backup of the migrated data")
    else:
        print("⚠️  Partial completion - check the logs above for issues")
        print("You can re-run individual steps as needed:")
        for i in range(successful_steps + 1, len(steps) + 1):
            step_script = steps[i-1][1]  
            print(f"  python {step_script}")

if __name__ == "__main__":
    main()