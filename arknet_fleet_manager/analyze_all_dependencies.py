#!/usr/bin/env python3
"""
Analyze all table dependencies to determine migration order
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

# Database connection parameters
REMOTE_DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # SSH tunnel port
    'database': 'arknetglobal',
    'user': 'arknetglobal',
    'password': 'password123'
}

# Strapi API configuration
STRAPI_API_URL = "http://localhost:1337/api"

def get_remote_table_structure(table_name):
    """Get the structure of a remote table"""
    try:
        conn = psycopg2.connect(**REMOTE_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get table columns
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        # Get foreign key constraints
        cursor.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
        """, (table_name,))
        
        foreign_keys = cursor.fetchall()
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_data = cursor.fetchall()
        
        conn.close()
        return {
            'columns': columns,
            'foreign_keys': foreign_keys,
            'sample_data': sample_data
        }
        
    except Exception as e:
        print(f"Error analyzing {table_name}: {e}")
        return None

def get_strapi_content_types():
    """Get available Strapi content types"""
    try:
        response = requests.get(f"{STRAPI_API_URL}/content-type-builder/content-types")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting Strapi content types: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error connecting to Strapi: {e}")
        return None

def analyze_table_dependencies():
    """Analyze all relevant tables and their dependencies"""
    
    tables_to_analyze = [
        'gps_devices',
        'drivers', 
        'depots',
        'routes',
        'vehicles'
    ]
    
    print("=== DEPENDENCY ANALYSIS FOR MIGRATION ORDER ===\n")
    
    table_info = {}
    
    for table in tables_to_analyze:
        print(f"--- Analyzing {table.upper()} ---")
        info = get_remote_table_structure(table)
        if info:
            table_info[table] = info
            
            print(f"Columns: {len(info['columns'])}")
            print("Foreign Key Dependencies:")
            if info['foreign_keys']:
                for fk in info['foreign_keys']:
                    print(f"  - {fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
            else:
                print("  - No foreign key dependencies")
                
            print(f"Sample records: {len(info['sample_data'])}")
            if info['sample_data']:
                # Show first record keys to understand structure
                sample_keys = list(info['sample_data'][0].keys()) if info['sample_data'] else []
                print(f"  Fields: {', '.join(sample_keys[:8])}{'...' if len(sample_keys) > 8 else ''}")
            print()
    
    # Determine migration order based on dependencies
    print("=== RECOMMENDED MIGRATION ORDER ===")
    
    # Analyze dependencies
    dependencies = {}
    for table, info in table_info.items():
        deps = []
        for fk in info['foreign_keys']:
            foreign_table = fk['foreign_table_name']
            if foreign_table in tables_to_analyze:
                deps.append(foreign_table)
            elif foreign_table == 'countries':
                deps.append('countries (already migrated)')
        dependencies[table] = deps
    
    print("Dependencies found:")
    for table, deps in dependencies.items():
        print(f"{table}: {deps if deps else 'No dependencies'}")
    
    # Simple topological sort for migration order
    order = []
    remaining = set(tables_to_analyze)
    
    while remaining:
        # Find tables with no remaining dependencies
        ready = []
        for table in remaining:
            table_deps = [dep for dep in dependencies[table] if dep in remaining]
            if not table_deps:
                ready.append(table)
        
        if not ready:
            print("Circular dependency detected!")
            ready = list(remaining)  # Force remaining
            
        ready.sort()  # Consistent ordering
        order.extend(ready)
        remaining -= set(ready)
    
    print(f"\nRecommended migration order:")
    for i, table in enumerate(order, 1):
        print(f"{i}. {table}")
    
    return table_info, order

if __name__ == "__main__":
    table_info, migration_order = analyze_table_dependencies()
    print(f"\n=== SUMMARY ===")
    print(f"Tables analyzed: {len(table_info)}")
    print(f"Migration order: {' → '.join(migration_order)}")