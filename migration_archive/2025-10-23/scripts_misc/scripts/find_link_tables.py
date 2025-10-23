"""
Find Strapi Relation Link Tables
"""
import psycopg2
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', 'arknet_fleet_manager', 'arknet-fleet-api', '.env')
load_dotenv(env_path)

DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', '127.0.0.1'),
    'port': os.getenv('DATABASE_PORT', '5432'),
    'database': os.getenv('DATABASE_NAME', 'arknettransit'),
    'user': os.getenv('DATABASE_USERNAME', 'david'),
    'password': os.getenv('DATABASE_PASSWORD', '')
}

def find_link_tables():
    """Find Strapi relation link tables"""
    print("=" * 80)
    print("Strapi Relation Link Tables Discovery")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get all tables that look like link tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (
                table_name LIKE '%_links'
                OR table_name LIKE '%_country_lnk'
                OR table_name LIKE '%_region_lnk'
                OR table_name LIKE 'pois_%'
                OR table_name LIKE 'landuse_zones_%'
                OR table_name LIKE 'regions_%'
                OR table_name LIKE 'spawn_configs_%'
            )
            ORDER BY table_name;
        """)
        
        link_tables = cursor.fetchall()
        
        if link_tables:
            print(f"\n✅ Found {len(link_tables)} link tables:")
            print("-" * 80)
            
            for (table_name,) in link_tables:
                print(f"\n📋 Table: {table_name}")
                
                # Get columns
                cursor.execute(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """)
                
                columns = cursor.fetchall()
                for col_name, col_type in columns:
                    print(f"   {col_name:30} {col_type}")
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"   Rows: {count}")
                except:
                    pass
        else:
            print("\n⚠️  No link tables found!")
            print("\nThis might mean:")
            print("  1. Strapi hasn't generated link tables yet")
            print("  2. Relations are defined but not used yet")
            print("  3. Need to restart Strapi to generate tables")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_link_tables()
