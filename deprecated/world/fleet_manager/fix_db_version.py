#!/usr/bin/env python3
"""
Fix Alembic database version
"""
import database
from sqlalchemy import text

print('Connecting to remote database via SSH tunnel...')
engine = database.get_engine()

with engine.connect() as conn:
    # Check current version
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    current_version = result.fetchone()
    print('Current version:', current_version[0] if current_version else 'None')
    
    # Fix the version
    if current_version:
        if current_version[0] == 'b72f0cb20b7f':
            print('Fixing invalid version...')
            conn.execute(text("UPDATE alembic_version SET version_num = 'f26a154d527c'"))
            conn.commit()
            print('✅ Fixed database version to f26a154d527c')
        else:
            print('Version looks OK:', current_version[0])
    else:
        print('Setting initial version...')
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('f26a154d527c')"))
        conn.commit()
        print('✅ Set initial database version to f26a154d527c')

print('Database version fix complete!')