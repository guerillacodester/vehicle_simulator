#!/usr/bin/env python3
"""
Test ORM models with remote database
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_orm_models():
    """Test ORM models with the remote database"""
    try:
        from world.fleet_manager.database import init_engine, get_session
        from world.fleet_manager.models import Vehicle, Route, Country, Stop
        
        print("🔌 Connecting to database...")
        engine = init_engine()
        session = get_session()
        
        print("✅ Database connected successfully")
        
        # Test basic queries
        print("\n📊 Testing ORM queries:")
        
        # Count vehicles
        vehicle_count = session.query(Vehicle).count()
        print(f"🚌 Vehicles in database: {vehicle_count}")
        
        # Count routes
        route_count = session.query(Route).count()
        print(f"🛣️  Routes in database: {route_count}")
        
        # Count countries
        country_count = session.query(Country).count()
        print(f"🌍 Countries in database: {country_count}")
        
        # Count stops
        stop_count = session.query(Stop).count()
        print(f"🚏 Stops in database: {stop_count}")
        
        # Test a join query
        if route_count > 0:
            sample_routes = session.query(Route).limit(3).all()
            print(f"\n📍 Sample routes:")
            for route in sample_routes:
                print(f"   - {route.short_name}: {route.long_name}")
        
        if vehicle_count > 0:
            sample_vehicles = session.query(Vehicle).limit(3).all()
            print(f"\n🚗 Sample vehicles:")
            for vehicle in sample_vehicles:
                print(f"   - {vehicle.reg_code}: {vehicle.status}")
        
        session.close()
        
        print("\n✅ All ORM tests passed successfully!")
        print("🎉 Fleet management models are synced with remote database!")
        
        return True
        
    except Exception as e:
        print(f"❌ ORM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Fleet Management ORM Test")
    print("=" * 60)
    
    if test_orm_models():
        print("\n✅ Migration verification complete!")
    else:
        print("\n❌ Migration verification failed!")
        sys.exit(1)
