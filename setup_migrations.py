#!/usr/bin/env python3
"""
Test database connection and generate Alembic migration
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_connection():
    """Test database connection"""
    try:
        from world.fleet_manager.database import init_engine, get_session
        
        print("🔌 Testing database connection...")
        engine = init_engine()
        
        print("✅ Database engine created successfully")
        
        # Test session
        session = get_session()
        from sqlalchemy import text
        result = session.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL Version: {version}")
        session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def generate_migration():
    """Generate Alembic migration"""
    try:
        print("\n🔄 Generating Alembic migration...")
        
        # Change to config directory for alembic commands
        os.chdir('config')
        
        # Generate migration
        exit_code = os.system('alembic revision --autogenerate -m "Initial fleet management models"')
        
        if exit_code == 0:
            print("✅ Migration generated successfully")
            return True
        else:
            print("❌ Migration generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration generation error: {e}")
        return False

def apply_migration():
    """Apply migrations to database"""
    try:
        print("\n📤 Applying migrations to remote database...")
        
        # Apply migrations
        exit_code = os.system('alembic upgrade head')
        
        if exit_code == 0:
            print("✅ Migrations applied successfully")
            return True
        else:
            print("❌ Migration application failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration application error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Fleet Management Database Migration Setup")
    print("=" * 60)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Generate migration
    if not generate_migration():
        sys.exit(1)
    
    # Ask user if they want to apply
    response = input("\n⚠️  Do you want to apply migrations to the remote database? (y/N): ")
    if response.lower() in ['y', 'yes']:
        if not apply_migration():
            sys.exit(1)
    else:
        print("ℹ️  Migration files generated but not applied. Run 'alembic upgrade head' to apply.")
    
    print("\n✅ Database setup complete!")
