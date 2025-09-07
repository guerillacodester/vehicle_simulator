#!/usr/bin/env python3
"""
Fix Missing Response Schemas
============================
Add missing Response schemas to all schema files
"""

import os
import re

schema_files = [
    'api/schemas/stop.py',
    'api/schemas/trip.py', 
    'api/schemas/depot.py',
    'api/schemas/driver.py',
    'api/schemas/timetable.py'
]

def add_response_schema(file_path, base_class_name):
    """Add Response schema to a schema file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if Response class already exists
        if f"{base_class_name}Response" in content:
            print(f"✅ {base_class_name}Response already exists in {file_path}")
            return
            
        # Find the base class definition
        pattern = rf"class {base_class_name}\([^)]+\):\s*\n([^{{}}]*?)(?=\nclass|\n\n|\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        
        if not match:
            print(f"❌ Could not find {base_class_name} class in {file_path}")
            return
            
        # Find where to insert the Response class (after the base class)
        end_of_base_class = match.end()
        
        # Insert the Response class
        response_class = f"""
class {base_class_name}Response({base_class_name}):
    \"\"\"Response schema for {base_class_name} model\"\"\"
    pass
"""
        
        new_content = content[:end_of_base_class] + response_class + content[end_of_base_class:]
        
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        print(f"✅ Added {base_class_name}Response to {file_path}")
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

def main():
    print("🔧 Adding missing Response schemas...")
    
    # Schema mappings: file -> base class name
    schema_mappings = {
        'api/schemas/stop.py': 'Stop',
        'api/schemas/trip.py': 'Trip', 
        'api/schemas/depot.py': 'Depot',
        'api/schemas/driver.py': 'Driver',
        'api/schemas/timetable.py': 'Timetable'
    }
    
    for file_path, base_class in schema_mappings.items():
        if os.path.exists(file_path):
            add_response_schema(file_path, base_class)
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print("🎉 Done!")

if __name__ == "__main__":
    main()
