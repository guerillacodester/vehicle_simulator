"""
Inspect Strapi Foreign Key Column Names
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

def inspect_columns():
    """Inspect column names in new tables"""
    print("=" * 80)
    print("Strapi Foreign Key Column Inspection")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        tables = ['pois', 'landuse_zones', 'regions', 'spawn_configs']
        
        for table in tables:
            print(f"\n📋 Table: {table}")
            print("-" * 80)
            
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            # Highlight potential foreign key columns
            for col_name, col_type, nullable in columns:
                marker = ""
                if "country" in col_name.lower():
                    marker = "  🔑 [COUNTRY FK]"
                elif "region" in col_name.lower():
                    marker = "  🔑 [REGION FK]"
                elif col_name.endswith("_id") or col_name.endswith("_uuid"):
                    marker = "  🔑 [FK?]"
                elif col_name in ['id', 'document_id']:
                    marker = "  🆔 [PRIMARY KEY]"
                
                print(f"  {col_name:30} {col_type:20} {'NULL' if nullable == 'YES' else 'NOT NULL':10} {marker}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_columns()
