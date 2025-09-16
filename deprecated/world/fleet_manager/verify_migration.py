#!/usr/bin/env python3
"""
Verify the vehicle-driver relationship migration
"""
import database
from sqlalchemy import text

print('Verifying vehicle-driver relationship migration...')
engine = database.get_engine()

with engine.connect() as conn:
    # Check if the assigned_driver_id column exists
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'vehicles' 
        AND column_name = 'assigned_driver_id'
    """))
    
    column_info = result.fetchone()
    if column_info:
        print(f'✅ Column exists: {column_info[0]} ({column_info[1]}, nullable: {column_info[2]})')
    else:
        print('❌ Column not found!')
    
    # Check foreign key constraint
    result = conn.execute(text("""
        SELECT constraint_name, table_name, column_name, foreign_table_name, foreign_column_name
        FROM information_schema.key_column_usage kcu
        JOIN information_schema.referential_constraints rc ON kcu.constraint_name = rc.constraint_name
        JOIN information_schema.key_column_usage fkcu ON rc.unique_constraint_name = fkcu.constraint_name
        WHERE kcu.table_name = 'vehicles' 
        AND kcu.column_name = 'assigned_driver_id'
    """))
    
    fk_info = result.fetchone()
    if fk_info:
        print(f'✅ Foreign key exists: {fk_info[0]} -> {fk_info[3]}.{fk_info[4]}')
    else:
        print('❌ Foreign key constraint not found!')

print('Migration verification complete!')