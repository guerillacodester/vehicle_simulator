#!/usr/bin/env python3
"""
Mark route description migration as applied
"""
import database
from sqlalchemy import text

print('Marking route_desc_color migration as applied...')
engine = database.get_engine()

with engine.connect() as conn:
    # Update version to skip the route description migration
    conn.execute(text("UPDATE alembic_version SET version_num = 'route_desc_color'"))
    conn.commit()
    print('✅ Marked route_desc_color as applied')

print('Ready to run vehicle-driver migration!')