"""
Database Structure Inspector
Analyzes current Strapi PostgreSQL database to determine what exists
and what needs to be added for PostGIS geographic support.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import Dict, List, Any

# Database connection from .env
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(**DB_CONFIG)

def check_postgis_installed(cursor) -> Dict[str, Any]:
    """Check if PostGIS extension is installed"""
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM pg_extension WHERE extname = 'postgis'
        ) as installed;
    """)
    result = cursor.fetchone()
    
    if result['installed']:
        cursor.execute("SELECT PostGIS_version();")
        version = cursor.fetchone()
        return {'installed': True, 'version': version[0]}
    return {'installed': False, 'version': None}

def get_all_tables(cursor) -> List[str]:
    """Get all tables in public schema"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    return [row['table_name'] for row in cursor.fetchall()]

def get_table_structure(cursor, table_name: str) -> Dict[str, Any]:
    """Get detailed structure of a table"""
    cursor.execute(f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    
    # Check for indexes
    cursor.execute(f"""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = '{table_name}';
    """)
    indexes = cursor.fetchall()
    
    return {
        'columns': columns,
        'indexes': indexes,
        'row_count': get_row_count(cursor, table_name)
    }

def get_row_count(cursor, table_name: str) -> int:
    """Get approximate row count"""
    try:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
        return cursor.fetchone()['count']
    except Exception as e:
        cursor.connection.rollback()  # Rollback on error
        return 0

def check_geometry_columns(cursor) -> List[Dict[str, Any]]:
    """Check for existing geometry columns (if PostGIS is installed)"""
    try:
        cursor.execute("""
            SELECT 
                f_table_name as table_name,
                f_geometry_column as column_name,
                type,
                srid
            FROM geometry_columns
            WHERE f_table_schema = 'public';
        """)
        return cursor.fetchall()
    except Exception as e:
        cursor.connection.rollback()  # Rollback on error
        return []

def analyze_gtfs_compliance(cursor, tables: List[str]) -> Dict[str, Any]:
    """Analyze GTFS-related tables"""
    gtfs_tables = {
        'routes': False,
        'stops': False,
        'shapes': False,
        'route_shapes': False,
        'trips': False,
        'countries': False
    }
    
    for table in tables:
        if table in gtfs_tables:
            gtfs_tables[table] = True
    
    # Check routes structure
    routes_has_geojson = False
    if 'routes' in tables:
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'routes' 
                AND column_name = 'geojson_data';
            """)
            routes_has_geojson = cursor.fetchone() is not None
        except:
            cursor.connection.rollback()
    
    # Check stops structure
    stops_has_location = False
    if 'stops' in tables:
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'stops' 
                AND column_name IN ('location', 'latitude', 'longitude');
            """)
            stops_has_location = len(cursor.fetchall()) > 0
        except:
            cursor.connection.rollback()
    
    # Check countries structure
    countries_has_code = False
    if 'countries' in tables:
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'countries' 
                AND column_name = 'code';
            """)
            countries_has_code = cursor.fetchone() is not None
        except:
            cursor.connection.rollback()
    
    return {
        'tables_present': gtfs_tables,
        'routes_has_geojson': routes_has_geojson,
        'stops_has_location': stops_has_location,
        'countries_has_code': countries_has_code
    }

def main():
    print("=" * 80)
    print("ArkNet Transit System - Database Structure Analysis")
    print("=" * 80)
    
    try:
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Check PostGIS
        print("\n1. POSTGIS STATUS")
        print("-" * 80)
        postgis = check_postgis_installed(cursor)
        if postgis['installed']:
            print(f"✅ PostGIS INSTALLED: Version {postgis['version']}")
        else:
            print("❌ PostGIS NOT INSTALLED - needs installation")
        
        # 2. List all tables
        print("\n2. EXISTING TABLES")
        print("-" * 80)
        tables = get_all_tables(cursor)
        print(f"Found {len(tables)} tables:\n")
        for table in tables:
            row_count = get_row_count(cursor, table)
            print(f"  • {table:<30} ({row_count:,} rows)")
        
        # 3. Check geometry columns
        print("\n3. GEOMETRY COLUMNS (PostGIS)")
        print("-" * 80)
        geom_cols = check_geometry_columns(cursor)
        if geom_cols:
            for col in geom_cols:
                print(f"  • {col['table_name']}.{col['column_name']} ({col['type']}, SRID: {col['srid']})")
        else:
            print("  ❌ No geometry columns found")
        
        # 4. Analyze GTFS compliance
        print("\n4. GTFS / GEOGRAPHIC DATA ANALYSIS")
        print("-" * 80)
        gtfs = analyze_gtfs_compliance(cursor, tables)
        
        print("\nGTFS Tables:")
        for table, exists in gtfs['tables_present'].items():
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")
        
        print("\nGeographic Data Fields:")
        print(f"  {'✅' if gtfs['routes_has_geojson'] else '❌'} routes.geojson_data")
        print(f"  {'✅' if gtfs['stops_has_location'] else '❌'} stops.location/lat/lon")
        print(f"  {'✅' if gtfs['countries_has_code'] else '❌'} countries.code")
        
        # 5. Detailed structure of key tables
        print("\n5. KEY TABLE STRUCTURES")
        print("-" * 80)
        
        key_tables = ['countries', 'routes', 'stops', 'shapes', 'route_shapes', 'depots']
        for table in key_tables:
            if table in tables:
                print(f"\n{table.upper()}:")
                structure = get_table_structure(cursor, table)
                for col in structure['columns']:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                    print(f"    {col['column_name']:<30} {col['data_type']:<20}{max_len:<10} {nullable}")
        
        # 6. Recommendations
        print("\n" + "=" * 80)
        print("6. RECOMMENDATIONS FOR POSTGIS MIGRATION")
        print("=" * 80)
        
        recommendations = []
        
        if not postgis['installed']:
            recommendations.append("❌ CRITICAL: Install PostGIS extension first!")
            recommendations.append("   Run: CREATE EXTENSION IF NOT EXISTS postgis;")
        
        if not gtfs['routes_has_geojson']:
            recommendations.append("⚠️  routes table missing geojson_data field")
        
        if not gtfs['stops_has_location']:
            recommendations.append("⚠️  stops table missing location/coordinates")
        
        # Check for missing tables needed for spawning
        needed_tables = {
            'pois': 'Points of Interest (amenities, bus stations, etc.)',
            'landuse_zones': 'Land use classifications for spawn density',
            'regions': 'Parishes/regions within countries',
            'spawn_configs': 'Country-specific spawn configurations'
        }
        
        for table, description in needed_tables.items():
            if table not in tables:
                recommendations.append(f"📝 NEW TABLE NEEDED: {table} - {description}")
        
        # Check if existing tables can be enhanced with PostGIS
        if 'stops' in tables and not any(col['column_name'] == 'geometry' for col in get_table_structure(cursor, 'stops')['columns']):
            recommendations.append("🔧 ENHANCE: Add geometry column to 'stops' table for spatial queries")
        
        if 'depots' in tables and not any(col['column_name'] == 'geometry' for col in get_table_structure(cursor, 'depots')['columns']):
            recommendations.append("🔧 ENHANCE: Add geometry column to 'depots' table for spatial queries")
        
        if 'countries' in tables and not any(col['column_name'] == 'geometry' for col in get_table_structure(cursor, 'countries')['columns']):
            recommendations.append("🔧 ENHANCE: Add geometry column to 'countries' for country boundaries")
        
        print("\nActions Required:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        if not recommendations:
            print("✅ Database structure is complete! Ready for PostGIS usage.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
