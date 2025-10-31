"""Quick script to check actual database schema"""
import asyncio
import sys
sys.path.append('geospatial_service')

from services.postgis_client import postgis_client

async def check_schema():
    """Check what columns actually exist"""
    
    tables = ['regions', 'landuse_zones', 'pois', 'highways']
    
    for table in tables:
        print(f"\n{'='*60}")
        print(f"Table: {table}")
        print(f"{'='*60}")
        
        query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """
        
        try:
            result = await postgis_client.execute_query(query)
            if result:
                for row in result:
                    print(f"  {row['column_name']:30} {row['data_type']}")
            else:
                print(f"  No columns found or table doesn't exist")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
