#!/usr/bin/env python3
"""
Fix Strapi permissions - ensure all content types appear in roles/permissions
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def fix_permissions():
    try:
        # Connect to local database
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="arknettransit",
            user="david",
            password="Ga25w123!",
            port="5432"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== FIXING STRAPI PERMISSIONS ===\n")
        
        # Define all your content types
        content_types = [
            'api::block.block',
            'api::country.country', 
            'api::depot.depot',
            'api::driver.driver',
            'api::gps-device.gps-device',
            'api::route.route',
            'api::service.service',
            'api::shape.shape',
            'api::stop.stop',
            'api::trip.trip',
            'api::vehicle.vehicle'
        ]
        
        # Standard permissions for each content type
        permissions = ['find', 'findOne', 'create', 'update', 'delete']
        
        # Check current permissions
        cursor.execute("""
            SELECT * FROM up_permissions 
            ORDER BY action, id;
        """)
        
        current_permissions = cursor.fetchall()
        print(f"📊 Current permissions count: {len(current_permissions)}")
        
        # Check what content types already have permissions
        existing_actions = set()
        for perm in current_permissions:
            if perm['action']:
                existing_actions.add(perm['action'])
        
        print(f"📋 Existing permission actions: {len(existing_actions)}")
        for action in sorted(existing_actions):
            print(f"  - {action}")
        
        print(f"\n🔧 Adding missing permissions for {len(content_types)} content types...")
        
        # Get the Public role ID (usually 1)
        cursor.execute("SELECT id FROM up_roles WHERE name = 'Public' OR type = 'public';")
        public_role = cursor.fetchone()
        public_role_id = public_role['id'] if public_role else 1
        
        # Get the Authenticated role ID (usually 2) 
        cursor.execute("SELECT id FROM up_roles WHERE name = 'Authenticated' OR type = 'authenticated';")
        auth_role = cursor.fetchone()
        auth_role_id = auth_role['id'] if auth_role else 2
        
        print(f"📝 Using role IDs - Public: {public_role_id}, Authenticated: {auth_role_id}")
        
        added_count = 0
        
        for content_type in content_types:
            for permission in permissions:
                action = f"{content_type}.{permission}"
                
                # Check if this permission already exists
                cursor.execute("""
                    SELECT id FROM up_permissions 
                    WHERE action = %s;
                """, (action,))
                
                if not cursor.fetchone():
                    # Add permission for Public role (usually disabled)
                    cursor.execute("""
                        INSERT INTO up_permissions (action, created_at, updated_at)
                        VALUES (%s, NOW(), NOW())
                        RETURNING id;
                    """, (action,))
                    
                    perm_result = cursor.fetchone()
                    perm_id = perm_result['id']
                    
                    # Link to Public role (disabled by default)
                    cursor.execute("""
                        INSERT INTO up_permissions_role_lnk (permission_id, role_id, permission_ord)
                        VALUES (%s, %s, 1);
                    """, (perm_id, public_role_id))
                    
                    # Link to Authenticated role (enabled by default for basic permissions)
                    cursor.execute("""
                        INSERT INTO up_permissions_role_lnk (permission_id, role_id, permission_ord)
                        VALUES (%s, %s, 1);
                    """, (perm_id, auth_role_id))
                    
                    added_count += 1
                    print(f"  ✅ Added: {action}")
        
        # Commit changes
        conn.commit()
        
        print(f"\n🎉 Successfully added {added_count} new permissions!")
        
        # Verify the result
        cursor.execute("SELECT COUNT(*) as total FROM up_permissions;")
        total_perms = cursor.fetchone()['total']
        print(f"📊 Total permissions now: {total_perms}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Permissions fix completed!")
        print("🔄 Please restart Strapi to see the changes in the admin panel.")
        
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    fix_permissions()