#!/usr/bin/env python3
"""
Reset Alembic state and create fresh migrations
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def reset_alembic():
    """Reset alembic version table"""
    try:
        from world.fleet_manager.database import get_session
        from sqlalchemy import text
        
        print("🔄 Resetting Alembic state...")
        session = get_session()
        
        # Clear alembic version table
        session.execute(text("DELETE FROM alembic_version"))
        session.commit()
        session.close()
        
        print("✅ Alembic state reset successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to reset Alembic state: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Resetting Alembic for Fresh Migrations")
    print("=" * 60)
    
    if reset_alembic():
        print("\n✅ Ready for fresh migrations!")
        print("Now run: cd config && alembic revision --autogenerate -m 'Initial migration'")
    else:
        print("❌ Reset failed")
        sys.exit(1)
